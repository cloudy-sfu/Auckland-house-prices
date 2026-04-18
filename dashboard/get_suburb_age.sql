SELECT
    a.suburb_id,
    a.age_group,
    a.percentage
FROM public.suburbs s
JOIN public.age_structure a
    ON s.suburb_id = a.suburb_id
WHERE a.year = :year
  AND s.suburb_id = :suburb_id
ORDER BY a.age_group;