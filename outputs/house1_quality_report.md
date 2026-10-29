# House 1 raw data: quality report

Files: RAW_House1_Part1.csv, RAW_House1_Part2.csv

## Inspection (raw, before cleaning)

| check | result |
|---|---|
| rows | 8518763 |
| unparseable Time | 0 |
| Time vs Unix differ by > 2 s | 0 |
| first timestamp | 2013-10-09 14:06:17 |
| last timestamp | 2015-07-10 11:56:32 |
| backward jumps in file order | 2 |
| rows earlier than a previous row | 946002 |
| large backward jumps at (local time) | 2013-10-27 01:00:01, 2014-06-27 21:57:50 |
| ~1 h forward jumps at (local time) | 2014-03-30 02:00:02, 2014-07-30 15:15:23, 2015-03-29 02:00:01 |
| exact duplicate rows | 595940 |
| duplicate Unix with different values | 1046136 |
| part 1 span (local) | 2013-10-09 14:06:17 -> 2014-10-01 01:27:07, 4,377,877 rows |
| part 1 NaN power values | 0 |
| part 2 span (local) | 2014-06-27 21:57:49 -> 2015-07-10 11:56:32, 4,140,886 rows |
| part 2 NaN power values | 5284083 |
| part 2 rows overlapping part 1 | 945403 |
| sampling interval median / p90 / p99 (s) | 7 / 13 / 15 |
| intervals > 2 min | 715 |
| intervals > 1 h | 33 |
| longest interval (days) | 41.6 |
| negative power values | 0 |
| Aggregate > 20000 W | 127 |
| appliance values > 4000 W | 3949 |
| max value per channel | Aggregate=29159, Appliance1=76677, Appliance2=98301, Appliance3=73725, Appliance4=98301, Appliance5=73725, Appliance6=37610, Appliance7=98299, Appliance8=98301, Appliance9=65535 |

## Cleaning log

| step | count |
|---|---|
| overlapping Part2 rows dropped | 945403 |
| rows in unresolvable repeated DST hour dropped | 986 |
| exact duplicate rows dropped | 884252 |
| same-timestamp rows merged | 131753 |
| Aggregate values set to NaN | 95 |
| appliance values set to NaN | 3228 |
| minutes in span | 920031 |
| minutes with no samples | 122187 |
| minutes filled by interpolation | 7061 |
| minutes flagged as outage | 121393 |
| outage share of span (%) | 13.19 |

## Outages longer than 5 min: 410

Ten longest:

| start (UTC) | end (UTC) | hours |
|---|---|---|
| 2014-01-24 01:57 | 2014-03-06 16:23 | 998.43 |
| 2015-05-10 22:37 | 2015-05-19 14:10 | 207.55 |
| 2015-06-10 12:20 | 2015-06-18 00:39 | 180.32 |
| 2014-08-30 11:01 | 2014-09-04 10:33 | 119.53 |
| 2015-04-03 00:44 | 2015-04-07 09:18 | 104.57 |
| 2015-03-22 08:16 | 2015-03-24 15:23 | 55.12 |
| 2015-05-24 09:10 | 2015-05-26 11:09 | 49.98 |
| 2014-10-27 00:06 | 2014-10-28 13:46 | 37.67 |
| 2015-03-31 03:23 | 2015-04-01 15:26 | 36.05 |
| 2015-03-15 10:03 | 2015-03-16 16:16 | 30.22 |