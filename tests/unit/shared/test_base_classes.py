"""Tests for shared base classes (logger DI + repository stub)."""

from __future__ import annotations

import uuid

import pytest

from shared.app_results import AppResult, PaginatedResult
from shared.base_classes.base_middleware import BaseMiddleware
from shared.base_classes.base_repository import IBaseRepository
from shared.base_classes.base_service import BaseService
from shared.base_classes.http_client.base_gateway import BaseGateway
from shared.logging import Logger


class StubService(BaseService):
    pass


class StubGateway(BaseGateway):
    pass


class StubRepo(IBaseRepository[dict]):
    async def find_by_id(self, entity_id: uuid.UUID) -> AppResult[dict | None]:
        return AppResult.ok({"id": str(entity_id)})

    async def find_all(
        self, page: int = 1, page_size: int = 20
    ) -> AppResult[PaginatedResult[dict]]:
        return AppResult.ok(
            PaginatedResult(items=[], total=0, page=page, page_size=page_size, total_pages=0)
        )

    async def create(self, entity: dict) -> AppResult[dict]:
        return AppResult.ok(entity)

    async def update(self, entity: dict) -> AppResult[dict]:
        return AppResult.ok(entity)

    async def delete(self, entity_id: uuid.UUID) -> AppResult[bool]:
        return AppResult.ok(True)


def test_base_service_logger(setup_di):
    svc = StubService()
    assert isinstance(svc.logger, Logger)


def test_base_gateway_logger(setup_di):
    gw = StubGateway()
    assert isinstance(gw.logger, Logger)


def test_base_repository_logger_and_methods(setup_di):
    repo = StubRepo()
    assert isinstance(repo.logger, Logger)


@pytest.mark.asyncio
async def test_stub_repo_crud(setup_di):
    repo = StubRepo()
    entity_id = uuid.uuid4()
    found = await repo.find_by_id(entity_id)
    assert found.is_success
    created = await repo.create({"name": "x"})
    assert created.data == {"name": "x"}
    deleted = await repo.delete(entity_id)
    assert deleted.data is True


def test_base_middleware_logger(setup_di):
    """BaseMiddleware needs an app; only exercise the logger property via a stub."""

    class TinyMiddleware(BaseMiddleware):
        async def dispatch(self, request, call_next):
            return await call_next(request)

    # Starlette BaseHTTPMiddleware requires app; pass a dummy callable app
    async def dummy_app(scope, receive, send):
        pass

    mw = TinyMiddleware(dummy_app)
    assert isinstance(mw.logger, Logger)
