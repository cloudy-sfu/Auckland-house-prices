WITH all_months AS (
    -- Generate all months from Jan 2020 up to the target end month
    SELECT
        CAST(EXTRACT(year FROM d_series) AS INT) AS year,
        CAST(EXTRACT(month FROM d_series) AS INT) AS month
    FROM generate_series(
        CAST('2020-01-01' AS date),
        CAST(:end_month AS date),
        CAST('1 month' AS interval)
    ) AS d_series
),
expected_records AS (
    -- Create a Cartesian product of all suburbs and all generated months
    SELECT
        cs.suburb_id,
        am.year,
        am.month
    FROM crime_suburbs cs
    CROSS JOIN all_months am
)
-- Find the expected records that are missing in the crime_count table
SELECT
    er.suburb_id,
    er.year,
    er.month
FROM expected_records er
LEFT JOIN crime_count cc
    ON er.suburb_id = cc.suburb_id
    AND er.year = cc.year
    AND er.month = cc.month
WHERE cc ISNULL;
