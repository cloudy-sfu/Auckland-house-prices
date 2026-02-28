select
    properties.listing_id,
    concat(properties.entity ->> 'address', ', ', properties.entity ->> 'suburb') as address
from public.properties_trademe properties
where not exists (
    select 1
    from properties_trademe_land_tax land
    where land.listing_id = properties.listing_id
);
