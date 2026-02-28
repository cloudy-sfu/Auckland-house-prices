select
    properties.listing_id,
    concat(properties.entity ->> 'address', ', ', properties.entity ->> 'suburb',
    ', Auckland') as address
from public.properties_trademe properties
where not exists (
    select 1
    from properties_trademe_broadband broadband
    where broadband.listing_id = properties.listing_id
);
