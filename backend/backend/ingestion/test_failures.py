from backend.ingestion.failures import build_failed_codes


def test_build_failed_codes_shapes_each_entry():
    result = build_failed_codes([("100001", "timeout"), ("100002", "bad json")])
    assert len(result) == 2
    assert result[0] == {"code": "100001", "error": "timeout", "at": result[0]["at"]}
    assert result[1]["code"] == "100002"
    assert "at" in result[0] and "at" in result[1]


def test_build_failed_codes_empty_input():
    assert build_failed_codes([]) == []
