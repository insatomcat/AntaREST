import json
import uuid
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.service import SimpleMatrixService
from antarest.study.business.area_management import AreaCreationDTO, AreaManager, AreaType, AreaUI
from antarest.study.business.link_management import LinkInfoDTO, LinkManager
from antarest.study.model import Patch, PatchArea, PatchCluster, RawStudy, StudyAdditionalData
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    Cluster,
    DistrictSet,
    FileStudyTreeConfig,
    Link,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import with_db_context
from tests.storage.business.assets import ASSETS_DIR


@pytest.fixture(name="empty_study")
def empty_study_fixture(tmp_path: Path) -> FileStudy:
    """
    Fixture for preparing an empty study in the `tmp_path`
    based on the "empty_study_810.zip" asset.

    Args:
        tmp_path: The temporary path provided by pytest.

    Returns:
        An instance of the `FileStudy` class representing the empty study.
    """
    study_id = "5c22caca-b100-47e7-bbea-8b1b97aa26d9"
    study_path = tmp_path.joinpath(study_id)
    study_path.mkdir()
    with ZipFile(ASSETS_DIR / "empty_study_810.zip") as zip_output:
        zip_output.extractall(path=study_path)
    config = build(study_path, study_id)
    return FileStudy(config, FileStudyTree(Mock(), config))


@pytest.fixture(name="matrix_service")
def matrix_service_fixture(tmp_path: Path) -> SimpleMatrixService:
    """
    Fixture for creating a matrix service in the `tmp_path`.

    Args:
        tmp_path: The temporary path provided by pytest.

    Returns:
        An instance of the `SimpleMatrixService` class representing the matrix service.
    """
    matrix_path = tmp_path.joinpath("matrix-store")
    matrix_path.mkdir()
    return SimpleMatrixService(matrix_path)


@with_db_context
def test_area_crud(empty_study: FileStudy, matrix_service: SimpleMatrixService):
    # Prepare the managers that are used in this UT
    raw_study_service = Mock(spec=RawStudyService)
    variant_study_service = Mock(spec=VariantStudyService)
    storage_service = StudyStorageService(raw_study_service, variant_study_service)
    area_manager = AreaManager(
        storage_service=storage_service,
        repository=StudyMetadataRepository(Mock()),
    )
    link_manager = LinkManager(storage_service=storage_service)

    # Check `AreaManager` behaviour with a RAW study
    study_id = str(uuid.uuid4())
    # noinspection PyArgumentList
    study = RawStudy(
        id=study_id,
        path=str(empty_study.config.study_path),
        additional_data=StudyAdditionalData(),
    )
    db.session.add(study)
    db.session.commit()

    raw_study_service.get_raw.return_value = empty_study
    raw_study_service.cache = Mock()
    variant_study_service.command_factory = CommandFactory(
        GeneratorMatrixConstants(matrix_service),
        matrix_service,
        patch_service=Mock(spec=PatchService),
    )
    assert len(empty_study.config.areas.keys()) == 0

    area_manager.create_area(study, AreaCreationDTO(name="test", type=AreaType.AREA))
    assert len(empty_study.config.areas.keys()) == 1
    assert json.loads((empty_study.config.study_path / "patch.json").read_text())["areas"]["test"]["country"] is None

    area_manager.update_area_ui(study, "test", AreaUI(x=100, y=200, color_rgb=(255, 0, 100)))
    assert empty_study.tree.get(["input", "areas", "test", "ui", "ui"]) == {
        "x": 100,
        "y": 200,
        "color_r": 255,
        "color_g": 0,
        "color_b": 100,
        "layers": 0,
    }

    area_manager.create_area(study, AreaCreationDTO(name="test2", type=AreaType.AREA))
    link_manager.create_link(study, LinkInfoDTO(area1="test", area2="test2"))
    assert empty_study.config.areas["test"].links.get("test2") is not None

    link_manager.delete_link(study, "test", "test2")
    assert empty_study.config.areas["test"].links.get("test2") is None
    area_manager.delete_area(study, "test")
    area_manager.delete_area(study, "test2")
    assert len(empty_study.config.areas.keys()) == 0

    # Check `AreaManager` behaviour with a variant study
    variant_id = str(uuid.uuid4())
    # noinspection PyArgumentList
    study = VariantStudy(
        id=variant_id,
        path=str(empty_study.config.study_path),
        additional_data=StudyAdditionalData(),
    )
    variant_study_service.get_raw.return_value = empty_study
    area_manager.create_area(
        study,
        AreaCreationDTO(name="test", type=AreaType.AREA, metadata=PatchArea(country="FR")),
    )
    variant_study_service.append_commands.assert_called_with(
        variant_id,
        [
            CommandDTO(
                action=CommandName.CREATE_AREA.value,
                args={"area_name": "test"},
            )
        ],
        RequestParameters(DEFAULT_ADMIN_USER),
    )
    assert (empty_study.config.study_path / "patch.json").exists()
    assert json.loads((empty_study.config.study_path / "patch.json").read_text())["areas"]["test"]["country"] == "FR"

    area_manager.update_area_ui(study, "test", AreaUI(x=100, y=200, color_rgb=(255, 0, 100)))
    variant_study_service.append_commands.assert_called_with(
        variant_id,
        [
            CommandDTO(
                action=CommandName.UPDATE_CONFIG.value,
                args=[
                    {
                        "target": "input/areas/test/ui/ui/x",
                        "data": "100",
                    },
                    {
                        "target": "input/areas/test/ui/ui/y",
                        "data": "200",
                    },
                    {
                        "target": "input/areas/test/ui/ui/color_r",
                        "data": "255",
                    },
                    {
                        "target": "input/areas/test/ui/ui/color_g",
                        "data": "0",
                    },
                    {
                        "target": "input/areas/test/ui/ui/color_b",
                        "data": "100",
                    },
                    {
                        "target": "input/areas/test/ui/layerX/0",
                        "data": "100",
                    },
                    {
                        "target": "input/areas/test/ui/layerY/0",
                        "data": "200",
                    },
                    {
                        "target": "input/areas/test/ui/layerColor/0",
                        "data": "255 , 0 , 100",
                    },
                ],
            ),
        ],
        RequestParameters(DEFAULT_ADMIN_USER),
    )

    area_manager.create_area(study, AreaCreationDTO(name="test2", type=AreaType.AREA))
    link_manager.create_link(study, LinkInfoDTO(area1="test", area2="test2"))
    variant_study_service.append_commands.assert_called_with(
        variant_id,
        [
            CommandDTO(
                action=CommandName.CREATE_LINK.value,
                args={
                    "area1": "test",
                    "area2": "test2",
                    "parameters": None,
                },
            ),
        ],
        RequestParameters(DEFAULT_ADMIN_USER),
    )
    link_manager.delete_link(study, "test", "test2")
    variant_study_service.append_commands.assert_called_with(
        variant_id,
        [
            CommandDTO(
                action=CommandName.REMOVE_LINK.value,
                args={"area1": "test", "area2": "test2"},
            ),
        ],
        RequestParameters(DEFAULT_ADMIN_USER),
    )
    area_manager.delete_area(study, "test2")
    variant_study_service.append_commands.assert_called_with(
        variant_id,
        [
            CommandDTO(action=CommandName.REMOVE_AREA.value, args={"id": "test2"}),
        ],
        RequestParameters(DEFAULT_ADMIN_USER),
    )


def test_get_all_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(
        storage_service=StudyStorageService(raw_study_service, Mock()),
        repository=Mock(spec=StudyMetadataRepository),
    )
    link_manager = LinkManager(storage_service=StudyStorageService(raw_study_service, Mock()))

    study = RawStudy()
    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={
            "a1": Area(
                name="a1",
                links={
                    "a2": Link(filters_synthesis=[], filters_year=[]),
                    "a3": Link(filters_synthesis=[], filters_year=[]),
                },
                thermals=[Cluster(id="a", name="a", enabled=True)],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "a2": Area(
                name="a2",
                links={"a3": Link(filters_synthesis=[], filters_year=[])},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "a3": Area(
                name="a3",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
        },
        sets={"s1": DistrictSet(areas=["a1"])},
    )
    file_tree_mock = Mock(spec=FileStudyTree, context=Mock(), config=config)
    raw_study_service.get_raw.return_value = FileStudy(config=config, tree=file_tree_mock)

    area_manager.patch_service = Mock()
    area_manager.patch_service.get.return_value = Patch(
        areas={"a1": PatchArea(country="fr")},
        thermal_clusters={"a1.a": PatchCluster.parse_obj({"code-oi": "1"})},
    )
    file_tree_mock.get.side_effect = [
        {
            "a": {
                "name": "A",
                "unitcount": 1,
                "nominalcapacity": 500,
                "min-stable-power": 200,
            }
        },
        {},
        {},
    ]

    expected_areas = [
        {
            "name": "a1",
            "type": AreaType.AREA,
            "metadata": {"country": "fr", "tags": []},
            "set": None,
            "thermals": [
                {
                    "id": "a",
                    "name": "A",
                    "enabled": True,
                    "unitcount": 1,
                    "nominalcapacity": 500,
                    "group": None,
                    "min_stable_power": 200,
                    "min_up_time": None,
                    "min_down_time": None,
                    "spinning": None,
                    "marginal_cost": None,
                    "spread_cost": None,
                    "market_bid_cost": None,
                    "type": None,
                    "code_oi": "1",
                }
            ],
            "id": "a1",
        },
        {
            "name": "a2",
            "type": AreaType.AREA,
            "metadata": {"country": None, "tags": []},
            "set": None,
            "thermals": [],
            "id": "a2",
        },
        {
            "name": "a3",
            "type": AreaType.AREA,
            "metadata": {"country": None, "tags": []},
            "set": None,
            "thermals": [],
            "id": "a3",
        },
    ]
    areas = area_manager.get_all_areas(study, AreaType.AREA)
    assert expected_areas == [area.dict() for area in areas]

    expected_clusters = [
        {
            "name": "s1",
            "type": AreaType.DISTRICT,
            "metadata": {"country": None, "tags": []},
            "set": ["a1"],
            "thermals": None,
            "id": "s1",
        }
    ]
    clusters = area_manager.get_all_areas(study, AreaType.DISTRICT)
    assert expected_clusters == [area.dict() for area in clusters]

    file_tree_mock.get.side_effect = [{}, {}, {}]
    expected_all = [
        {
            "name": "a1",
            "type": AreaType.AREA,
            "metadata": {"country": "fr", "tags": []},
            "set": None,
            "thermals": [],
            "id": "a1",
        },
        {
            "name": "a2",
            "type": AreaType.AREA,
            "metadata": {"country": None, "tags": []},
            "set": None,
            "thermals": [],
            "id": "a2",
        },
        {
            "name": "a3",
            "type": AreaType.AREA,
            "metadata": {"country": None, "tags": []},
            "set": None,
            "thermals": [],
            "id": "a3",
        },
        {
            "name": "s1",
            "type": AreaType.DISTRICT,
            "metadata": {"country": None, "tags": []},
            "set": ["a1"],
            "thermals": None,
            "id": "s1",
        },
    ]
    all_areas = area_manager.get_all_areas(study)
    assert expected_all == [area.dict() for area in all_areas]

    links = link_manager.get_all_links(study)
    assert [
        {"area1": "a1", "area2": "a2", "ui": None},
        {"area1": "a1", "area2": "a3", "ui": None},
        {"area1": "a2", "area2": "a3", "ui": None},
    ] == [link.dict() for link in links]


def test_update_area():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(
        storage_service=StudyStorageService(raw_study_service, Mock()),
        repository=Mock(spec=StudyMetadataRepository),
    )

    study = RawStudy()
    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={
            "a1": Area(
                name="a1",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
            "a2": Area(
                name="a2",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            ),
        },
        sets={"s1": DistrictSet(areas=["a1"])},
    )
    raw_study_service.get_raw.return_value = FileStudy(config=config, tree=FileStudyTree(context=Mock(), config=config))

    area_manager.patch_service = Mock()
    area_manager.patch_service.get.return_value = Patch(areas={"a1": PatchArea(country="fr")})

    new_area_info = area_manager.update_area_metadata(study, "a1", PatchArea(country="fr"))
    assert new_area_info.id == "a1"
    assert new_area_info.metadata == {"country": "fr", "tags": []}


def test_update_clusters():
    raw_study_service = Mock(spec=RawStudyService)
    area_manager = AreaManager(
        storage_service=StudyStorageService(raw_study_service, Mock()),
        repository=Mock(spec=StudyMetadataRepository),
    )

    study = RawStudy()
    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={
            "a1": Area(
                name="a1",
                links={},
                thermals=[Cluster(id="a", name="a", enabled=True)],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            )
        },
    )
    file_tree_mock = Mock(spec=FileStudyTree, context=Mock(), config=config)
    raw_study_service.get_raw.return_value = FileStudy(config=config, tree=file_tree_mock)

    area_manager.patch_service = Mock()
    area_manager.patch_service.get.return_value = Patch(
        areas={"a1": PatchArea(country="fr")},
        thermal_clusters={"a1.a": PatchCluster.parse_obj({"code-oi": "1"})},
    )
    file_tree_mock.get.side_effect = [
        {
            "a": {
                "name": "A",
                "unitcount": 1,
                "nominalcapacity": 500,
                "min-stable-power": 200,
            }
        }
    ]

    new_area_info = area_manager.update_thermal_cluster_metadata(study, "a1", {"a": PatchCluster(type="a")})
    assert len(new_area_info.thermals) == 1
    assert new_area_info.thermals[0].type == "a"
    assert new_area_info.thermals[0].code_oi is None
