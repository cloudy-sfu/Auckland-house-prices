with suburbs_last_updated_time as (
    select
        suburbs.suburb_id,
        suburbs.geometry,
        max(search_time_utc) as last_updated_time
    from suburbs left join properties_homes
        on suburbs.suburb_id = properties_homes.suburb_id
    group by suburbs.suburb_id
)
select suburb_id, geometry -> 'coordinates' as coordinates
from suburbs_last_updated_time
where (now() - last_updated_time > interval '6 days 20 hours') or
      (last_updated_time is null)
