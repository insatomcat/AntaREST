from pathlib import Path
from zipfile import ZipFile

import pytest

from api_iso_antares.custom_types import SUB_JSON
from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.root.study import Study
from tests.filesystem.utils import extract_sta


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, exp",
    [
        ("layers/layers/layers/0", "All"),
    ],
)
def test_get_settings_it(
    project_path: Path, tmp_path: Path, url: str, exp: SUB_JSON
):
    path = extract_sta(project_path, tmp_path)
    study = Study(config=Config.from_path(path))

    assert study.get(url.split("/")) == exp


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url, exp",
    [
        ("layers/layers/layers/0", "One"),
    ],
)
def test_save_settings_it(
    project_path: Path, tmp_path: Path, url: str, exp: SUB_JSON
):
    path = extract_sta(project_path, tmp_path)
    study = Study(config=Config.from_path(path))

    study.save(exp, url.split("/"))
    assert study.get(url.split("/")) == exp
