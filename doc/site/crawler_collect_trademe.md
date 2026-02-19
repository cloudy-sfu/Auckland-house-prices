# Crawler: collect "trademe"

This job collects currently listing properties (houses) for sale in Auckland from "trademe".

>   [!WARNING]
>
>   This job requires New Zealand residence IP and HTTPS connection.
>
>   Foreign or data center source IP doesn't work. HTTP proxy doesn't work.



Data source: [Auckland properties](https://www.trademe.co.nz/a/property/residential/sale/auckland)



## Install

![](https://shields.io/badge/OS-Linux-blue) 

Let `$base_dir` be the root directory of this (Auckland house pricing) program.

Let `$neon_db` be the connection string to the database.

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
