from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputLinkAreaLink(InputSeriesMatrix):
    def __init__(self, context: ContextServer, config: StudyConfig):
        super(InputLinkAreaLink, self).__init__(context, config, nb_columns=8)
