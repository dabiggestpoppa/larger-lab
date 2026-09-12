"""LF3 terrain plots. PNG files are generated locally and follow repository
binary-output conventions; they are not required for statistical artifacts."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import lf3_common as C
P=C.ROOT/'plots'; P.mkdir(exist_ok=True)

def main():
 d=pd.read_csv(C.RESULTS/'14_SHHM_VS_SHMC.csv')
 x=d.pivot(index='rank_band',columns='state',values='p_abs2s')
 x.reindex(C.PRIMARY_BANDS).plot(kind='bar',figsize=(8,4),title='SHHM vs SHMC normalized 7D tails')
 plt.ylabel('P(|fwd7| >= 2 sigma)'); plt.tight_layout(); plt.savefig(P/'shhm_vs_shmc.png',dpi=110); plt.close()
 d=pd.read_csv(C.RESULTS/'12_SIGN_PARTICIPATION_TOPOLOGY.csv')
 x=d.pivot(index='participation',columns='event_sign_label',values='p_rev7')
 x.plot(kind='bar',figsize=(8,4),title='Reversal by participation topology and sign')
 plt.ylabel('P(reversal by 7D)'); plt.tight_layout(); plt.savefig(P/'participation_reversal.png',dpi=110); plt.close()
 d=pd.read_csv(C.RESULTS/'15_HIGH_BRD_HIGH_DISP_ASSET_ANATOMY.csv')
 x=d.groupby('quadrant')['tail3'].mean().sort_values()
 x.plot(kind='bar',figsize=(8,4),title='Tail share by breadth-dispersion quadrant')
 plt.ylabel('mean P(>=3 sigma)'); plt.tight_layout(); plt.savefig(P/'breadth_dispersion_tail.png',dpi=110); plt.close()
 print('plots written',P)
if __name__=='__main__': main()
