# Auckland house prices

Price assessment models for houses in Auckland, New Zealand

![](https://shields.io/badge/dependencies-Python_3.13-blue)
![](https://shields.io/badge/dependencies-New_Zealand_residential_IP-blue)

## Install

### Database

Create a [Neon](https://neon.com/) PostgreSQL 17.7 database. "Settings > Compute defaults > Scale to zero" must keep default (5 minutes) or longer.

Setup the database schema by `database_schema.sql`.

>   [!note]
>
>   Any other PostgreSQL database release may work, but is not tested. If using other database, replace the [connection string](https://neon.com/docs/connect/connect-from-any-app) to Neon database by the [connection string](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING) to your own PostgreSQL database.



### GitHub Actions

Deploy this program in GitHub and enable GitHub Actions for this repository.

Manually run each scheduled job once, to initially save data into database and ensure all the GitHub Actions are active.

Add the following variables into GitHub repository settings "Secrets and variables > Actions > Secrets > Repository secrets".

| Used by             | Variable       | Description                         |
| ------------------- | -------------- | ----------------------------------- |
| (All)               | NEON_DB        | Connection string to Neon database. |
| `collect_gaspy.yml` | GASPY_EMAIL    | Email of "gaspy" account.           |
| `collect_gaspy.yml` | GASPY_PASSWORD | Password of "gaspy" account.        |



### Self-hosted scheduled jobs

The computer which hosts scheduled jobs should satisfy the following requirements.

-   Based on any Linux X64 operation system.
-   Never turn off when scheduled jobs are active.
-   Connect to the Internet by a New Zealand residential IP.
-   Installed Chromium or Google Chrome.
-   The system time zone should be Pacific/Auckland. (Run `date` in terminal to confirm; the job still works if using different time zone, but data collection time will be sifted from described.)

Create and activate a Python virtual environment. Run the following command in terminal.

```
sudo apt install xvfb
pip install -r requirements.txt
```

Add the following variables into environment variables.

| Variable     | Description                                                  |
| ------------ | ------------------------------------------------------------ |
| NEON_DB      | Connection string to Neon database.                          |
| TG_BOT_TOKEN | Access token of the new bot, which you created in telegram with `@BotFather`. |
| TG_CHAT_ID   | Create a group and invite the bot. Send any message in the group. Visit `https://api.telegram.org/bot${BOT_TOKEN}/getUpdates`. In the response, find the message like `"from":{"id": ..., "is_bot":false, "first_name": ...,"language_code":"en"},`. This variable is the value in `id` field in this response. |

Run the following commands in terminal to install the self-hosted jobs.

```bash
chmod -R 755 scheduled_jobs/
./scheduled_jobs/install_collect_trademe.sh
./scheduled_jobs/install_collect_schools.sh
```

>   [!important]
>
>   The secret tokens will be written to bash scripts in the folder. Do not re-distribute after installation, unless you intended to copy over the secret tokens.



### Dashboards

Create and activate a Python virtual environment. Run the following command in terminal.

```
pip install -r requirements-dash.txt
```

Add the following variables into environment variables.

| Variable | Description                         |
| -------- | ----------------------------------- |
| NEON_DB  | Connection string to Neon database. |



## Usage

### Descriptive visualization

Activate "Dashboards" Python virtual environment. Run the following command in terminal.

```
python dashboard/app.py
```

Find the URL in terminal output and open in the browser.

