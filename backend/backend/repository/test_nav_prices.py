from datetime import date
from decimal import Decimal

from backend.repository.nav_prices import _group_rows


def test_group_rows_buckets_by_scheme_code_in_order():
    rows = [
        {"scheme_code": "A", "nav_date": date(2024, 1, 1), "nav": Decimal("10.0")},
        {"scheme_code": "B", "nav_date": date(2024, 1, 1), "nav": Decimal("20.0")},
        {"scheme_code": "A", "nav_date": date(2024, 1, 2), "nav": Decimal("10.5")},
    ]
    result = _group_rows(["A", "B"], rows)
    assert result["A"] == [(date(2024, 1, 1), Decimal("10.0")), (date(2024, 1, 2), Decimal("10.5"))]
    assert result["B"] == [(date(2024, 1, 1), Decimal("20.0"))]


def test_group_rows_includes_empty_list_for_codes_with_no_rows():
    result = _group_rows(["A", "C"], [{"scheme_code": "A", "nav_date": date(2024, 1, 1), "nav": Decimal("1")}])
    assert result["C"] == []


def test_group_rows_empty_input():
    assert _group_rows([], []) == {}
