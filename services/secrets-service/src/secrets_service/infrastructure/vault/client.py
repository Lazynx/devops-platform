import asyncio
import contextlib

import hvac
from hvac.exceptions import VaultError


class VaultClient:
    def __init__(self, url: str, token: str):
        self._client = hvac.Client(url=url, token=token)
        with contextlib.suppress(Exception):
            self._client.auth.token.renew_self()

    async def write_secret(self, path: str, data: dict[str, str]) -> None:
        try:
            await asyncio.to_thread(
                self._client.secrets.kv.v2.create_or_update_secret,
                path=path,
                secret=data,
            )
        except VaultError as e:
            raise RuntimeError(f'Failed to write secret to Vault: {e}') from e

    async def read_secret(self, path: str) -> dict[str, str]:
        try:
            response = await asyncio.to_thread(
                self._client.secrets.kv.v2.read_secret_version,
                path=path,
            )
            return response['data']['data']
        except VaultError as e:
            raise RuntimeError(f'Failed to read secret from Vault: {e}') from e

    async def delete_secret(self, path: str) -> None:
        try:
            await asyncio.to_thread(
                self._client.secrets.kv.v2.delete_metadata_and_all_versions,
                path=path,
            )
        except VaultError as e:
            raise RuntimeError(f'Failed to delete secret from Vault: {e}') from e

    async def list_secrets(self, path: str) -> list[str]:
        try:
            response = await asyncio.to_thread(
                self._client.secrets.kv.v2.list_secrets,
                path=path,
            )
            return response['data']['keys']
        except VaultError:
            return []

    def is_authenticated(self) -> bool:
        return self._client.is_authenticated()

    async def create_policy(self, name: str, rules: str) -> None:
        try:
            await asyncio.to_thread(
                self._client.sys.create_or_update_policy,
                name=name,
                policy=rules,
            )
        except VaultError as e:
            raise RuntimeError(f'Failed to create policy in Vault: {e}') from e
