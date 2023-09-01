import json
import re

import numpy as np
import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from tests.integration.utils import wait_task_completion


@pytest.mark.unit_test
class TestSTStorage:
    # noinspection GrazieInspection
    """
    Test the end points related to short term storage.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    def test_lifecycle__nominal(
        self,
        client: TestClient,
        user_access_token: str,
        study_id: str,
    ) -> None:
        """
        The purpose of this integration test is to test the endpoints
        related to short-term storage management.

        To ensure functionality, the test needs to be performed on a study
        in version 860 or higher. That's why we will upgrade the "STA-mini"
        study, which is in an older version.

        We will test the creation of multiple short-term storages.

        We will test reading the properties of a short-term storage
        and reading a matrix from a short-term storage.

        We will test reading the list of short-term storages and
        verify that the list is properly ordered by group and name.

        We will test updating a short-term storage:

        - updating properties,
        - updating a matrix.

        We will test the deletion of short-term storages.
        """

        # Upgrade study to version 860
        res = client.put(
            f"/v1/studies/{study_id}/upgrade",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"target_version": 860},
        )
        res.raise_for_status()
        task_id = res.json()
        task = wait_task_completion(client, user_access_token, task_id)
        assert task.status == TaskStatus.COMPLETED, task

        # creation with default values (only mandatory properties specified)
        area_id = transform_name_to_id("FR")
        siemens_battery = "Siemens Battery"
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Battery"},
        )
        assert res.status_code == 200, res.json()
        siemens_battery_id = res.json()["id"]
        assert siemens_battery_id == transform_name_to_id(siemens_battery)
        assert res.json() == {
            "efficiency": 1.0,
            "group": "Battery",
            "id": siemens_battery_id,
            "initialLevel": 0.0,
            "initialLevelOptim": False,
            "injectionNominalCapacity": 0.0,
            "name": siemens_battery,
            "reservoirCapacity": 0.0,
            "withdrawalNominalCapacity": 0.0,
        }

        # reading the properties of a short-term storage
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == {
            "efficiency": 1.0,
            "group": "Battery",
            "id": siemens_battery_id,
            "initialLevel": 0.0,
            "initialLevelOptim": False,
            "injectionNominalCapacity": 0.0,
            "name": siemens_battery,
            "reservoirCapacity": 0.0,
            "withdrawalNominalCapacity": 0.0,
        }

        # updating the matrix of a short-term storage
        array = np.random.rand(8760, 1) * 1000
        res = client.put(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}/series/inflows",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "index": list(range(array.shape[0])),
                "columns": list(range(array.shape[1])),
                "data": array.tolist(),
            },
        )
        assert res.status_code == 200, res.json()
        assert res.json() is None

        # reading the matrix of a short-term storage
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}/series/inflows",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        matrix = res.json()
        actual = np.array(matrix["data"], dtype=np.float64)
        assert actual.all() == array.all()

        # validating the matrices of a short-term storage
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}/validate",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() is True

        # Reading the list of short-term storages
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == [
            {
                "efficiency": 1.0,
                "group": "Battery",
                "id": siemens_battery_id,
                "initialLevel": 0.0,
                "initialLevelOptim": False,
                "injectionNominalCapacity": 0.0,
                "name": siemens_battery,
                "reservoirCapacity": 0.0,
                "withdrawalNominalCapacity": 0.0,
            }
        ]

        # updating properties
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
            },
        )
        assert res.status_code == 200, res.json()
        assert json.loads(res.text) == {
            "id": siemens_battery_id,
            "name": "New Siemens Battery",
            "group": "Battery",
            "efficiency": 1.0,
            "initialLevel": 0.0,
            "initialLevelOptim": False,
            "injectionNominalCapacity": 0.0,
            "withdrawalNominalCapacity": 0.0,
            "reservoirCapacity": 2500,
        }

        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == {
            "id": siemens_battery_id,
            "name": "New Siemens Battery",
            "group": "Battery",
            "efficiency": 1.0,
            "initialLevel": 0.0,
            "initialLevelOptim": False,
            "injectionNominalCapacity": 0.0,
            "withdrawalNominalCapacity": 0.0,
            "reservoirCapacity": 2500,
        }

        # updating properties
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "initialLevel": 5900,
                "reservoirCapacity": 0,
            },
        )
        assert res.status_code == 200, res.json()
        assert json.loads(res.text) == {
            "id": siemens_battery_id,
            "name": "New Siemens Battery",
            "group": "Battery",
            "efficiency": 1.0,
            "initialLevel": 5900,
            "initialLevelOptim": False,
            "injectionNominalCapacity": 0.0,
            "withdrawalNominalCapacity": 0.0,
            "reservoirCapacity": 0,
        }

        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        assert res.json() == {
            "id": siemens_battery_id,
            "name": "New Siemens Battery",
            "group": "Battery",
            "efficiency": 1.0,
            "initialLevel": 5900,
            "initialLevelOptim": False,
            "injectionNominalCapacity": 0.0,
            "withdrawalNominalCapacity": 0.0,
            "reservoirCapacity": 0,
        }

        # deletion of short-term storages
        res = client.delete(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[siemens_battery_id],
        )
        assert res.status_code == 204, res.json()
        assert res.text == "null"

        # deletion of short-term storages with empty list
        res = client.delete(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[],
        )
        assert res.status_code == 204, res.json()
        assert res.text == "null"

        # deletion of short-term storages with multiple IDs
        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Battery"},
        )
        assert res.status_code == 200, res.json()
        siemens_battery_id1 = res.json()["id"]

        siemens_battery_del = f"{siemens_battery}del"

        res = client.post(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery_del, "group": "Battery"},
        )
        assert res.status_code == 200, res.json()
        siemens_battery_id2 = res.json()["id"]

        res = client.delete(
            f"/v1/studies/{study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[siemens_battery_id1, siemens_battery_id2],
        )
        assert res.status_code == 204, res.json()
        assert res.text == "null"

        # Check the removal
        res = client.get(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        obj = res.json()
        description = obj["description"]
        assert siemens_battery_id in description
        assert re.search(
            r"fields of storage", description, flags=re.IGNORECASE
        )
        assert re.search(r"not found", description, flags=re.IGNORECASE)

        assert res.status_code == 404, res.json()

        # Check delete with the wrong value of area_id
        bad_area_id = "bad_area"
        res = client.delete(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[siemens_battery_id],
        )
        assert res.status_code == 500, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert re.search(
            r"CommandName.REMOVE_ST_STORAGE",
            description,
            flags=re.IGNORECASE,
        )

        # Check delete with the wrong value of study_id
        bad_study_id = "bad_study"
        res = client.delete(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=[siemens_battery_id],
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check get with wrong area_id

        res = client.get(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert res.status_code == 404, res.json()

        # Check get with wrong study_id

        res = client.get(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check post with wrong study_id
        res = client.post(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Battery"},
        )
        obj = res.json()
        description = obj["description"]
        assert res.status_code == 404, res.json()
        assert bad_study_id in description

        # Check post with wrong area_id
        res = client.post(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "Battery"},
        )
        assert res.status_code == 500, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert re.search(r"Area ", description, flags=re.IGNORECASE)
        assert re.search(r"does not exist ", description, flags=re.IGNORECASE)

        # Check post with wrong group
        res = client.post(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/storages",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"name": siemens_battery, "group": "GroupFoo"},
        )
        assert res.status_code == 422, res.json()
        obj = res.json()
        description = obj["description"]
        assert re.search(
            r"not a valid enumeration member", description, flags=re.IGNORECASE
        )

        # Check the put with the wrong area_id
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{bad_area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_area_id in description
        assert re.search(r"not a child of ", description, flags=re.IGNORECASE)

        # Check the put with the wrong siemens_battery_id
        res = client.patch(
            f"/v1/studies/{study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert siemens_battery_id in description
        assert re.search(
            r"fields of storage", description, flags=re.IGNORECASE
        )
        assert re.search(r"not found", description, flags=re.IGNORECASE)

        # Check the put with the wrong study_id
        res = client.patch(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 1.0,
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        assert res.status_code == 404, res.json()
        obj = res.json()
        description = obj["description"]
        assert bad_study_id in description

        # Check the put with the wrong efficiency
        res = client.patch(
            f"/v1/studies/{bad_study_id}/areas/{area_id}/storages/{siemens_battery_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={
                "efficiency": 2.0,
                "initialLevel": 0.0,
                "initialLevelOptim": True,
                "injectionNominalCapacity": 2450,
                "name": "New Siemens Battery",
                "reservoirCapacity": 2500,
                "withdrawalNominalCapacity": 2350,
            },
        )
        assert res.status_code == 422, res.json()
