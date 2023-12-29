import datetime
import io
import re
import uuid
from typing import Any, MutableMapping, Sequence, cast
from unittest.mock import Mock

import numpy as np
import pytest
from pydantic import ValidationError
from sqlalchemy.orm.session import Session  # type: ignore

from antarest.core.exceptions import (
    STStorageConfigNotFoundError,
    STStorageFieldsNotFoundError,
    STStorageMatrixNotFoundError,
)
from antarest.core.model import PublicMode
from antarest.login.model import Group, User
from antarest.study.business.areas.st_storage_management import STStorageManager
from antarest.study.model import RawStudy, Study, StudyContentStatus
from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import STStorageGroup
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

# noinspection SpellCheckingInspection
LIST_INI = """
[storage1]
name = Storage1
group = Battery
injectionnominalcapacity = 1500
withdrawalnominalcapacity = 1500
reservoircapacity = 20000
efficiency = 0.94
initialleveloptim = true

[storage2]
name = Storage2
group = PSP_closed
injectionnominalcapacity = 2000
withdrawalnominalcapacity = 1500
reservoircapacity = 20000
efficiency = 0.78
initiallevel = 0.5

[storage3]
name = Storage3
group = PSP_closed
injectionnominalcapacity = 1500
withdrawalnominalcapacity = 1500
reservoircapacity = 21000
efficiency = 0.72
initiallevel = 1
"""

LIST_CFG = IniReader().read(io.StringIO(LIST_INI))


class TestSTStorageManager:
    @pytest.fixture(name="study_storage_service")
    def study_storage_service(self) -> StudyStorageService:
        """Return a mocked StudyStorageService."""
        return Mock(
            spec=StudyStorageService,
            variant_study_service=Mock(
                spec=VariantStudyService,
                command_factory=Mock(
                    spec=CommandFactory,
                    command_context=Mock(spec=CommandContext),
                ),
            ),
            get_storage=Mock(return_value=Mock(spec=RawStudyService, get_raw=Mock(spec=FileStudy))),
        )

    # noinspection PyArgumentList
    @pytest.fixture(name="study_uuid")
    def study_uuid_fixture(self, db_session: Session) -> str:
        user = User(id=0, name="admin")
        group = Group(id="my-group", name="group")
        raw_study = RawStudy(
            id=str(uuid.uuid4()),
            name="Dummy",
            version="850",
            author="John Smith",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            workspace="default",
            path="/path/to/study",
            content_status=StudyContentStatus.WARNING,
        )
        db_session.add(raw_study)
        db_session.commit()
        return cast(str, raw_study.id)

    def test_get_st_storages__nominal_case(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        This unit test is to verify the behavior of the `get_storages`
        method in the `STStorageManager` class under nominal conditions.
        It checks whether the method returns the expected storage list
        based on a specific configuration.
        """
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=LIST_CFG),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # run
        groups = manager.get_storages(study, area_id="West")

        # Check
        actual = [form.dict(by_alias=True) for form in groups]
        expected = [
            {
                "efficiency": 0.94,
                "group": STStorageGroup.BATTERY,
                "id": "storage1",
                "initialLevel": 0.5,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 1500.0,
                "name": "Storage1",
                "reservoirCapacity": 20000.0,
                "withdrawalNominalCapacity": 1500.0,
            },
            {
                "efficiency": 0.78,
                "group": STStorageGroup.PSP_CLOSED,
                "id": "storage2",
                "initialLevel": 0.5,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 2000.0,
                "name": "Storage2",
                "reservoirCapacity": 20000.0,
                "withdrawalNominalCapacity": 1500.0,
            },
            {
                "efficiency": 0.72,
                "group": STStorageGroup.PSP_CLOSED,
                "id": "storage3",
                "initialLevel": 1,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 1500.0,
                "name": "Storage3",
                "reservoirCapacity": 21000.0,
                "withdrawalNominalCapacity": 1500.0,
            },
        ]
        assert actual == expected

    def test_get_st_storages__config_not_found(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        This test verifies that when the `get_storages` method is called
        with a study and area ID, and the corresponding configuration is not found
        (indicated by the `KeyError` raised by the mock), it correctly
        raises the `STStorageConfigNotFoundError` exception with the expected error
        message containing the study ID and area ID.
        """
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(side_effect=KeyError("Oops!")),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # run
        with pytest.raises(STStorageConfigNotFoundError, match="not found") as ctx:
            manager.get_storages(study, area_id="West")

        # ensure the error message contains at least the study ID and area ID
        err_msg = str(ctx.value)
        assert "West" in err_msg

    def test_get_st_storage__nominal_case(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        Test the `get_st_storage` method of the `STStorageManager` class under nominal conditions.

        This test verifies that the `get_st_storage` method returns the expected storage fields
        for a specific study, area, and storage ID combination.

        Args:
            db_session: A database session fixture.
            study_storage_service: A study storage service fixture.
            study_uuid: The UUID of the study to be tested.
        """

        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=LIST_CFG["storage1"]),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # Run the method being tested
        edit_form = manager.get_storage(study, area_id="West", storage_id="storage1")

        # Assert that the returned storage fields match the expected fields
        actual = edit_form.dict(by_alias=True)
        expected = {
            "efficiency": 0.94,
            "group": STStorageGroup.BATTERY,
            "id": "storage1",
            "initialLevel": 0.5,
            "initialLevelOptim": True,
            "injectionNominalCapacity": 1500.0,
            "name": "Storage1",
            "reservoirCapacity": 20000.0,
            "withdrawalNominalCapacity": 1500.0,
        }
        assert actual == expected

    def test_get_st_storage__config_not_found(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        Test the `get_st_storage` method of the `STStorageManager` class when the configuration is not found.

        This test verifies that the `get_st_storage` method raises an `STStorageFieldsNotFoundError`
        exception when the configuration for the provided study, area, and storage ID combination is not found.

        Args:
            db_session: A database session fixture.
            study_storage_service: A study storage service fixture.
            study_uuid: The UUID of the study to be tested.
        """

        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(side_effect=KeyError("Oops!")),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # Run the method being tested and expect an exception
        with pytest.raises(STStorageFieldsNotFoundError, match="not found") as ctx:
            manager.get_storage(study, area_id="West", storage_id="storage1")
        # ensure the error message contains at least the study ID, area ID and storage ID
        err_msg = str(ctx.value)
        assert "storage1" in err_msg

    def test_get_matrix__nominal_case(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        Test the `get_matrix` method of the `STStorageManager` class under nominal conditions.

        This test verifies that the `get_matrix` method returns the expected storage matrix
        for a specific study, area, storage ID, and Time Series combination.

        Args:
            db_session: A database session fixture.
            study_storage_service: A study storage service fixture.
            study_uuid: The UUID of the study to be tested.
        """

        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        array = np.random.rand(8760, 1) * 1000
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(
                return_value={
                    "index": list(range(8760)),
                    "columns": [0],
                    "data": array.tolist(),
                }
            ),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # Run the method being tested
        matrix = manager.get_matrix(study, area_id="West", storage_id="storage1", ts_name="inflows")

        # Assert that the returned storage fields match the expected fields
        actual = matrix.dict(by_alias=True)
        assert actual == matrix

    def test_get_matrix__config_not_found(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        Test the `get_matrix` method of the `STStorageManager` class when the time series is not found.

        This test verifies that the `get_matrix` method raises an `STStorageFieldsNotFoundError`
        exception when the configuration for the provided study, area, time series,
        and storage ID combination is not found.

        Args:
            db_session: A database session fixture.
            study_storage_service: A study storage service fixture.
            study_uuid: The UUID of the study to be tested.
        """

        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(side_effect=KeyError("Oops!")),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # Run the method being tested and expect an exception
        with pytest.raises(STStorageMatrixNotFoundError, match="not found") as ctx:
            manager.get_matrix(study, area_id="West", storage_id="storage1", ts_name="inflows")
        # ensure the error message contains at least the study ID, area ID and storage ID
        err_msg = str(ctx.value)
        assert "storage1" in err_msg
        assert "inflows" in err_msg

    def test_get_matrix__invalid_matrix(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        """
        Test the `get_matrix` method of the `STStorageManager` class when the time series is not found.

        This test verifies that the `get_matrix` method raises an `STStorageFieldsNotFoundError`
        exception when the configuration for the provided study, area, time series,
        and storage ID combination is not found.

        Args:
            db_session: A database session fixture.
            study_storage_service: A study storage service fixture.
            study_uuid: The UUID of the study to be tested.
        """

        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # Prepare the mocks
        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        array = np.random.rand(365, 1) * 1000
        matrix = {
            "index": list(range(365)),
            "columns": [0],
            "data": array.tolist(),
        }
        file_study.tree = Mock(
            spec=FileStudyTree,
            get=Mock(return_value=matrix),
        )

        # Given the following arguments
        manager = STStorageManager(study_storage_service)

        # Run the method being tested and expect an exception
        with pytest.raises(
            ValidationError,
            match=re.escape("time series must have shape (8760, 1)"),
        ):
            manager.get_matrix(study, area_id="West", storage_id="storage1", ts_name="inflows")

    # noinspection SpellCheckingInspection
    def test_validate_matrices__nominal(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # prepare some random matrices, insuring `lower_rule_curve` <= `upper_rule_curve`
        matrices = {
            "pmax_injection": np.random.rand(8760, 1),
            "pmax_withdrawal": np.random.rand(8760, 1),
            "lower_rule_curve": np.random.rand(8760, 1) / 2,
            "upper_rule_curve": np.random.rand(8760, 1) / 2 + 0.5,
            "inflows": np.random.rand(8760, 1) * 1000,
        }

        # Prepare the mocks
        def tree_get(url: Sequence[str], **_: Any) -> MutableMapping[str, Any]:
            name = url[-1]
            array = matrices[name]
            return {
                "index": list(range(array.shape[0])),
                "columns": list(range(array.shape[1])),
                "data": array.tolist(),
            }

        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(spec=FileStudyTree, get=tree_get)

        # Given the following arguments, the validation shouldn't raise any exception
        manager = STStorageManager(study_storage_service)
        assert manager.validate_matrices(study, area_id="West", storage_id="storage1")

    # noinspection SpellCheckingInspection
    def test_validate_matrices__out_of_bound(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # prepare some random matrices, insuring `lower_rule_curve` <= `upper_rule_curve`
        matrices = {
            "pmax_injection": np.random.rand(8760, 1) * 2 - 0.5,  # out of bound
            "pmax_withdrawal": np.random.rand(8760, 1) * 2 - 0.5,  # out of bound
            "lower_rule_curve": np.random.rand(8760, 1) * 2 - 0.5,  # out of bound
            "upper_rule_curve": np.random.rand(8760, 1) * 2 - 0.5,  # out of bound
            "inflows": np.random.rand(8760, 1) * 1000,
        }

        # Prepare the mocks
        def tree_get(url: Sequence[str], **_: Any) -> MutableMapping[str, Any]:
            name = url[-1]
            array = matrices[name]
            return {
                "index": list(range(array.shape[0])),
                "columns": list(range(array.shape[1])),
                "data": array.tolist(),
            }

        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(spec=FileStudyTree, get=tree_get)

        # Given the following arguments, the validation shouldn't raise any exception
        manager = STStorageManager(study_storage_service)

        # Run the method being tested and expect an exception
        with pytest.raises(
            ValidationError,
            match=re.escape("4 validation errors"),
        ) as ctx:
            manager.validate_matrices(study, area_id="West", storage_id="storage1")
        errors = ctx.value.errors()
        assert errors == [
            {
                "loc": ("pmax_injection",),
                "msg": "Matrix values should be between 0 and 1",
                "type": "value_error",
            },
            {
                "loc": ("pmax_withdrawal",),
                "msg": "Matrix values should be between 0 and 1",
                "type": "value_error",
            },
            {
                "loc": ("lower_rule_curve",),
                "msg": "Matrix values should be between 0 and 1",
                "type": "value_error",
            },
            {
                "loc": ("upper_rule_curve",),
                "msg": "Matrix values should be between 0 and 1",
                "type": "value_error",
            },
        ]

    # noinspection SpellCheckingInspection
    def test_validate_matrices__rule_curve(
        self,
        db_session: Session,
        study_storage_service: StudyStorageService,
        study_uuid: str,
    ) -> None:
        # The study must be fetched from the database
        study: RawStudy = db_session.query(Study).get(study_uuid)

        # prepare some random matrices, insuring `lower_rule_curve` <= `upper_rule_curve`
        matrices = {
            "pmax_injection": np.random.rand(8760, 1),
            "pmax_withdrawal": np.random.rand(8760, 1),
            "lower_rule_curve": np.random.rand(8760, 1),
            "upper_rule_curve": np.random.rand(8760, 1),
            "inflows": np.random.rand(8760, 1) * 1000,
        }

        # Prepare the mocks
        def tree_get(url: Sequence[str], **_: Any) -> MutableMapping[str, Any]:
            name = url[-1]
            array = matrices[name]
            return {
                "index": list(range(array.shape[0])),
                "columns": list(range(array.shape[1])),
                "data": array.tolist(),
            }

        storage = study_storage_service.get_storage(study)
        file_study = storage.get_raw(study)
        file_study.tree = Mock(spec=FileStudyTree, get=tree_get)

        # Given the following arguments, the validation shouldn't raise any exception
        manager = STStorageManager(study_storage_service)

        # Run the method being tested and expect an exception
        with pytest.raises(
            ValidationError,
            match=re.escape("1 validation error"),
        ) as ctx:
            manager.validate_matrices(study, area_id="West", storage_id="storage1")
        error = ctx.value.errors()[0]
        assert error["loc"] == ("__root__",)
        assert "lower_rule_curve" in error["msg"]
        assert "upper_rule_curve" in error["msg"]
