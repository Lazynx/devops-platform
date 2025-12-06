from sqlalchemy.orm import registry

from auth_service.domain.entities import OAuthConnection, User
from auth_service.infrastructure.persistence.sqlalchemy.models import oauth_connections_table, users_table

mapper_registry = registry()

mapper_registry.map_imperatively(User, users_table)
mapper_registry.map_imperatively(OAuthConnection, oauth_connections_table)