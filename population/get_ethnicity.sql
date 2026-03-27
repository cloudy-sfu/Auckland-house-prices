SELECT
    s.suburb_id,
    s.name,
    s.geometry,
    e.percentage,
    p.value AS population
FROM public.suburbs s
JOIN public.ethnicity e
    ON s.suburb_id = e.suburb_id
LEFT JOIN public.population p
    ON s.suburb_id = p.suburb_id AND e.year = p.year
WHERE e.year = :year
  AND e.ethnicity = :ethnicity;