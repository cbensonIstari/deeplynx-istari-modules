"""Thin wrapper around the DeepLynx REST API."""

from __future__ import annotations

import requests


class DeepLynxClient:
    def __init__(self, base_url: str, org_id: int, project_id: int, bearer_token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.org_id = org_id
        self.project_id = project_id
        self.session = requests.Session()
        if bearer_token:
            self.session.headers["Authorization"] = f"Bearer {bearer_token}"

    def _org_proj(self) -> str:
        return f"{self.base_url}/api/v1/organizations/{self.org_id}/projects/{self.project_id}"

    def _proj(self) -> str:
        return f"{self.base_url}/api/v1/projects/{self.project_id}"

    # ── Records ──────────────────────────────────────────────────────

    def get_all_records(self, data_source_id: int | None = None) -> list[dict]:
        params = {}
        if data_source_id is not None:
            params["dataSourceId"] = data_source_id
        resp = self.session.get(f"{self._org_proj()}/records", params=params)
        resp.raise_for_status()
        return resp.json()

    def get_record(self, record_id: int) -> dict:
        resp = self.session.get(f"{self._org_proj()}/records/{record_id}")
        resp.raise_for_status()
        return resp.json()

    def get_record_graph(self, record_id: int, depth: int = 2) -> dict:
        resp = self.session.get(
            f"{self._org_proj()}/records/{record_id}/graph",
            params={"depth": depth},
        )
        resp.raise_for_status()
        return resp.json()

    def create_record(self, data_source_id: int, record: dict) -> dict:
        resp = self.session.post(
            f"{self._org_proj()}/records",
            params={"dataSourceId": data_source_id},
            json=record,
        )
        resp.raise_for_status()
        return resp.json()

    def bulk_create_records(self, data_source_id: int, records: list[dict]) -> list[dict]:
        resp = self.session.post(
            f"{self._org_proj()}/records/bulk",
            params={"dataSourceId": data_source_id},
            json=records,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Edges ────────────────────────────────────────────────────────

    def get_all_edges(self, data_source_id: int | None = None) -> list[dict]:
        params = {}
        if data_source_id is not None:
            params["dataSourceId"] = data_source_id
        resp = self.session.get(f"{self._org_proj()}/edges", params=params)
        resp.raise_for_status()
        return resp.json()

    def create_edge(self, data_source_id: int, edge: dict) -> dict:
        resp = self.session.post(
            f"{self._org_proj()}/edges",
            params={"dataSourceId": data_source_id},
            json=edge,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Classes ──────────────────────────────────────────────────────

    def get_classes(self) -> list[dict]:
        resp = self.session.get(f"{self._proj()}/classes")
        resp.raise_for_status()
        return resp.json()

    # ── Relationships ────────────────────────────────────────────────

    def get_relationships(self) -> list[dict]:
        resp = self.session.get(f"{self._proj()}/relationships")
        resp.raise_for_status()
        return resp.json()

    # ── Tags ─────────────────────────────────────────────────────────

    def get_tags(self) -> list[dict]:
        resp = self.session.get(f"{self._proj()}/tags")
        resp.raise_for_status()
        return resp.json()

    def create_tag(self, name: str) -> dict:
        resp = self.session.post(f"{self._proj()}/tags", json={"name": name})
        resp.raise_for_status()
        return resp.json()

    def attach_tag(self, record_id: int, tag_id: int) -> None:
        resp = self.session.post(
            f"{self._org_proj()}/records/{record_id}/tags",
            params={"tagId": tag_id},
        )
        resp.raise_for_status()
