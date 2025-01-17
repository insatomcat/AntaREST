from starlette.testclient import TestClient


class TestupdateStudyMetadata:
    """
    Test the study tags update through the `update_study_metadata` API endpoint.
    """

    def test_update_tags(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """
        This test verifies that we can update the tags of a study.
        It also tests the tags normalization.
        """

        # Classic usage: set some tags to a study
        study_tags = ["Tag1", "Tag2"]
        res = client.put(
            f"/v1/studies/{internal_study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"tags": study_tags},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["tags"]) == set(study_tags)

        # Update the tags with already existing tags (case-insensitive):
        # - "Tag1" is preserved, but with the same case as the existing one.
        # - "Tag2" is replaced by "Tag3".
        study_tags = ["tag1", "Tag3"]
        res = client.put(
            f"/v1/studies/{internal_study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"tags": study_tags},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["tags"]) != set(study_tags)  # not the same case
        assert set(tag.upper() for tag in actual["tags"]) == {"TAG1", "TAG3"}

        # String normalization: whitespaces are stripped and
        # consecutive whitespaces are replaced by a single one.
        study_tags = [" \xa0Foo  \t  Bar  \n  ", "  \t  Baz\xa0\xa0"]
        res = client.put(
            f"/v1/studies/{internal_study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"tags": study_tags},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["tags"]) == {"Foo Bar", "Baz"}

        # We can have symbols in the tags
        study_tags = ["Foo-Bar", ":Baz%"]
        res = client.put(
            f"/v1/studies/{internal_study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"tags": study_tags},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        assert set(actual["tags"]) == {"Foo-Bar", ":Baz%"}

    def test_update_tags__invalid_tags(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        # We cannot have empty tags
        study_tags = [""]
        res = client.put(
            f"/v1/studies/{internal_study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"tags": study_tags},
        )
        assert res.status_code == 422, res.json()
        description = res.json()["description"]
        assert "Tag cannot be empty" in description

        # We cannot have tags longer than 40 characters
        study_tags = ["very long tags, very long tags, very long tags"]
        assert len(study_tags[0]) > 40
        res = client.put(
            f"/v1/studies/{internal_study_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"tags": study_tags},
        )
        assert res.status_code == 422, res.json()
        description = res.json()["description"]
        assert "Tag is too long" in description
