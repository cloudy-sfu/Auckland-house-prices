# Collect Internet outage map

This job collects Internet outage area and time from "chorus", which is the monopoly Internet fiber installer in Auckland. The database includes not only Auckland, but also other cities where "chorus" provides Internet hardware.

Data source: https://www.chorus.co.nz/help/tools/internet-outages-map

## Usage

This job is defined in `.github/workflows/crawler_collect_chorus.yml` and deployed to GitHub Actions.

This job runs everyday at 10:00 UTC.

