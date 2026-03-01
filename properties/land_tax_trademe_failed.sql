-- delete from properties_trademe_land_rate_account_key that
-- land_id exists (address found) but land_id not in properties_land_tax table
-- (fail when fetching detailed information)

delete from properties_trademe_land_rate_account_key
where land_id is not null
and not exists (
    select 1
    from properties_land_tax
    where properties_trademe_land_rate_account_key.land_id = properties_land_tax.land_id
);
