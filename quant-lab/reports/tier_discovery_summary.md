# CEREBUS ST — Tier Discovery Summary

**Method:** K-Means Clustering (k=3) on Asian Range (Code 6 from manual)

---

## Tier Configs (Copy-Paste Ready)

| Pair | T1 Range | T1 AU | T1 Trig | T2 Range | T2 AU | T2 Trig | T3 Range | T3 AU | T3 Trig |
|------|----------|-------|---------|----------|-------|---------|----------|-------|----------|
| EURGBP | <20.98 | 7 | 8 | 20.98-40.33 | 14 | 17 | >40.33 | 19 | 23 |
| EURJPY | <91.57 | 29 | 35 | 91.57-160.35 | 63 | 75 | >160.35 | 63 | 76 |
| EURAUD | <77.51 | 27 | 32 | 77.51-135.4 | 51 | 61 | >135.4 | 58 | 69 |
| EURNZD | <77.48 | 28 | 34 | 77.48-143.25 | 49 | 59 | >143.25 | 61 | 73 |
| EURCHF | <28.55 | 9 | 11 | 28.55-53.15 | 19 | 23 | >53.15 | 22 | 27 |
| EURCAD | <38.86 | 13 | 16 | 38.86-75.87 | 25 | 31 | >75.87 | 32 | 38 |
| USDCAD | <31.17 | 11 | 13 | 31.17-56.88 | 20 | 24 | >56.88 | 27 | 32 |
| AUDJPY | <65.94 | 21 | 26 | 65.94-119.73 | 45 | 53 | >119.73 | 49 | 59 |
| AUDNZD | <36.17 | 12 | 14 | 36.17-65.5 | 24 | 29 | >65.5 | 27 | 33 |
| AUDCHF | <28.05 | 10 | 12 | 28.05-55.24 | 18 | 22 | >55.24 | 23 | 28 |
| AUDCAD | <36.92 | 13 | 16 | 36.92-67.8 | 24 | 29 | >67.8 | 28 | 33 |
| NZDJPY | <62.7 | 20 | 24 | 62.7-100.51 | 44 | 53 | >100.51 | 43 | 51 |
| NZDCHF | <27.68 | 9 | 11 | 27.68-49.57 | 18 | 22 | >49.57 | 21 | 25 |
| NZDCAD | <33.79 | 12 | 15 | 33.79-63.21 | 22 | 26 | >63.21 | 27 | 32 |
| CADJPY | <61.54 | 19 | 23 | 61.54-107.57 | 43 | 51 | >107.57 | 42 | 50 |
| CADCHF | <21.73 | 7 | 9 | 21.73-41.15 | 14 | 17 | >41.15 | 17 | 21 |
| GBPCAD | <59.7 | 20 | 24 | 59.7-104.24 | 45 | 55 | >104.24 | 42 | 50 |

---

## Python Config Snippets

```python  # EURGBP
"EURGBP": {
    "tiers": {
        "T1": {"ar_max": 20.98, "au": 7, "trigger": 8},
        "T2": {"ar_max": 40.33, "au": 14, "trigger": 17},
        "T3": {"ar_max": 40.33, "au": 19, "trigger": 23},
    },
    "gear_shifts": {
        "T1": [(40.33, "T2"), (40.33, "T3")],
        "T2": [(40.33, "T3")],
    },
}
```

```python  # EURJPY
"EURJPY": {
    "tiers": {
        "T1": {"ar_max": 91.57, "au": 29, "trigger": 35},
        "T2": {"ar_max": 160.35, "au": 63, "trigger": 75},
        "T3": {"ar_max": 160.35, "au": 63, "trigger": 76},
    },
    "gear_shifts": {
        "T1": [(160.35, "T2"), (160.35, "T3")],
        "T2": [(160.35, "T3")],
    },
}
```

```python  # EURAUD
"EURAUD": {
    "tiers": {
        "T1": {"ar_max": 77.51, "au": 27, "trigger": 32},
        "T2": {"ar_max": 135.4, "au": 51, "trigger": 61},
        "T3": {"ar_max": 135.4, "au": 58, "trigger": 69},
    },
    "gear_shifts": {
        "T1": [(135.4, "T2"), (135.4, "T3")],
        "T2": [(135.4, "T3")],
    },
}
```

```python  # EURNZD
"EURNZD": {
    "tiers": {
        "T1": {"ar_max": 77.48, "au": 28, "trigger": 34},
        "T2": {"ar_max": 143.25, "au": 49, "trigger": 59},
        "T3": {"ar_max": 143.25, "au": 61, "trigger": 73},
    },
    "gear_shifts": {
        "T1": [(143.25, "T2"), (143.25, "T3")],
        "T2": [(143.25, "T3")],
    },
}
```

```python  # EURCHF
"EURCHF": {
    "tiers": {
        "T1": {"ar_max": 28.55, "au": 9, "trigger": 11},
        "T2": {"ar_max": 53.15, "au": 19, "trigger": 23},
        "T3": {"ar_max": 53.15, "au": 22, "trigger": 27},
    },
    "gear_shifts": {
        "T1": [(53.15, "T2"), (53.15, "T3")],
        "T2": [(53.15, "T3")],
    },
}
```

```python  # EURCAD
"EURCAD": {
    "tiers": {
        "T1": {"ar_max": 38.86, "au": 13, "trigger": 16},
        "T2": {"ar_max": 75.87, "au": 25, "trigger": 31},
        "T3": {"ar_max": 75.87, "au": 32, "trigger": 38},
    },
    "gear_shifts": {
        "T1": [(75.87, "T2"), (75.87, "T3")],
        "T2": [(75.87, "T3")],
    },
}
```

```python  # USDCAD
"USDCAD": {
    "tiers": {
        "T1": {"ar_max": 31.17, "au": 11, "trigger": 13},
        "T2": {"ar_max": 56.88, "au": 20, "trigger": 24},
        "T3": {"ar_max": 56.88, "au": 27, "trigger": 32},
    },
    "gear_shifts": {
        "T1": [(56.88, "T2"), (56.88, "T3")],
        "T2": [(56.88, "T3")],
    },
}
```

```python  # AUDJPY
"AUDJPY": {
    "tiers": {
        "T1": {"ar_max": 65.94, "au": 21, "trigger": 26},
        "T2": {"ar_max": 119.73, "au": 45, "trigger": 53},
        "T3": {"ar_max": 119.73, "au": 49, "trigger": 59},
    },
    "gear_shifts": {
        "T1": [(119.73, "T2"), (119.73, "T3")],
        "T2": [(119.73, "T3")],
    },
}
```

```python  # AUDNZD
"AUDNZD": {
    "tiers": {
        "T1": {"ar_max": 36.17, "au": 12, "trigger": 14},
        "T2": {"ar_max": 65.5, "au": 24, "trigger": 29},
        "T3": {"ar_max": 65.5, "au": 27, "trigger": 33},
    },
    "gear_shifts": {
        "T1": [(65.5, "T2"), (65.5, "T3")],
        "T2": [(65.5, "T3")],
    },
}
```

```python  # AUDCHF
"AUDCHF": {
    "tiers": {
        "T1": {"ar_max": 28.05, "au": 10, "trigger": 12},
        "T2": {"ar_max": 55.24, "au": 18, "trigger": 22},
        "T3": {"ar_max": 55.24, "au": 23, "trigger": 28},
    },
    "gear_shifts": {
        "T1": [(55.24, "T2"), (55.24, "T3")],
        "T2": [(55.24, "T3")],
    },
}
```

```python  # AUDCAD
"AUDCAD": {
    "tiers": {
        "T1": {"ar_max": 36.92, "au": 13, "trigger": 16},
        "T2": {"ar_max": 67.8, "au": 24, "trigger": 29},
        "T3": {"ar_max": 67.8, "au": 28, "trigger": 33},
    },
    "gear_shifts": {
        "T1": [(67.8, "T2"), (67.8, "T3")],
        "T2": [(67.8, "T3")],
    },
}
```

```python  # NZDJPY
"NZDJPY": {
    "tiers": {
        "T1": {"ar_max": 62.7, "au": 20, "trigger": 24},
        "T2": {"ar_max": 100.51, "au": 44, "trigger": 53},
        "T3": {"ar_max": 100.51, "au": 43, "trigger": 51},
    },
    "gear_shifts": {
        "T1": [(100.51, "T2"), (100.51, "T3")],
        "T2": [(100.51, "T3")],
    },
}
```

```python  # NZDCHF
"NZDCHF": {
    "tiers": {
        "T1": {"ar_max": 27.68, "au": 9, "trigger": 11},
        "T2": {"ar_max": 49.57, "au": 18, "trigger": 22},
        "T3": {"ar_max": 49.57, "au": 21, "trigger": 25},
    },
    "gear_shifts": {
        "T1": [(49.57, "T2"), (49.57, "T3")],
        "T2": [(49.57, "T3")],
    },
}
```

```python  # NZDCAD
"NZDCAD": {
    "tiers": {
        "T1": {"ar_max": 33.79, "au": 12, "trigger": 15},
        "T2": {"ar_max": 63.21, "au": 22, "trigger": 26},
        "T3": {"ar_max": 63.21, "au": 27, "trigger": 32},
    },
    "gear_shifts": {
        "T1": [(63.21, "T2"), (63.21, "T3")],
        "T2": [(63.21, "T3")],
    },
}
```

```python  # CADJPY
"CADJPY": {
    "tiers": {
        "T1": {"ar_max": 61.54, "au": 19, "trigger": 23},
        "T2": {"ar_max": 107.57, "au": 43, "trigger": 51},
        "T3": {"ar_max": 107.57, "au": 42, "trigger": 50},
    },
    "gear_shifts": {
        "T1": [(107.57, "T2"), (107.57, "T3")],
        "T2": [(107.57, "T3")],
    },
}
```

```python  # CADCHF
"CADCHF": {
    "tiers": {
        "T1": {"ar_max": 21.73, "au": 7, "trigger": 9},
        "T2": {"ar_max": 41.15, "au": 14, "trigger": 17},
        "T3": {"ar_max": 41.15, "au": 17, "trigger": 21},
    },
    "gear_shifts": {
        "T1": [(41.15, "T2"), (41.15, "T3")],
        "T2": [(41.15, "T3")],
    },
}
```

```python  # GBPCAD
"GBPCAD": {
    "tiers": {
        "T1": {"ar_max": 59.7, "au": 20, "trigger": 24},
        "T2": {"ar_max": 104.24, "au": 45, "trigger": 55},
        "T3": {"ar_max": 104.24, "au": 42, "trigger": 50},
    },
    "gear_shifts": {
        "T1": [(104.24, "T2"), (104.24, "T3")],
        "T2": [(104.24, "T3")],
    },
}
```

