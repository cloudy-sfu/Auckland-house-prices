# Crawler: collect "gaspy"

This job collects the fuel (petrol and diesel) prices every day in most petrol stations in Auckland, Hamilton, Wellington, and Christchurch. It includes the prices of different types of fuels, alongside with the location of the fuel station.



## Install

Import data in `fuel/fuel_stations.csv` to `public.fuel_stations` table in database.

>   [!NOTE]
>
>   To search for fuel (petrol) stations in Gaspy, the program reads `geo_hash` in table  `fuel_stations`, functioning as the input argument (searching query). Gaspy returns `geo_hash` of stations and the current fuel prices of each fuel type in each fuel station. The returned stations list may be different than the searching query, therefore the program can  update the stations table.
>
>   To start with, the program needs a initial `fuel_stations` table.

Besides environment variables in the global installation guidance, also include the following variables into environment variables.

| Variable       | Description                  |
| -------------- | ---------------------------- |
| GASPY_EMAIL    | Email of "gaspy" account.    |
| GASPY_PASSWORD | Password of "gaspy" account. |



## Usage

This job is defined in `.github/workflows/crawler_collect_gaspy.yml` and deployed to GitHub Actions.

This job runs everyday at 6:00 UTC.

