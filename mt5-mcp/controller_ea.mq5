//+------------------------------------------------------------------+
//|                                        MT5_Backtest_Controller.mq5 |
//|        Helper EA for MCP-driven backtesting via file IPC           |
//+------------------------------------------------------------------+
#property copyright "MT5 MCP Agent"
#property link      ""
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>
#include <Files/FileTxt.mqh>

// Input parameters
input string InpCommandFile   = "backtest_command.json";    // Command file path
input string InpResultFile    = "backtest_result.json";     // Result file path
input string InpEaName        = "";                         // EA name to test (auto-detect if empty)
input string InpSymbol        = "EURUSD";                   // Default symbol
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_H1;             // Default timeframe
input double   InpDeposit     = 10000.0;                    // Deposit for backtest
input datetime InpFromDate    = D'2024.01.01';               // Backtest start
input datetime InpToDate      = D'2025.12.31';               // Backtest end
input bool     InpOptimization = false;                     // Run optimization

CTrade trade;

//+------------------------------------------------------------------+
//| Expert initialization                                            |
//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(234000);
   trade.SetDeviationInPoints(10);
   
   // Enable testing mode
   if(!MQLInfoInteger(MQL_TESTER))
     {
      Print("Warning: This EA is designed to run in Strategy Tester");
     }
   
   EventSetMillisecondTimer(1000); // Check for commands every second
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   EventKillTimer();
  }

//+------------------------------------------------------------------+
//| Timer - checks for command file                                  |
//+------------------------------------------------------------------+
void OnTimer()
  {
   // Check if command file exists
   if(!FileIsExist(InpCommandFile))
      return;
   
   // Read and parse command
   string command = ReadFile(InpCommandFile);
   if(command == "")
      return;
   
   // Delete command file to prevent re-execution
   FileDelete(InpCommandFile);
   
   // Parse JSON command (simplified parsing)
   string ea_name = ParseJsonField(command, "ea_name");
   string symbol = ParseJsonField(command, "symbol");
   string timeframe_str = ParseJsonField(command, "timeframe");
   string from_date_str = ParseJsonField(command, "from_date");
   string to_date_str = ParseJsonField(command, "to_date");
   string deposit_str = ParseJsonField(command, "deposit");
   
   if(ea_name == "") ea_name = InpEaName;
   if(symbol == "") symbol = InpSymbol;
   if(deposit_str == "") deposit_str = DoubleToString(InpDeposit, 2);
   
   // Run backtest
   RunBacktest(ea_name, symbol, timeframe_str, from_date_str, to_date_str, deposit_str);
  }

//+------------------------------------------------------------------+
//| Run backtest and write results                                   |
//+------------------------------------------------------------------+
void RunBacktest(string ea_name, string symbol, string timeframe_str,
                 string from_date_str, string to_date_str, string deposit_str)
  {
   // Set symbol
   if(!SymbolSelect(symbol, true))
     {
      WriteResult("error", "Symbol not found: " + symbol);
      return;
     }
   
   // Parse timeframe
   ENUM_TIMEFRAMES tf = StringToTimeframe(timeframe_str);
   
   // Parse dates
   datetime from_date = StringToTime(from_date_str);
   datetime to_date = StringToTime(to_date_str);
   double deposit = StringToDouble(deposit_str);
   
   // Set testing parameters
   TesterSetDeposit(deposit);
   TesterSetSymbols(symbol);
   
   // Initialize tester
   if(!TesterInit(symbol, tf, from_date, to_date, deposit,
                  MODE_EVERY_TICK, 1, ea_name))
     {
      WriteResult("error", "TesterInit failed");
      return;
     }
   
   // Start test
   TesterStart();
   
   // Wait for completion
   while(!TesterIsStopped())
     {
      Sleep(100);
     }
   
   // Get results
   double profit = TesterStatistics(STAT_PROFIT);
   double balance = TesterStatistics(STAT_BALANCE);
   double profit_factor = TesterStatistics(STAT_PROFIT_FACTOR);
   double sharpe = TesterStatistics(STAT_SHARPE);
   double max_dd = TesterStatistics(STAT_EQUITY_DDREL_PERCENT);
   int total_trades = (int)TesterStatistics(STAT_TRADES);
   int profit_trades = (int)TesterStatistics(STAT_PROFIT_TRADES);
   int loss_trades = (int)TesterStatistics(STAT_LOSS_TRADES);
   double expected_payoff = TesterStatistics(STAT_EXPECTED_PAYOFF);
   double recovery_factor = TesterStatistics(STAT_RECOVERY_FACTOR);
   
   // Format results as JSON
   string result = "";
   result += "{";
   result += "\"status\": \"completed\",";
   result += "\"ea_name\": \"" + ea_name + "\",";
   result += "\"symbol\": \"" + symbol + "\",";
   result += "\"timeframe\": \"" + timeframe_str + "\",";
   result += "\"from_date\": \"" + from_date_str + "\",";
   result += "\"to_date\": \"" + to_date_str + "\",";
   result += "\"deposit\": " + deposit_str + ",";
   result += "\"profit\": " + DoubleToString(profit, 2) + ",";
   result += "\"balance\": " + DoubleToString(balance, 2) + ",";
   result += "\"profit_factor\": " + DoubleToString(profit_factor, 4) + ",";
   result += "\"sharpe_ratio\": " + DoubleToString(sharpe, 4) + ",";
   result += "\"max_drawdown_pct\": " + DoubleToString(max_dd, 2) + ",";
   result += "\"total_trades\": " + IntegerToString(total_trades) + ",";
   result += "\"profit_trades\": " + IntegerToString(profit_trades) + ",";
   result += "\"loss_trades\": " + IntegerToString(loss_trades) + ",";
   result += "\"expected_payoff\": " + DoubleToString(expected_payoff, 2) + ",";
   result += "\"recovery_factor\": " + DoubleToString(recovery_factor, 2);
   result += "}";
   
   // Write results
   WriteResult("success", result);
   
   // Deinitialize tester
   TesterDeinit();
  }

//+------------------------------------------------------------------+
//| Write result to file                                              |
//+------------------------------------------------------------------+
void WriteResult(string status, string data)
  {
   int handle = FileOpen(InpResultFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
     {
      FileWriteString(handle, "{\"status\": \"" + status + "\",");
      if(status == "success")
         FileWriteString(handle, data);
      else
         FileWriteString(handle, "\"message\": \"" + data + "\"");
      FileWriteString(handle, "}");
      FileClose(handle);
      Print("Result written to " + InpResultFile);
     }
   else
      Print("Error writing result file");
  }

//+------------------------------------------------------------------+
//| Parse JSON field (simplified)                                     |
//+------------------------------------------------------------------+
string ParseJsonField(string json, string field)
  {
   string search = "\"" + field + "\":";
   int pos = StringFind(json, search);
   if(pos < 0) return "";
   
   pos += StringLen(search);
   
   // Skip whitespace
   while(pos < StringLen(json) && (json[pos] == ' ' || json[pos] == '\t'))
      pos++;
   
   if(pos >= StringLen(json)) return "";
   
   // Check if string value
   if(json[pos] == '"')
     {
      pos++;
      int end = StringFind(json, "\"", pos);
      if(end > pos)
         return StringSubstr(json, pos, end - pos);
     }
   else
     {
      // Number or boolean value
      int end = pos;
      while(end < StringLen(json) && json[end] != ',' && json[end] != '}' && json[end] != ' ')
         end++;
      return StringSubstr(json, pos, end - pos);
     }
   
   return "";
  }

//+------------------------------------------------------------------+
//| String to timeframe                                               |
//+------------------------------------------------------------------+
ENUM_TIMEFRAMES StringToTimeframe(string tf)
  {
   if(tf == "M1")  return PERIOD_M1;
   if(tf == "M5")  return PERIOD_M5;
   if(tf == "M15") return PERIOD_M15;
   if(tf == "M30") return PERIOD_M30;
   if(tf == "H1")  return PERIOD_H1;
   if(tf == "H4")  return PERIOD_H4;
   if(tf == "D1")  return PERIOD_D1;
   if(tf == "W1")  return PERIOD_W1;
   if(tf == "MN1") return PERIOD_MN1;
   return PERIOD_H1;
  }
//+------------------------------------------------------------------+