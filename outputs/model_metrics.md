# Model results

Train houses [2, 5, 7, 9], validation house [15], test house [17]. Best iterations: direct 125, classifier 65, running-power regressor 283. Two-stage threshold (chosen on validation house): 0.1.

## Test house 17

             MAE all minutes (W)  MAE while running (W)  total energy error (%)  daily energy MAE (kWh/day)  on/off precision  on/off recall  on/off F1
always_off                10.507                435.109                -100.000                       0.245             0.000          0.000      0.000
profile                   35.296                399.195                 154.972                       0.479             0.037          0.801      0.070
lgbm_direct               14.109                295.968                   1.081                       0.202             0.253          0.790      0.383
lgbm_2stage               16.419                193.576                  89.810                       0.259             0.329          0.791      0.465

## Validation house 15

             MAE all minutes (W)  MAE while running (W)  total energy error (%)  daily energy MAE (kWh/day)  on/off precision  on/off recall  on/off F1
always_off                17.221                585.997                -100.000                       0.381             0.000          0.000      0.000
profile                   42.206                556.901                  55.821                       0.590             0.038          0.680      0.072
lgbm_direct               13.696                357.845                 -41.622                       0.248             0.566          0.694      0.624
lgbm_2stage               10.212                215.434                  -6.778                       0.147             0.724          0.747      0.735

## Top 10 features of the classifier (split count)

min_120     370
hour        343
max_120     324
std_120     235
dow         192
std_5       132
lag_30      130
lead_30     130
max_60      119
mean_120    113