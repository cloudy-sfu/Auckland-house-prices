#!/bin/bash

BASE_DIR=$(pwd)
JOB_SCRIPT_PATH="$BASE_DIR/collect_schools.sh"

# Create job script
# Defining NEON_DB is necessary because environment variables aren't guaranteed to
# be defined before called.
cat > "$JOB_SCRIPT_PATH" <<EOF
#!/bin/bash
cd $BASE_DIR
source .venv/bin/activate
export NEON_DB="$NEON_DB"
export TG_BOT_TOKEN="$TG_BOT_TOKEN"
export TG_CHAT_ID="$TG_CHAT_ID"
export PYTHONPATH=\$PYTHONPATH:$BASE_DIR
python schools/get_school_meta.py
python schools/get_school_zone.py
EOF
chmod +x "$JOB_SCRIPT_PATH"

# Register job in crontab
# Once every year
CRON_JOB="0 0 1 1 * $JOB_SCRIPT_PATH"
# Ref: https://man7.org/linux/man-pages/man1/crontab.1.html
(crontab -l 2>/dev/null | grep -v "$JOB_SCRIPT_PATH"; echo "$CRON_JOB") | crontab -

echo "Done. $JOB_SCRIPT_PATH created and cron job registered."
