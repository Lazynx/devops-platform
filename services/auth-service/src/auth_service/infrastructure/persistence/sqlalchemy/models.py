from sqlalchemy import Column, DateTime, Enum as SqlEnum, ForeignKey, Index, MetaData, String, Table, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from auth_service.domain.entities import OAuthProvider, UserRole

metadata = MetaData()

users_table = Table(
    'users',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True),
    Column('email', String(255), unique=True, nullable=False),
    Column('username', String(255), unique=True, nullable=False),
    Column('avatar_url', String(512), nullable=True),
    Column('role', SqlEnum(UserRole), nullable=False),
    Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column('updated_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column('last_login_at', DateTime(timezone=True), nullable=True),
    Index('ix_users_email', 'email'),
    Index('ix_users_username', 'username'),
)

oauth_connections_table = Table(
    'oauth_connections',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('provider', SqlEnum(OAuthProvider), nullable=False),
    Column('provider_user_id', String(255), nullable=False),
    Column('access_token', String(512), nullable=False),
    Column('refresh_token', String(512), nullable=True),
    Column('token_expires_at', DateTime(timezone=True), nullable=True),
    Column('scopes', String(512), nullable=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column('updated_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
    Index('ix_oauth_connections_user_id', 'user_id'),
    Index('ix_oauth_user_provider', 'user_id', 'provider'),
    UniqueConstraint(
        'user_id',
        'provider',
        'provider_user_id',
        name='uq_user_provider_account',
    ),
)