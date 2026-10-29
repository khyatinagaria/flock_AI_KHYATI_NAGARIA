# Model results

Train houses [2, 5, 7, 9], validation house [15], test house [17]. Best iteration: 156.

## Test house 17

            MAE all minutes (W)  MAE while running (W)  total energy error (%)  daily energy MAE (kWh/day)  on/off precision  on/off recall  on/off F1
always_off               10.460                435.109                -100.000                       0.245             0.000          0.000      0.000
profile                  34.904                399.503                 152.529                       0.473             0.036          0.791      0.070
lightgbm                 15.319                291.691                  15.386                       0.230             0.249          0.812      0.382

## Validation house 15

            MAE all minutes (W)  MAE while running (W)  total energy error (%)  daily energy MAE (kWh/day)  on/off precision  on/off recall  on/off F1
always_off               17.194                585.997                -100.000                       0.381             0.000          0.000      0.000
profile                  41.830                557.162                  53.917                       0.587             0.038          0.671      0.071
lightgbm                 13.685                362.338                 -43.086                       0.250             0.542          0.716      0.617

## Top 10 features (split count)

min_120        610
hour           540
std_120        478
max_120        445
above_min60    383
mean_120       371
min_60         359
lead_30        356
steps_60       336
lag_30         294