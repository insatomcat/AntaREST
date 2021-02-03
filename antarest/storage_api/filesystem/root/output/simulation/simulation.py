from antarest.storage_api.filesystem.config.model import (
    StudyConfig,
    Simulation,
)
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.output.simulation.about.about import (
    OutputSimulationAbout,
)
from antarest.storage_api.filesystem.root.output.simulation.annualSystemCost import (
    OutputSimulationAnnualSystemCost,
)
from antarest.storage_api.filesystem.root.output.simulation.checkIntegrity import (
    OutputSimulationCheckIntegrity,
)
from antarest.storage_api.filesystem.root.output.simulation.mode.economy import (
    OutputSimulationMode,
)
from antarest.storage_api.filesystem.root.output.simulation.info_antares_output import (
    OutputSimulationInfoAntaresOutput,
)
from antarest.storage_api.filesystem.root.output.simulation.simulation_comments import (
    OutputSimulationSimulationComments,
)
from antarest.storage_api.filesystem.root.output.simulation.simulation_log import (
    OutputSimulationSimulationLog,
)
from antarest.storage_api.filesystem.root.output.simulation.ts_numbers.ts_numbers import (
    OutputSimulationTsNumbers,
)


class OutputSimulation(FolderNode):
    def __init__(self, config: StudyConfig, simulation: Simulation):
        FolderNode.__init__(self, config)
        self.simulation = simulation

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "about-the-study": OutputSimulationAbout(
                config.next_file("about-the-study")
            ),
            "ts-numbers": OutputSimulationTsNumbers(
                config.next_file("ts-numbers")
            ),
            "annualSystemCost": OutputSimulationAnnualSystemCost(
                config.next_file("annualSystemCost.txt")
            ),
            "checkIntegrity": OutputSimulationCheckIntegrity(
                config.next_file("checkIntegrity.txt")
            ),
            "simulation-comments": OutputSimulationSimulationComments(
                config.next_file("simulation-comments.txt")
            ),
            "simulation": OutputSimulationSimulationLog(
                config.next_file("simulation.log")
            ),
            "info": OutputSimulationInfoAntaresOutput(
                config.next_file("info.antares-output")
            ),
        }
        if self.simulation.mode == "economy":
            children["economy"] = OutputSimulationMode(
                config.next_file("economy"), self.simulation
            )

        elif self.simulation.mode == "adequacy":
            children["adequacy"] = OutputSimulationMode(
                config.next_file("adequacy"), self.simulation
            )

        return children
