from typing import TypedDict

from pydantic import BaseModel

DEFAULT_TASK_STATUS = "TODO"
DEFAULT_TASK_PRIORITY = "MEDIUM"


class Identity(TypedDict):
    username: str
    role: str


class TaskCreateRequest(BaseModel):
    title: str = ""
    description: str = ""
    status: str = DEFAULT_TASK_STATUS
    priority: str = DEFAULT_TASK_PRIORITY
    owner: str | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    owner: str
    priority: str
    createdAt: str


class TaskSummaryResponse(BaseModel):
    owner: str
    total: int
    byStatus: dict[str, int]
    highPriorityOpen: int


class RequirementUploadResponse(BaseModel):
    owner: str
    fileName: str | None
    storedAt: str
    size: int


class BackendHealthResponse(BaseModel):
    requestedBy: str
    status: int
    body: str