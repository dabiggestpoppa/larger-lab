/**
 * ParameterOverlay — Live ML-Optimized Parameter Display
 * 
 * Shows optimized parameters per asset per regime, overlaid on the
 * existing OCE display. Updates when regime changes or optimizer runs.
 */
import React, { useEffect, useState } from 'react';
import { useMlStore, RegimeLabel } from '../../stores/mlStore';

const REGIME_COLORS: Record<RegimeLabel, string> = {
  CONFIRMED: '#51cf66',
  CAUTION: '#ffd43b',
  FAILED: '#ff6b6b',
  'NO-GO': '#868e96',
};

const ALL_SYMBOLS = [
  'EURUSD', 'GBPUSD', 'USDCHF', 'USDJPY', 'AUDUSD', 'NZDUSD',
  'GBPJPY', 'GBPAUD', 'GBPNZD', 'GBPCHF', 'CHFJPY',
  'US500', 'DE30', 'FR40',
  'XAUUSD', 'XAGUSD', 'BTCUSD', 'ETHUSD',
];

export const ParameterOverlay: React.FC = () => {
  const {
    optimizedParams,
    regimes,
    selectedSymbol,
    setSelectedSymbol,
    setOptimizedParams,
  } = useMlStore();

  const [expanded, setExpanded] = useState(false);

  const params = optimizedParams[selectedSymbol] || [];
  const currentRegime = regimes[selectedSymbol];
  const activeParam = params.find(p => p.regime === currentRegime?.regime);

  // Poll optimized params from ML backend
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch('/api/v1/ml/params/' + selectedSymbol);
        if (res.ok) {
          const data = await res.json();
          setOptimizedParams(selectedSymbol, data);
        }
      } catch {
        // Backend not ready
      }
    };

    poll();
    const interval = setInterval(poll, 60000);  // Params change less frequently
    return () => clearInterval(interval);
  }, [selectedSymbol, setOptimizedParams]);

  return (
    <div className="flex flex-col h-full bg-[#0a0a0f] text-gray-200 font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <span className="text-gray-400 font-semibold">ML PARAMETERS</span>
          {currentRegime && (
            <span
              className="px-2 py-0.5 rounded text-[10px] font-bold"
              style={{
                backgroundColor: REGIME_COLORS[currentRegime.regime] + '20',
                color: REGIME_COLORS[currentRegime.regime],
              }}
            >
              {currentRegime.regime}
            </span>
          )}
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-500 hover:text-gray-300 transition-colors"
        >
          {expanded ? '▾' : '▸'}
        </button>
      </div>

      {/* Asset tabs */}
      <div className="flex flex-wrap gap-1 px-3 py-2 border-b border-gray-800/50">
        {ALL_SYMBOLS.map(sym => {
          const r = regimes[sym];
          const isSelected = sym === selectedSymbol;
          const color = r ? REGIME_COLORS[r.regime] : '#495057';
          return (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              className={`px-1.5 py-0.5 rounded text-[9px] font-mono transition-all ${
                isSelected
                  ? 'bg-gray-700 text-white'
                  : 'bg-gray-800/30 text-gray-500 hover:bg-gray-700/50'
              }`}
              style={{ borderBottom: `2px solid ${color}` }}
            >
              {sym}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* Active regime params */}
        {activeParam ? (
          <div className="space-y-2">
            <div className="text-gray-500 text-[10px] uppercase tracking-wider">
              Active — {currentRegime?.regime}
            </div>
            <ParamRow label="AU Multiplier" value={activeParam.au_multiplier} format="0.00" />
            <ParamRow label="Buffer" value={activeParam.buffer} format="0.0" suffix="pts" />
            <ParamRow label="DZ Width" value={activeParam.dz_width} format="0.00" />
            <ParamRow label="Trigger Mult" value={activeParam.trigger_multiplier} format="0.00" />
            <div className="border-t border-gray-800 pt-2 mt-2">
              <ParamRow label="Sharpe" value={activeParam.sharpe} format="0.00" />
              <ParamRow label="Win Rate" value={activeParam.win_rate * 100} format="0.0" suffix="%" />
              <ParamRow label="Max DD" value={activeParam.max_dd} format="0.00" suffix="%" />
            </div>
          </div>
        ) : (
          <div className="text-gray-600 text-center py-4">
            {currentRegime ? 'Optimizing...' : 'Awaiting regime...'}
          </div>
        )}

        {/* All regimes (expanded) */}
        {expanded && (
          <div className="border-t border-gray-800 pt-3 space-y-3">
            <div className="text-gray-500 text-[10px] uppercase tracking-wider">
              All Regimes
            </div>
            {params.length > 0 ? (
              <table className="w-full text-[10px]">
                <thead>
                  <tr className="text-gray-500 border-b border-gray-800">
                    <th className="text-left py-1">Regime</th>
                    <th className="text-right">AU Mult</th>
                    <th className="text-right">Buffer</th>
                    <th className="text-right">WR</th>
                    <th className="text-right">Sharpe</th>
                  </tr>
                </thead>
                <tbody>
                  {params.map(p => (
                    <tr
                      key={p.regime}
                      className="border-b border-gray-800/30 text-gray-300"
                    >
                      <td
                        className="py-1 font-bold"
                        style={{ color: REGIME_COLORS[p.regime] }}
                      >
                        {p.regime}
                      </td>
                      <td className="text-right">{p.au_multiplier.toFixed(2)}</td>
                      <td className="text-right">{p.buffer.toFixed(1)}</td>
                      <td className="text-right">{(p.win_rate * 100).toFixed(1)}%</td>
                      <td className="text-right">{p.sharpe.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-gray-600 text-center py-2">
                No optimized params yet
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const ParamRow: React.FC<{ label: string; value: number; format: string; suffix?: string }> = ({
  label, value, format, suffix
}) => {
  const formatted = value.toFixed(parseInt(format.split('.')[1] || '0'));
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-400">{label}</span>
      <span className="text-gray-200">
        {formatted}{suffix ? ` ${suffix}` : ''}
      </span>
    </div>
  );
};

export default ParameterOverlay;
