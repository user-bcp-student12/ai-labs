from fastapi import APIRouter, Depends, File, UploadFile, status

from app.dependencies import get_upload_dir
from app.models import Identity, RequirementUploadResponse
from app.security import get_identity
from app.services import requirements as requirement_service

router = APIRouter()


@router.post(
    "/requirements",
    status_code=status.HTTP_201_CREATED,
    response_model=RequirementUploadResponse,
)
async def upload_requirement(
    file: UploadFile = File(...),
    identity: Identity = Depends(get_identity),
    upload_dir: str = Depends(get_upload_dir),
) -> RequirementUploadResponse:
    content = await file.read()
    return requirement_service.store_requirement(
        upload_dir, identity["username"], file.filename, content
    )