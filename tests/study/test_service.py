from pathlib import Path

import pytest

from antarest.study.service import get_disk_usage


def test_get_disk_usage__nominal_case(tmp_path: Path):
    """Nominal case: the study path in a directory."""
    tmp_path.joinpath("input").mkdir()
    ini_data = b"[config]\nkey = value"
    tmp_path.joinpath("input/params.ini").write_bytes(ini_data)
    tmp_path.joinpath("input/series").mkdir()
    series_data = b"10\n20\n"
    tmp_path.joinpath("input/series/data.tsv").write_bytes(series_data)
    assert get_disk_usage(tmp_path) == len(ini_data) + len(series_data)


@pytest.mark.parametrize("suffix", [".zip", ".7z", ".ZIP"])
def test_get_disk__usage_archive(tmp_path: Path, suffix: str):
    """Test archived files .7z and .zip"""
    compressed_path = tmp_path.joinpath("study").with_suffix(suffix)
    compressed_data = b"dummy archive content"
    compressed_path.write_bytes(compressed_data)
    assert get_disk_usage(tmp_path) == len(compressed_data)


def test_gest_disk_usage__unknown_format(tmp_path: Path) -> None:
    """Test unusual directories"""
    path = tmp_path.joinpath("study.dat")
    path.touch()
    with pytest.raises(NotADirectoryError):
        get_disk_usage(path)
