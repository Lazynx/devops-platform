from datetime import datetime

from pydantic import BaseModel

from ci_service.application.dtos import AnalyzeRepositoryInputDTO, RepositoryConfigDTO


class AnalyzeRepositoryRequest(BaseModel):
    owner: str
    repo: str
    root_directory: str = './'

    @staticmethod
    def to_input_dto(
        owner: str,
        repo: str,
        root_directory: str,
        user_access_token: str
    ) -> AnalyzeRepositoryInputDTO:
        return AnalyzeRepositoryInputDTO(
            owner=owner,
            repo=repo,
            root_directory=root_directory,
            user_access_token=user_access_token,
        )


class GitHubRepositoryResponse(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    description: str | None
    fork: bool
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime | None
    size: int
    stargazers_count: int
    watchers_count: int
    language: str | None
    forks_count: int
    open_issues_count: int
    default_branch: str

class RepositoryConfigResponse(BaseModel):
    repository: str
    root_directory: str
    framework: str
    confidence: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    detected_files: list[str]

    @classmethod
    def from_dto(cls, dto: RepositoryConfigDTO) -> 'RepositoryConfigResponse':
        return cls(
            repository=dto.repository,
            root_directory=dto.root_directory,
            framework=dto.framework,
            confidence=dto.confidence,
            install_command=dto.install_command,
            build_command=dto.build_command,
            start_command=dto.start_command,
            detected_files=dto.detected_files,
        )


class GetRepositoriesResponse(BaseModel):
    repositories: list[GitHubRepositoryResponse]


