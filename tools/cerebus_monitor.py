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
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime, timezone, timedelta, timedelta as td
from collections import deque

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
ALERTS_FILE = DATA_DIR / "alerts_history.json"
LATEST_ALERT_FILE = DATA_DIR / "latest_alert.txt"
CONFIG_FILE = DATA_DIR / "monitor_config.json"
SCANNER_LOG = REPO_ROOT / "quant-lab" / "ml" / "cerebus_scanner.log"

EST = timezone(td(hours=-5))


# ── Data helpers ──────────────────────────────────────────────

def load_alerts_history():
    if ALERTS_FILE.exists():
        try:
            with open(ALERTS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_alerts_history(alerts):
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts[-500:], f, indent=2)  # keep last 500


def load_config():
    defaults = {
        "symbols": ["EURUSD", "BTCUSD"],
        "interval": 300,
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                cfg = json.load(f)
                defaults.update(cfg)
        except Exception:
            pass
    return defaults


def save_config(cfg):
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
    """Check if the CEREBUS scanner process is running."""
    try:
        import subprocess
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split("\n"):
            if "run_cerebus_unified" in line.lower():
                parts = line.split(",")
                if len(parts) >= 2:
                    pid = parts[1].strip('"')
                    return True, pid
    except Exception:
        pass
    return False, None


# ── Main App ──────────────────────────────────────────────────

class CerebusMonitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CEREBUS Monitor")
        self.geometry("900x650")
        self.minsize(750, 500)
        self.configure(bg="#1a1a2e")

        self.config_data = load_config()
        self.alerts_history = load_alerts_history()
        self.filter_days = tk.IntVar(value=1)

        self._setup_styles()
        self._build_ui()
        self._refresh()

    # ── Styles ─────────────────────────────────────────────

    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        bg = "#1a1a2e"
        fg = "#e0e0e0"
        accent = "#0f3460"
        highlight = "#e94560"

        self.style.configure(".", background=bg, foreground=fg, fieldbackground=accent)
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#00d2ff")
        self.style.configure("Status.TLabel", font=("Segoe UI", 9))
        self.style.configure("AlertTitle.TLabel", font=("Segoe UI", 11, "bold"), foreground="#00d2ff")
        self.style.configure("AlertDetail.TLabel", font=("Segoe UI", 9), foreground="#b0b0b0")
        self.style.configure("TButton", background=accent, foreground=fg, font=("Segoe UI", 9))
        self.style.configure("Accent.TButton", background=highlight, foreground="white")
        self.style.configure("TNotebook", background=bg)
        self.style.configure("TNotebook.Tab", background=accent, foreground=fg, padding=[12, 4])
        self.style.map("TNotebook.Tab", background=[("selected", highlight)])
        self.style.configure("Treeview", background="#16213e", foreground=fg, fieldbackground="#16213e")
        self.style.configure("Treeview.Heading", background=accent, foreground=fg)
        self.style.map("Treeview", background=[("selected", highlight)])

    # ── UI ──────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=(10, 4))
        ttk.Label(header, text="CEREBUS Monitor", style="Header.TLabel").pack(side="left")

        self.status_label = ttk.Label(header, text="● Checking...", style="Status.TLabel")
        self.status_label.pack(side="right")

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=4)

        self._build_conditions_tab()
        self._build_alerts_tab()
        self._build_config_tab()

        # Footer
        footer = ttk.Frame(self)
        footer.pack(fill="x", padx=10, pady=(0, 8))
        self.time_label = ttk.Label(footer, text="", style="Status.TLabel")
        self.time_label.pack(side="right")
        ttk.Button(footer, text="Refresh", command=self._refresh).pack(side="left", padx=2)
        ttk.Button(footer, text="Start Scanner", command=self._start_scanner).pack(side="left", padx=2)
        ttk.Button(footer, text="Stop Scanner", command=self._stop_scanner).pack(side="left", padx=2)

    # ── Tab 1: Market Conditions ────────────────────────────

    def _build_conditions_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Market Conditions  ")

        # Latest alert display
        alert_frame = ttk.LabelFrame(frame, text="Latest Alert")
        alert_frame.pack(fill="x", padx=8, pady=6)

        self.alert_title = ttk.Label(alert_frame, text="No alerts yet", style="AlertTitle.TLabel")
        self.alert_title.pack(anchor="w", padx=10, pady=(6, 2))

        self.alert_body = scrolledtext.ScrolledText(
            alert_frame, height=6, bg="#16213e", fg="#e0e0e0",
            font=("Consolas", 9), relief="flat", state="disabled"
        )
        self.alert_body.pack(fill="x", padx=10, pady=(0, 6))

        # Pairs status
        pairs_frame = ttk.LabelFrame(frame, text="Tracked Pairs")
        pairs_frame.pack(fill="both", expand=True, padx=8, pady=6)

        columns = ("pair", "status", "last_scan")
        self.pairs_tree = ttk.Treeview(pairs_frame, columns=columns, show="headings", height=6)
        self.pairs_tree.heading("pair", text="Pair")
        self.pairs_tree.heading("status", text="Status")
        self.pairs_tree.heading("last_scan", text="Last Scan")
        self.pairs_tree.column("pair", width=120)
        self.pairs_tree.column("status", width=200)
        self.pairs_tree.column("last_scan", width=180)
        self.pairs_tree.pack(fill="both", expand=True, padx=4, pady=4)

    # ── Tab 2: Alerts History ───────────────────────────────

    def _build_alerts_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Alerts  ")

        # Filter bar
        filter_bar = ttk.Frame(frame)
        filter_bar.pack(fill="x", padx=8, pady=6)
        ttk.Label(filter_bar, text="Show last:").pack(side="left")
        for val, label in [(1, "24h"), (7, "7d"), (30, "30d"), (0, "All")]:
            ttk.Radiobutton(filter_bar, text=label, variable=self.filter_days,
                            value=val, command=self._refresh_alerts).pack(side="left", padx=4)
        ttk.Button(filter_bar, text="Export CSV", command=self._export_csv).pack(side="right")

        # Alerts tree
        columns = ("time", "symbol", "direction", "confidence", "pathway", "regime", "pips")
        self.alerts_tree = ttk.Treeview(frame, columns=columns, show="headings", height=14)
        self.alerts_tree.heading("time", text="Time (EST)")
        self.alerts_tree.heading("symbol", text="Symbol")
        self.alerts_tree.heading("direction", text="Direction")
        self.alerts_tree.heading("confidence", text="Conf.")
        self.alerts_tree.heading("pathway", text="Pathway")
        self.alerts_tree.heading("regime", text="Regime")
        self.alerts_tree.heading("pips", text="Pips")
        for col in columns:
            self.alerts_tree.column(col, width=100)
        self.alerts_tree.column("time", width=140)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.alerts_tree.yview)
        self.alerts_tree.configure(yscrollcommand=scrollbar.set)
        self.alerts_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        scrollbar.pack(side="right", fill="y", pady=4, padx=(0, 8))

        # Detail view
        self.alert_detail = scrolledtext.ScrolledText(
            frame, height=5, bg="#16213e", fg="#e0e0e0",
            font=("Consolas", 9), relief="flat", state="disabled"
        )
        self.alert_detail.pack(fill="x", padx=8, pady=(0, 6))
        self.alerts_tree.bind("<<TreeviewSelect>>", self._on_alert_select)

    # ── Tab 3: Configuration ────────────────────────────────

    def _build_config_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="  Configuration  ")

        # Pairs
        pairs_frame = ttk.LabelFrame(frame, text="Scanned Pairs (comma-separated)")
        pairs_frame.pack(fill="x", padx=8, pady=8)
        self.pairs_entry = ttk.Entry(pairs_frame, font=("Segoe UI", 11))
        self.pairs_entry.insert(0, ", ".join(self.config_data.get("symbols", ["EURUSD", "BTCUSD"])))
        self.pairs_entry.pack(fill="x", padx=10, pady=8)

        # Interval
        interval_frame = ttk.LabelFrame(frame, text="Scan Interval (seconds)")
        interval_frame.pack(fill="x", padx=8, pady=8)
        self.interval_entry = ttk.Entry(interval_frame, font=("Segoe UI", 11))
        self.interval_entry.insert(0, str(self.config_data.get("interval", 300)))
        self.interval_entry.pack(fill="x", padx=10, pady=8)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", padx=8, pady=12)
        ttk.Button(btn_frame, text="Save Config", style="Accent.TButton",
                   command=self._save_config).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Apply & Restart Scanner",
                   command=self._apply_and_restart).pack(side="left", padx=4)

        # Info
        info_frame = ttk.LabelFrame(frame, text="Scanner Command")
        info_frame.pack(fill="x", padx=8, pady=8)
        self.cmd_label = ttk.Label(info_frame, text="", style="Status.TLabel")
        self.cmd_label.pack(anchor="w", padx=10, pady=8)
        self._update_cmd_label()

    # ── Actions ─────────────────────────────────────────────

    def _refresh(self):
        self._refresh_status()
        self._refresh_conditions()
        self._refresh_alerts()
        self._update_time()
        self.after(5000, self._refresh)  # auto-refresh every 5s

    def _refresh_status(self):
        running, pid = get_scanner_status()
        if running:
            self.status_label.configure(text=f"● Scanner RUNNING (PID {pid})", foreground="#00ff88")
        else:
            self.status_label.configure(text="● Scanner STOPPED", foreground="#ff4444")

    def _refresh_conditions(self):
        # Latest alert
        alert = parse_alert_file()
        if alert:
            self.alert_title.configure(text=f"[{alert['timestamp']}] {alert['title']}")
            self.alert_body.configure(state="normal")
            self.alert_body.delete("1.0", "end")
            self.alert_body.insert("1.0", "\n".join(alert["details"]))
            self.alert_body.configure(state="disabled")
        else:
            self.alert_title.configure(text="No alerts yet")
            self.alert_body.configure(state="normal")
            self.alert_body.delete("1.0", "end")
            self.alert_body.insert("1.0", "Waiting for trade calls...")
            self.alert_body.configure(state="disabled")

        # Pairs
        for item in self.pairs_tree.get_children():
            self.pairs_tree.delete(item)
        symbols = self.config_data.get("symbols", ["EURUSD", "BTCUSD"])
        now_est = datetime.now(EST)
        for sym in symbols:
            # Check if we have recent alert data for this pair
            recent = [a for a in self.alerts_history if a.get("symbol") == sym]
            if recent:
                last = recent[-1]
                self.pairs_tree.insert("", "end", values=(
                    sym, f"Last: {last.get('direction', '?')} ({last.get('confidence', 0):.0%})",
                    last.get("timestamp", "?")
                ))
            else:
                self.pairs_tree.insert("", "end", values=(sym, "Scanning...", now_est.strftime("%H:%M:%S")))

    def _refresh_alerts(self):
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)

        days = self.filter_days.get()
        cutoff = None
        if days > 0:
            cutoff = datetime.now(EST) - td(days=days)

        filtered = self.alerts_history
        if cutoff:
            filtered = [a for a in filtered if a.get("datetime", datetime.min.replace(tzinfo=EST)) >= cutoff]

        for alert in reversed(filtered[-200:]):  # last 200
            self.alerts_tree.insert("", "end", values=(
                alert.get("timestamp", ""),
                alert.get("symbol", ""),
                alert.get("direction", ""),
                f"{alert.get('confidence', 0):.0%}",
                alert.get("pathway", ""),
                alert.get("regime", ""),
                f"{alert.get('dtb_pips', 0):.1f}" if alert.get("dtb_pips") else "—",
            ))

    def _on_alert_select(self, event):
        sel = self.alerts_tree.selection()
        if not sel:
            return
        idx = self.alerts_tree.index(sel[0])
        days = self.filter_days.get()
        cutoff = datetime.now(EST) - td(days=days) if days > 0 else None
        filtered = [a for a in self.alerts_history
                    if not cutoff or a.get("datetime", datetime.min.replace(tzinfo=EST)) >= cutoff]
        filtered = list(reversed(filtered[-200:]))
        if idx < len(filtered):
            alert = filtered[idx]
            self.alert_detail.configure(state="normal")
            self.alert_detail.delete("1.0", "end")
            self.alert_detail.insert("1.0", alert.get("message", ""))
            self.alert_detail.configure(state="disabled")

    def _update_time(self):
        now_est = datetime.now(EST)
        self.time_label.configure(text=f"EST: {now_est.strftime('%Y-%m-%d %H:%M:%S')}")

    def _update_cmd_label(self):
        pairs = ", ".join(self.config_data.get("symbols", ["EURUSD", "BTCUSD"]))
        interval = self.config_data.get("interval", 300)
        cmd = f"python quant-lab/ml/run_cerebus_unified.py --interval {interval} --symbols {pairs}"
        self.cmd_label.configure(text=cmd)

    def _save_config(self):
        pairs_text = self.pairs_entry.get().strip()
        symbols = [s.strip().upper() for s in pairs_text.split(",") if s.strip()]
        try:
            interval = int(self.interval_entry.get().strip())
        except ValueError:
            interval = 300
        self.config_data["symbols"] = symbols
        self.config_data["interval"] = interval
        save_config(self.config_data)
        self._update_cmd_label()
        messagebox.showinfo("Saved", "Configuration saved.")

    def _apply_and_restart(self):
        self._save_config()
        self._stop_scanner()
        time.sleep(1)
        self._start_scanner()

    def _start_scanner(self):
        running, _ = get_scanner_status()
        if running:
            messagebox.showinfo("Info", "Scanner is already running.")
            return
        symbols = self.config_data.get("symbols", ["EURUSD", "BTCUSD"])
        interval = self.config_data.get("interval", 300)
        cmd = [
            sys.executable,
            str(REPO_ROOT / "quant-lab" / "ml" / "run_cerebus_unified.py"),
            "--interval", str(interval),
            "--symbols",
        ] + symbols
        try:
            subprocess.Popen(cmd, cwd=str(REPO_ROOT),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0)
            messagebox.showinfo("Started", f"Scanner started (PID will appear on refresh).")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start scanner: {e}")

    def _stop_scanner(self):
        try:
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=5
            )
            killed = 0
            for line in result.stdout.strip().split("\n"):
                if "run_cerebus_unified" in line.lower():
                    parts = line.split(",")
                    if len(parts) >= 2:
                        pid = int(parts[1].strip('"'))
                        subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                                       capture_output=True, timeout=5)
                        killed += 1
            if killed:
                messagebox.showinfo("Stopped", f"Scanner stopped ({killed} process(es)).")
            else:
                messagebox.showinfo("Info", "Scanner was not running.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop scanner: {e}")

    def _export_csv(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"cerebus_alerts_{datetime.now(EST).strftime('%Y%m%d')}.csv"
        )
        if not path:
            return
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Time", "Symbol", "Direction", "Confidence", "Pathway", "Regime", "Pips"])
                for alert in self.alerts_history:
                    writer.writerow([
                        alert.get("timestamp", ""),
                        alert.get("symbol", ""),
                        alert.get("direction", ""),
                        f"{alert.get('confidence', 0):.0%}",
                        alert.get("pathway", ""),
                        alert.get("regime", ""),
                        alert.get("dtb_pips", ""),
                    ])
            messagebox.showinfo("Exported", f"Alerts exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")


# ── Entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    app = CerebusMonitor()
    app.mainloop()
