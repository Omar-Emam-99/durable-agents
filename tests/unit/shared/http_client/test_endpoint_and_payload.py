"""Tests for BaseEndpoint and BasePayload."""

from __future__ import annotations

from typing import Any

from shared.base_classes.http_client.base_endpoint import BaseEndpoint, HttpMethod
from shared.base_classes.http_client.base_http_client import BaseHttpClient
from shared.base_classes.http_client.base_payload import BasePayload
from shared.base_classes.http_client.handlers import LoggingHandler


class GetDoc(BaseEndpoint):
    method = HttpMethod.GET
    path = "/api/v1/documents/{document_id}"


class NamePayload(BasePayload):
    def __init__(self, name: str) -> None:
        self.name = name

    def to_payload(self) -> dict[str, Any]:
        return {"name": self.name}


def test_build_url_with_path_params():
    ep = GetDoc()
    url = ep.build_url("https://api.example.com/", {"document_id": "abc"})
    assert url == "https://api.example.com/api/v1/documents/abc"


def test_build_url_without_params():
    class ListDocs(BaseEndpoint):
        method = HttpMethod.GET
        path = "/docs"

    assert ListDocs().build_url("http://x", None) == "http://x/docs"


def test_payload_serialized_in_request_message(setup_di):
    class PostDoc(BaseEndpoint):
        method = HttpMethod.POST
        path = "/docs"

    client = BaseHttpClient("http://test", handlers=[LoggingHandler()])
    msg = client._build_request_message(PostDoc(), body=NamePayload("widget"))
    assert msg.body == {"name": "widget"}
    assert msg.headers["Content-Type"] == "application/json"
