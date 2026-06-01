with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\cerebus_live.py", "r") as f:
    c = f.read()

c = c.replace("tier=%%s AR=%%.1fp origin=%%.5f", "tier=%s AR=%.1fp origin=%.5f")
c = c.replace("AR=%%.1fp", "AR=%.1fp")
c = c.replace('" %% (self.symbol, self.tier_name, ar_pips, self.swing_origin))',
              '", self.symbol, self.tier_name, ar_pips, self.swing_origin)')
c = c.replace('" %% (self.symbol, ar_pips))',
              '", self.symbol, ar_pips)')

# Fix the logging calls - they use % formatting, convert to , formatting
old_log1 = 'logging.info("[%s] Session INIT: tier=%s AR=%.1fp origin=%.5f", self.symbol, self.tier_name, ar_pips, self.swing_origin)'
new_log1 = 'logging.info("[%s] Session INIT: tier=%s AR=%.1fp origin=%.5f", self.symbol, self.tier_name, ar_pips, self.swing_origin)'

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\cerebus_live.py", "w") as f:
    f.write(c)
print("Fixed")
