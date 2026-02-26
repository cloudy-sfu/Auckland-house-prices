#!/bin/bash

BASE_DIR=$(pwd)
JOB_SCRIPT_PATH="$BASE_DIR/collect_trademe.sh"

# Create job script
# Defining NEON_DB is necessary because environment variables aren't guaranteed to
# be defined before called.
cat > "$JOB_SCRIPT_PATH" <<EOF
#!/bin/bash
cd $BASE_DIR
source .venv/bin/activate
export NEON_DB="$NEON_DB"
export PYTHONPATH=\$PYTHONPATH:$BASE_DIR
python properties/get_trademe_listing.py
EOF
chmod +x "$JOB_SCRIPT_PATH"

# Register job in crontab
# Work days 16:00 UTC+12/UTC+13
CRON_JOB="0 16 * * 1-5 $JOB_SCRIPT_PATH"
# Ref: https://man7.org/linux/man-pages/man1/crontab.1.html
(crontab -l 2>/dev/null | grep -Fq "$JOB_SCRIPT_PATH") || \
  (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Done. $JOB_SCRIPT_PATH created and cron job registered."
