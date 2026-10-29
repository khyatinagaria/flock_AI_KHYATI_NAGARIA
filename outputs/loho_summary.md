# Leave-one-house-out results

Each row: model trained on 4 houses, validation house for early stopping and threshold, evaluated on the held-out test house.

## MAE while running (W)

test_house         2        5        7        9       15       17   median      min      max
model                                                                                       
always_off   384.721  390.718  451.614  558.313  585.997  435.109  443.361  384.721  585.997
profile      357.610  370.608  422.712  521.432  556.901  401.001  411.856  357.610  556.901
lgbm_direct  358.179  360.214  416.427  368.603  357.845  280.173  359.197  280.173  416.427
lgbm_2stage  305.334  386.779  330.061  278.555  244.439  195.467  291.945  195.467  386.779

## total energy error (%)

test_house         2        5        7        9       15       17   median      min      max
model                                                                                       
always_off  -100.000 -100.000 -100.000 -100.000 -100.000 -100.000 -100.000 -100.000 -100.000
profile       16.573  -50.702  -46.759   59.904   55.821  151.515   36.197  -50.702  151.515
lgbm_direct   16.718  -34.681  -42.258   94.758  -41.622    8.254  -13.214  -42.258   94.758
lgbm_2stage   67.391  -61.732    7.952  244.189  -20.832  135.279   37.672  -61.732  244.189

## daily energy MAE (kWh/day)

test_house       2      5      7      9     15     17  median    min    max
model                                                                      
always_off   0.411  0.710  0.881  0.364  0.381  0.245   0.396  0.245  0.881
profile      0.409  0.695  0.565  0.516  0.590  0.472   0.541  0.409  0.695
lgbm_direct  0.392  0.628  0.513  0.457  0.248  0.187   0.424  0.187  0.628
lgbm_2stage  0.535  0.653  0.456  0.899  0.154  0.365   0.496  0.154  0.899

## on/off precision

test_house       2      5      7      9     15     17  median    min    max
model                                                                      
always_off   0.000  0.000  0.000  0.000  0.000  0.000   0.000  0.000  0.000
profile      0.070  0.115  0.143  0.042  0.038  0.034   0.056  0.034  0.143
lgbm_direct  0.148  0.217  0.288  0.145  0.566  0.243   0.230  0.145  0.566
lgbm_2stage  0.276  0.354  0.618  0.246  0.765  0.307   0.331  0.246  0.765

## on/off recall

test_house       2      5      7      9     15     17  median    min    max
model                                                                      
always_off   0.000  0.000  0.000  0.000  0.000  0.000   0.000  0.000  0.000
profile      0.675  0.457  0.737  0.734  0.680  0.728   0.704  0.457  0.737
lgbm_direct  0.388  0.332  0.780  0.924  0.694  0.839   0.737  0.332  0.924
lgbm_2stage  0.331  0.068  0.594  0.947  0.667  0.822   0.631  0.068  0.947

## on/off F1

test_house       2      5      7      9     15     17  median    min    max
model                                                                      
always_off   0.000  0.000  0.000  0.000  0.000  0.000   0.000  0.000  0.000
profile      0.127  0.183  0.239  0.080  0.072  0.065   0.103  0.065  0.239
lgbm_direct  0.214  0.263  0.421  0.251  0.624  0.377   0.320  0.214  0.624
lgbm_2stage  0.301  0.114  0.606  0.391  0.713  0.447   0.419  0.114  0.713

## Folds

 test_house  val_house  threshold
          2          5       0.10
          5          7       0.35
          7          9       0.40
          9         15       0.15
         15         17       0.15
         17          2       0.10