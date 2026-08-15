-- Ad hoc spot-check, not part of the migration sequence -- run manually after
-- 0005 to confirm the backfill is complete and accurate. Compares each
-- scheme's blob array length in the old table against its row count in the
-- new table.
--
-- Expect zero rows back. Any row returned is either a real gap (investigate)
-- or explained by malformed entries 0005's regex guards intentionally skip
-- (spot-check a few against the raw `history` blob to confirm which).

SELECT h.scheme_code,
       jsonb_array_length(h.history::jsonb) AS blob_count,
       COALESCE(p.row_count, 0)             AS normalized_count
FROM mf_nav_history h
LEFT JOIN (
    SELECT scheme_code, COUNT(*) AS row_count
    FROM mf_nav_prices
    GROUP BY scheme_code
) p ON p.scheme_code = h.scheme_code
WHERE jsonb_array_length(h.history::jsonb) <> COALESCE(p.row_count, 0)
ORDER BY scheme_code
LIMIT 50;
