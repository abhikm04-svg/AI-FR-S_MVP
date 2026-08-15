from unittest.mock import MagicMock

from backend.data.mftool_client import RobustMftool


def _client_with_fake_response(body: str) -> RobustMftool:
    client = RobustMftool()
    fake_response = MagicMock()
    fake_response.text = body
    client._session = MagicMock()
    client._session.get.return_value = fake_response
    return client


def test_skips_malformed_lines_missing_fields():
    client = _client_with_fake_response(
        "100001;ISIN1;ISIN2;ABC Fund Direct Growth\n"
        "not-enough-fields;only-two\n"
        "100002;ISIN3;ISIN4;XYZ Fund Direct Growth\n"
    )
    result = client.get_scheme_codes()
    assert result == {
        "100001": "ABC Fund Direct Growth",
        "100002": "XYZ Fund Direct Growth",
    }


def test_ignores_lines_without_semicolons():
    client = _client_with_fake_response("Open Ended Schemes(Equity)\n100001;a;b;Fund A\n")
    result = client.get_scheme_codes()
    assert result == {"100001": "Fund A"}


def test_returns_empty_dict_on_request_failure():
    client = RobustMftool()
    client._session = MagicMock()
    client._session.get.side_effect = Exception("network down")
    assert client.get_scheme_codes() == {}
