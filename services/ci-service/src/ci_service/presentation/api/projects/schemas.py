from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ci_service.application.dtos import CreateProjectInputDTO


class CreateProjectRequest(BaseModel):
    name: str
    owner: str
    repo: str
    github_repo_url: str
    language: str | None = None
    framework: str | None = None
    root_directory: str = './'
    install_command: str | None = None
    build_command: str | None = None
    start_command: str | None = None
    description: str | None = None

    def to_input_dto(self, user_access_token: str) -> CreateProjectInputDTO:
        return CreateProjectInputDTO(
            user_access_token=user_access_token,
            **self.model_dump(),
        )


class ProjectResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    github_repo_url: str
    github_webhook_id: int
    language: str | None
    framework: str | None
    root_directory: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    status: str
    created_at: datetime
    updated_at: datetime
