# CEREBUS v2.1 Architecture

> 2026-06-01 15:35 UTC

#cerebus #architecture #v2.1

Engine: quant-lab/mt5/cerebus_live.py
Magic: 20260601 | Lot: 0.01 | M5 | MT5: 650898

ST States: SEARCH, WAIT_RETRACE, WAIT_OCC, IN_TRADE

Tiers: T1(AR<=20,p10,t12) T2(AR<=30,p12,t15) T3(AR<=45,p15,t19) NO-GO(AR>45p)

P90: INITIAL(SL=80%%body) CASCADE(SL=168%%body) TP1=25%%AR TP2=50%%AR

Key Methods: initialize_session, process_bar, _st_state_machine, _p90_search
