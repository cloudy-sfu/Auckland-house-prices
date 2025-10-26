create table public.trademe_crawler
(
    solving_start_time  timestamp with time zone,
    solving_end_time    timestamp with time zone,
    stop_before_page    smallint,
    failed_pages        integer[],
    id                  serial
        primary key,
    complete_after_page smallint
);

comment on table public.trademe_crawler is 'Web crawler jobs to retrieve Trademe properties.';

comment on column public.trademe_crawler.solving_start_time is 'Start time of web crawler job.';

comment on column public.trademe_crawler.solving_end_time is 'End time of web crawler job. If this field is not null, the web crawler is successfully executed.';

comment on column public.trademe_crawler.stop_before_page is 'Web crawler stopped (without completed) before retrieving this page.';

comment on column public.trademe_crawler.failed_pages is 'List of page numbers that failed to be retrieved.';

comment on column public.trademe_crawler.complete_after_page is 'Web crawler is successfully executed after retrieving this page.';

alter table public.trademe_crawler
    owner to neondb_owner;

