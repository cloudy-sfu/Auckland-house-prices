select s.suburb_id, geometry
from suburbs s
    join (
        select suburb_id, max(search_time_utc)
        from properties_homes
        group by suburb_id
        having now() - max(search_time_utc) > interval '6 days 20 hours'
    ) p
    on s.suburb_id = p.suburb_id
