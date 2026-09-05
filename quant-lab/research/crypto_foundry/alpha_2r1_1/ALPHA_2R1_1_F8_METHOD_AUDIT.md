# ALPHA-2R1.1 F8 Method Audit

## Frozen F8 Contract (ALPHA_1_FALSIFICATION_RULES.json)

- condition: control_net_PF >= strategy_net_PF (CI overlap)
- method: paired_bootstrap_difference
- n_resamples: 10,000
- seed: 31082026
- ci_level: 0.95
- reason: STATE_ADDS_NO_VALUE

## Pairing Method

Strategy and control trades paired by nearest entry timestamp.
Greedy nearest-neighbor without replacement.

## Trigger Condition

F8 triggers when control point-estimate net_R mean >= strategy point-estimate net_R mean.
CI reported for reference. Primary gate is mechanical PF comparison.

## Per-Strategy Results

### ALPHA1_S001 vs ALPHA1_C006

- Strategy net_PF: 0.8023
- Control net_PF: 0.7614
- Paired samples: 397
- Observed diff (ctrl-strat): -0.0764
- Bootstrap mean: -0.0747
- 95% CI: [-0.2256, 0.0763]
- PF condition (ctrl>=strat): False
- CI overlaps zero: True
- F8 trigger: False

### ALPHA1_S002 vs ALPHA1_C001

- Strategy net_PF: 1.0163
- Control net_PF: 0.7986
- Paired samples: 176
- Observed diff (ctrl-strat): -0.0361
- Bootstrap mean: -0.0348
- 95% CI: [-0.4084, 0.3455]
- PF condition (ctrl>=strat): False
- CI overlaps zero: True
- F8 trigger: False

### ALPHA1_S003 vs ALPHA1_C001

- Strategy net_PF: 1.0093
- Control net_PF: 0.7986
- Paired samples: 174
- Observed diff (ctrl-strat): -0.0873
- Bootstrap mean: -0.0869
- 95% CI: [-0.3154, 0.1418]
- PF condition (ctrl>=strat): False
- CI overlaps zero: True
- F8 trigger: False

### ALPHA1_S004 vs ALPHA1_C002

- Strategy net_PF: 0.8777
- Control net_PF: 0.7986
- Paired samples: 331
- Observed diff (ctrl-strat): -0.0182
- Bootstrap mean: -0.0209
- 95% CI: [-0.2345, 0.1933]
- PF condition (ctrl>=strat): False
- CI overlaps zero: True
- F8 trigger: False

### ALPHA1_S005 vs ALPHA1_C002

- Strategy net_PF: 0.7702
- Control net_PF: 0.7986
- Paired samples: 45
- Observed diff (ctrl-strat): 0.0817
- Bootstrap mean: 0.0832
- 95% CI: [-0.3211, 0.4877]
- PF condition (ctrl>=strat): True
- CI overlaps zero: True
- F8 trigger: True

### ALPHA1_S006 vs ALPHA1_C002

- Strategy net_PF: 0.5908
- Control net_PF: 0.7986
- Paired samples: 30
- Observed diff (ctrl-strat): -0.2107
- Bootstrap mean: -0.2111
- 95% CI: [-0.6559, 0.2041]
- PF condition (ctrl>=strat): False
- CI overlaps zero: True
- F8 trigger: False

### ALPHA1_S007 vs ALPHA1_C003

- Strategy net_PF: 0.9558
- Control net_PF: 0.7519
- Paired samples: 205
- Observed diff (ctrl-strat): -0.1495
- Bootstrap mean: -0.1509
- 95% CI: [-0.4899, 0.1955]
- PF condition (ctrl>=strat): False
- CI overlaps zero: True
- F8 trigger: False

### ALPHA1_S008 vs ALPHA1_C003

- Strategy net_PF: 0.6220
- Control net_PF: 0.7519
- Paired samples: 76
- Observed diff (ctrl-strat): -0.1670
- Bootstrap mean: -0.1705
- 95% CI: [-0.7947, 0.4608]
- PF condition (ctrl>=strat): False
- CI overlaps zero: True
- F8 trigger: False

### ALPHA1_S009 vs ALPHA1_C004

- Strategy net_PF: 0.7133
- Control net_PF: 0.7433
- Paired samples: 141
- Observed diff (ctrl-strat): -0.1912
- Bootstrap mean: -0.1958
- 95% CI: [-0.7749, 0.3849]
- PF condition (ctrl>=strat): False
- CI overlaps zero: True
- F8 trigger: False

### ALPHA1_S010 vs ALPHA1_C004

- Strategy net_PF: 0.7292
- Control net_PF: 0.7433
- Paired samples: 141
- Observed diff (ctrl-strat): -0.2317
- Bootstrap mean: -0.2349
- 95% CI: [-0.8055, 0.3373]
- PF condition (ctrl>=strat): False
- CI overlaps zero: True
- F8 trigger: False

### ALPHA1_S011 vs ALPHA1_C005

- Strategy net_PF: 0.9922
- Control net_PF: 1.2311
- Paired samples: 79
- Observed diff (ctrl-strat): 0.2939
- Bootstrap mean: 0.2956
- 95% CI: [0.0077, 0.5998]
- PF condition (ctrl>=strat): True
- CI overlaps zero: False
- F8 trigger: True

### ALPHA1_S012 vs ALPHA1_C005

- Strategy net_PF: 0.8800
- Control net_PF: 1.2311
- Paired samples: 76
- Observed diff (ctrl-strat): 0.3638
- Bootstrap mean: 0.3639
- 95% CI: [0.1450, 0.5974]
- PF condition (ctrl>=strat): True
- CI overlaps zero: False
- F8 trigger: True

### ALPHA1_S013 vs ALPHA1_C006

- Strategy net_PF: 0.9633
- Control net_PF: 0.7614
- Paired samples: 397
- Observed diff (ctrl-strat): -0.1078
- Bootstrap mean: -0.1086
- 95% CI: [-0.2678, 0.0514]
- PF condition (ctrl>=strat): False
- CI overlaps zero: True
- F8 trigger: False
