from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True, frozen=True)
class GitHubRepositoryDTO:
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


@dataclass(slots=True, frozen=True)
class RepositoryConfigDTO:
    repository: str
    root_directory: str
    framework: str
    confidence: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    detected_files: list[str]


@dataclass(slots=True, frozen=True)
class RepositoryFileDTO:
    name: str
    path: str
    type: str


@dataclass(slots=True, frozen=True)
class AnalyzeRepositoryInputDTO:
    user_access_token: str
    owner: str
    repo: str
    root_directory: str


@dataclass(slots=True, frozen=True)
class AnalyzeRepositoryOutputDTO:
    repository: str
    root_directory: str
    framework: str
    confidence: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    detected_files: list[str]


@dataclass(slots=True, frozen=True)
class CreateProjectInputDTO:
    user_access_token: str
    name: str
    owner: str
    repo: str
    github_repo_url: str
    language: str | None
    framework: str | None
    root_directory: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    description: str | None = None


@dataclass(slots=True, frozen=True)
class CreateProjectOutputDTO:
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

@dataclass(slots=True, frozen=True)
class GitHubWebhookDTO:
    webhook_id: int
    webhook_secret: str
    webhook_url: str
