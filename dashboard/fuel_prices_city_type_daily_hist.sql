-- Ref: https://www.postgresql.org/docs/current/functions-math.html
-- Ref: https://www.postgresql.org/docs/current/functions-datetime.html

WITH raw_data AS (
    SELECT
        p.fuel_type,
        CASE
            -- Auckland: https://bboxfinder.com/#-37.300000,174.000000,-36.000000,175.300000
            WHEN s.latitude >= -37.3 AND s.longitude BETWEEN 174.0 AND 175.3 THEN 'Auckland'
            -- Hamilton: https://bboxfinder.com/#-38.500000,174.800000,-37.300000,176.000000
            WHEN s.latitude BETWEEN -38.5 AND -37.3 AND s.longitude BETWEEN 174.8 AND 176.0 THEN 'Hamilton'
            -- Wellington: https://bboxfinder.com/#-41.500000,174.500000,-40.800000,175.500000
            WHEN s.latitude BETWEEN -41.5 AND -40.8 AND s.longitude BETWEEN 174.5 AND 175.5 THEN 'Wellington'
            -- Christchurch: https://bboxfinder.com/#-44.000000,172.000000,-43.000000,173.500000
            WHEN s.latitude BETWEEN -44.0 AND -43.0 AND s.longitude BETWEEN 172.0 AND 173.5 THEN 'Christchurch'
            ELSE 'Rural'
        END AS city,
        -- Convert to local NZ date for grouping
        DATE(p.update_time AT TIME ZONE 'Pacific/Auckland') AS price_date,
        p.price
    FROM public.fuel_prices p
    JOIN public.fuel_stations s
      ON p.station_id = s.station_id
    WHERE
        p.update_time >= :start_date
        AND p.update_time < :end_date
        AND p.price IS NOT NULL
        AND s.latitude IS NOT NULL
),
group_bounds AS (
    SELECT
        fuel_type,
        city,
        price_date,
        MIN(price) AS min_v,
        MAX(price) AS max_v,
        COUNT(*) AS total_count
    FROM raw_data
    GROUP BY fuel_type, city, price_date
),
binned_data AS (
    SELECT
        r.fuel_type,
        r.city,
        r.price_date,
        -- Add 0.001 to max_v to prevent division by zero if min_v = max_v
        width_bucket(r.price, b.min_v, b.max_v + 0.001, 100) AS bucket,
        COUNT(*) AS freq
    FROM raw_data r
    JOIN group_bounds b
      ON r.fuel_type = b.fuel_type
     AND r.city = b.city
     AND r.price_date = b.price_date
    GROUP BY r.fuel_type, r.city, r.price_date, bucket
)
SELECT
    bd.fuel_type,
    bd.city,
    bd.price_date,
    -- Calculate the starting price of the bucket
    CAST(b.min_v + (bd.bucket - 1) * ((b.max_v + 0.001 - b.min_v) / 100.0) AS numeric(6, 2))
        AS price_bucket_start,
    -- Calculate probability density
    (cast(bd.freq AS FLOAT) / b.total_count) AS probability_density
FROM binned_data bd
JOIN group_bounds b
  ON bd.fuel_type = b.fuel_type
 AND bd.city = b.city
 AND bd.price_date = b.price_date
ORDER BY bd.fuel_type, bd.city, bd.price_date, price_bucket_start;