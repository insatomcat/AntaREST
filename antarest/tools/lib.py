import json
import logging
import os
import shutil
import time
from abc import ABC, abstractmethod
from zipfile import ZipFile

import requests
from pathlib import Path
from typing import List, Optional, Union, Callable, Set

from requests import Session

from antarest.core.tasks.model import TaskDTO
from antarest.core.utils.utils import StopWatch, get_local_path
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.utils import (
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import CacheConfig, Config, StorageConfig
from antarest.matrixstore.service import (
    SimpleMatrixService,
)
from antarest.study.common.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.variantstudy.variant_command_extractor import (
    VariantCommandsExtractor,
)
from antarest.study.storage.variantstudy.variant_command_generator import (
    VariantCommandGenerator,
)

logger = logging.getLogger(__name__)
COMMAND_FILE = "commands.json"
MATRIX_STORE_DIR = "matrices"


class IVariantGenerator(ABC):
    @abstractmethod
    def apply_commands(
        self, commands: List[CommandDTO], matrices_dir: Path
    ) -> GenerationResultInfoDTO:
        raise NotImplementedError()


class RemoteVariantGenerator(IVariantGenerator):
    def __init__(
        self,
        study_id: str,
        host: Optional[str] = None,
        token: Optional[str] = None,
        session: Optional[Session] = None,
    ):
        self.study_id = study_id
        self.session = session or requests.session()
        # TODO fix this
        self.session.verify = False
        self.host = host
        if session is None and host is None:
            raise ValueError("Missing either session or host")
        if token is not None:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def apply_commands(
        self,
        commands: List[CommandDTO],
        matrices_dir: Path,
    ) -> GenerationResultInfoDTO:
        stopwatch = StopWatch()
        study = self.session.get(
            self.build_url(f"/v1/studies/{self.study_id}")
        ).json()
        assert study is not None

        logger.info("Uploading matrices")
        matrix_dataset: List[str] = []
        for matrix in os.listdir(matrices_dir):
            with open(matrices_dir / matrix, "r") as fh:
                matrix_data = json.load(fh)
                res = self.session.post(
                    self.build_url(f"/v1/matrix"), json=matrix_data
                )
                assert res.status_code == 200
                matrix_id = res.json()
                assert matrix_id == matrix
                matrix_dataset.append(matrix_id)
        # TODO could create a dataset from theses matrices using "variant_<study_id>" as name
        # also the matrix could be named after the command name where they are used
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Matrix upload done in {x}s")
        )

        res = self.session.post(
            self.build_url(f"/v1/studies/{self.study_id}/commands"),
            json=[command.dict() for command in commands],
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Command upload done in {x}s")
        )
        assert res.status_code == 200

        res = self.session.put(
            self.build_url(
                f"/v1/studies/{self.study_id}/generate?denormalize=true"
            )
        )
        assert res.status_code == 200
        task_id = res.json()
        res = self.session.get(
            self.build_url(f"/v1/tasks/{task_id}?wait_for_completion=true")
        )
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Generation done in {x}s")
        )
        assert res.status_code == 200
        task_result = TaskDTO.parse_obj(res.json())
        assert task_result.result is not None
        return GenerationResultInfoDTO.parse_raw(
            task_result.result.return_value or ""
        )

    def build_url(self, url: str) -> str:
        if self.host is not None:
            return f"{self.host.strip('/')}/{url.strip('/')}"
        return url


class LocalVariantGenerator(IVariantGenerator):
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.init_dest_path()

    def apply_commands(
        self, commands: List[CommandDTO], matrices_dir: Path
    ) -> GenerationResultInfoDTO:
        stopwatch = StopWatch()
        matrix_service = SimpleMatrixService(matrices_dir)
        matrix_resolver = UriResolverService(matrix_service)
        study_factory = StudyFactory(
            matrix=matrix_service,
            resolver=matrix_resolver,
            cache=LocalCache(CacheConfig()),
        )
        generator = VariantCommandGenerator(study_factory)
        command_factory = CommandFactory(
            generator_matrix_constants=GeneratorMatrixConstants(
                matrix_service
            ),
            matrix_service=matrix_service,
        )

        command_objs: List[ICommand] = []
        logger.info("Parsing command objects")
        for command_block in commands:
            command_objs.extend(command_factory.to_icommand(command_block))
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Command objects parsed in {x}s")
        )
        result = generator.generate(
            command_objs, self.output_path, delete_on_failure=False
        )
        if result.success:
            logger.info("Building new study tree")
            config, study_tree = study_factory.create_from_fs(
                self.output_path, study_id="", use_cache=False
            )
            logger.info("Denormalizing study")
            stopwatch.reset_current()
            study_tree.denormalize()
            stopwatch.log_elapsed(
                lambda x: logger.info(f"Denormalized done in {x}s")
            )
        return result

    def init_dest_path(self) -> None:
        if not os.listdir(self.output_path):
            version_template = RawStudyService.study_templates[
                RawStudyService.new_default_version
            ]
            empty_study_zip = get_local_path() / "resources" / version_template
            with ZipFile(empty_study_zip) as zip_output:
                zip_output.extractall(path=self.output_path)
                # remove preexisting sets
                (
                    self.output_path / "input" / "areas" / "sets.ini"
                ).write_bytes(b"")


def extract_commands(study_path: Path, commands_output_dir: Path) -> None:
    if not commands_output_dir.exists():
        commands_output_dir.mkdir(parents=True)
    matrices_dir = commands_output_dir / MATRIX_STORE_DIR
    matrices_dir.mkdir()

    matrix_service = SimpleMatrixService(matrices_dir)
    matrix_resolver = UriResolverService(matrix_service)
    study_factory = StudyFactory(
        matrix=matrix_service,
        resolver=matrix_resolver,
        cache=LocalCache(CacheConfig()),
    )

    study_config, study_tree = study_factory.create_from_fs(
        study_path, str(study_path), use_cache=False
    )
    local_matrix_service = SimpleMatrixService(matrices_dir)
    extractor = VariantCommandsExtractor(local_matrix_service)
    command_list = extractor.extract(FileStudy(study_config, study_tree))

    with open(commands_output_dir / COMMAND_FILE, "w") as fh:
        json.dump(
            [command.dict(exclude={"id"}) for command in command_list], fh
        )


def generate_diff(base: Path, variant: Path, output_dir: Path) -> None:
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    matrices_dir = output_dir / MATRIX_STORE_DIR
    matrices_dir.mkdir(exist_ok=True)

    base_command_file = base / COMMAND_FILE
    if not base_command_file.exists():
        raise ValueError(f"Missing {COMMAND_FILE}")
    variant_command_file = variant / COMMAND_FILE
    if not variant_command_file.exists():
        raise ValueError(f"Missing {COMMAND_FILE}")

    stopwatch = StopWatch()
    logger.info("Copying input matrices")
    if (base / MATRIX_STORE_DIR).exists():
        for matrix_file in os.listdir(base / MATRIX_STORE_DIR):
            shutil.copyfile(
                base / MATRIX_STORE_DIR / matrix_file,
                matrices_dir / matrix_file,
            )
    stopwatch.log_elapsed(
        lambda x: logger.info(f"Base input matrix copied in {x}s")
    )
    if (variant / MATRIX_STORE_DIR).exists():
        for matrix_file in os.listdir(variant / MATRIX_STORE_DIR):
            shutil.copyfile(
                variant / MATRIX_STORE_DIR / matrix_file,
                matrices_dir / matrix_file,
            )
    stopwatch.log_elapsed(
        lambda x: logger.info(f"Variant input matrix copied in {x}s")
    )

    local_matrix_service = SimpleMatrixService(matrices_dir)
    extractor = VariantCommandsExtractor(local_matrix_service)
    diff_commands = extractor.diff(
        parse_commands(base_command_file),
        parse_commands(variant_command_file),
    )

    with open(output_dir / COMMAND_FILE, "w") as fh:
        json.dump(
            [
                command.to_dto().dict(exclude={"id"})
                for command in diff_commands
            ],
            fh,
        )
    needed_matrices: Set[str] = set()
    for command in diff_commands:
        for matrix in command.get_inner_matrices():
            needed_matrices.add(matrix)
    for matrix_file in os.listdir(matrices_dir):
        if matrix_file not in needed_matrices:
            os.unlink(matrices_dir / matrix_file)


def parse_commands(file: Path) -> List[CommandDTO]:
    stopwatch = StopWatch()
    logger.info("Parsing commands script")
    with open(file, "r") as fh:
        json_commands = json.load(fh)
    stopwatch.log_elapsed(lambda x: logger.info(f"Script file read in {x}s"))

    commands: List[CommandDTO] = []
    for command in json_commands:
        commands.append(CommandDTO.parse_obj(command))
    stopwatch.log_elapsed(
        lambda x: logger.info(f"Script commands parsed in {x}s")
    )

    return commands


def apply_commands_from_dir(
    command_dir: Path, generator: IVariantGenerator
) -> GenerationResultInfoDTO:
    matrix_dir: Path = command_dir / MATRIX_STORE_DIR
    command_file = command_dir / COMMAND_FILE
    if matrix_dir and not matrix_dir.exists():
        matrix_dir.mkdir()
    if not command_file.exists():
        raise ValueError(f"Missing {COMMAND_FILE}")

    commands = parse_commands(command_file)
    return generator.apply_commands(commands, matrix_dir)


def generate_study(
    input: Path,
    study_id: Optional[str],
    output: Optional[str] = None,
    host: Optional[str] = None,
    token: Optional[str] = None,
) -> GenerationResultInfoDTO:

    if study_id is not None and host is not None:
        generator: IVariantGenerator = RemoteVariantGenerator(
            study_id, host, token
        )
    else:
        assert output is not None
        output_dir = Path(output)
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        generator = LocalVariantGenerator(output_dir)
    return apply_commands_from_dir(input, generator)