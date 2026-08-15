"""AMFI/mftool client. Ported from the Application/app.py and
Multi Page Test/shared_lib.py copies -- this is now the single canonical
version; those two should not keep their own copies once they're retired
in Phase 5.
"""
from __future__ import annotations

from mftool import Mftool


class RobustMftool(Mftool):
    def get_scheme_codes(self, as_json: bool = False):
        """Overridden to handle malformed lines in AMFI data robustly."""
        scheme_info = {}
        url = self._get_quote_url
        try:
            response = self._session.get(url)
            data = response.text.split("\n")
            for scheme_data in data:
                if ";" in scheme_data:
                    scheme = scheme_data.split(";")
                    if len(scheme) >= 4:
                        scheme_info[scheme[0]] = scheme[3]
        except Exception as e:
            print(f"Error fetching scheme codes in RobustMftool: {e}")

        if as_json:
            import json

            return json.dumps(scheme_info)
        return scheme_info
