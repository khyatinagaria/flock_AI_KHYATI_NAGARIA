# Recommendation: washing-machine estimates from smart-meter data

*For: distribution utility / customer-insight team. Based on 6 UK REFIT homes, 1-minute data,
2013 to 2015. Details in [RESULTS.md](RESULTS.md).*

## What the model can and cannot do

| Use | Suitable? | Why |
|---|---|---|
| **Detecting when a household washes** (time of day, weekday, cycles per week) | **Yes, with care** | Tested on each of six homes it never saw: median F1 0.42 (range 0.11 to 0.71), against 0.10 for a usage-profile baseline. Beats the baselines in 5 of 6 homes; fails on a home with very short, low-energy washes. |
| **Aggregated timing patterns across many homes** (e.g. share of washes in the evening peak) | **Yes** | Individual false alarms average out across a population; timing is what the model gets right. |
| **Per-home washing-machine kWh on a bill** | **No** | Across six unseen homes the energy error ranged from -62% to +244%. |
| **Real-time alerts** ("your wash just finished") | **Not as built** | It uses 60 minutes of future data; it would need a delayed version. |
| **15- or 30-minute smart-meter data** | **No** | Built and tested only on 1-minute data (see below). |

## One opportunity: shift washing out of the evening peak

**Insight.** 41% of cycles start between 07:00 and 12:00 and 24% between 17:00 and 22:00. A typical
cycle draws ~2.1 kW for 10 to 20 minutes and uses 0.3 to 0.7 kWh. Washing machines are one of the
easiest loads to move, because they have delay timers and nobody needs to be present.

**Offer.** Identify homes whose detected cycles often start between 17:00 and 20:00 and offer them a
time-of-use tariff or a "delay your wash" nudge (app message with a reminder to use the timer).

**How to measure it.** Randomised trial: half of the eligible homes get the nudge, half do not.
Primary outcome: share of detected cycles starting 17:00 to 20:00, before vs after, treated vs control
(difference-in-differences). Secondary: household load from 17:00 to 20:00 on the feeder or meter
(which needs no disaggregation and so is not affected by model error). Because the outcome is a
*change in timing* measured the same way in both groups, model false alarms mostly cancel out.
Validate with a small sub-sample of homes fitted with a plug monitor.

Note: this targets peak load, not total energy. A washing machine is only 2.6 to 6.8% of household
energy in these homes, so the bill saving for the customer is small; the value is in network peak.

## Limitations

- **Overlapping signatures.** The washing machine's signature is a ~2 kW heating block, the same as
  kettles, ovens, hobs, dishwashers, tumble dryers and immersion heaters. The worst errors came from
  cooking and from cycles that overlapped other loads.
- **Missing data.** 6 to 25% of minutes were missing per house, with outages up to 62 days. Stalled
  meters can repeat one value for hours; these must be filtered or they look like long appliance runs.
- **Household differences.** Cycles per week (3.5 to 11), energy per cycle (0.31 to 0.70 kWh) and
  timing differ a lot between homes. A model learned on four homes generalises unevenly (F1 0.11
  to 0.71 across six held-out homes); washer-dryers and other heating appliances inflate estimates.
- **UK to India.** These results should not be transferred without new data. Many Indian washing
  machines (especially semi-automatics and top-loaders) have no internal heater and wash cold, which
  removes the ~2 kW signature the model depends on. Other differences: different appliance mix
  (air conditioners, geysers, water pumps, inverters/UPS that charge batteries); voltage fluctuation
  and supply interruptions; shared or multi-family meters; and different weekly routines. A model for
  India needs locally sub-metered training homes.

## If only 15- or 30-minute data were available

At 15 or 30 minutes a washing machine's 10 to 20-minute heating phase falls inside one or two
readings and is averaged with everything else in that interval. The sharp ~2 kW on/off steps that
separate it from other loads disappear, as does the cycle's shape (heat, tumble, spin), so a 2 kW
block becomes indistinguishable from a kettle plus an oven. What remains possible is coarse: energy
per half-hour, and statistically estimating which half-hours *probably* include a wash across many
homes. Per-cycle detection, duration, peak power and per-home energy would become unreliable. The
model would also need retraining on downsampled data, because every feature here assumes 1-minute steps.
