from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.wind.prepro.area.conversion import (
    InputWindPreproAreaConversation,
)
from api_iso_antares.domain.study.root.input.wind.prepro.area.data import (
    InputWindPreproAreaData,
)
from api_iso_antares.domain.study.root.input.wind.prepro.area.k import (
    InputWindPreproAreaK,
)
from api_iso_antares.domain.study.root.input.wind.prepro.area.settings import (
    InputWindPreproAreaSettings,
)
from api_iso_antares.domain.study.root.input.wind.prepro.area.translation import (
    InputWindPreproAreaTranslation,
)


class InputWindPreproArea(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "conversation": InputWindPreproAreaConversation(
                config.next_file("conversation.txt")
            ),
            "data": InputWindPreproAreaData(config.next_file("data.txt")),
            "k": InputWindPreproAreaK(config.next_file("k.txt")),
            "translation": InputWindPreproAreaTranslation(
                config.next_file("translation.txt")
            ),
            "settings": InputWindPreproAreaSettings(
                config.next_file("settings.ini")
            ),
        }
        FolderNode.__init__(self, children)
