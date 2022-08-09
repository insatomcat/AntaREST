from typing import List

import pandas as pd  # type:ignore

from antarest.core.exceptions import (
    ShouldNotHappenException,
    BadEditInstructionException,
)
from antarest.matrixstore.business.matrix_editor import (
    MatrixEditor,
    MatrixEditInstructionDTO,
)
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.utils import is_managed
from antarest.study.storage.variantstudy.business.utils import (
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)


class MatrixManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def update_matrix(
        self,
        study: Study,
        path: str,
        edit_instructions: List[MatrixEditInstructionDTO],
    ) -> None:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        matrix_service = (
            self.storage_service.variant_study_service.command_factory.command_context.matrix_service
        )

        matrix_node = file_study.tree.get_node(url=path.split("/"))

        if not isinstance(matrix_node, InputSeriesMatrix):
            raise ShouldNotHappenException()

        matrix_dataframe: pd.DataFrame = matrix_node.parse(
            return_dataframe=True
        )
        for edit_instruction in edit_instructions:
            if edit_instruction.slices:
                matrix_dataframe = (
                    MatrixEditor.update_matrix_content_with_slices(
                        matrix_data=matrix_dataframe,
                        slices=edit_instruction.slices,
                        operation=edit_instruction.operation,
                    )
                )
            elif edit_instruction.coordinates:
                matrix_dataframe = (
                    MatrixEditor.update_matrix_content_with_coordinates(
                        df=matrix_dataframe,
                        coordinates=edit_instruction.coordinates,
                        operation=edit_instruction.operation,
                    )
                )
            else:
                raise BadEditInstructionException(
                    "A matrix edition instruction must contain coordinates or slices"
                )

        new_matrix_id = matrix_service.create(
            matrix_dataframe.to_numpy().tolist()
        )

        command = [
            ReplaceMatrix(
                target=path,
                matrix=strip_matrix_protocol(new_matrix_id),
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
            )
        ]

        execute_or_add_commands(
            study=study,
            file_study=file_study,
            commands=command,
            storage_service=self.storage_service,
        )
        if not is_managed(study):
            matrix_node = file_study.tree.get_node(path.split("/"))
            matrix_node.denormalize()
