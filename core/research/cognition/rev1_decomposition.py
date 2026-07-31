"""
REV-1: Structural Decomposition Hardening Engine
Part 1: Claim Isolation + Assumption Extraction
"""

from __future__ import annotations
import re
import uuid
from typing import Any, Dict, List, Optional

# ─── REV-1.1 Claim Isolation Engine ───

CLAIM_PATTERNS = [
    r"(?:we (?:show|demonstrate|prove|establish|find|observe|report|confirm))\s+(?:that\s+)?(.{20,300})",
    r"(?:results? (?:show|indicate|suggest|demonstrate|reveal|confirm))\s+(?:that\s+)?(.{20,300})",
    r"(?:this (?:study|paper|work|research))\s+(?:shows|demonstrates|proves|establishes|confirms)\s+(?:that\s+)?(.{20,300})",
    r"(?:our (?:findings?|results?|analysis|data))\s+(?:show|indicate|suggest|demonstrate|reveal)\s+(?:that\s+)?(.{20,300})",
    r"(?:we (?:argue|propose|hypothesize|conclude|assert))\s+(?:that\s+)?(.{20,300})",
    r"(?:this (?:suggests|implies|indicates|means|reveals))\s+(?:that\s+)?(.{20,300})",
]

CLAIM_TYPE_PATTERNS = {
    "causal": [r"causes?", r"leads? to", r"results? in", r"produces?", r"drives?", r"induces?", r"triggers?"],
    "correlational": [r"correlates?", r"associated with", r"linked to", r"related to"],
    "comparative": [r"higher than", r"lower than", r"greater than", r"less than", r"compared to"],
    "definitional": [r"is defined as", r"refers to", r"means?", r"constitutes?"],
    "methodological": [r"we use", r"we employ", r"we apply", r"we measure", r"we estimate"],
    "normative": [r"should", r"must", r"ought to", r"needs? to", r"requires?"],
}


def extract_claims(text: str, paper_id: str = "") -> List[Dict[str, Any]]:
    """REV-1.1: Extract every assertion independently. No narrative merging."""
    claims = []
    seen = set()
    for pattern in CLAIM_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            claim_text = match.group(1).strip()
            claim_text = re.sub(r'\s+', ' ', claim_text).rstrip('.')
            normalized = claim_text.lower().strip()[:80]
            if normalized in seen or len(claim_text) < 15:
                continue
            seen.add(normalized)
            claim_type = "primary"
            for ctype, patterns in CLAIM_TYPE_PATTERNS.items():
                if any(re.search(p, claim_text, re.IGNORECASE) for p in patterns):
                    claim_type = ctype
                    break
            confidence = 0.5
            if re.search(r"\d+\.?\d*\s*%", claim_text): confidence += 0.15
            if re.search(r"p\s*[<>=]\s*0?\.\d+", claim_text, re.IGNORECASE): confidence += 0.2
            claims.append({
                "claim_id": f"claim_{paper_id}_{len(claims):03d}",
                "claim": claim_text[:300], "claim_type": claim_type,
                "confidence": min(confidence, 1.0), "source_paper": paper_id,
            })
    return claims[:15]


# ─── REV-1.2 + REV-1.3 Assumption Extraction ───

EXPLICIT_ASSUMPTION_PATTERNS = [
    r"(?:we assume|assuming|assumption|it is assumed|presupposes?)\s+(?:that\s+)?(.{10,200})",
    r"(?:this (?:requires|depends on|presupposes?|rests? on))\s+(.{10,200})",
    r"(?:under the assumption|given that|provided that|conditional on)\s+(.{10,200})",
    r"(?:if we assume|let us assume|suppose that)\s+(.{10,200})",
    r"(?:the model assumes|the framework assumes|the theory assumes)\s+(.{10,200})",
]

IMPLICIT_TRIGGERS = {
    "causal": ([r"causes?", r"leads? to", r"results? in", r"produces?", r"drives?"], "relationship is causal not correlational"),
    "generalization": ([r"all ", r"every ", r"always ", r"universally", r"in general"], "finding applies universally across contexts"),
    "stability": ([r"stable", r"constant", r"unchanging", r"persistent", r"robust"], "relationship is stable over time"),
    "rationality": ([r"rational", r"optimal", r"efficient", r"maximiz", r"utility"], "agents behave rationally with perfect information"),
    "equilibrium": ([r"equilibrium", r"balanced", r"steady state", r"converges?"], "system tends toward equilibrium"),
    "linearity": ([r"linear", r"proportional", r"direct relationship"], "relationships are linear and additive"),
    "measurement": ([r"we measure", r"we proxy", r"we use .* as a measure"], "chosen metrics accurately capture the underlying construct"),
}


def extract_explicit_assumptions(text: str, paper_id: str = "") -> List[Dict[str, Any]]:
    """REV-1.2: Extract assumptions stated directly by authors."""
    assumptions, seen = [], set()
    for pattern in EXPLICIT_ASSUMPTION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            t = re.sub(r'\s+', ' ', match.group(1).strip()).rstrip('.')
            n = t.lower().strip()[:60]
            if n not in seen and len(t) >= 10:
                seen.add(n)
                assumptions.append({"assumption_id": f"assump_{paper_id}_{len(assumptions):03d}", "assumption": t[:200], "explicit": True, "confidence": 0.8, "source_paper": paper_id})
    return assumptions[:10]


def infer_implicit_assumptions(text: str, claims: List[Dict], paper_id: str = "") -> List[Dict[str, Any]]:
    """REV-1.3: Infer unstated assumptions from claims and language."""
    assumptions, seen = [], set()
    for claim in claims:
        ct = claim.get("claim", "")
        for atype, (patterns, implicit) in IMPLICIT_TRIGGERS.items():
            if any(re.search(p, ct, re.IGNORECASE) for p in patterns):
                n = implicit.lower()[:60]
                if n not in seen:
                    seen.add(n)
                    assumptions.append({"assumption_id": f"iassump_{paper_id}_{len(assumptions):03d}", "assumption": implicit, "explicit": False, "confidence": 0.5, "inferred_from_claim": claim.get("claim_id", ""), "assumption_type": atype, "source_paper": paper_id})
    method_patterns = [
        (r"we use (?:a |the )?(?:regression|OLS|linear model)", "linearity and additivity of effects"),
        (r"we use (?:a |the )?(?:survey|questionnaire)", "self-reported data is reliable and valid"),
        (r"sample (?:of|size)", "sample is representative of the population"),
        (r"we control for", "controlled variables capture all relevant confounders"),
        (r"we limit(?:ed)? to", "findings generalize beyond the studied population"),
    ]
    for pattern, implicit in method_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            n = implicit.lower()[:60]
            if n not in seen:
                seen.add(n)
                assumptions.append({"assumption_id": f"iassump_{paper_id}_{len(assumptions):03d}", "assumption": implicit, "explicit": False, "confidence": 0.6, "assumption_type": "methodological", "source_paper": paper_id})
    return assumptions[:12]
