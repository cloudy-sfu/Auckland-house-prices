select
    t1.listing_id,
    concat(t1.entity ->> 'address', ', ', t1.entity ->> 'suburb',
    ', Auckland') as address
from public.properties_trademe t1
where not exists (
    select 1
    from properties_trademe_chorus_tlc t2
    where t1.listing_id = t2.listing_id
);
