"""Tests for AppResult and PaginatedResult."""

from shared.app_results import AppResult, PaginatedResult


def test_ok_result():
    result = AppResult.ok({"a": 1})
    assert result.is_success
    assert not result.is_failure
    assert result.data == {"a": 1}
    assert result.error_code is None
    assert not result.is_error


def test_failure_result():
    result = AppResult.failure("E_CODE", "something broke", errors=["x"])
    assert result.is_failure
    assert not result.is_success
    assert result.error_code == "E_CODE"
    assert result.message == "something broke"
    assert result.errors == ["x"]
    assert result.is_error


def test_paginated_result():
    page = PaginatedResult(
        items=[1, 2],
        total=2,
        page=1,
        page_size=10,
        total_pages=1,
    )
    assert page.items == [1, 2]
    assert page.total_pages == 1
