select
    t1.property_id
from public.properties_homes t1
where not exists (
    select 1
    from public.properties_homes_detail t2
    where t2.property_id = t1.property_id
);