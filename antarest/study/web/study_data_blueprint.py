import logging
from typing import Any, Optional, List, Dict, Union, cast

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import (
    RequestParameters,
)
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth
from antarest.study.business.link_management import LinkInfoDTO
from antarest.study.model import PatchCluster, PatchArea
from antarest.study.service import StudyService
from antarest.study.business.area_management import (
    AreaType,
    AreaCreationDTO,
    AreaInfoDTO,
    AreaUI,
)

logger = logging.getLogger(__name__)


def create_study_data_routes(
    study_service: StudyService, config: Config
) -> APIRouter:
    """
    Endpoint implementation for studies area management
    Args:
        study_service: study service facade to handle request
        config: main server configuration

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.get(
        "/studies/{uuid}/areas",
        tags=[APITag.study_data],
        summary="Get all areas basic info",
        response_model=List[AreaInfoDTO],
    )
    def get_areas(
        uuid: str,
        type: Optional[AreaType] = None,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching area list (type={type}) for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        areas_list = study_service.get_all_areas(uuid, type, params)
        return areas_list

    @bp.get(
        "/studies/{uuid}/links",
        tags=[APITag.study_data],
        summary="Get all links",
        response_model=List[LinkInfoDTO],
    )
    def get_links(
        uuid: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Fetching link list for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        areas_list = study_service.get_all_links(uuid, params)
        return areas_list

    @bp.post(
        "/studies/{uuid}/areas",
        tags=[APITag.study_data],
        summary="Create a new area/cluster",
        response_model=AreaInfoDTO,
    )
    def create_area(
        uuid: str,
        area_creation_info: AreaCreationDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating new area for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.create_area(uuid, area_creation_info, params)

    @bp.post(
        "/studies/{uuid}/links",
        tags=[APITag.study_data],
        summary="Create a link",
        response_model=AreaInfoDTO,
    )
    def create_link(
        uuid: str,
        link_creation_info: LinkInfoDTO,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Creating new link for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.create_link(uuid, link_creation_info, params)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}/ui",
        tags=[APITag.study_data],
        summary="Update area information",
        response_model=AreaInfoDTO,
    )
    def update_area_ui(
        uuid: str,
        area_id: str,
        area_ui: AreaUI,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating area ui {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        return study_service.update_area_ui(uuid, area_id, area_ui, params)

    @bp.put(
        "/studies/{uuid}/areas/{area_id}",
        tags=[APITag.study_data],
        summary="Update area information",
        response_model=AreaInfoDTO,
    )
    def update_area_info(
        uuid: str,
        area_id: str,
        area_patch_dto: Union[PatchArea, Dict[str, PatchCluster]],
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Updating area {area_id} for study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        if isinstance(area_patch_dto, PatchArea):
            return study_service.update_area(
                uuid, area_id, area_patch_dto, params
            )
        else:
            return study_service.update_thermal_cluster_metadata(
                uuid,
                area_id,
                area_patch_dto,
                params,
            )

    @bp.delete(
        "/studies/{uuid}/areas/{area_id}",
        tags=[APITag.study_data],
        summary="Delete an area",
        response_model=str,
    )
    def delete_area(
        uuid: str,
        area_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Removing area {area_id} in study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.delete_area(uuid, area_id, params)
        return area_id

    @bp.delete(
        "/studies/{uuid}/links/{area_from}/{area_to}",
        tags=[APITag.study_data],
        summary="Delete a link",
        response_model=str,
    )
    def delete_link(
        uuid: str,
        area_from: str,
        area_to: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        logger.info(
            f"Removing link {area_from}%{area_to} in study {uuid}",
            extra={"user": current_user.id},
        )
        params = RequestParameters(user=current_user)
        study_service.delete_link(uuid, area_from, area_to, params)
        return f"{area_from}%{area_to}"

    return bp