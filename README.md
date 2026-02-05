# Auckland house prices

Price assessment models for houses in Auckland, New Zealand

![](https://shields.io/badge/dependencies-Python_3.13-blue)



## Install

### Database

Create a PostgreSQL 17 database in [Neon](https://neon.com/) database, or your own PostgreSQL database.

Run `database_schema.sql` in database console to mock the database schema.

Import `fuel_stations.csv`  to database table `public.fuel_stations` as the initialization. The program will update this table when it gets fuel prices.



### Python environments

Include the following variables into environment variables.

| Variable       | Description                                                  |
| -------------- | ------------------------------------------------------------ |
| NEON_DB        | Connection string to Neon database. If using other database, set to connection string of your own PostgreSQL database. |
| GASPY_EMAIL    | Email of "gaspy" account.                                    |
| GASPY_PASSWORD | Password of "gaspy" account.                                 |



Main environment:

>   Create and activate a Python 3.13 virtual environment.
>
>   Run the following command.
>
>   ```
>   pip install -r requirements.txt
>   ```
>

Dashboard environment:

>   Create and activate a Python 3.13 virtual environment.
>
>   Run the following command.
>
>   ```
>   pip install -r requirements-dash.txt
>   ```
>



### Automatic jobs

Use the main Python environment.

This program can get data from the following sources and saves to Neon database.

| Data source                                                  | Items                             | Entrance script          | Host                                                       | Frequency                    |
| ------------------------------------------------------------ | --------------------------------- | ------------------------ | ---------------------------------------------------------- | ---------------------------- |
| [Gaspy](https://gaspy.nz)                                    | Petrol and diesel prices          | `get_gaspy.py`           | GitHub Actions `get_gaspy.yml`                             | Everyday, 6:00 UTC           |
| [Chorus](https://www.chorus.co.nz/help/tools/internet-outages-map) | Internet outage map               | `get_chorus_outage.py`   | GitHub Actions `get_chorus_outage.yml`                     | Everyday, 10:00 UTC          |
| [Trademe](https://www.trademe.co.nz/a/property/residential/sale/auckland) | Property listing, houses on sales | `get_trademe_listing.py` | Self-hosted (require New Zealand residence IP, only HTTPS) | Monday to Friday, 16:08 NZDT |



## Usage

### Fuel prices dashboard

Steps:

>   Activate the dashboard environment and run the following command.
>
>   ```
>   python dashboard_fuel_prices.py
>   ```
>
>   Copy the link from output of terminal and visit the link in browser.

