from app.utils.pagination import PaginationParams, build_meta, resolve_sort_field, sort_direction
from app.utils.response import success_response
from app.utils.time_helpers import is_valid_time_format, time_str_to_minutes


def test_success_response_has_the_documented_envelope_shape():
    body = success_response(data={"id": "1"}, message="OK")
    assert body == {"success": True, "message": "OK", "data": {"id": "1"}}


def test_success_response_includes_meta_only_when_provided():
    without_meta = success_response(data=[])
    assert "meta" not in without_meta

    with_meta = success_response(data=[], meta={"total": 0})
    assert with_meta["meta"] == {"total": 0}


def test_pagination_skip_math():
    p = PaginationParams(page=3, limit=10, search=None, sort_by=None, sort_order="asc")
    assert p.skip == 20


def test_build_meta_reports_correct_page_count_and_flags():
    p = PaginationParams(page=2, limit=10, search=None, sort_by=None, sort_order="asc")
    meta = build_meta(p, total=25)
    assert meta == {"page": 2, "limit": 10, "total": 25, "total_pages": 3, "has_next": True, "has_prev": True}


def test_build_meta_handles_zero_results():
    p = PaginationParams(page=1, limit=10, search=None, sort_by=None, sort_order="asc")
    meta = build_meta(p, total=0)
    assert meta["total_pages"] == 0
    assert meta["has_next"] is False
    assert meta["has_prev"] is False


def test_resolve_sort_field_rejects_fields_outside_the_whitelist():
    allowed = {"name", "code"}
    assert resolve_sort_field("name", allowed, default_field="name") == "name"
    assert resolve_sort_field("password_hash", allowed, default_field="name") == "name"
    assert resolve_sort_field(None, allowed, default_field="name") == "name"


def test_sort_direction_maps_asc_desc_to_mongo_values():
    assert sort_direction("asc") == 1
    assert sort_direction("desc") == -1


def test_time_format_validation():
    assert is_valid_time_format("09:00") is True
    assert is_valid_time_format("23:59") is True
    assert is_valid_time_format("24:00") is False
    assert is_valid_time_format("9:00") is False
    assert is_valid_time_format("09:60") is False


def test_time_str_to_minutes():
    assert time_str_to_minutes("00:00") == 0
    assert time_str_to_minutes("09:30") == 570
    assert time_str_to_minutes("23:59") == 1439
