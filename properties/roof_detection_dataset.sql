select setseed(-0.7049451881264432);

select
    p.property_id,
    p.latitude,
    p.longitude
from properties_homes p
    join suburbs s on p.suburb_id = s.suburb_id
where ownership_type in ('Freehold', 'Cross Lease')
order by random()
limit 1200;
