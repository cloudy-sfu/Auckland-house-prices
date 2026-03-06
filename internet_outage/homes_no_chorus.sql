select
    property_id,
    address
from properties_homes entity
where not exists (
    select 1
    from properties_homes_internet_availability_link link
    where entity.property_id = link.property_id
);
