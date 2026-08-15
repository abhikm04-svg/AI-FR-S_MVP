from datetime import date
from decimal import Decimal

from backend.ingestion.nav_history import compute_delta

RAW = {
    "data": [
        {"date": "01-01-2024", "nav": "10.5000"},
        {"date": "02-01-2024", "nav": "10.6000"},
        {"date": "not-a-date", "nav": "10.7000"},
        {"date": "03-01-2024", "nav": "not-a-number"},
    ]
}


def test_new_scheme_keeps_all_entries_within_window():
    delta, latest = compute_delta("100001", RAW, last_nav_date=None)
    assert delta == [
        ("100001", date(2024, 1, 1), Decimal("10.5000")),
        ("100001", date(2024, 1, 2), Decimal("10.6000")),
    ]
    assert latest == (date(2024, 1, 2), Decimal("10.6000"))


def test_existing_scheme_keeps_only_rows_newer_than_last_nav_date():
    delta, latest = compute_delta("100001", RAW, last_nav_date=date(2024, 1, 1))
    assert delta == [("100001", date(2024, 1, 2), Decimal("10.6000"))]
    assert latest == (date(2024, 1, 2), Decimal("10.6000"))


def test_up_to_date_scheme_yields_no_delta_but_still_reports_latest():
    delta, latest = compute_delta("100001", RAW, last_nav_date=date(2024, 1, 2))
    assert delta == []
    assert latest == (date(2024, 1, 2), Decimal("10.6000"))


def test_malformed_entries_are_skipped_not_fatal():
    delta, latest = compute_delta("100001", RAW, last_nav_date=None)
    dates = [row[1] for row in delta]
    assert date(2024, 1, 3) not in dates  # bad nav value, skipped
    assert latest is not None  # bad entries didn't block finding a valid latest


def test_handles_missing_or_empty_data():
    assert compute_delta("100001", None, None) == ([], None)
    assert compute_delta("100001", {}, None) == ([], None)
    assert compute_delta("100001", {"data": []}, None) == ([], None)


def test_old_scheme_five_year_cutoff_excludes_stale_entries():
    old_raw = {"data": [{"date": "01-01-2000", "nav": "5.0000"}]}
    delta, latest = compute_delta("100001", old_raw, last_nav_date=None)
    assert delta == []
    assert latest == (date(2000, 1, 1), Decimal("5.0000"))
