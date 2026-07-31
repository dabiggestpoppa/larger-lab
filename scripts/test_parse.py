"""Debug JSON parsing issue."""
import json
import sys
sys.path.insert(0, '.')

from core.research.cognition.llm_reasoning import LLMReasoning

# Simulated LLM response (what we'd expect)
test_response = '''{
  "main_claims": [
    {
      "claim": "SkMTEB is the first comprehensive MTEB-style text embedding benchmark for Slovak.",
      "confidence": 0.95,
      "claim_type": "primary"
    },
    {
      "claim": "SkMTEB comprises 31 datasets across 7 task types.",
      "confidence": 0.9,
      "claim_type": "primary"
    }
  ],
  "mechanisms": [],
  "assumptions": [
    {
      "assumption": "Slovak language has sufficient data for benchmarking",
      "explicit": false,
      "confidence": 0.7
    }
  ],
  "equations": [],
  "limitations": [
    {
      "limitation": "limited to Slovak language",
      "severity": "medium",
      "is_stated": true
    }
  ],
  "novel_contribution": {
    "contribution": "First MTEB benchmark for Slovak",
    "novelty_score": 0.9,
    "prior_literature_gap": "No prior Slovak embedding benchmark"
  },
  "causal_relationships": [],
  "implicit_theory": "",
  "methodology": "MTEB benchmark with 31 datasets",
  "domain": "computer science",
  "confidence_score": 0.85
}'''

llm = LLMReasoning.__new__(LLMReasoning)
result = llm._parse_json(test_response)
print(f"Parsed: {json.dumps(result, indent=2)[:500]}")
print(f"Success: {bool(result)}")
