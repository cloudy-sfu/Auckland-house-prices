-- Get total crime counts per suburb within a date range
SELECT
    s.suburb_id,
    s.name,
    s.geometry,
    COALESCE(SUM(c.assault), 0)
      + COALESCE(SUM(c.burglary), 0)
      + COALESCE(SUM(c.endanger_people), 0)
      + COALESCE(SUM(c.robbery), 0)
      + COALESCE(SUM(c.sexual_offence), 0)
      + COALESCE(SUM(c.theft), 0) AS total_crimes
FROM public.suburbs s
LEFT JOIN public.crimes c
    ON s.suburb_id = c.suburb_id
   AND (c.year * 12 + c.month) >= (:start_year * 12 + :start_month)
   AND (c.year * 12 + c.month) <= (:end_year * 12 + :end_month)
GROUP BY s.suburb_id, s.name, s.geometry;