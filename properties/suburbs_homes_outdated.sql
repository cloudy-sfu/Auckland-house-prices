with suburbs_last_updated_time as (
    select
        suburbs.suburb_id,
        suburbs.geometry,
        max(search_time_utc) as last_updated_time
    from suburbs left join properties_homes
        on suburbs.suburb_id = properties_homes.suburb_id
    where suburbs.suburb_id not in (
        -- Suburbs of no house
        113700 -- Riverhead Forest
        ,154600 -- Botany Central
        ,161700 -- Takanini Industrial
        ,149600 -- Ōtāhuhu Industrial
        ,138800 -- Wesley South
        ,147700 -- Mount Wellington Industrial
        )
    group by suburbs.suburb_id
)
select suburb_id, geometry -> 'coordinates' as coordinates
from suburbs_last_updated_time
where (now() - last_updated_time > interval '6 days 20 hours') or
      (last_updated_time is null)
