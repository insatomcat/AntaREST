from antarest.storage_api.filesystem.config.model import Config
from antarest.storage_api.filesystem.ini_file_node import IniFileNode
from antarest.storage_api.filesystem.root.settings.generaldata import (
    GeneralData,
)


class OutputSimulationAboutParameters(IniFileNode):
    def __init__(self, config: Config):
        IniFileNode.__init__(self, config, GeneralData.TYPES)
