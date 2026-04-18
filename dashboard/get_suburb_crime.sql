-- Get monthly crime breakdown for a single suburb
SELECT
    c.year,
    c.month,
    COALESCE(c.assault, 0)         AS assault,
    COALESCE(c.burglary, 0)        AS burglary,
    COALESCE(c.endanger_people, 0) AS endanger_people,
    COALESCE(c.robbery, 0)         AS robbery,
    COALESCE(c.sexual_offence, 0)  AS sexual_offence,
    COALESCE(c.theft, 0)           AS theft
FROM public.crimes c
WHERE c.suburb_id = :suburb_id
ORDER BY c.year, c.month;