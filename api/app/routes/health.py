from fastapi import APIRouter, Depends

from app.models import BackendHealthResponse, Identity
from app.security import get_identity
from app.services import health as health_service

router = APIRouter()


@router.get("/backend-health", response_model=BackendHealthResponse)
def backend_health(
    identity: Identity = Depends(get_identity),
) -> BackendHealthResponse:
    return health_service.check_backend_health(identity["username"])