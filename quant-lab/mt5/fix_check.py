with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\cerebus_live.py", "r") as f:
    c = f.read()

old1 = "tier=%s AR=%.1fp origin=%.5f" + '"' + " % (self.symbol, self.tier_name, ar_pips, self.swing_origin))"
new1 = "tier=%s AR=%.1fp origin=%.5f" + '", self.symbol, self.tier_name, ar_pips, self.swing_origin)'

old2 = "AR=%.1fp" + '"' + " % (self.symbol, ar_pips))"
new2 = "AR=%.1fp" + '", self.symbol, ar_pips)'

print("old1 found:", old1 in c)
print("old2 found:", old2 in c)
