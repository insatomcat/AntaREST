import logging
from pathlib import Path
from typing import Callable, Dict, List

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.variantstudy.business.utils import (
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import (
    CreateRenewablesCluster,
)
from antarest.study.storage.variantstudy.model.command.create_st_storage import (
    CreateSTStorage,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.remove_binding_constraint import (
    RemoveBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.remove_cluster import (
    RemoveCluster,
)
from antarest.study.storage.variantstudy.model.command.remove_district import (
    RemoveDistrict,
)
from antarest.study.storage.variantstudy.model.command.remove_link import (
    RemoveLink,
)
from antarest.study.storage.variantstudy.model.command.remove_renewables_cluster import (
    RemoveRenewablesCluster,
)
from antarest.study.storage.variantstudy.model.command.remove_st_storage import (
    RemoveSTStorage,
)
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import (
    UpdateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.update_comments import (
    UpdateComments,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command.update_district import (
    UpdateDistrict,
)
from antarest.study.storage.variantstudy.model.command.update_playlist import (
    UpdatePlaylist,
)
from antarest.study.storage.variantstudy.model.command.update_raw_file import (
    UpdateRawFile,
)
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import (
    UpdateScenarioBuilder,
)

logger = logging.getLogger(__name__)


class CommandReverter:
    def __init__(self) -> None:
        self.method_dict: Dict[
            CommandName,
            Callable[[ICommand, List[ICommand], FileStudy], List[ICommand]],
        ] = {
            command_name: getattr(self, f"_revert_{command_name.value}")
            for command_name in CommandName
        }

    @staticmethod
    def _revert_create_area(
        base_command: CreateArea, history: List["ICommand"], base: FileStudy
    ) -> List[ICommand]:
        area_id = transform_name_to_id(base_command.area_name)
        return [
            RemoveArea(
                id=area_id, command_context=base_command.command_context
            )
        ]

    @staticmethod
    def _revert_remove_area(
        base_command: RemoveArea, history: List["ICommand"], base: FileStudy
    ) -> List[ICommand]:
        raise NotImplementedError(
            "The revert function for RemoveArea is not available"
        )

    @staticmethod
    def _revert_create_district(
        base_command: CreateDistrict,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        district_id = transform_name_to_id(base_command.name)
        return [
            RemoveDistrict(
                id=district_id, command_context=base_command.command_context
            )
        ]

    @staticmethod
    def _revert_remove_district(
        base_command: RemoveDistrict,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        raise NotImplementedError(
            "The revert function for RemoveDistrict is not available"
        )

    @staticmethod
    def _revert_create_link(
        base_command: CreateLink, history: List["ICommand"], base: FileStudy
    ) -> List[ICommand]:
        return [
            RemoveLink(
                area1=base_command.area1,
                area2=base_command.area2,
                command_context=base_command.command_context,
            )
        ]

    @staticmethod
    def _revert_remove_link(
        base_command: RemoveLink, history: List["ICommand"], base: FileStudy
    ) -> List[ICommand]:
        raise NotImplementedError(
            "The revert function for RemoveLink is not available"
        )

    @staticmethod
    def _revert_create_binding_constraint(
        base_command: CreateBindingConstraint,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        bind_id = transform_name_to_id(base_command.name)
        return [
            RemoveBindingConstraint(
                id=bind_id, command_context=base_command.command_context
            )
        ]

    @staticmethod
    def _revert_update_binding_constraint(
        base_command: UpdateBindingConstraint,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        for command in reversed(history):
            if (
                isinstance(command, UpdateBindingConstraint)
                and command.id == base_command.id
            ):
                return [command]
            elif (
                isinstance(command, CreateBindingConstraint)
                and transform_name_to_id(command.name) == base_command.id
            ):
                return [
                    UpdateBindingConstraint(
                        id=base_command.id,
                        enabled=command.enabled,
                        time_step=command.time_step,
                        operator=command.operator,
                        coeffs=command.coeffs,
                        values=strip_matrix_protocol(command.values),
                        filter_year_by_year=command.filter_year_by_year,
                        filter_synthesis=command.filter_synthesis,
                        comments=command.comments,
                        command_context=command.command_context,
                    )
                ]

        return base_command.get_command_extractor().extract_binding_constraint(
            base, base_command.id
        )

    @staticmethod
    def _revert_remove_binding_constraint(
        base_command: RemoveBindingConstraint,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        raise NotImplementedError(
            "The revert function for RemoveBindingConstraint is not available"
        )

    @staticmethod
    def _revert_update_scenario_builder(
        base_command: UpdateScenarioBuilder,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        # todo make the diff between base study scenariobuilder data and base_command
        raise NotImplementedError(
            "The revert function for UpdateScenarioBuilder is not available"
        )

    @staticmethod
    def _revert_create_cluster(
        base_command: CreateCluster, history: List["ICommand"], base: FileStudy
    ) -> List[ICommand]:
        cluster_id = transform_name_to_id(base_command.cluster_name)
        return [
            RemoveCluster(
                area_id=base_command.area_id,
                cluster_id=cluster_id,
                command_context=base_command.command_context,
            )
        ]

    @staticmethod
    def _revert_remove_cluster(
        base_command: RemoveCluster, history: List["ICommand"], base: FileStudy
    ) -> List[ICommand]:
        raise NotImplementedError(
            "The revert function for RemoveCluster is not available"
        )

    @staticmethod
    def _revert_create_renewables_cluster(
        base_command: CreateRenewablesCluster,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        cluster_id = transform_name_to_id(base_command.cluster_name)
        return [
            RemoveRenewablesCluster(
                area_id=base_command.area_id,
                cluster_id=cluster_id,
                command_context=base_command.command_context,
            )
        ]

    @staticmethod
    def _revert_remove_renewables_cluster(
        base_command: RemoveRenewablesCluster,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        raise NotImplementedError(
            "The revert function for RemoveRenewablesCluster is not available"
        )

    @staticmethod
    def _revert_create_st_storage(
        base_command: CreateSTStorage,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        storage_id = base_command.parameters.id
        return [
            RemoveSTStorage(
                area_id=base_command.area_id,
                storage_id=storage_id,
                command_context=base_command.command_context,
            )
        ]

    @staticmethod
    def _revert_remove_st_storage(
        base_command: RemoveSTStorage,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        raise NotImplementedError(
            "The revert function for RemoveSTStorage is not available"
        )

    @staticmethod
    def _revert_replace_matrix(
        base_command: ReplaceMatrix, history: List["ICommand"], base: FileStudy
    ) -> List[ICommand]:
        for command in reversed(history):
            if (
                isinstance(command, ReplaceMatrix)
                and command.target == base_command.target
            ):
                return [command]

        try:
            return [
                base_command.get_command_extractor().generate_replace_matrix(
                    base.tree, base_command.target.split("/")
                )
            ]
        except ChildNotFoundError:
            return (
                []
            )  # if the matrix does not exist, there is nothing to revert

    @staticmethod
    def _revert_update_config(
        base_command: UpdateConfig, history: List["ICommand"], base: FileStudy
    ) -> List[ICommand]:
        update_config_list: List[UpdateConfig] = []
        self_target_path = Path(base_command.target)
        parent_path: Path = Path("../model/command")
        for command in reversed(history):
            if isinstance(command, UpdateConfig):
                # adding all the UpdateConfig commands until we find one containing self (or the end)
                update_config_list.append(command)
                if command.target == base_command.target:
                    return [command]
                elif Path(command.target) in self_target_path.parents:
                    # found the last parent command.
                    parent_path = Path(command.target)
                    break

        output_list: List[ICommand] = [
            command
            for command in update_config_list[::-1]
            if parent_path in Path(command.target).parents
            or str(parent_path) == command.target
        ]

        if output_list:
            return output_list

        try:
            return [
                base_command.get_command_extractor().generate_update_config(
                    base.tree, base_command.target.split("/")
                )
            ]
        except ChildNotFoundError as e:
            logger.warning(
                f"Failed to extract revert command for update_config {base_command.target}",
                exc_info=e,
            )
            return []

    @staticmethod
    def _revert_update_comments(
        base_command: UpdateComments,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        for command in reversed(history):
            if isinstance(command, UpdateComments):
                return [command]

        try:
            return [
                base_command.get_command_extractor().generate_update_comments(
                    base.tree
                )
            ]
        except ChildNotFoundError:
            return []  # if the file does not exist, there is nothing to revert

    @staticmethod
    def _revert_update_playlist(
        base_command: UpdatePlaylist,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        for command in reversed(history):
            if isinstance(command, UpdatePlaylist):
                return [command]

        try:
            return [
                base_command.get_command_extractor().generate_update_playlist(
                    base.tree
                )
            ]
        except ChildNotFoundError:
            return []  # if the file does not exist, there is nothing to revert

    @staticmethod
    def _revert_update_file(
        base_command: UpdateRawFile, history: List["ICommand"], base: FileStudy
    ) -> List[ICommand]:
        for command in reversed(history):
            if (
                isinstance(command, UpdateRawFile)
                and command.target == base_command.target
            ):
                return [command]

        return [
            base_command.get_command_extractor().generate_update_rawfile(
                base.tree, base_command.target.split("/")
            )
        ]

    @staticmethod
    def _revert_update_district(
        base_command: UpdateDistrict,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        for command in reversed(history):
            if (
                isinstance(command, UpdateDistrict)
                and command.id == base_command.id
            ):
                return [command]
            elif (
                isinstance(command, CreateDistrict)
                and transform_name_to_id(command.name) == base_command.id
            ):
                return [command]

        return [
            base_command.get_command_extractor().generate_update_district(
                base, base_command.id
            )
        ]

    def revert(
        self,
        base_command: ICommand,
        history: List["ICommand"],
        base: FileStudy,
    ) -> List[ICommand]:
        """
        Generate a list of commands to revert the given command.

        Args:
            base_command: The command to revert.
            history: The history of commands.
            base: The base study.

        Returns:
            A list of commands to revert the given command.
        """

        return self.method_dict[base_command.command_name](
            base_command, history, base
        )
