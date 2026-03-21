select count(*)
from properties_homes_broadband_availability_link link
where link.tlc is not null
  and not exists (
    select 1
    from broadband_availability entity
    where entity.tlc = link.tlc
  );

delete
from properties_homes_broadband_availability_link link
where link.tlc is not null
  and not exists (
    select 1
    from broadband_availability entity
    where entity.tlc = link.tlc
  );
