select
    property_id,
    record_of_title,
    regexp_replace(address, ', Auckland$', '') as address
from properties_homes entity
where not exists (
    select 1
    from properties_homes_land_tax_link link
    where entity.property_id = link.property_id
);
