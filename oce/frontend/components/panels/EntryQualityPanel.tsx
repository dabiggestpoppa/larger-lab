/**
 * EntryQualityPanel — ML Entry Quality Indicator
 * 
 * Shows real-time entry quality score with feature breakdown,
 * action recommendation, and quality gauge.
 */
import React, { useEffect } from 'react';
import { useMlStore } from '../../stores/mlStore';

const ACTION_COLORS = {
  ENTER_FULL: '#51cf66',
  HALF_SIZE: '#ffd43b',
  SKIP: '#ff6b6b',
};

const ACTION_LABELS = {
  ENTER_FULL: 'ENTER FULL',
  HALF_SIZE: 'HALF SIZE',
  SKIP: 'SKIP',
};

export const EntryQualityPanel: React.FC = () => {
  const {
    entryQuality,
    selectedSymbol,
    setEntryQuality,
  } = useMlStore();

  const quality = entryQuality[selectedSymbol];

  // Poll entry quality from ML backend
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch('/api/v1/ml/entry-quality/' + selectedSymbol);
        if (res.ok) {
          const data = await res.json();
          setEntryQuality(data);
        }
      } catch {
        // Backend not ready
      }
    };

    poll();
    const interval = setInterval(poll, 3000);
    return () => clearInterval(interval);
  }, [selectedSymbol, setEntryQuality]);

  return (
    <div className="flex flex-col h-full bg-[#0a0a0f] text-gray-200 font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <span className="text-gray-400 font-semibold">ENTRY QUALITY</span>
        <span className="text-gray-500">{selectedSymbol}</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {quality ? (
          <>
            {/* Quality gauge */}
            <div className="text-center">
              <div className="relative w-32 h-32 mx-auto">
                {/* Background circle */}
                <svg className="w-full h-full" viewBox="0 0 100 100">
                  <circle
                    cx="50" cy="50" r="42"
                    fill="none"
                    stroke="#1a1a2e"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50" cy="50" r="42"
                    fill="none"
                    stroke={quality.score >= 0.7 ? '#51cf66' : quality.score >= 0.5 ? '#ffd43b' : '#ff6b6b'}
                    strokeWidth="8"
                    strokeDasharray={`${quality.score * 264} 264`}
                    strokeLinecap="round"
                    transform="rotate(-90 50 50)"
                    className="transition-all duration-700"
                  />
                  <text
                    x="50" y="50"
                    textAnchor="middle"
                    dominantBaseline="central"
                    className="fill-gray-200 text-lg font-bold"
                    fontSize="18"
                  >
                    {(quality.score * 100).toFixed(0)}
                  </text>
                  <text
                    x="50" y="65"
                    textAnchor="middle"
                    className="fill-gray-500"
                    fontSize="8"
                  >
                    QUALITY
                  </text>
                </svg>
              </div>

              {/* Action badge */}
              <div
                className="mt-3 inline-block px-4 py-1.5 rounded-full text-sm font-bold tracking-wider"
                style={{
                  backgroundColor: ACTION_COLORS[quality.action] + '20',
                  color: ACTION_COLORS[quality.action],
                  border: `1px solid ${ACTION_COLORS[quality.action]}40`,
                }}
              >
                {ACTION_LABELS[quality.action]}
              </div>
            </div>

            {/* Feature breakdown */}
            <div className="space-y-2">
              <div className="text-gray-500 text-[10px] uppercase tracking-wider">Feature Breakdown</div>
              <FeatureBar label="Pullback %" value={quality.features.pullback_pct} max={1} />
              <FeatureBar label="OCC Body Ratio" value={quality.features.occ_body_ratio} max={2} />
              <FeatureBar label="Time Since Impulse" value={quality.features.time_since_impulse} max={60} />
              <FeatureBar label="Volume Spike" value={quality.features.volume_spike} max={3} />
              <FeatureBar label="Regime Conf." value={quality.features.regime_confidence} max={1} />
              <FeatureBar label="DZ Distance" value={quality.features.distance_to_dz} max={1} />
            </div>

            {/* Timestamp */}
            <div className="text-gray-600 text-[10px] text-center">
              Updated: {new Date(quality.timestamp).toLocaleTimeString()}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-48 text-gray-600">
            <div className="text-center">
              <div className="text-2xl mb-2">📊</div>
              <div>Waiting for entry quality...</div>
              <div className="text-gray-700 mt-1">Scoring entries in real-time</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const FeatureBar: React.FC<{ label: string; value: number; max: number }> = ({ label, value, max }) => {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex items-center gap-2">
      <span className="w-28 text-right text-gray-400 truncate">{label}</span>
      <div className="flex-1 h-2 bg-gray-800 rounded overflow-hidden">
        <div
          className="h-full bg-blue-500/70 rounded transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-12 text-right text-gray-300">{value.toFixed(2)}</span>
    </div>
  );
};

export default EntryQualityPanel;
