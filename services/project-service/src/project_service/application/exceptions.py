from uuid import UUID


class DeploymentServiceError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DeploymentServiceTimeoutError(DeploymentServiceError):
    def __init__(self, message: str = "Deployment service request timed out"):
        super().__init__(message, status_code=504)


class DeploymentConfigCreationError(Exception):
    def __init__(self, project_id: UUID, error_message: str):
        self.project_id = project_id
        self.error_message = error_message
        super().__init__(f"Deployment config creation failed for project {project_id}: {error_message}")


class SecretsCreationError(Exception):
    def __init__(self, project_id: UUID, failed_secrets: list[str]):
        self.project_id = project_id
        self.failed_secrets = failed_secrets
        super().__init__(f"Secrets creation failed for project {project_id}: {failed_secrets}")


class ProjectNotReadyError(Exception):
    def __init__(self, project_id: UUID, current_status: str):
        self.project_id = project_id
        self.current_status = current_status
        super().__init__(f"Project {project_id} is not ready for deployment. Current status: {current_status}")


class ProjectNotFoundError(Exception):
    def __init__(self, project_id: UUID):
        self.project_id = project_id
        super().__init__(f"Project {project_id} not found")
