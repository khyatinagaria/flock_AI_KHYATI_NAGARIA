# Washing-machine EDA summary (CLEAN REFIT, 1-minute)

Cycle rule: running when > 20 W; pauses <= 10 min joined; kept if >= 10 min, peak >= 200 W, >= 0.05 kWh; cycles touching a data gap dropped.

| | House 2 | House 5 | House 7 | House 9 | House 15 | House 17 |
|---|---|---|---|---|---|---|
| channel | Appliance2 | Appliance3 | Appliance5 | Appliance3 | Appliance3 | Appliance4 |
| first day | 2013-09-17 | 2013-09-26 | 2013-11-01 | 2013-12-17 | 2013-12-17 | 2014-03-06 |
| last day | 2015-05-28 | 2015-07-06 | 2015-07-08 | 2015-07-08 | 2015-07-08 | 2015-06-19 |
| span (days) | 617 | 648 | 613 | 568 | 567 | 470 |
| missing minutes (%) | 24.6 | 9.2 | 12.5 | 15.3 | 13.5 | 6.1 |
| gaps > 5 min | 463 | 817 | 118 | 79 | 691 | 109 |
| longest gap (days) | 62.0 | 8.6 | 41.6 | 41.6 | 8.6 | 8.6 |
| minutes with REFIT issue flag (%) | 2.0 | 8.4 | 4.6 | 2.4 | 1.6 | 4.3 |
| WM exactly 0 W (%) | 94.4 | 52.1 | 74.9 | 90.6 | 96.1 | 96.6 |
| WM off, <= 20 W (%) | 95.3 | 92.2 | 91.6 | 97.3 | 97.1 | 97.6 |
| cycles detected | 313 | 699 | 844 | 243 | 248 | 280 |
| cycles per week | 4.7 | 8.3 | 11.0 | 3.5 | 3.5 | 4.4 |
| median duration (min) | 98.0 | 46.0 | 60.0 | 74.0 | 91.0 | 61.0 |
| median peak (W) | 2091 | 2074 | 2083 | 2210 | 2180 | 2046 |
| median energy (kWh) | 0.63 | 0.31 | 0.54 | 0.65 | 0.7 | 0.38 |
| WM share of household energy (%) | 3.9 | 4.2 | 6.8 | 2.6 | 6.7 | 2.6 |

Most common start hour per house: H2: 09:00, H5: 10:00, H7: 07:00, H9: 11:00, H15: 05:00, H17: 09:00
Share of cycles at weekends (%): H2: 25, H5: 59, H7: 29, H9: 52, H15: 29, H17: 29