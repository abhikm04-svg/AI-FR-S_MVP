from backend.ingestion.schemes import filter_direct_growth


def test_filter_direct_growth_keeps_only_matching_schemes():
    codes = {
        "100001": "ABC Fund Direct Growth",
        "100002": "ABC Fund Regular Growth",
        "100003": "XYZ Fund Direct Dividend",
        "100004": "XYZ Fund Direct Growth",
    }
    result = filter_direct_growth(codes)
    assert set(code for code, _ in result) == {"100001", "100004"}


def test_filter_direct_growth_preserves_names():
    codes = {"100001": "ABC Fund Direct Growth"}
    assert filter_direct_growth(codes) == [("100001", "ABC Fund Direct Growth")]


def test_filter_direct_growth_empty_input():
    assert filter_direct_growth({}) == []
