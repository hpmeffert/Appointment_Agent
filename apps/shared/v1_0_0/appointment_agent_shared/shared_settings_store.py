from __future__ import annotations

from copy import deepcopy
from typing import Any

from sqlalchemy.orm import Session

from .repositories import LekabConfigRepository


SETTINGS_STORE_KEY = "shared_settings_store"
DEFAULT_SETTINGS_STORE = {
    "lekab": {},
    "google": {},
    "demo": {},
    "orchestrator": {},
}


class SharedSettingsStoreService:
    """Keep one release-local settings document across modules.

    The repository reuses the existing JSON-backed config table so Patch 7 can
    introduce a shared settings source of truth without a destructive schema
    migration. Config values, secret values, and status values stay separated,
    but every module reads and writes through the same top-level store key.
    """

    def __init__(self, session: Session) -> None:
        self.repo = LekabConfigRepository(session)

    def _read_record(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        record = self.repo.get(SETTINGS_STORE_KEY)
        if record is None:
            return deepcopy(DEFAULT_SETTINGS_STORE), {}, {}
        config_payload = deepcopy(record.config_payload or {})
        secret_payload = deepcopy(record.secret_payload or {})
        status_payload = deepcopy(record.status_payload or {})
        for namespace, default_value in DEFAULT_SETTINGS_STORE.items():
            config_payload.setdefault(namespace, deepcopy(default_value))
        return config_payload, secret_payload, status_payload

    def get_store(self) -> dict[str, Any]:
        config_payload, secret_payload, status_payload = self._read_record()
        return {
            "config": config_payload,
            "secrets": secret_payload,
            "status": status_payload,
        }

    def get_namespace(self, namespace: str) -> dict[str, Any]:
        return deepcopy(self.get_store()["config"].get(namespace) or {})

    def merge_namespace(
        self,
        namespace: str,
        values: dict[str, Any],
        *,
        secret_values: dict[str, Any] | None = None,
        status_values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        config_payload, secret_payload, status_payload = self._read_record()
        merged_namespace = {**deepcopy(config_payload.get(namespace) or {}), **deepcopy(values)}
        config_payload[namespace] = merged_namespace
        if secret_values is not None:
            secret_payload[namespace] = {
                **deepcopy(secret_payload.get(namespace) or {}),
                **deepcopy(secret_values),
            }
        if status_values is not None:
            status_payload[namespace] = {
                **deepcopy(status_payload.get(namespace) or {}),
                **deepcopy(status_values),
            }
        self.repo.save(
            config_key=SETTINGS_STORE_KEY,
            config_payload=config_payload,
            secret_payload=secret_payload,
            status_payload=status_payload,
        )
        return deepcopy(merged_namespace)
