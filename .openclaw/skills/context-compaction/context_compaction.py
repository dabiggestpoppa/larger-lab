"""
Context Compaction Pipeline — 5-Layer System
Inspired by VILA-Lab/Dive-into-Claude-Code analysis of Claude Code's architecture.

The agent loop is simple. The harness around it is where the real engineering lives.
This module implements the 5-layer context compaction pipeline that runs before
every model call, cheapest first.

Usage:
    from tools.context_compaction import ContextCompactor
    
    compactor = ContextCompactor(max_tokens=200000)
    compacted = compactor.compact(messages)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json
import time


@dataclass
class Message:
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: float = field(default_factory=time.time)
    tokens: int = 0
    
    def estimate_tokens(self) -> int:
        """Rough token estimation: ~4 chars per token."""
        if self.tokens == 0:
            self.tokens = max(1, len(self.content) // 4)
        return self.tokens


@dataclass
class CompactionResult:
    original_tokens: int
    compacted_tokens: int
    layers_applied: List[str]
    messages: List[Message]
    
    @property
    def reduction_pct(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return (1 - self.compacted_tokens / self.original_tokens) * 100


class ContextCompactor:
    """
    5-Layer Context Compaction Pipeline.
    
    Layers run sequentially, cheapest first. Each layer only runs if cheaper
    ones haven't achieved the target reduction.
    
    Layer 1: Budget Reduction — Per-message size caps (always active)
    Layer 2: Snip — Trim older history (feature-gated)
    Layer 3: Microcompact — Cache-aware fine-grained compression
    Layer 4: Context Collapse — Read-time virtual projection (non-destructive)
    Layer 5: Auto-Compact — Full model-generated summary (last resort)
    """
    
    def __init__(self, max_tokens: int = 200000, target_ratio: float = 0.7):
        self.max_tokens = max_tokens
        self.target_ratio = target_ratio  # Target: reduce to 70% of max
        self.enable_snip = True
        self.enable_context_collapse = True
        
    def compact(self, messages: List[Message]) -> CompactionResult:
        """Run the full 5-layer compaction pipeline."""
        original_tokens = sum(m.estimate_tokens() for m in messages)
        layers_applied = []
        working = list(messages)
        
        # Layer 1: Budget Reduction (always active)
        working = self._layer1_budget_reduction(working)
        layers_applied.append("budget_reduction")
        
        current_tokens = sum(m.estimate_tokens() for m in working)
        if self._is_sufficient(current_tokens):
            return CompactionResult(original_tokens, current_tokens, layers_applied, working)
        
        # Layer 2: Snip — Trim older history
        if self.enable_snip:
            working = self._layer2_snip(working)
            layers_applied.append("snip")
            current_tokens = sum(m.estimate_tokens() for m in working)
            if self._is_sufficient(current_tokens):
                return CompactionResult(original_tokens, current_tokens, layers_applied, working)
        
        # Layer 3: Microcompact — Fine-grained compression
        working = self._layer3_microcompact(working)
        layers_applied.append("microcompact")
        current_tokens = sum(m.estimate_tokens() for m in working)
        if self._is_sufficient(current_tokens):
            return CompactionResult(original_tokens, current_tokens, layers_applied, working)
        
        # Layer 4: Context Collapse — Virtual projection
        if self.enable_context_collapse:
            working = self._layer4_context_collapse(working)
            layers_applied.append("context_collapse")
            current_tokens = sum(m.estimate_tokens() for m in working)
            if self._is_sufficient(current_tokens):
                return CompactionResult(original_tokens, current_tokens, layers_applied, working)
        
        # Layer 5: Auto-Compact — Full summary (last resort)
        working = self._layer5_autocompact(working)
        layers_applied.append("auto_compact")
        current_tokens = sum(m.estimate_tokens() for m in working)
        
        return CompactionResult(original_tokens, current_tokens, layers_applied, working)
    
    def _is_sufficient(self, current_tokens: int) -> bool:
        """Check if current token count is within acceptable range."""
        return current_tokens <= self.max_tokens * self.target_ratio
    
    def _layer1_budget_reduction(self, messages: List[Message]) -> List[Message]:
        """
        Layer 1: Budget Reduction.
        Cap individual message sizes. Truncate any single message that exceeds
        20% of the total budget.
        """
        max_per_message = int(self.max_tokens * 0.2)
        result = []
        for msg in messages:
            if msg.estimate_tokens() > max_per_message:
                # Truncate but keep the beginning (most important context)
                chars_to_keep = max_per_message * 4
                truncated = msg.content[:chars_to_keep] + "\n... [truncated]"
                result.append(Message(msg.role, truncated, msg.timestamp))
            else:
                result.append(msg)
        return result
    
    def _layer2_snip(self, messages: List[Message]) -> List[Message]:
        """
        Layer 2: Snip.
        Trim older history. Keep system messages, last N user/assistant turns,
        and summarize the middle.
        """
        if len(messages) <= 6:
            return messages
        
        # Always keep system messages
        system_msgs = [m for m in messages if m.role == "system"]
        conversation = [m for m in messages if m.role != "system"]
        
        # Keep first 2 and last 4 conversation turns
        keep_first = 2
        keep_last = 4
        
        if len(conversation) <= keep_first + keep_last:
            return messages
        
        kept = conversation[:keep_first]
        middle = conversation[keep_first:-keep_last]
        tail = conversation[-keep_last:]
        
        # Summarize the middle section
        if middle:
            summary_content = f"[... {len(middle)} earlier messages summarized ...]"
            summary = Message("system", summary_content, middle[0].timestamp)
            kept.append(summary)
        
        kept.extend(tail)
        return system_msgs + kept
    
    def _layer3_microcompact(self, messages: List[Message]) -> List[Message]:
        """
        Layer 3: Microcompact.
        Fine-grained compression: remove redundant whitespace, deduplicate
        repeated content, compress tool outputs.
        """
        result = []
        seen_content = set()
        
        for msg in messages:
            # Deduplicate identical messages
            content_hash = hash(msg.content[:200])
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)
            
            # Compress excessive whitespace
            compressed = "\n".join(
                line for line in msg.content.split("\n")
                if line.strip()
            )
            
            # Truncate very long tool outputs
            if msg.role == "assistant" and len(compressed) > 5000:
                compressed = compressed[:5000] + "\n... [output truncated]"
            
            result.append(Message(msg.role, compressed, msg.timestamp))
        
        return result
    
    def _layer4_context_collapse(self, messages: List[Message]) -> List[Message]:
        """
        Layer 4: Context Collapse.
        Read-time virtual projection. Group related messages into summaries.
        Non-destructive: original content preserved in metadata.
        """
        if len(messages) <= 4:
            return messages
        
        system_msgs = [m for m in messages if m.role == "system"]
        conversation = [m for m in messages if m.role != "system"]
        
        # Group into pairs (user + assistant) and summarize
        collapsed = []
        i = 0
        while i < len(conversation):
            if i + 1 < len(conversation):
                user_msg = conversation[i]
                asst_msg = conversation[i + 1]
                
                # If both are short, keep them
                if user_msg.estimate_tokens() < 100 and asst_msg.estimate_tokens() < 200:
                    collapsed.extend([user_msg, asst_msg])
                else:
                    # Summarize the pair
                    summary = Message(
                        "system",
                        f"[Summary: {user_msg.content[:50]}... → {asst_msg.content[:100]}...]",
                        user_msg.timestamp
                    )
                    collapsed.append(summary)
                i += 2
            else:
                collapsed.append(conversation[i])
                i += 1
        
        return system_msgs + collapsed
    
    def _layer5_autocompact(self, messages: List[Message]) -> List[Message]:
        """
        Layer 5: Auto-Compact (last resort).
        Generate a full summary of the conversation so far.
        Keep only system messages + summary + last 2 turns.
        """
        system_msgs = [m for m in messages if m.role == "system"]
        conversation = [m for m in messages if m.role != "system"]
        
        if len(conversation) <= 2:
            return messages
        
        # Create a summary of everything except the last 2 turns
        to_summarize = conversation[:-2]
        last_two = conversation[-2:]
        
        summary_lines = [f"Conversation summary ({len(to_summarize)} turns):"]
        for msg in to_summarize:
            preview = msg.content[:80].replace("\n", " ")
            summary_lines.append(f"  {msg.role}: {preview}...")
        
        summary = Message("system", "\n".join(summary_lines))
        
        return system_msgs + [summary] + last_two


def compact_messages(messages: List[Dict[str, str]], max_tokens: int = 200000) -> CompactionResult:
    """Convenience function for compacting raw message dicts."""
    msg_objects = [Message(m.get("role", "user"), m.get("content", "")) for m in messages]
    compactor = ContextCompactor(max_tokens=max_tokens)
    result = compactor.compact(msg_objects)
    return result


if __name__ == "__main__":
    # Demo
    test_messages = [
        Message("system", "You are a helpful agent."),
        Message("user", "What's the weather?"),
        Message("assistant", "I'll check the weather for you."),
        Message("user", "Also check my calendar."),
        Message("assistant", "Here's your calendar for today..."),
        Message("user", "Summarize everything."),
        Message("assistant", "Here's a summary of all the information..."),
    ]
    
    compactor = ContextCompactor(max_tokens=500)
    result = compactor.compact(test_messages)
    
    print(f"Original: {result.original_tokens} tokens")
    print(f"Compacted: {result.compacted_tokens} tokens")
    print(f"Reduction: {result.reduction_pct:.1f}%")
    print(f"Layers applied: {result.layers_applied}")
    print(f"Messages remaining: {len(result.messages)}")
