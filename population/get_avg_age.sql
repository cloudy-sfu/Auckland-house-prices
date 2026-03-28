SELECT
    s.suburb_id,
    s.name,
    s.geometry,
    SUM(a.percentage / 100 * (a.age_group + 2.5)) AS avg_age,
    MAX(p.value) AS population
FROM public.suburbs s
JOIN public.age_structure a
    ON s.suburb_id = a.suburb_id
LEFT JOIN public.population p
    ON s.suburb_id = p.suburb_id AND a.year = p.year
WHERE a.year = :year
GROUP BY s.suburb_id, s.name, s.geometry;