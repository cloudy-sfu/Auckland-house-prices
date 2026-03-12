select count(*)
from properties_homes_land_tax_link link
where not exists (
    select 1
    from properties_land_tax entity
    where entity.assessment_id = link.assessment_id
);

delete from properties_homes_land_tax_link link
where not exists (
    select 1
    from properties_land_tax entity
    where entity.assessment_id = link.assessment_id
);