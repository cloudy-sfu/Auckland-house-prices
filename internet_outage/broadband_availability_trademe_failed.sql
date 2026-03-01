-- delete from properties_trademe_chorus_tlc that
-- tlc exists (address found) but tlc not in internet_availability table
-- (fail when fetching detailed information)

delete from properties_trademe_chorus_tlc
where tlc is not null
and not exists (
    select 1
    from internet_availability
    where properties_trademe_chorus_tlc.tlc = internet_availability.tlc
);
