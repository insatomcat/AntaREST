import os
from copy import deepcopy
from glob import glob
from pathlib import Path
from typing import Tuple, Optional

from jsonschema import validate

from api_iso_antares.antares_io.reader.ini_reader import IniReader
from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.custom_types import JSON, SUB_JSON


class PathNotMatchJsonSchema(HtmlException):
    def __init__(self, message: str) -> None:
        super(PathNotMatchJsonSchema, self).__init__(message, 405)


class FolderReader:
    def __init__(self, reader_ini: IniReader, jsonschema: JSON, root: Path):
        self._reader_ini = reader_ini
        self.jsonschema = jsonschema
        self.root = root

    def read(self, folder: Path) -> JSON:
        jsonschema = deepcopy(self.jsonschema)
        output: JSON = dict()
        self._parse_recursive(folder, jsonschema, output)
        return output

    def _parse_recursive(
        self, current_path: Path, jsonschema: JSON, output: JSON
    ) -> None:
        keys = jsonschema["properties"].items()
        for key, value in keys:
            child_path = current_path / key
            if not child_path.exists():
                raise PathNotMatchJsonSchema(
                    f"{child_path} not in study. Needs keys {keys}"
                )

            child_jsonschema = jsonschema["properties"][key]

            if child_path.is_dir():
                output[key] = dict()
                self._parse_recursive(
                    child_path, child_jsonschema, output[key]
                )
            else:
                output[key] = self._parse_file(child_path)

    def _parse_file(self, path: Path) -> SUB_JSON:
        if path.suffix == ".txt":
            path_parent = f"{self.root}{os.sep}"
            relative_path = str(path).replace(path_parent, "")
            return f"matrices{os.sep}{relative_path}"
        elif path.suffix == ".ini":
            return self._reader_ini.read(path)
        raise NotImplemented(
            f"File extension {path.suffix} not implemented"
        )  # TODO custom exception

    def validate(self, folder_json: JSON) -> None:
        if (not self.jsonschema) and folder_json:
            raise ValueError("Jsonschema is empty.")
        validate(folder_json, self.jsonschema)
