/**
 * ShapPanel — SHAP Feature Importance Visualization
 * 
 * Horizontal bar chart showing feature importance from SHAP analysis.
 * Used for model audit trail and interpretability.
 */
import React, { useEffect, useState } from 'react';
import { useMlStore } from '../../stores/mlStore';

const MAX_BAR_WIDTH = 180;

export const ShapPanel: React.FC = () => {
  const { featureImportance, selectedSymbol, setFeatureImportance } = useMlStore();
  const [loading, setLoading] = useState(false);

  const features = featureImportance[selectedSymbol] || [];

  useEffect(() => {
    const fetchShap = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/v1/ml/features/${selectedSymbol}`);
        if (res.ok) {
          const data = await res.json();
          setFeatureImportance(selectedSymbol, data);
        }
      } catch {
        // Backend not ready
      }
      setLoading(false);
    };

    fetchShap();
    const interval = setInterval(fetchShap, 60000);
    return () => clearInterval(interval);
  }, [selectedSymbol, setFeatureImportance]);

  const maxImportance = features.length > 0
    ? Math.max(...features.map(f => f.importance))
    : 1;

  return (
    <div className="flex flex-col h-full bg-[#0a0a0f] text-gray-200 font-mono text-xs">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <span className="text-gray-400 font-semibold">SHAP FEATURES</span>
        <span className="text-gray-500">{selectedSymbol}</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {loading && features.length === 0 ? (
          <div className="text-gray-600 text-center py-8">Loading SHAP values...</div>
        ) : features.length > 0 ? (
          features.map((feat, i) => {
            const barWidth = maxImportance > 0
              ? (feat.importance / maxImportance) * MAX_BAR_WIDTH
              : 0;
            const colors = ['#74c0fc', '#a9e34b', '#ffd43b', '#ff6b6b', '#da77f2', '#ffa8a8', '#63e6be', '#748ffc'];
            const color = colors[i % colors.length];

            return (
              <div key={feat.feature} className="flex items-center gap-2 py-1">
                <span className="w-6 text-right text-gray-500 text-[10px]">{feat.rank}</span>
                <span className="w-32 text-right text-gray-400 truncate text-[10px]">{feat.feature}</span>
                <div className="flex-1 h-3 bg-gray-800 rounded overflow-hidden">
                  <div
                    className="h-full rounded transition-all duration-500"
                    style={{ width: `${barWidth}px`, backgroundColor: color, opacity: 0.8 }}
                  />
                </div>
                <span className="w-14 text-right text-gray-300 text-[10px]">
                  {feat.importance > 0 ? feat.importance.toFixed(4) : '—'}
                </span>
              </div>
            );
          })
        ) : (
          <div className="text-gray-600 text-center py-8">
            <div className="text-2xl mb-2">📊</div>
            <div>No SHAP data yet</div>
            <div className="text-gray-700 mt-1">Train model to generate</div>
          </div>
        )}
      </div>

      <div className="px-4 py-2 border-t border-gray-800 text-gray-600 text-[10px]">
        SHAP = SHapley Additive exPlanations | Model interpretability audit trail
      </div>
    </div>
  );
};

export default ShapPanel;
