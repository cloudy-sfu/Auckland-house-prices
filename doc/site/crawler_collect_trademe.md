# Collect Auckland properties

This job collects currently listing properties (houses) for sale in Auckland from "trademe".

![](./assets/OS-Linux-blue.svg)
![](https://shields.io/badge/dependencies-Python_3.13-blue)
![](https://shields.io/badge/network-New_Zealand_IP_HTTPS-brown)

Data source: https://www.trademe.co.nz/a/property/residential/sale/auckland



## Install

Let `$base_dir` be the root directory of this (Auckland house pricing) program.

Let `$neon_db` be the connection string to the database.

Activate Python environment "Data collection - Self-hosted".

Create a `crawler_colelct_trademe.sh` script and write the following content.

```
#!/bin/bash
cd $base_dir
source .venv/bin/activate
export NEON_DB="$neon_db"
export PYTHONPATH=$PYTHONPATH:$base_dir
python properties/get_trademe_listing.py > log.txt 2>&1
```

>   [!NOTE]
>
>   Line 4 is necessary, because this script will be triggered by `crontab`. There is no way to define this environment variables before the script is called, unless registering the variable to the global user/machine's environment variables.

>   [!TIP]
>
>   **Telegram notification**
>
>   To send the log file to Telegram group, letting you get notified, follow the steps below.
>
>   Create a new bot in telegram.
>
>   Let `${BOT_TOKEN|` be the robot's access token.
>
>   Create a group and invite the bot.
>
>   Send any message in the group.
>
>   Visit `https://api.telegram.org/bot${BOT_TOKEN}/getUpdates`. Find the following message in the response.
>
>   ```
>   "from":{"id": ..., "is_bot":false, "first_name": ...,"language_code":"en"},
>   ```
>
>   Let `${CHAT_ID|` be the value in `id` field in this response.
>
>   Append the following content to `crawler_colelct_trademe.sh`.
>
>   ```
>   curl -s -F document=@"log.txt" \
>        -F caption="Auckland houses log" \
>        "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument?chat_id=${CHAT_ID}" > /dev/null
>   ```

Run the following command.

```
date
```

>   [!NOTE]
>
>   Assume the system time zone is NZST or NZDT. Otherwise, the job starting time will be different from that described in usage.

Run the following command.

```
chmod +x $base_dir/crawler_colelct_trademe.sh
crontab -e
```

`crontab` config file will be open. Append the following content to the end of the file and save.

```
0 16 * * 1-5 $base_dir/crawler_colelct_trademe.sh
```



## Usage

This job will run in local machine automatically every working day 16:00 in New Zealand time zone.
