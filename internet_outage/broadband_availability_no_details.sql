with link as (
    select property_id, tlc, row_number() over () as row_id
    from properties_homes_internet_availability_link
)
select property_id, tlc, row_id
from link
where not exists(
    select 1
    from internet_availability entity
    where entity.tlc = link.tlc
)