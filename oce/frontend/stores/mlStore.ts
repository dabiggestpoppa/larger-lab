/**
 * ML Store — Zustand state for CEREBUS ML integration
 * 
 * Manages: regime predictions, confidence scores, entry quality,
 * optimized parameters, feature importance (SHAP), and model status.
 */
import { create } from 'zustand';

// ── Types ──────────────────────────────────────────────────

export type RegimeLabel = 'CONFIRMED' | 'CAUTION' | 'FAILED' | 'NO-GO';

export interface RegimePrediction {
  symbol: string;
  regime: RegimeLabel;
  confidence: number;        // 0-1
  probabilities: {
    CONFIRMED: number;
    CAUTION: number;
    FAILED: number;
    'NO-GO': number;
  };
  timestamp: string;
}

export interface EntryQuality {
  symbol: string;
  score: number;             // 0-1 continuous
  action: 'ENTER_FULL' | 'HALF_SIZE' | 'SKIP';
  features: {
    pullback_pct: number;
    occ_body_ratio: number;
    time_since_impulse: number;
    volume_spike: number;
    regime_confidence: number;
    distance_to_dz: number;
  };
  timestamp: string;
}

export interface OptimizedParams {
  symbol: string;
  regime: RegimeLabel;
  au_multiplier: number;
  buffer: number;
  dz_width: number;
  trigger_multiplier: number;
  sharpe: number;
  win_rate: number;
  max_dd: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;        // SHAP mean_abs value
  rank: number;
}

export interface ModelStatus {
  regime_model_loaded: boolean;
  entry_model_loaded: boolean;
  optimizer_ready: boolean;
  last_training: string;
  data_hash: string;
  cv_accuracy: number;
  heldout_accuracy: number;
  psi_score: number;         // Population Stability Index
  drift_detected: boolean;
}

export interface MlState {
  // Per-symbol state
  regimes: Record<string, RegimePrediction>;
  entryQuality: Record<string, EntryQuality>;
  optimizedParams: Record<string, OptimizedParams[]>;
  featureImportance: Record<string, FeatureImportance[]>;
  
  // Global model status
  modelStatus: ModelStatus;
  
  // Selected symbol for detail view
  selectedSymbol: string;
  
  // Actions
  setRegime: (prediction: RegimePrediction) => void;
  setEntryQuality: (quality: EntryQuality) => void;
  setOptimizedParams: (symbol: string, params: OptimizedParams[]) => void;
  setFeatureImportance: (symbol: string, features: FeatureImportance[]) => void;
  setModelStatus: (status: Partial<ModelStatus>) => void;
  setSelectedSymbol: (symbol: string) => void;
  
  // Computed
  getRegimeForSymbol: (symbol: string) => RegimePrediction | null;
  getEntryQualityForSymbol: (symbol: string) => EntryQuality | null;
  getParamsForSymbolRegime: (symbol: string, regime: RegimeLabel) => OptimizedParams | null;
}

// ── Store ──────────────────────────────────────────────────

export const useMlStore = create<MlState>((set, get) => ({
  regimes: {},
  entryQuality: {},
  optimizedParams: {},
  featureImportance: {},
  
  modelStatus: {
    regime_model_loaded: false,
    entry_model_loaded: false,
    optimizer_ready: false,
    last_training: '',
    data_hash: '',
    cv_accuracy: 0,
    heldout_accuracy: 0,
    psi_score: 0,
    drift_detected: false,
  },
  
  selectedSymbol: 'EURUSD',
  
  // Actions
  setRegime: (prediction) => set((state) => ({
    regimes: { ...state.regimes, [prediction.symbol]: prediction },
  })),
  
  setEntryQuality: (quality) => set((state) => ({
    entryQuality: { ...state.entryQuality, [quality.symbol]: quality },
  })),
  
  setOptimizedParams: (symbol, params) => set((state) => ({
    optimizedParams: { ...state.optimizedParams, [symbol]: params },
  })),
  
  setFeatureImportance: (symbol, features) => set((state) => ({
    featureImportance: { ...state.featureImportance, [symbol]: features },
  })),
  
  setModelStatus: (status) => set((state) => ({
    modelStatus: { ...state.modelStatus, ...status },
  })),
  
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
  
  // Computed
  getRegimeForSymbol: (symbol) => get().regimes[symbol] || null,
  getEntryQualityForSymbol: (symbol) => get().entryQuality[symbol] || null,
  getParamsForSymbolRegime: (symbol, regime) => {
    const params = get().optimizedParams[symbol];
    if (!params) return null;
    return params.find(p => p.regime === regime) || null;
  },
}));
