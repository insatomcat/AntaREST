from typing import Dict, Any, Union, List, Optional

from antarest.core.custom_types import JSON, SUB_JSON
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)


class UpdateConfig(ICommand):
    target: str
    data: Union[str, int, float, bool, JSON]

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_CONFIG, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        url = self.target.split("/")
        tree_node = study_data.tree.get_node(url)
        if not isinstance(tree_node, IniFileNode):
            return CommandOutput(
                status=False,
                message=f"Study node at path {self.target} is invalid",
            )

        study_data.tree.save(self.data, url)
        return CommandOutput(status=True, message="ok")

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_CONFIG.value,
            args={
                "target": self.target,
                "data": self.data,
            },
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.target
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, UpdateConfig):
            return False
        simple_match = self.target == other.target
        if not equal:
            return simple_match
        return simple_match and self.data == other.data

    def revert(
        self, history: List["ICommand"], base: Optional[FileStudy] = None
    ) -> List["ICommand"]:
        for command in reversed(history):
            if (
                isinstance(command, UpdateConfig)
                and command.target == self.target
            ):
                return [command]
        if base is not None:
            from antarest.study.storage.variantstudy.model.command.utils_extractor import (
                CommandExtraction,
            )

            return [
                (
                    self.command_context.command_extractor
                    or CommandExtraction(self.command_context.matrix_service)
                ).generate_update_config(base.tree, self.target.split("/"))
            ]
        return []

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> List[str]:
        return []