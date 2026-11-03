import logging
import os

import urllib3

from app.models import BackendHealthResponse

AUTH_HEALTH_URL_ENV = "AUTH_HEALTH_URL"
DEFAULT_AUTH_HEALTH_URL = "http://localhost:8080/q/health"
BACKEND_HEALTH_TIMEOUT_SECONDS = 3.0
BACKEND_UNAVAILABLE_STATUS = 0
BACKEND_HEALTH_FAILURE_MESSAGE = "Backend health check failed"
LOGGER = logging.getLogger(__name__)


def check_backend_health(username: str) -> BackendHealthResponse:
    url = os.getenv(AUTH_HEALTH_URL_ENV, DEFAULT_AUTH_HEALTH_URL)
    try:
        response = urllib3.PoolManager().request(
            "GET", url, timeout=BACKEND_HEALTH_TIMEOUT_SECONDS
        )
        return BackendHealthResponse(
            requestedBy=username,
            status=response.status,
            body=response.data.decode("utf-8"),
        )
    except (urllib3.exceptions.HTTPError, OSError):
        LOGGER.warning("Backend health check failed")
        return BackendHealthResponse(
            requestedBy=username,
            status=BACKEND_UNAVAILABLE_STATUS,
            body=BACKEND_HEALTH_FAILURE_MESSAGE,
        )