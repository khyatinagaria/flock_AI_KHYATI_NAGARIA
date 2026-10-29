# Recommendation: washing-machine estimates from smart-meter data

*For a distribution utility's customer-insight team. Based on 6 UK REFIT homes, 1-minute data,
2013 to 2015, each tested as a home the model never saw. Details in [RESULTS.md](RESULTS.md).*

## Suitable uses and limits

| Use | Suitable? | Evidence |
|---|---|---|
| **When households wash, across many homes** (hour, weekday, evening-peak share) | **Yes** | Median F1 0.42 on unseen homes vs 0.10 for a usage-profile baseline; individual errors average out over a population. |
| **When one specific home washes** | **With care** | Works in 5 of 6 homes (F1 0.30 to 0.71); fails on a home with very short, low-energy washes (F1 0.11). |
| **Per-home washing-machine kWh (e.g. on a bill)** | **No** | Energy error ranged from -62% to +244% across the six homes. |
| **Real-time alerts** | **Not as built** | Uses 60 minutes of future data. |
| **15- or 30-minute meter data** | **No** | Needs 1-minute data (see last section). |

## Opportunity: move washing out of the evening peak

**Insight.** 24% of cycles start between 17:00 and 22:00. A cycle draws ~2.1 kW for 10 to 20 minutes;
machines have delay timers, so this is one of the easiest household loads to shift.

**Action.** Target homes whose detected cycles often start 17:00 to 20:00 with a "delay your wash"
nudge or a time-of-use tariff.

**Measurement.** Randomise eligible homes into nudge and control groups. Primary outcome: share of
detected cycles starting 17:00 to 20:00, before vs after (difference-in-differences); model errors
affect both groups equally and largely cancel. Secondary outcome: whole-home 17:00 to 20:00 load,
which needs no disaggregation. Confirm on a small sub-sample with plug monitors.

The value is network peak relief, not bill savings: washing is only 2.6 to 6.8% of household energy.

## Limitations

- **Overlapping signatures.** The washing machine's signature is a ~2 kW heating block, like kettles,
  ovens, dishwashers, tumble dryers and washer-dryers. The worst errors came from cooking and, most likely, from a
  home with a second, washer-dryer machine (+244% energy).
- **Missing data.** 6 to 25% of minutes were missing per home, with outages up to 62 days; stalled
  meters can repeat one value for hours and must be filtered.
- **Household differences.** Cycles per week (3.5 to 11), energy per cycle (0.31 to 0.70 kWh) and
  timing differ widely, so a model trained on four homes generalises unevenly.
- **UK to India.** Do not transfer without local data. Many Indian washing machines (semi-automatic
  and top-loading) wash cold with no heater, removing the signature the model relies on. Load mix
  (air conditioners, geysers, pumps, inverter batteries), voltage fluctuation, supply interruptions,
  shared meters and routines also differ. A model for India needs locally sub-metered homes.

## If only 15- or 30-minute data were available

A 10 to 20-minute heating phase would fall inside one or two readings and be averaged with
everything else in that interval. The sharp ~2 kW on/off steps and the heat-tumble-spin shape that
separate a wash from a kettle plus an oven would disappear. Per-cycle detection, duration, peak power
and per-home energy would become unreliable; what remains is energy per interval and, across many
homes, a statistical estimate of which intervals probably contain a wash. The model would also need
retraining, since every feature assumes 1-minute steps.
