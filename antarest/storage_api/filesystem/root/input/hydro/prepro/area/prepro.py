from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.ini_file_node import IniFileNode


class InputHydroPreproAreaPrepro(IniFileNode):
    def __init__(self, config: StudyConfig):
        types = {"prepro": {"intermonthly-correlation": float}}
        IniFileNode.__init__(self, config, types)
