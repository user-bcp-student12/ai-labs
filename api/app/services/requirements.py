from app.models import RequirementUploadResponse
from app.repositories import requirements as requirement_repository


def store_requirement(
    upload_dir: str,
    owner: str,
    filename: str | None,
    content: bytes,
) -> RequirementUploadResponse:
    target = requirement_repository.store_upload(upload_dir, str(filename), content)
    return RequirementUploadResponse(
        owner=owner,
        fileName=filename,
        storedAt=str(target),
        size=len(content),
    )