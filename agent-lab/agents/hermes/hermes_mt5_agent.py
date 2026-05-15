#!/usr/bin/env python3
"""
Hermes MT5 Strategy Agent v3 — REAL BACKTEST EDITION
=====================================================
Reproduces winning strategies from CEREBUS_FX_v4_Complete_Manual.pdf
using REAL MetaEditor compilation + MT5 Strategy Tester backtesting.

WORKSPACE: hermes_workspace/ — all work here, originals never touched.
BACKTEST:  Real MT5 Strategy Tester via mt5_backtest_terminal (.set files).
           Results read via mt5_get_last_report (XML parsing).
STRATEGY:  Hand-crafted MQL5 templates based on CEREBUS manual rules.
           AI optimizes parameters only — never generates raw code.

Mission: Reproduce at least 2 winning strategies from the manual.
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

# ── Paths ────────────────────────────────────────────────────────────────────
LAB_ROOT = Path(__file__).parent.parent.parent.parent
AGENT_DIR = Path(__file__).parent
WORKSPACE = AGENT_DIR / "hermes_workspace"
MANUAL_PATH = WORKSPACE / "CEREBUS_FX_v4_Complete_Manual.pdf"
MT5_MCP_COPY = WORKSPACE / "mt5-mcp-copy"
MT5_MCP_SERVER = MT5_MCP_COPY / "mt5_mcp_server.py"
STRATEGIES_DIR = WORKSPACE / "strategies"
REPORTS_DIR = WORKSPACE / "reports"

sys.path.insert(0, str(LAB_ROOT))

from parallel_thought.parallel_thought_synthesizer import (
    ParallelThoughtSynthesizer, SynthesisStrategy,
)
from parallel_thought.hermes_parallel_agent import ParallelThinkingAgent

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("hermes")


# ── Telegram Notifier ───────────────────────────────────────────────────────
class TelegramNotifier:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)

    async def send(self, message: str):
        if not self.enabled:
            return
        try:
            from telegram import Bot
            bot = Bot(token=self.token)
            await bot.send_message(chat_id=self.chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Telegram send failed: {e}")


# ── MT5 MCP Client (direct import) ──────────────────────────────────────────
class MT5MCPClient:
    def __init__(self, server_script: Path):
        self.server_script = server_script
        self._tools = {}
        self._imported = False

    def _ensure_imported(self):
        if self._imported:
            return
        try:
            server_dir = str(self.server_script.parent)
            if server_dir not in sys.path:
                sys.path.insert(0, server_dir)
            import importlib.util
            spec = importlib.util.spec_from_file_location("mt5_mcp_server", str(self.server_script))
            mod = importlib.util.module_from_spec(spec)
            old_argv = sys.argv
            sys.argv = ["mt5_mcp_server"]
            try:
                spec.loader.exec_module(mod)
            finally:
                sys.argv = old_argv
            self._tools = {
                name: getattr(mod, name, None)
                for name in [
                    "mt5_connect", "mt5_get_account_info", "mt5_create_ea",
                    "mt5_compile_file", "mt5_backtest_python", "mt5_backtest_terminal",
                    "mt5_get_last_report", "mt5_get_market_data", "mt5_write_mql5",
                ]
            }
            self._imported = True
            logger.info("MT5 MCP server imported OK")
        except Exception as e:
            logger.error(f"MT5 MCP import failed: {e}")
            self._imported = True

    def call(self, tool_name: str, **kwargs) -> str:
        self._ensure_imported()
        func = self._tools.get(tool_name)
        if not func:
            return f"Error: tool '{tool_name}' not found"
        try:
            return str(func(**kwargs))
        except Exception as e:
            return f"Error: {e}"

    def connect(self): return self.call("mt5_connect")
    def compile_file(self, path): return self.call("mt5_compile_file", filepath=path)
    def backtest_terminal(self, ea_name, symbol="EURUSD", tf="H1", deposit=10000,
                          from_date="2024.01.01", to_date="2025.12.31"):
        return self.call("mt5_backtest_terminal", ea_name=ea_name, symbol=symbol,
                         timeframe=tf, deposit=deposit, from_date=from_date, to_date=to_date)
    def get_last_report(self): return self.call("mt5_get_last_report")
    def write_mql5(self, filename, content, folder="Experts"):
        return self.call("mt5_write_mql5", filename=filename, content=content, folder=folder)


# ── MQL5 Strategy Templates (HAND-CRAFTED — not AI-generated) ───────────────

def cerebus_option_b_mql5(lot_size=0.1, magic=123456, tier_trigger=19,
                          stop_loss=15, take_profit=19, max_loops=8):
    """CEREBUS FX Option B — Continuous Loop Super Scalper. Manual page 187+."""
    session_filter_str = "true"
    return f'''//+------------------------------------------------------------------+
//| CEREBUS_OptionB.mq5 — Continuous Loop Super Scalper              |
//| CEREBUS FX v4 Manual page 187+                                   |
//+------------------------------------------------------------------+
#property copyright "Hermes AI — CEREBUS Manual"
#property version   "3.00"
#property strict

input double   InpLotSize       = {lot_size};
input int      InpMagicNum      = {magic};
input int      InpTierTrigger   = {tier_trigger};
input int      InpStopLoss      = {stop_loss};
input int      InpTakeProfit    = {take_profit};
input bool     InpUseSession    = {session_filter_str};
input int      InpMaxLoops      = {max_loops};
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_M5;

#include <Trade/Trade.mqh>
CTrade trade;

datetime g_lastExitTime = 0;
int      g_loopCount   = 0;
bool     g_inSession   = false;

int OnInit() {{
   trade.SetExpertMagicNumber(InpMagicNum);
   trade.SetDeviationInPoints(10);
   Print("CEREBUS Option B v3 initialized.");
   return(INIT_SUCCEEDED);
}}

bool IsSessionActive() {{
   datetime now = TimeCurrent();
   int hourEST = (TimeHour(now) - 5 + 24) % 24;
   return (hourEST < 12);
}}

double GetImpulsePips() {{
   double o = iOpen(_Symbol, InpTimeframe, 1);
   double c = iClose(_Symbol, InpTimeframe, 1);
   return MathAbs(c - o) / _Point;
}}

bool InDensityZone(double price) {{
   double zh = iHigh(_Symbol, InpTimeframe, 1);
   double zl = iLow(_Symbol, InpTimeframe, 1);
   return (price >= zl && price <= zh);
}}

int CountPositions() {{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNum)
         count++;
   return count;
}}

void OnTick() {{
   bool sessionActive = IsSessionActive();
   if(!sessionActive && g_inSession) {{
      g_loopCount = 0;
      g_inSession = false;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
         if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNum)
            trade.PositionClose(PositionGetTicket(i));
      return;
   }}
   g_inSession = sessionActive;
   if(!sessionActive) return;
   if(g_loopCount >= InpMaxLoops) return;
   if(CountPositions() > 0) return;
   if(Bars(_Symbol, InpTimeframe) < 3) return;

   double impulse = GetImpulsePips();
   double prevClose = iClose(_Symbol, InpTimeframe, 1);
   double prevOpen  = iOpen(_Symbol, InpTimeframe, 1);

   if(impulse >= InpTierTrigger * 10) {{
      if(prevClose > prevOpen) {{
         double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         if(InDensityZone(ask)) {{
            double sl = ask - InpStopLoss * 10 * _Point;
            double tp = ask + InpTakeProfit * 10 * _Point;
            if(trade.Buy(InpLotSize, _Symbol, ask, sl, tp, "CEREBUS_B")) {{
               g_loopCount++;
               Print("BUY loop ", g_loopCount, "/", InpMaxLoops);
            }}
         }}
      }} else if(prevClose < prevOpen) {{
         double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         if(InDensityZone(bid)) {{
            double sl = bid + InpStopLoss * 10 * _Point;
            double tp = bid - InpTakeProfit * 10 * _Point;
            if(trade.Sell(InpLotSize, _Symbol, bid, sl, tp, "CEREBUS_B")) {{
               g_loopCount++;
               Print("SELL loop ", g_loopCount, "/", InpMaxLoops);
            }}
         }}
      }}
   }}
}}
//+------------------------------------------------------------------+
'''


def cerebus_option_a_mql5(lot_size=0.01, magic=654321, impulse_threshold=20,
                          sl_buffer=20, tp_units=25, max_trades=5):
    """CEREBUS FX Option A — Original Scalper."""
    return f'''//+------------------------------------------------------------------+
//| CEREBUS_OptionA.mq5 — Original Scalper                           |
//| CEREBUS FX v4 Manual                                             |
//+------------------------------------------------------------------+
#property copyright "Hermes AI — CEREBUS Manual"
#property version   "3.00"
#property strict

input double   InpLotSize        = {lot_size};
input int      InpMagicNum       = {magic};
input int      InpImpulseThresh  = {impulse_threshold};
input int      InpSLBuffer       = {sl_buffer};
input int      InpTPUnits        = {tp_units};
input int      InpMaxTrades      = {max_trades};
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_M5;

#include <Trade/Trade.mqh>
CTrade trade;

int g_tradeCount = 0;

int OnInit() {{
   trade.SetExpertMagicNumber(InpMagicNum);
   trade.SetDeviationInPoints(10);
   Print("CEREBUS Option A v3 initialized.");
   return(INIT_SUCCEEDED);
}}

int CountPositions() {{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNum)
         count++;
   return count;
}}

double GetImpulsePips() {{
   double o = iOpen(_Symbol, InpTimeframe, 1);
   double c = iClose(_Symbol, InpTimeframe, 1);
   return MathAbs(c - o) / _Point;
}}

bool InDensityZone(double price) {{
   double zh = iHigh(_Symbol, InpTimeframe, 1);
   double zl = iLow(_Symbol, InpTimeframe, 1);
   return (price >= zl && price <= zh);
}}

void OnTick() {{
   static int lastDay = 0;
   int today = TimeDay(TimeCurrent());
   if(today != lastDay) {{ g_tradeCount = 0; lastDay = today; }}
   if(g_tradeCount >= InpMaxTrades) return;
   if(CountPositions() > 0) return;
   if(Bars(_Symbol, InpTimeframe) < 3) return;

   double impulse = GetImpulsePips();
   double prevClose = iClose(_Symbol, InpTimeframe, 1);
   double prevOpen  = iOpen(_Symbol, InpTimeframe, 1);

   if(impulse >= InpImpulseThresh * 10) {{
      if(prevClose > prevOpen) {{
         double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         if(InDensityZone(ask)) {{
            double sl = ask - InpSLBuffer * 10 * _Point;
            double tp = ask + InpTPUnits * 10 * _Point;
            if(trade.Buy(InpLotSize, _Symbol, ask, sl, tp, "CEREBUS_A")) {{
               g_tradeCount++;
               Print("BUY trade ", g_tradeCount, "/", InpMaxTrades);
            }}
         }}
      }} else if(prevClose < prevOpen) {{
         double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         if(InDensityZone(bid)) {{
            double sl = bid + InpSLBuffer * 10 * _Point;
            double tp = bid - InpTPUnits * 10 * _Point;
            if(trade.Sell(InpLotSize, _Symbol, bid, sl, tp, "CEREBUS_A")) {{
               g_tradeCount++;
               Print("SELL trade ", g_tradeCount, "/", InpMaxTrades);
            }}
         }}
      }}
   }}
}}
//+------------------------------------------------------------------+
'''


# ── Strategy definitions ───────────────────────────────────────────────────
STRATEGY_TEMPLATES = {
    "CEREBUS_OptionB": {
        "generator": cerebus_option_b_mql5,
        "defaults": {"lot_size": 0.1, "magic": 123456, "tier_trigger": 19,
                     "stop_loss": 15, "take_profit": 19, "max_loops": 8},
        "param_ranges": {
            "lot_size": [0.01, 0.05, 0.1, 0.2],
            "tier_trigger": [15, 17, 19, 21, 25],
            "stop_loss": [10, 12, 15, 18, 20],
            "take_profit": [15, 17, 19, 21, 25],
            "max_loops": [4, 6, 8, 10],
        },
    },
    "CEREBUS_OptionA": {
        "generator": cerebus_option_a_mql5,
        "defaults": {"lot_size": 0.01, "magic": 654321, "impulse_threshold": 20,
                     "sl_buffer": 20, "tp_units": 25, "max_trades": 5},
        "param_ranges": {
            "lot_size": [0.01, 0.05, 0.1],
            "impulse_threshold": [15, 18, 20, 25],
            "sl_buffer": [15, 18, 20, 25],
            "tp_units": [20, 25, 30],
            "max_trades": [3, 5, 8],
        },
    },
}


# ── Strategy Tracker ────────────────────────────────────────────────────────
class StrategyTracker:
    TRACKER_FILE = WORKSPACE / "strategy_tracker.json"
    def __init__(self): self.data = self._load()
    def _load(self):
        if self.TRACKER_FILE.exists():
            with open(self.TRACKER_FILE) as f: return json.load(f)
        return {"strategies": [], "completed": [], "best_results": {}, "iteration": 0}
    def save(self):
        with open(self.TRACKER_FILE, "w") as f: json.dump(self.data, f, indent=2)
    def add_result(self, name, params, metrics, is_winner):
        entry = {"name": name, "params": params, "metrics": metrics,
                 "is_winner": is_winner, "timestamp": datetime.now().isoformat()}
        self.data["strategies"].append(entry)
        if is_winner and name not in self.data["completed"]:
            self.data["completed"].append(name)
            self.data["best_results"][name] = entry
        self.save()
    @property
    def completed_count(self): return len(self.data["completed"])
    @property
    def target_reached(self): return self.completed_count >= 2


# ── Hermes Agent v3 ────────────────────────────────────────────────────────
class HermesMT5Agent:
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.synthesizer = ParallelThoughtSynthesizer()
        self.agent = ParallelThinkingAgent()
        self.iteration = 0
        self.max_iterations = self.config.get("schedule", {}).get("max_iterations", 200)
        self.notifier = TelegramNotifier()
        self.mcp = MT5MCPClient(MT5_MCP_SERVER)
        self.tracker = StrategyTracker()
        self._paused = False
        self._stopped = False
        STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_config(self, path):
        if path and Path(path).exists():
            with open(path) as f: return json.load(f)
        return {"goal": "Reproduce 2+ winning CEREBUS strategies", "schedule": {"max_iterations": 200}}

    async def run_continuous(self):
        goal = self.config["goal"]
        print(f"\n{'='*70}\n⚡ HERMES MT5 AGENT v3 — REAL BACKTEST\n🎯 {goal}\n📁 {WORKSPACE}\n{'='*70}")
        await self.notifier.send(f"⚡ *Hermes MT5 v3 Started*\n🎯 {goal}")

        print("\n🔌 Connecting to MT5...")
        mt5_status = self.mcp.connect()
        print(f"   {mt5_status[:300]}")
        await self.notifier.send(f"🔌 MT5:\n`{mt5_status[:400]}`")

        pending = [k for k in STRATEGY_TEMPLATES if k not in self.tracker.data.get("completed", [])]
        param_history = {}

        while self.iteration < self.max_iterations:
            if self._stopped:
                await self.notifier.send("🔴 Hermes stopped."); break
            while self._paused: await asyncio.sleep(10)

            self.iteration += 1
            self.tracker.data["iteration"] = self.iteration
            self.tracker.save()

            if not pending:
                pending = [k for k in STRATEGY_TEMPLATES if k not in self.tracker.data.get("completed", [])]
            strategy_key = pending[0] if pending else list(STRATEGY_TEMPLATES.keys())[0]
            template = STRATEGY_TEMPLATES[strategy_key]

            print(f"\n{'='*70}\n🔄 ITER {self.iteration}/{self.max_iterations} | {strategy_key} | Done: {self.tracker.completed_count}/2\n{'='*70}")

            try:
                params = await self._optimize_params(strategy_key, template, param_history)
                print(f"   📊 Params: {json.dumps(params)}")

                mql5_code = template["generator"](**params)
                ea_name = f"{strategy_key}_v3"
                mql5_path = STRATEGIES_DIR / f"{ea_name}.mq5"
                mql5_path.write_text(mql5_code, encoding="utf-8")
                print(f"   📝 {mql5_path.name} ({len(mql5_code)} chars)")

                # Write .mq5 directly to MT5 Experts folder for Strategy Tester
                mt5_data = self.mcp.call("find_mt5_data_dir") if hasattr(self.mcp, 'call') else None
                write_result = self.mcp.write_mql5(f"{ea_name}.mq5", mql5_code, "Experts")
                print(f"   📂 MT5 write: {write_result[:150]}")

                # Try compilation (may fail with GUI MetaEditor, that's OK)
                print(f"   🔨 Compiling...")
                compile_result = self.mcp.compile_file(str(mql5_path))
                compiled = "successful" in compile_result.lower() or "✅" in compile_result
                print(f"   {'✅' if compiled else '⚠️'} {compile_result[:200]}")

                # REAL backtest via MT5 Strategy Tester (launches terminal with .set config)
                print(f"   🧪 MT5 Strategy Tester backtest...")
                bt_result = self.mcp.backtest_terminal(ea_name=ea_name, symbol="EURUSD", tf="H1",
                    deposit=10000, from_date="2024.01.01", to_date="2025.12.31")
                print(f"   📈 {bt_result[:400]}")

                # Wait for Strategy Tester to complete
                wait_time = 60
                print(f"   ⏳ Waiting {wait_time}s for Strategy Tester...")
                await asyncio.sleep(wait_time)

                # Read backtest report
                report = self.mcp.get_last_report()
                print(f"   📄 Report length: {len(report)} chars")
                print(f"   📄 Report preview: {report[:600]}")

                metrics = self._parse_report_metrics(report)
                is_winner = self._evaluate_winner(metrics)
                print(f"   📊 Metrics: {json.dumps(metrics)}")
                print(f"   {'🏆 WINNER!' if is_winner else '📊 Not yet'}")

                self.tracker.add_result(strategy_key, params, metrics, is_winner)
                param_history.setdefault(strategy_key, []).append(params)

                # Save detailed report
                (REPORTS_DIR / f"{strategy_key}_iter{self.iteration}.json").write_text(
                    json.dumps({"iteration": self.iteration, "strategy": strategy_key,
                                "params": params, "compiled": compiled, "metrics": metrics,
                                "is_winner": is_winner, "backtest_raw": bt_result[:1000],
                                "report_raw": report[:2000],
                                "timestamp": datetime.now().isoformat()}, indent=2), encoding="utf-8")

                # Update simple status file for easy monitoring
                status = {
                    "last_update": datetime.now().isoformat(),
                    "iteration": self.iteration,
                    "current_strategy": strategy_key,
                    "completed": self.tracker.completed_count,
                    "target": 2,
                    "winners": self.tracker.data.get("completed", []),
                    "last_metrics": metrics,
                    "last_compiled": compiled,
                    "status": "running",
                }
                (WORKSPACE / "hermes_status.json").write_text(
                    json.dumps(status, indent=2), encoding="utf-8")

                if self.notifier.enabled:
                    emoji = "🏆" if is_winner else "📊"
                    msg = (f"{emoji} *Hermes v3 — Iter {self.iteration}*\nStrategy: *{strategy_key}*\n"
                           f"Compiled: {'✅' if compiled else '⚠️'}\n")
                    if metrics:
                        msg += (f"Win Rate: *{metrics.get('win_rate', 'N/A')}*\n"
                                f"P&L: *{metrics.get('net_pnl', 'N/A')}*\n"
                                f"Max DD: *{metrics.get('max_dd', 'N/A')}*\n"
                                f"Trades: *{metrics.get('trades', 'N/A')}*\n")
                    msg += f"\nDone: *{self.tracker.completed_count}/2*"
                    await self.notifier.send(msg)

                if self.tracker.target_reached:
                    msg = f"🎉 *TARGET REACHED!* {self.tracker.completed_count} winning strategies!"
                    print(f"\n{msg}"); await self.notifier.send(msg); break

            except Exception as e:
                err = f"❌ Error iter {self.iteration}: {e}"
                logger.exception("Iteration error"); print(err)
                await self.notifier.send(err)

            await asyncio.sleep(15)

        print(f"\n🏁 Done. {self.tracker.completed_count}/2 strategies. Reports: {REPORTS_DIR}")

    async def _optimize_params(self, strategy_key, template, param_history):
        history = param_history.get(strategy_key, [])
        defaults = template["defaults"]
        ranges = template["param_ranges"]
        if not history:
            return dict(defaults)
        try:
            prompt = f"""Optimize {strategy_key} parameters. Previous tries: {json.dumps(history[-5:])}.
Ranges: {json.dumps(ranges, indent=2)}. Suggest better params as JSON."""
            result = await self.agent.plan(goal=f"Optimize {strategy_key}", context=prompt,
                                           strategy=SynthesisStrategy.WEIGHTED_CONSENSUS)
            json_match = re.search(r'\{[^}]+\}', result.plan, re.DOTALL)
            if json_match:
                params = json.loads(json_match.group(0))
                for key, value in params.items():
                    if key in ranges and isinstance(ranges[key], list) and value not in ranges[key]:
                        params[key] = defaults.get(key, ranges[key][0])
                for key, default_val in defaults.items():
                    if key not in params: params[key] = default_val
                return params
        except Exception as e:
            logger.warning(f"Param optimization failed: {e}")
        return dict(defaults)

    def _parse_report_metrics(self, report_text):
        metrics = {}
        for key, pattern in {
            "trades": r"Trades:\s*<value>(\d+)",
            "net_pnl": r"Net Profit:\s*<value>\$?([-\d,.]+)",
            "max_dd": r"Max Drawdown:\s*<value>[\d.]+%?\s*\$?([-\d,.]+)",
            "win_rate": r"Win Rate:\s*<value>[\d.]+",
            "profit_factor": r"Profit Factor:\s*<value>([\d.]+)",
            "sharpe": r"Sharpe Ratio:\s*<value>([\d.]+)",
        }.items():
            m = re.search(pattern, report_text, re.IGNORECASE)
            if m:
                try: metrics[key] = float(m.group(1).replace(",", ""))
                except: pass
        for key, pattern in {
            "trades": r"Total Trades:\s*(\d+)",
            "net_pnl": r"Net P&L:\s*\$?([-\d,.]+)",
            "max_dd": r"Max Drawdown:\s*([-\d.]+)",
            "win_rate": r"Win Rate:\s*([\d.]+)",
        }.items():
            if key not in metrics:
                m = re.search(pattern, report_text, re.IGNORECASE)
                if m:
                    try: metrics[key] = float(m.group(1).replace(",", ""))
                    except: pass
        return metrics

    def _evaluate_winner(self, metrics):
        if not metrics: return False
        return (metrics.get("trades", 0) >= 5 and metrics.get("net_pnl", 0) > 0
                and metrics.get("max_dd", -999) > -20 and metrics.get("win_rate", 0) > 40)


async def main():
    config_path = AGENT_DIR / "hermes_mt5_config.json"
    agent = HermesMT5Agent(str(config_path))
    await agent.run_continuous()

if __name__ == "__main__":
    asyncio.run(main())
