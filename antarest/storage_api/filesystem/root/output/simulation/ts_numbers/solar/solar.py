from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.output.simulation.ts_numbers.solar.area import (
    OutputSimulationTsNumbersSolarArea,
)


class OutputSimulationTsNumbersSolar(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            area: OutputSimulationTsNumbersSolarArea(
                config.next_file(area + ".txt")
            )
            for area in config.area_names()
        }
        return children
