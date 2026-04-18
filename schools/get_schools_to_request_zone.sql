select
    school_number
from schools
where enrollment_scheme is true
    and not exists (
    select 1
    from schools_zones
    where schools.school_number = schools_zones.school_number
);
