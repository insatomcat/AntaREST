import logging
from typing import List, Optional, cast, Union

import numpy as np
import pandas as pd  # type: ignore

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode
from antarest.study.storage.rawstudy.model.filesystem.matrix.date_serializer import (
    IDateMatrixSerializer,
    FactoryDateSerializer,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.head_writer import (
    HeadWriter,
    LinkHeadWriter,
    AreaHeadWriter,
)

logger = logging.getLogger(__name__)


class OutputSeriesMatrix(
    LazyNode[Union[bytes, JSON], Union[bytes, JSON], JSON]
):
    """
    Generic node to handle output matrix behavior.
    Node needs a DateSerializer and a HeadWriter to work
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        date_serializer: IDateMatrixSerializer,
        head_writer: HeadWriter,
        freq: str,
    ):
        super().__init__(context=context, config=config)
        self.date_serializer = date_serializer
        self.head_writer = head_writer

    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"matrixfile://{self.config.path.name}"

    def parse(
        self,
    ) -> JSON:
        df = pd.read_csv(
            self.config.path,
            sep="\t",
            skiprows=4,
            na_values="N/A",
            float_precision="legacy",
        )

        date, body = self.date_serializer.extract_date(df)

        header = body.iloc[:2]
        header.fillna("", inplace=True)
        header = np.array(
            [header.columns, header.iloc[0], header.iloc[1]]
        ).tolist()

        matrix = body.iloc[2:].astype(float)
        matrix = matrix.where(pd.notna(matrix), None)
        matrix.index = date
        matrix.columns = header

        return cast(JSON, matrix.to_dict(orient="split"))

    def _dump_json(self, data: JSON) -> None:
        df = pd.DataFrame(**data)

        headers = pd.DataFrame(df.columns.values.tolist()).T
        matrix = pd.concat([headers, pd.DataFrame(df.values)], axis=0)

        time = self.date_serializer.build_date(df.index)
        matrix.index = time.index

        matrix = pd.concat([time, matrix], axis=1)

        head = self.head_writer.build(var=df.columns.size, end=df.index.size)
        self.config.path.write_text(head)

        matrix.to_csv(
            open(self.config.path, "a", newline="\n"),
            sep="\t",
            index=False,
            header=False,
            line_terminator="\n",
        )

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        self._assert_url_end(url)

        errors = []
        if not self.config.path.exists():
            errors.append(
                f"Output Series Matrix f{self.config.path} not exists"
            )
        return errors

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> Union[bytes, JSON]:
        if not formatted:
            if self.config.path.exists():
                return self.config.path.read_bytes()

            logger.warning(f"Missing file {self.config.path}")
            return b""

        return self.parse()

    def dump(
        self, data: Union[bytes, JSON], url: Optional[List[str]] = None
    ) -> None:
        if isinstance(data, bytes):
            self.config.path.parent.mkdir(exist_ok=True, parents=True)
            self.config.path.write_bytes(data)
        else:
            self._dump_json(data)

    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node


class LinkOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: str,
        src: str,
        dest: str,
    ):
        super(LinkOutputSeriesMatrix, self).__init__(
            context=context,
            config=config,
            date_serializer=FactoryDateSerializer.create(freq, src),
            head_writer=LinkHeadWriter(src, dest, freq),
            freq=freq,
        )


class AreaOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: str,
        area: str,
    ):
        super(AreaOutputSeriesMatrix, self).__init__(
            context,
            config=config,
            date_serializer=FactoryDateSerializer.create(freq, area),
            head_writer=AreaHeadWriter(area, freq),
            freq=freq,
        )
