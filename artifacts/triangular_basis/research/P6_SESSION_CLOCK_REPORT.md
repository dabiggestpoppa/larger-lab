# P6.3 — SESSION-CLOCK REPORT

Entry quality vs time. Signal preserved; only conditioning is measured. Spread is NOT in the frozen OHLC feed — recorded as unavailable; the liquidity-adjacent state variable is 5-min realized basis vol (fingerprint).

## Hour-of-day (EST)

| hour | N | EV TB-B | EV TB-C5% | PF TB-B | WR | conv med | fail |
|---|---|---|---|---|---|---|---|
| 3 | 75 | 26.81 | 25.16 | 175.34 | 97.3% | 232 | 7% |
| 4 | 41 | 27.42 | 25.78 | 4943.66 | 97.6% | 218 | 12% |
| 5 | 50 | 19.23 | 18.07 | 13.92 | 92.0% | 205 | 14% |
| 6 | 59 | 19.74 | 18.63 | 28.34 | 93.2% | 135 | 24% |
| 7 | 63 | 14.24 | 13.03 | 10.14 | 85.7% | 205 | 44% |
| 8 | 67 | 11.70 | 10.97 | 7.11 | 77.6% | 160 | 55% |
| 9 | 27 | -3.96 | -4.58 | 0.47 | 44.4% | 58 | 93% |
| 10 | 23 | 17.34 | 15.91 | 6.10 | 69.6% | 30 | 74% |

## Session thirds + transition proximity

- **third = early:** N=166, EV TB-B 24.68, PF 48.55, conv median 215 min, failure 10%
- **third = late:** N=50, EV TB-B 5.83, PF 2.05, conv median 50 min, failure 84%
- **third = mid:** N=189, EV TB-B 15.06, PF 11.58, conv median 168 min, failure 42%
- **within 30m of 5 EST (Tokyo overlap) = False:** N=353, EV TB-B 17.53, PF 11.27, conv median 195 min, failure 37%
- **within 30m of 5 EST (Tokyo overlap) = True:** N=52, EV TB-B 20.09, PF 34.39, conv median 210 min, failure 17%
- **within 30m of 8 EST (NY open) = False:** N=337, EV TB-B 18.76, PF 12.81, conv median 192 min, failure 31%
- **within 30m of 8 EST (NY open) = True:** N=68, EV TB-B 13.41, PF 10.28, conv median 195 min, failure 51%

## Dead zones & dominance
- Dead zones (bucket N>=10, EV TB-B <= 0): ['half_hour=12', 'half_hour=13', 'quarter_hour=26'].
- Best half-hour: 60-90 min after London open (EV TB-B 33.91, N=20).
- Convergence speed: early median 215 min vs late 50 min → late similar or faster.

## Threshold x session third (TB-B / TB-C-5% EV, N)

| z | early | mid | late |
|---|---|---|---|
| 1.50 | 16.0/14.8 (N=679) | 7.0/6.4 (N=459) | -0.8/-1.3 (N=203) |
| 1.75 | 18.9/17.6 (N=520) | 9.1/8.4 (N=378) | 1.1/0.5 (N=156) |
| 2.00 | 20.6/19.2 (N=367) | 10.8/10.0 (N=303) | 4.1/3.2 (N=117) |
| 2.25 | 22.6/21.0 (N=250) | 13.1/12.2 (N=241) | 5.3/4.3 (N=85) |
| 2.50 | 24.7/23.2 (N=166) | 15.1/14.0 (N=189) | 5.8/4.8 (N=50) |
| 2.75 | 27.8/26.0 (N=103) | 16.9/16.0 (N=133) | 9.4/8.1 (N=36) |
| 3.00 | 28.4/26.5 (N=72) | 21.4/20.2 (N=89) | 16.1/14.7 (N=33) |
| 3.25 | 30.4/28.6 (N=41) | 21.2/20.1 (N=68) | 15.4/13.9 (N=25) |
| 3.50 | 35.6/33.5 (N=24) | 19.5/18.0 (N=37) | 21.0/19.3 (N=18) |
| 3.75 | 27.0/25.1 (N=13) | 28.2/26.8 (N=23) | 27.6/25.2 (N=13) |
| 4.00 | 33.8/31.7 (N=11) | 32.8/30.5 (N=13) | 38.0/35.0 (N=8) |
