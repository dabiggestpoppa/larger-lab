/**
 * RegimePanel — ML Regime Display with Confidence Bars
 * 
 * Shows current regime prediction per asset with probability distribution,
 * model status, and drift indicator.
 */
import React, { useEffect } from 'react';
import { useMlStore, RegimeLabel } from '../../stores/mlStore';

const REGIME_COLORS: Record<RegimeLabel, string> = {
  CONFIRMED: '#51cf66',
  CAUTION: '#ffd43b',
  FAILED: '#ff6b6b',
  'NO-GO': '#868e96',
};

const REGIME_BG: Record<RegimeLabel, string> = {
  CONFIRMED: 'rgba(81, 207, 102, 0.15)',
  CAUTION: 'rgba(255, 212, 59, 0.15)',
  FAILED: 'rgba(255, 107, 107, 0.15)',
  'NO-GO': 'rgba(134, 142, 150, 0.15)',
};

const ALL_SYMBOLS = [
  'EURUSD', 'GBPUSD', 'USDCHF', 'USDJPY', 'AUDUSD', 'NZDUSD',
  'GBPJPY', 'GBPAUD', 'GBPNZD', 'GBPCHF', 'CHFJPY',
  'US500', 'DE30', 'FR40',
  'XAUUSD', 'XAGUSD', 'BTCUSD', 'ETHUSD',
];

export const RegimePanel: React.FC = () => {
  const {
    regimes,
    modelStatus,
    selectedSymbol,
    setSelectedSymbol,
    setRegime,
    setModelStatus,
  } = useMlStore();

  // Poll ML backend for regime updates
  useEffect(() => {
    const pollRegime = async () => {
      try {
        const res = await fetch('/api/v1/ml/regime/' + selectedSymbol);
        if (res.ok) {
          const data = await res.json();
          setRegime(data);
        }
      } catch {
        // Backend not ready yet — silent fail
      }
    };

    const pollStatus = async () => {
      try {
        const res = await fetch('/api/v1/ml/status');
        if (res.ok) {
          const data = await res.json();
          setModelStatus(data);
        }
      } catch {
        // Backend not ready yet
      }
    };

    pollRegime();
    pollStatus();
    const interval = setInterval(pollRegime, 5000);
    const statusInterval = setInterval(pollStatus, 30000);
    return () => {
      clearInterval(interval);
      clearInterval(statusInterval);
    };
  }, [selectedSymbol, setRegime, setModelStatus]);

  const currentRegime = regimes[selectedSymbol];

  return (
    <div className="flex flex-col h-full bg-[#0a0a0f] text-gray-200 font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${modelStatus.regime_model_loaded ? 'bg-green-500' : 'bg-gray-600'}`} />
          <span className="text-gray-400 font-semibold">REGIME CLASSIFIER</span>
        </div>
        <div className="flex items-center gap-3">
          {modelStatus.drift_detected && (
            <span className="text-yellow-500 animate-pulse">⚠ DRIFT</span>
          )}
          <span className="text-gray-500">
            CV: {modelStatus.cv_accuracy > 0 ? (modelStatus.cv_accuracy * 100).toFixed(1) + '%' : '—'}
          </span>
        </div>
      </div>

      {/* Asset selector */}
      <div className="flex flex-wrap gap-1 px-3 py-2 border-b border-gray-800/50">
        {ALL_SYMBOLS.map(sym => {
          const r = regimes[sym];
          const isSelected = sym === selectedSymbol;
          const color = r ? REGIME_COLORS[r.regime] : '#495057';
          return (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all ${
                isSelected
                  ? 'bg-gray-700 text-white ring-1 ring-gray-500'
                  : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700/50'
              }`}
              style={{ borderBottom: `2px solid ${color}` }}
            >
              {sym}
            </button>
          );
        })}
      </div>

      {/* Main regime display */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {currentRegime ? (
          <>
            {/* Current regime badge */}
            <div
              className="rounded-lg p-4 text-center"
              style={{ backgroundColor: REGIME_BG[currentRegime.regime] }}
            >
              <div
                className="text-3xl font-bold tracking-wider"
                style={{ color: REGIME_COLORS[currentRegime.regime] }}
              >
                {currentRegime.regime}
              </div>
              <div className="text-gray-400 mt-1">
                Confidence: {(currentRegime.confidence * 100).toFixed(1)}%
              </div>
              <div className="text-gray-500 text-[10px] mt-1">
                {new Date(currentRegime.timestamp).toLocaleTimeString()}
              </div>
            </div>

            {/* Probability bars */}
            <div className="space-y-2">
              <div className="text-gray-500 text-[10px] uppercase tracking-wider">Probability Distribution</div>
              {(Object.entries(currentRegime.probabilities) as [RegimeLabel, number][]).map(([label, prob]) => (
                <div key={label} className="flex items-center gap-2">
                  <span className="w-16 text-right text-gray-400">{label}</span>
                  <div className="flex-1 h-4 bg-gray-800 rounded overflow-hidden">
                    <div
                      className="h-full rounded transition-all duration-500"
                      style={{
                        width: `${prob * 100}%`,
                        backgroundColor: REGIME_COLORS[label],
                        opacity: 0.8,
                      }}
                    />
                  </div>
                  <span className="w-12 text-right text-gray-300">{(prob * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-32 text-gray-600">
            <div className="text-center">
              <div className="text-2xl mb-2">⏳</div>
              <div>Waiting for regime prediction...</div>
              <div className="text-gray-700 mt-1">ML backend loading</div>
            </div>
          </div>
        )}

        {/* Model status */}
        <div className="border-t border-gray-800 pt-3 space-y-1">
          <div className="text-gray-500 text-[10px] uppercase tracking-wider mb-2">Model Status</div>
          <StatusRow label="Regime Model" loaded={modelStatus.regime_model_loaded} />
          <StatusRow label="Entry Scorer" loaded={modelStatus.entry_model_loaded} />
          <StatusRow label="Optimizer" loaded={modelStatus.optimizer_ready} />
          <div className="flex justify-between text-gray-400 mt-2">
            <span>PSI Score</span>
            <span className={modelStatus.psi_score > 0.2 ? 'text-yellow-500' : 'text-green-500'}>
              {modelStatus.psi_score > 0 ? modelStatus.psi_score.toFixed(3) : '—'}
            </span>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>Last Training</span>
            <span>{modelStatus.last_training ? new Date(modelStatus.last_training).toLocaleDateString() : '—'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const StatusRow: React.FC<{ label: string; loaded: boolean }> = ({ label, loaded }) => (
  <div className="flex justify-between text-gray-400">
    <span>{label}</span>
    <span className={loaded ? 'text-green-500' : 'text-gray-600'}>
      {loaded ? '● LOADED' : '○ NOT READY'}
    </span>
  </div>
);

export default RegimePanel;
