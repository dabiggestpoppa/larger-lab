# PFT-B3 — Test Report

- tests run: 177
- failures: 0
- errors: 0
- suite pass: True

Coverage matrix rows (formula -> implementation -> fixture class -> causality class):

| formula_id                | reference_fixture_class   | causality_test_class   | fixture_status   |
|:--------------------------|:--------------------------|:-----------------------|:-----------------|
| A1.F01.LOG_RETURN         | TestLogReturn             | TestReturnsCausal      | PASS             |
| A1.F02.PARKINSON_14H      | TestParkinson             | TestParkinsonCausal    | PASS             |
| A1.F03.GAMMA_RAW          | TestGamma                 | TestK2Causal           | PASS             |
| A1.F04.GAMMA_SMA3         | TestGammaSmooth           | TestK2Causal           | PASS             |
| A1.F05.ACCELERATION       | TestAcceleration          | TestK2Causal           | PASS             |
| A1.F06.DMD_OPERATOR       | TestDMD                   | TestK1Causal           | PASS             |
| A1.F07.MODE_PARTICIPATION | TestDMDParticipation      | TestK1Causal           | PASS             |
| A1.F08.PHASE_DISTANCE     | TestCircularPhase         | TestK1Causal           | PASS             |
| A1.F09.VR_DISTANCE        | TestVRDistance            | TestK3Causal           | PASS             |
| A1.F10.VR_CLASSIFICATION  | TestVRTopology            | TestK3Causal           | PASS             |
| A1.F11.K3_OLS             | TestK3OLS                 | TestK3Causal           | PASS             |
| A1.F12.K3_ALPHA           | TestK3Alpha               | TestK3Causal           | PASS             |
| A1.F13.RV6                | TestRV6                   | TestK4Causal           | PASS             |
| A1.F14.COMMUTATOR         | TestCommutator            | TestK4Causal           | PASS             |
| A1.F15.CLUSTER_FSM        | TestFSM                   | TestPortfolioCausal    | PASS             |
| A1.F16.GROSS_CAP          | TestGrossCap              | TestPortfolioCausal    | PASS             |
| A1.F17.FADE               | TestFade                  | TestPortfolioCausal    | PASS             |
| A1.F18.DRAWDOWN           | TestDrawdown              | TestPortfolioCausal    | PASS             |
| A1.F19.LEG_STOP           | TestLegStop               | TestPortfolioCausal    | PASS             |
