create table public.trademe_properties
(
    listing_id varchar(16) not null
        constraint properties_pkey
            primary key,
    start_time timestamp with time zone,
    entity     jsonb,
    task_id    integer
        constraint task_id
            references public.trademe_crawler
);

comment on table public.trademe_properties is 'Auckland houses'' properties information in Trademe.';

comment on column public.trademe_properties.listing_id is 'The house''s ID listed in Trademe.';

comment on column public.trademe_properties.start_time is 'Start time of the house listed in Trademe.';

comment on column public.trademe_properties.entity is 'House''s detailed information.';

comment on column public.trademe_properties.task_id is 'The record is retrieved by which web crawler job.';

alter table public.trademe_properties
    owner to neondb_owner;

