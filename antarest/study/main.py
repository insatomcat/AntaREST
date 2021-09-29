from typing import Optional

from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus, DummyEventBusService
from antarest.core.tasks.service import ITaskService
from antarest.login.service import LoginService
from antarest.matrixstore.service import MatrixService
from antarest.study.common.uri_resolver_service import (
    UriResolverService,
)
from antarest.study.repository import (
    StudyMetadataRepository,
)
from antarest.study.service import StudyService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    StudyFactory,
)
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.storage.rawstudy.watcher import Watcher
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.repository import (
    VariantStudyRepository,
)
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)
from antarest.study.web.areas_blueprint import create_study_area_routes
from antarest.study.web.raw_studies_blueprint import create_raw_study_routes
from antarest.study.web.studies_blueprint import create_study_routes
from antarest.study.web.variant_blueprint import create_study_variant_routes


def build_storage(
    application: FastAPI,
    config: Config,
    user_service: LoginService,
    matrix_service: MatrixService,
    cache: ICache,
    task_service: ITaskService,
    metadata_repository: Optional[StudyMetadataRepository] = None,
    variant_repository: Optional[VariantStudyRepository] = None,
    storage_service: Optional[StudyService] = None,
    patch_service: Optional[PatchService] = None,
    generator_matrix_constants: Optional[GeneratorMatrixConstants] = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> StudyService:
    """
    Storage module linking dependencies.

    Args:
        application: flask application
        config: server config
        user_service: user service facade
        matrix_service: matrix store service
        cache: cache service
        task_service: task job service
        metadata_repository: used by testing to inject mock. Let None to use true instantiation
        variant_repository: used by testing to inject mock. Let None to use true instantiation
        storage_service: used by testing to inject mock. Let None to use true instantiation
        patch_service: used by testing to inject mock. Let None to use true instantiation
        generator_matrix_constants: used by testing to inject mock. Let None to use true instantiation
        event_bus: used by testing to inject mock. Let None to use true instantiation

    Returns:

    """

    path_resources = config.resources_path

    resolver = UriResolverService(matrix_service=matrix_service)
    study_factory = StudyFactory(
        matrix=matrix_service, resolver=resolver, cache=cache
    )
    metadata_repository = metadata_repository or StudyMetadataRepository()
    variant_repository = variant_repository or VariantStudyRepository()

    patch_service = patch_service or PatchService()

    raw_study_service = RawStudyService(
        config=config,
        study_factory=study_factory,
        path_resources=path_resources,
        patch_service=patch_service,
        cache=cache,
    )

    generator_matrix_constants = (
        generator_matrix_constants
        or GeneratorMatrixConstants(matrix_service=matrix_service)
    )
    command_factory = CommandFactory(
        generator_matrix_constants=generator_matrix_constants,
        matrix_service=matrix_service,
    )
    variant_study_service = VariantStudyService(
        task_service=task_service,
        cache=cache,
        raw_study_service=raw_study_service,
        command_factory=command_factory,
        study_factory=study_factory,
        repository=variant_repository,
        event_bus=event_bus,
        config=config,
        patch_service=patch_service,
    )

    storage_service = storage_service or StudyService(
        raw_study_service=raw_study_service,
        variant_study_service=variant_study_service,
        user_service=user_service,
        repository=metadata_repository,
        event_bus=event_bus,
        task_service=task_service,
        config=config,
    )

    watcher = Watcher(config=config, service=storage_service)
    watcher.start()

    application.include_router(create_study_routes(storage_service, config))
    application.include_router(
        create_raw_study_routes(storage_service, config)
    )
    application.include_router(
        create_study_area_routes(storage_service, config)
    )
    application.include_router(
        create_study_variant_routes(
            study_service=storage_service,
            variant_study_service=variant_study_service,
            config=config,
        )
    )

    return storage_service