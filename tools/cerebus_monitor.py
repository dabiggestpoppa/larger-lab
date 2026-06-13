"""
CEREBUS Monitor — Lightweight Desktop App
==========================================
Live market conditions + alerts viewer + pair configuration.
No dependencies beyond Python stdlib (tkinter).

Usage:
    python tools/cerebus_monitor.py
"""
import os
import sys
import json
import time
import csv
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
from datetime import datetime, timezone, timedelta as td

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
ALERTS_FILE = DATA_DIR / "alerts_history.json"
LATEST_ALERT_FILE = DATA_DIR / "latest_alert.txt"
CONFIG_FILE = DATA_DIR / "monitor_config.json"

EST = timezone(td(hours=-5))

# All available pairs
ALL_PAIRS = [
    "EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD",
    "EURGBP", "EURCHF", "EURJPY", "GBPCHF", "GBPJPY", "AUDJPY", "NZDJPY",
    "BTCUSD", "ETHUSD",
]


# ── Data helpers ──────────────────────────────────────────────

def load_alerts_history():
    if ALERTS_FILE.exists():
        try:
            with open(ALERTS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def load_config():
    defaults = {"symbols": ["EURUSD", "BTCUSD"], "interval": 300}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                cfg = json.load(f)
                defaults.update(cfg)
        except Exception:
            pass
    return defaults


def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def parse_alert_file():
    if not LATEST_ALERT_FILE.exists():
        return None
    try:
        text = LATEST_ALERT_FILE.read_text(encoding="utf-8").strip()
        if not text:
            return None
        lines = text.split("\n")
        timestamp = ""
        title = ""
        details = []
        for line in lines:
            if line.startswith("[") and "]" in line:
                timestamp = line.split("]")[0].lstrip("[")
                title = line.split("]", 1)[1].strip()
            else:
                details.append(line.strip())
        return {"timestamp": timestamp, "title": title, "details": details, "raw": text}
    except Exception:
        return None


def get_scanner_status():
    """Check if the CEREBUS scanner process is running. Returns (running, pid)."""
    try:
        helper = REPO_ROOT / "tools" / "_check_scanner.ps1"
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(helper)],
            capture_output=True, text=True, timeout=8,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        pid_str = result.stdout.strip()
        if pid_str and pid_str.isdigit():
            return True, pid_str
    except Exception:
        pass
    return False, None


# ── Main App ──────────────────────────────────────────────────

class CerebusMonitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CEREBUS Monitor")
        self.geometry("920x680")
        self.minsize(780, 520)
        self.configure(bg="#1a1a2e")

        self.config_data = load_config()
        self.alerts_history = load_alerts_history()
        self.filter_var = tk.StringVar(value="24h")
        self.pair_vars = {}

        self._setup_styles()
        self._build_ui()
        self._refresh()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        bg, fg, accent, hi = "#1a1a2e", "#e0e0e0", "#0f3460", "#e94560"

        style.configure(".", background=bg, foreground=fg, fieldbackground=accent)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#00d2ff")
        style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#888888")
        style.configure("Status.TLabel", font=("Segoe UI", 9))
        style.configure("AlertTitle.TLabel", font=("Segoe UI", 11, "bold"), foreground="#00d2ff")
        style.configure("TButton", background=accent, foreground=fg, font=("Segoe UI", 9))
        style.configure("Accent.TButton", background=hi, foreground="white")
        style.configure("TNotebook", background=bg)
        style.configure("TNotebook.Tab", background=accent, foreground=fg, padding=[14, 5])
        style.map("TNotebook.Tab", background=[("selected", hi)])
        style.configure("Treeview", background="#16213e", foreground=fg,
                        fieldbackground="#16213e", borderwidth=0)
        style.configure("Treeview.Heading", background=accent, foreground=fg,
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", hi)])
        style.configure("TLabelframe", background=bg, foreground="#aaaaaa")
        style.configure("TLabelframe.Label", background=bg, foreground="#aaaaaa",
                        font=("Segoe UI", 9, "bold"))

    def _build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill="x", padx=12, pady=(10, 2))
        ttk.Label(header, text="CEREBUS Monitor", style="Header.TLabel").pack(side="left")
        self.status_label = ttk.Label(header, text="...", style="Status.TLabel")
        self.status_label.pack(side="right")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=4)
        self.notebook = nb

        self._build_conditions_tab(nb)
        self._build_alerts_tab(nb)
        self._build_config_tab(nb)

        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=12, pady=(0, 8))
        self.time_label = ttk.Label(footer, text="", style="Sub.TLabel")
        self.time_label.pack(side="right")
        ttk.Button(footer, text="Refresh", command=self._manual_refresh).pack(side="left", padx=2)
        ttk.Button(footer, text="Start Scanner", command=self._start_scanner).pack(side="left", padx=2)
        ttk.Button(footer, text="Stop Scanner", command=self._stop_scanner).pack(side="left", padx=2)

    def _build_conditions_tab(self, nb):
        frame = ttk.Frame(nb)
        nb.add(frame, text="  Market Conditions  ")

        alert_frame = ttk.LabelFrame(frame, text="Latest Alert")
        alert_frame.pack(fill="x", padx=8, pady=6)

        self.alert_title = ttk.Label(alert_frame, text="No alerts yet", style="AlertTitle.TLabel")
        self.alert_title.pack(anchor="w", padx=10, pady=(6, 2))

        self.alert_body = scrolledtext.ScrolledText(
            alert_frame, height=5, bg="#16213e", fg="#e0e0e0",
            font=("Consolas", 9), relief="flat", state="disabled", wrap="word"
        )
        self.alert_body.pack(fill="x", padx=10, pady=(0, 6))

        pairs_frame = ttk.LabelFrame(frame, text="Tracked Pairs (click to toggle)")
        pairs_frame.pack(fill="both", expand=True, padx=8, pady=6)

        canvas = tk.Canvas(pairs_frame, bg="#1a1a2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(pairs_frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        current_symbols = set(self.config_data.get("symbols", []))
        cols = 4
        for i, pair in enumerate(ALL_PAIRS):
            var = tk.BooleanVar(value=(pair in current_symbols))
            self.pair_vars[pair] = var
            row, col = i // cols, i % cols
            cb = tk.Checkbutton(
                scroll_frame, text=pair, variable=var,
                bg="#16213e", fg="#e0e0e0", selectcolor="#0f3460",
                activebackground="#0f3460", activeforeground="#00d2ff",
                font=("Segoe UI", 10),
                command=self._on_pair_toggle
            )
            cb.grid(row=row, column=col, padx=4, pady=2, sticky="w")

        canvas.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scrollbar.pack(side="right", fill="y", pady=4)

        status_frame = ttk.LabelFrame(frame, text="Pair Status")
        status_frame.pack(fill="x", padx=8, pady=(0, 6))

        columns = ("pair", "direction", "confidence", "last_alert")
        self.pairs_tree = ttk.Treeview(status_frame, columns=columns,
                                        show="headings", height=4)
        self.pairs_tree.heading("pair", text="Pair")
        self.pairs_tree.heading("direction", text="Direction")
        self.pairs_tree.heading("confidence", text="Confidence")
        self.pairs_tree.heading("last_alert", text="Last Alert")
        self.pairs_tree.column("pair", width=100)
        self.pairs_tree.column("direction", width=100)
        self.pairs_tree.column("confidence", width=100)
        self.pairs_tree.column("last_alert", width=200)
        self.pairs_tree.pack(fill="x", padx=4, pady=4)

    def _build_alerts_tab(self, nb):
        frame = ttk.Frame(nb)
        nb.add(frame, text="  Alerts  ")

        bar = ttk.Frame(frame)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Label(bar, text="Show:").pack(side="left")
        for val, label in [("24h", "24 Hours"), ("7d", "7 Days"),
                           ("30d", "30 Days"), ("all", "All")]:
            rb = tk.Radiobutton(
                bar, text=label, variable=self.filter_var, value=val,
                bg="#1a1a2e", fg="#e0e0e0", selectcolor="#0f3460",
                activebackground="#0f3460", activeforeground="#00d2ff",
                font=("Segoe UI", 9),
                command=self._refresh_alerts
            )
            rb.pack(side="left", padx=6)
        ttk.Button(bar, text="Export CSV", command=self._export_csv).pack(side="right")

        columns = ("time", "symbol", "direction", "confidence", "pathway", "regime", "pips")
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=2)

        self.alerts_tree = ttk.Treeview(tree_frame, columns=columns,
                                         show="headings", height=12)
        for col, txt, w in [
            ("time", "Time (EST)", 140), ("symbol", "Symbol", 80),
            ("direction", "Dir", 60), ("confidence", "Conf", 60),
            ("pathway", "Pathway", 100), ("regime", "Regime", 100),
            ("pips", "Pips", 70),
        ]:
            self.alerts_tree.heading(col, text=txt)
            self.alerts_tree.column(col, width=w)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.alerts_tree.yview)
        self.alerts_tree.configure(yscrollcommand=vsb.set)
        self.alerts_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.alert_detail = scrolledtext.ScrolledText(
            frame, height=4, bg="#16213e", fg="#e0e0e0",
            font=("Consolas", 9), relief="flat", state="disabled", wrap="word"
        )
        self.alert_detail.pack(fill="x", padx=8, pady=(2, 6))
        self.alerts_tree.bind("<<TreeviewSelect>>", self._on_alert_select)

    def _build_config_tab(self, nb):
        frame = ttk.Frame(nb)
        nb.add(frame, text="  Settings  ")

        int_frame = ttk.LabelFrame(frame, text="Scan Interval")
        int_frame.pack(fill="x", padx=8, pady=8)
        inner = ttk.Frame(int_frame)
        inner.pack(fill="x", padx=10, pady=8)
        ttk.Label(inner, text="Seconds:").pack(side="left")
        self.interval_entry = ttk.Entry(inner, width=10, font=("Segoe UI", 11))
        self.interval_entry.insert(0, str(self.config_data.get("interval", 300)))
        self.interval_entry.pack(side="left", padx=8)
        ttk.Label(inner, text="(60-3600)", style="Sub.TLabel").pack(side="left")

        active_frame = ttk.LabelFrame(frame, text="Active Pairs")
        active_frame.pack(fill="x", padx=8, pady=8)
        self.active_pairs_label = ttk.Label(active_frame, text="", style="Status.TLabel")
        self.active_pairs_label.pack(anchor="w", padx=10, pady=8)
        self._update_active_label()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", padx=8, pady=12)
        ttk.Button(btn_frame, text="Save Settings", style="Accent.TButton",
                   command=self._save_config).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Apply & Restart Scanner",
                   command=self._apply_and_restart).pack(side="left", padx=4)

        cmd_frame = ttk.LabelFrame(frame, text="Scanner Command")
        cmd_frame.pack(fill="x", padx=8, pady=8)
        self.cmd_label = ttk.Label(cmd_frame, text="", style="Sub.TLabel")
        self.cmd_label.pack(anchor="w", padx=10, pady=8)
        self._update_cmd_label()

    def _manual_refresh(self):
        self.alerts_history = load_alerts_history()
        self._refresh()

    def _refresh(self):
        self._refresh_status()
        self._refresh_conditions()
        self._refresh_alerts()
        self._update_time()
        self._update_active_label()
        self.after(5000, self._refresh)

    def _refresh_status(self):
        running, pid = get_scanner_status()
        if running:
            self.status_label.configure(
                text="  Scanner RUNNING (PID {})  ".format(pid),
                foreground="#00ff88")
        else:
            self.status_label.configure(
                text="  Scanner STOPPED  ",
                foreground="#ff4444")

    def _refresh_conditions(self):
        alert = parse_alert_file()
        if alert:
            self.alert_title.configure(
                text="[{}] {}".format(alert["timestamp"], alert["title"]))
            self.alert_body.configure(state="normal")
            self.alert_body.delete("1.0", "end")
            self.alert_body.insert("1.0", "\n".join(alert["details"]))
            self.alert_body.configure(state="disabled")
        else:
            self.alert_title.configure(text="No alerts yet")
            self.alert_body.configure(state="normal")
            self.alert_body.delete("1.0", "end")
            self.alert_body.insert("1.0",
                "Waiting for trade calls...\n\nScanner checks every {}s during "
                "active hours (3AM-12PM EST for FX, 24/7 for crypto).".format(
                    self.config_data.get("interval", 300)))
            self.alert_body.configure(state="disabled")

        for item in self.pairs_tree.get_children():
            self.pairs_tree.delete(item)
        active = self._get_active_pairs()
        for sym in active:
            recent = [a for a in self.alerts_history if a.get("symbol") == sym]
            if recent:
                last = recent[-1]
                self.pairs_tree.insert("", "end", values=(
                    sym, last.get("direction", "?"),
                    "{:.0%}".format(last.get("confidence", 0)),
                    last.get("timestamp", "?"),
                ))
            else:
                self.pairs_tree.insert("", "end",
                                       values=(sym, "—", "—", "No alerts yet"))

    def _refresh_alerts(self):
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)

        filt = self.filter_var.get()
        now = datetime.now(EST)
        cutoff = None
        if filt == "24h":
            cutoff = now - td(hours=24)
        elif filt == "7d":
            cutoff = now - td(days=7)
        elif filt == "30d":
            cutoff = now - td(days=30)

        filtered = self.alerts_history
        if cutoff:
            filtered = [a for a in filtered
                        if _parse_dt(a.get("datetime", "")) >= cutoff]

        for alert in reversed(filtered[-300:]):
            pips = alert.get("dtb_pips")
            self.alerts_tree.insert("", "end", values=(
                alert.get("timestamp", ""), alert.get("symbol", ""),
                alert.get("direction", ""),
                "{:.0%}".format(alert.get("confidence", 0)),
                alert.get("pathway", ""), alert.get("regime", ""),
                "{:.1f}".format(pips) if pips else "—",
            ))

    def _on_alert_select(self, event):
        sel = self.alerts_tree.selection()
        if not sel:
            return
        idx = self.alerts_tree.index(sel[0])
        filt = self.filter_var.get()
        now = datetime.now(EST)
        cutoff = None
        if filt == "24h":
            cutoff = now - td(hours=24)
        elif filt == "7d":
            cutoff = now - td(days=7)
        elif filt == "30d":
            cutoff = now - td(days=30)
        filtered = [a for a in self.alerts_history
                    if not cutoff or _parse_dt(a.get("datetime", "")) >= cutoff]
        filtered = list(reversed(filtered[-300:]))
        if idx < len(filtered):
            alert = filtered[idx]
            self.alert_detail.configure(state="normal")
            self.alert_detail.delete("1.0", "end")
            self.alert_detail.insert("1.0", alert.get("message", ""))
            self.alert_detail.configure(state="disabled")

    def _on_pair_toggle(self):
        active = self._get_active_pairs()
        self.config_data["symbols"] = active
        save_config(self.config_data)
        self._update_cmd_label()
        self._update_active_label()
        self._refresh_conditions()

    def _get_active_pairs(self):
        return [p for p, v in sorted(self.pair_vars.items()) if v.get()]

    def _update_active_label(self):
        active = self._get_active_pairs()
        self.active_pairs_label.configure(
            text="{} pairs: {}".format(len(active), ", ".join(active)))

    def _update_cmd_label(self):
        pairs = " ".join(self._get_active_pairs())
        interval = self.config_data.get("interval", 300)
        self.cmd_label.configure(
            text="python quant-lab/ml/run_cerebus_unified.py "
                 "--interval {} --symbols {}".format(interval, pairs))

    def _update_time(self):
        now = datetime.now(EST)
        self.time_label.configure(text="EST: {}".format(now.strftime("%Y-%m-%d %H:%M:%S")))

    def _save_config(self):
        try:
            interval = int(self.interval_entry.get().strip())
            interval = max(60, min(3600, interval))
        except ValueError:
            interval = 300
        self.config_data["interval"] = interval
        self.interval_entry.delete(0, "end")
        self.interval_entry.insert(0, str(interval))
        save_config(self.config_data)
        self._update_cmd_label()
        messagebox.showinfo("Saved", "Settings saved.")

    def _apply_and_restart(self):
        self._save_config()
        self._stop_scanner()
        time.sleep(2)
        self._start_scanner()

    def _start_scanner(self):
        running, _ = get_scanner_status()
        if running:
            messagebox.showinfo("Info", "Scanner is already running.")
            return
        symbols = self._get_active_pairs()
        if not symbols:
            messagebox.showwarning("Warning", "No pairs selected.")
            return
        interval = self.config_data.get("interval", 300)
        cmd = [
            sys.executable,
            str(REPO_ROOT / "quant-lab" / "ml" / "run_cerebus_unified.py"),
            "--interval", str(interval), "--symbols",
        ] + symbols
        try:
            subprocess.Popen(
                cmd, cwd=str(REPO_ROOT),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            messagebox.showinfo("Started", "Scanner started.")
        except Exception as e:
            messagebox.showerror("Error", "Failed to start: {}".format(e))

    def _stop_scanner(self):
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(REPO_ROOT / "tools" / "_stop_scanner.ps1")],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            messagebox.showinfo("Stopped", "Scanner stopped.")
        except Exception as e:
            messagebox.showerror("Error", "Failed to stop: {}".format(e))

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="cerebus_alerts_{}.csv".format(
                datetime.now(EST).strftime("%Y%m%d")))
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Time", "Symbol", "Direction", "Confidence",
                            "Pathway", "Regime", "Pips"])
                for a in self.alerts_history:
                    w.writerow([
                        a.get("timestamp", ""), a.get("symbol", ""),
                        a.get("direction", ""),
                        "{:.0%}".format(a.get("confidence", 0)),
                        a.get("pathway", ""), a.get("regime", ""),
                        a.get("dtb_pips", ""),
                    ])
            messagebox.showinfo("Exported", "Alerts exported to:\n{}".format(path))
        except Exception as e:
            messagebox.showerror("Error", "Export failed: {}".format(e))


def _parse_dt(s):
    if not s:
        return datetime.min.replace(tzinfo=EST)
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.min.replace(tzinfo=EST)


if __name__ == "__main__":
    app = CerebusMonitor()
    app.mainloop()
