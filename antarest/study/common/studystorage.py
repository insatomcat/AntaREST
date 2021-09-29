from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, Generic, List, Union, Optional, IO

from antarest.core.custom_types import JSON, SUB_JSON
from antarest.core.exceptions import StudyNotFoundError
from antarest.study.model import (
    Study,
    StudySimResultDTO,
    StudyMetadataDTO,
    StudyMetadataPatchDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

T = TypeVar("T", bound=Study)


class IStudyStorageService(ABC, Generic[T]):
    @abstractmethod
    def create(self, metadata: T) -> T:
        """
        Create empty new study
        Args:
            metadata: study information

        Returns: new study information

        """
        raise NotImplementedError()

    @abstractmethod
    def get(
        self,
        metadata: T,
        url: str = "",
        depth: int = 3,
        formatted: bool = True,
    ) -> JSON:
        """
        Entry point to fetch data inside study.
        Args:
            metadata: study
            url: path data inside study to reach
            depth: tree depth to reach after reach data path
            formatted: indicate if raw files must be parsed and formatted

        Returns: study data formatted in json

        """
        raise NotImplementedError()

    @abstractmethod
    def exists(self, metadata: T) -> bool:
        """
        Check study exist.
        Args:
            metadata: study

        Returns: true if study presents in disk, false else.

        """
        raise NotImplementedError()

    @abstractmethod
    def copy(
        self, src_meta: T, dest_name: str, with_outputs: bool = False
    ) -> T:
        """
        Copy study to a new destination
        Args:
            src_meta: source study
            dest_meta: destination study
            with_outputs: indicate either to copy the output or not

        Returns: destination study

        """
        raise NotImplementedError()

    @abstractmethod
    def edit_study(self, metadata: T, url: str, new: SUB_JSON) -> SUB_JSON:
        """
        Replace data on disk with new
        Args:
            metadata: study
            url: data path to reach
            new: new data to replace

        Returns: new data replaced

        """
        raise NotImplementedError()

    @abstractmethod
    def patch_update_study_metadata(
        self, study: T, metadata: StudyMetadataPatchDTO
    ) -> StudyMetadataDTO:
        """
        Update patch study metadata
        Args:
            study: study
            metadata: patch

        Returns: study metadata

        """
        raise NotImplementedError()

    @abstractmethod
    def import_output(
        self, study: T, output: Union[IO[bytes], Path]
    ) -> Optional[str]:
        """
        Import an output
        Args:
            study: the study
            output: Path of the output or raw data
        Returns: None
        """
        raise NotImplementedError()

    @abstractmethod
    def get_study_information(
        self, metadata: T, summary: bool = False
    ) -> StudyMetadataDTO:
        raise NotImplementedError()

    @abstractmethod
    def get_raw(self, metadata: T) -> FileStudy:
        """
        Fetch a study raw tree object and its config
        Args:
            metadata: study

        Returns: the config and study tree object

        """
        raise NotImplementedError()

    @abstractmethod
    def get_study_sim_result(self, metadata: T) -> List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study: study
        Returns: study output data

        """
        raise NotImplementedError()

    @abstractmethod
    def set_reference_output(
        self, metadata: T, output_id: str, status: bool
    ) -> None:
        """
        Set an output to the reference output of a study
        Args:
            metadata: study
            output_id: the id of output to set the reference status
            status: true to set it as reference, false to unset it

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def delete(self, metadata: T) -> None:
        """
        Delete study
        Args:
            metadata: study

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def delete_output(self, metadata: T, output_id: str) -> None:
        """
        Delete a simulation output
        Args:
            metadata: study
            output_id: output simulation

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def get_study_path(self, metadata: Study) -> Path:
        """
        Get study path
        Args:
            metadata: study information

        Returns: study path

        """
        raise NotImplementedError()

    def _check_study_exists(self, metadata: Study) -> None:
        """
        Check study on filesystem.

        Args:
            metadata: study

        Returns: none or raise error if not found

        """
        if not self.exists(metadata):
            raise StudyNotFoundError(
                f"Study with the uuid {metadata.id} does not exist."
            )

    @abstractmethod
    def export_study(
        self, metadata: T, target: Path, outputs: bool = True
    ) -> Path:
        """
        Export and compresse study inside zip
        Args:
            metadata: study
            target: path of the file to export to
            outputs: ask to integrated output folder inside exportation

        Returns: zip file with study files compressed inside

        """
        raise NotImplementedError()

    @abstractmethod
    def export_study_flat(
        self, metadata: T, dest: Path, outputs: bool = True
    ) -> None:
        """
        Export study to destination

        Args:
            metadata: study
            dest: destination path
            outputs: keep outputs or not
        Returns: None

        """
        raise NotImplementedError()