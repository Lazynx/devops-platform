from uuid import UUID

from faststream.kafka import KafkaBroker


class ProjectEventPublisher:
    def __init__(self, broker: KafkaBroker):
        self._broker = broker

    async def publish_project_created(
        self,
        project_id: UUID,
        owner_id: UUID,
        name: str,
        github_repo_url: str,
        framework: str | None,
    ) -> None:
        await self._broker.publish(
            {
                'project_id': str(project_id),
                'owner_id': str(owner_id),
                'name': name,
                'github_repo_url': github_repo_url,
                'framework': framework,
            },
            'project.created',
        )
