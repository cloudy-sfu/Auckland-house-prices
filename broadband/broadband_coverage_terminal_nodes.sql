SELECT
    p.z,
    p.x,
    p.y
FROM
    :table_name p
WHERE
    -- Check Q1: partially full but child (2*x, 2*y) is missing
    (p.q1_empty = FALSE AND p.q1_full = FALSE AND NOT EXISTS (
        SELECT 1 FROM public.broadband_coverage_tree c
        WHERE c.z = p.z + 1 AND c.x = p.x * 2 AND c.y = p.y * 2
    ))
    OR
    -- Check Q2: partially full but child (2*x + 1, 2*y) is missing
    (p.q2_empty = FALSE AND p.q2_full = FALSE AND NOT EXISTS (
        SELECT 1 FROM public.broadband_coverage_tree c
        WHERE c.z = p.z + 1 AND c.x = p.x * 2 + 1 AND c.y = p.y * 2
    ))
    OR
    -- Check Q3: partially full but child (2*x, 2*y + 1) is missing
    (p.q3_empty = FALSE AND p.q3_full = FALSE AND NOT EXISTS (
        SELECT 1 FROM public.broadband_coverage_tree c
        WHERE c.z = p.z + 1 AND c.x = p.x * 2 AND c.y = p.y * 2 + 1
    ))
    OR
    -- Check Q4: partially full but child (2*x + 1, 2*y + 1) is missing
    (p.q4_empty = FALSE AND p.q4_full = FALSE AND NOT EXISTS (
        SELECT 1 FROM public.broadband_coverage_tree c
        WHERE c.z = p.z + 1 AND c.x = p.x * 2 + 1 AND c.y = p.y * 2 + 1
    ));