"""
Parallel Thought Synthesis System using OpenRouter
A system that queries multiple AI models in parallel and synthesizes their responses.
"""

import asyncio
import hashlib
import logging
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelResponse:
    """Container for model responses."""
    model: str
    content: str
    tokens: int
    latency: float
    error: Optional[str] = None
    score: float = 0.0
    
    def __str__(self) -> str:
        return f"{self.model}: {len(self.content) if self.content else 0} chars, {self.tokens} tokens"

class SynthesisStrategy(Enum):
    """Different strategies for combining model responses."""
    WEIGHTED_CONSENSUS = "weighted_consensus"
    CONTRARIAN_SCA = "contrarian_scoring"
    BEST_SCORE = "best_score"
    VOTE = "vote"
    CONTRAST = "contrast"

class ParallelThoughtSynthesizer:
    """
    A system that queries multiple AI models in parallel and synthesizes their responses.
    Uses OpenRouter as the unified API interface.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_weights: Optional[Dict[str, float]] = None,
                 default_models: List[str] = None):
        """
        Initialize the synthesizer.
        
        Args:
            api_key: OpenRouter API key (uses env var if not provided)
            model_weights: Custom weights for models (higher = more influence)
            default_models: List of model IDs to query
        """
        self.api_key = api_key or self._get_api_key()
        self.model_weights = model_weights or self._get_default_weights()
        self.models = default_models or self._get_default_models()
        self.response_cache = {}
        
        # Import OpenRouter client
        try:
            from openrouter import OpenRouter
            self.client = OpenRouter(api_key=self.api_key)
        except ImportError:
            logger.error("OpenRouter client not installed. Install with: pip install openrouter")
            raise
    
    def _get_api_key(self) -> str:
        """Get API key from environment or file."""
        import os
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            # Try to read from common locations
            try_paths = [
                "c:\\Users\\wifik\\Downloads\\open_router_key.txt",
                "/secrets/openrouter_api_key.txt"
            ]
            for path in try_paths:
                try:
                    with open(path, 'r') as f:
                        key = f.read().strip()
                        if key:
                            return key
                except:
                    continue
        if not key:
            raise ValueError("No OpenRouter API key found. Set OPENROUTER_API_KEY environment variable or create a key file.")
        return key
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Get default model weights based on model capabilities.
        
        Free model configuration for Hermes:
        - poolside/laguna-m.1:free - Main agent (primary)
        - nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free - Orchestrator
        - inclusionai/ring-2.6-1t:free - Large code tasks (fallback to poolside if rate limited)
        """
        return {
            "poolside/laguna-m.1:free": 1.0,  # Main agent - primary
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": 0.9,  # Orchestrator
            "inclusionai/ring-2.6-1t:free": 0.8,  # Large code tasks
        }
    
    def _get_default_models(self) -> List[str]:
        """Get default models (mix of free/paid)."""
        return list(self._get_default_weights().keys())
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        if not text:
            return 0
        return len(text.split()) // 4
    
    async def dispatch_thoughts(self, 
                               prompt: str, 
                               max_tokens: int = 512,
                               temperature: float = 0.7,
                               top_p: float = 0.9) -> List[ModelResponse]:
        """
        Dispatch the same prompt to all configured models in parallel.
        
        Args:
            prompt: The prompt to send to all models
            max_tokens: Maximum tokens for each response
            temperature: Temperature for sampling
            top_p: Top_p for sampling
            
        Returns:
            List of ModelResponse objects
        """
        logger.info(f"Dispatching to {len(self.models)} models. Prompt length: {len(prompt.split())} words")
        
        # Create tasks for all models
        tasks = []
        for model in self.models:
            task = self._query_model(model, prompt, max_tokens, temperature, top_p)
            tasks.append(task)
        
        # Run all queries concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        responses = []
        for model, result in zip(self.models, results):
            if isinstance(result, Exception):
                responses.append(ModelResponse(
                    model=model,
                    content="",
                    tokens=0,
                    latency=0,
                    error=str(result)
                ))
            else:
                responses.append(result)
        
        return responses
    
    async def _query_model(self, model: str, prompt: str, max_tokens: int, temperature: float, top_p: float):
        """Query a single model via OpenRouter."""
        import time
        
        start = time.time()
        try:
            result = self.client.chat.send(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            
            # Extract content from response
            content = ""
            if hasattr(result, 'choices') and result.choices:
                content = result.choices[0].message.content if hasattr(result.choices[0], 'message') else ""
            elif hasattr(result, 'data') and result.data:
                content = result.data.get('content', '')
            
            # Extract token usage - handle ChatUsage object
            tokens = 0
            if hasattr(result, 'usage') and result.usage:
                usage = result.usage
                if hasattr(usage, 'total_tokens'):
                    tokens = usage.total_tokens
                elif isinstance(usage, dict):
                    tokens = usage.get('total_tokens', 0)
            
            return ModelResponse(
                model=model,
                content=content.strip() if content else "",
                tokens=tokens,
                latency=time.time() - start
            )
        except Exception as e:
            logger.error(f"Error querying {model}: {e}")
            return ModelResponse(
                model=model,
                content="",
                tokens=0,
                latency=time.time() - start,
                error=str(e)
            )
    
    async def dispatch_with_cache(self, prompt: str, **kwargs) -> List[ModelResponse]:
        """
        Dispatch thoughts with caching to avoid re-querying same prompt.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments for dispatch_thoughts
            
        Returns:
            List of ModelResponse objects
        """
        # Create a hash of the prompt for caching
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        
        if prompt_hash in self.response_cache:
            logger.info(f"Using cached responses for prompt (hash: {prompt_hash[:8]})")
            return self.response_cache[prompt_hash]
        
        responses = await self.dispatch_thoughts(prompt, **kwargs)
        self.response_cache[prompt_hash] = responses
        
        # Limit cache size
        if len(self.response_cache) > 100:
            # Remove oldest items
            oldest = sorted(self.response_cache.items(), key=lambda x: x[0])[:20]
            for key, _ in oldest:
                del self.response_cache[key]
        
        return responses
    
    def score_responses(self, responses: List[ModelResponse]) -> List[ModelResponse]:
        """
        Score responses based on multiple criteria.
        
        Args:
            responses: List of ModelResponse objects
            
        Returns:
            Sorted list of responses by score
        """
        for resp in responses:
            if resp.error:
                resp.score = -1.0
                continue
                
            # Factor 1: Response quality signals
            token_efficiency = 1.0 / (resp.tokens + 1)  # Lower tokens often better
            speed_bonus = max(0, 10 - resp.latency) / 10  # Faster is better
            
            # Factor 2: Content analysis (simple heuristics)
            uniqueness = len(set(resp.content.split())) / max(len(resp.content.split()), 1)
            length = min(len(resp.content) / 1000, 1.0)  # Longer is better up to 1000 chars
            
            # Combined score (tweak weights as needed)
            resp.score = (
                token_efficiency * 0.3 + 
                speed_bonus * 0.2 + 
                uniqueness * 0.3 + 
                length * 0.2
            )
            
        return sorted(responses, key=lambda x: x.score if x.score is not None else -1.0, reverse=True)
    
    def synthesize(self, 
                   responses: List[ModelResponse], 
                   agent_own_idea: str = "",
                   strategy: SynthesisStrategy = SynthesisStrategy.WEIGHTED_CONSENSUS,
                   top_k: int = 3) -> Dict[str, Any]:
        """
        Synthesize multiple responses into a single output.
        
        Args:
            responses: List of ModelResponse objects
            agent_own_idea: The agent's own idea/plan
            strategy: Synthesis strategy to use
            top_k: Number of top responses to consider
            
        Returns:
            Dictionary with synthesized result and metadata
        """
        if not responses:
            return {"synthesized": "No valid responses from models", "confidence": 0}
        
        # Score and filter responses
        scored_responses = self.score_responses(responses)
        valid_responses = [r for r in scored_responses if r.score > 0]
        
        if not valid_responses:
            return {"synthesized": "No valid responses from models", "confidence": 0}
        
        # Include agent's own idea if provided
        if agent_own_idea and strategy != SynthesisStrategy.CONTRAST:
            agent_resp = ModelResponse(
                model="AgentCore",
                content=agent_own_idea,
                tokens=self._estimate_tokens(agent_own_idea),
                latency=0,
                score=1.0  # Agent's own idea gets highest base score
            )
            valid_responses.insert(0, agent_resp)
        
        # Apply synthesis strategy
        try:
            if strategy == SynthesisStrategy.WEIGHTED_CONSENSUS:
                result = self._weighted_consensus(valid_responses[:top_k])
            elif strategy == SynthesisStrategy.CONTRARIAN_SCA:
                result = self._contrarian_scoring(valid_responses[:top_k])
            elif strategy == SynthesisStrategy.BEST_SCORE:
                result = self._best_score(valid_responses[0])
            elif strategy == SynthesisStrategy.VOTE:
                result = self._vote_merge(valid_responses[:top_k])
            elif strategy == SynthesisStrategy.CONTRAST:
                result = self._contrast_synthesis(valid_responses[:top_k])
            else:
                result = self._simple_merge(valid_responses)
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            result = self._simple_merge(valid_responses)
        
        # Calculate confidence
        confidence = self._calculate_confidence(valid_responses[:top_k])
        
        return {
            "synthesized": result,
            "confidence": confidence,
            "model_breakdown": self._get_model_breakdown(valid_responses[:top_k]),
            "strategy": strategy.value
        }
    
    def _weighted_consensus(self, responses: List[ModelResponse]) -> str:
        """Create a weighted consensus from multiple responses."""
        if len(responses) == 1:
            return responses[0].content
        
        # Extract key points from each response
        all_points = []
        for resp in responses:
            weight = self.model_weights.get(resp.model, 0.5)
            sentences = self._extract_key_sentences(resp.content)
            for sentence in sentences[:3]:  # Take top 3 sentences per model
                all_points.append((sentence, weight))
        
        # Weighted selection (simplified - you could use more sophisticated ranking)
        if not all_points:
            return "No mergeable content."
        
        # Simple approach: concatenate weighted contributions
        result_parts = []
        for sentence, weight in all_points:
            if random.random() < weight / 2:  # Adjust probability
                result_parts.append(f"[{(weight*100):.0f}%]: {sentence}")
        
        return "\n\n".join(result_parts) if result_parts else "No mergeable content."
    
    def _contrarian_scoring(self, responses: List[ModelResponse]) -> str:
        """Score against consensus to find unique insights."""
        if len(responses) < 2:
            return responses[0].content if responses else ""
        
        # Find common elements
        all_sentences = []
        for resp in responses:
            all_sentences.extend(self._extract_key_sentences(resp.content))
        
        # Count sentence occurrences
        from collections import Counter
        sentence_counts = Counter(all_sentences)
        
        # Find unique or low-frequency insights
        unique_insights = []
        for resp in responses:
            for sentence in self._extract_key_sentences(resp.content):
                if sentence_counts[sentence] <= 1:  # Only show unique insights
                    weight = self.model_weights.get(resp.model, 0.5)
                    unique_insights.append((sentence, weight))
        
        if unique_insights:
            # Sort by weight and pick top
            unique_insights.sort(key=lambda x: x[1], reverse=True)
            return "Unique Insights:\n\n" + "\n\n".join(
                f"{insight} ({weight:.0f}%)" for insight, weight in unique_insights[:3]
            )
        
        # Fallback to consensus if no unique insights
        return self._weighted_consensus(responses)
    
    def _best_score(self, response: ModelResponse) -> str:
        """Select the best scoring response."""
        return f"Selected Response ({response.model}):\n{response.content}"
    
    def _vote_merge(self, responses: List[ModelResponse]) -> str:
        """Merge based on voting for common actions/steps."""
        from collections import Counter
        
        all_actions = []
        for resp in responses:
            actions = self._extract_actions(resp.content)
            all_actions.extend(actions)
        
        if not all_actions:
            return self._simple_merge(responses)
        
        # Vote on most common actions
        counter = Counter(all_actions)
        top_actions = counter.most_common(5)
        
        return "Consensus Plan:\n" + "\n".join(
            f"{i+1}. {action}" for action, _ in top_actions
        )
    
    def _contrast_synthesis(self, responses: List[ModelResponse]) -> str:
        """Show contrasts between different models' outputs."""
        result = "Expert Panel Discussion:\n\n"
        for resp in responses:
            weight = self.model_weights.get(resp.model, 0.5)
            sentences = self._extract_key_sentences(resp.content)[:2]
            result += f"{resp.model} ({weight:.0f}% weight):\n"
            result += "\n".join(f"• {s}" for s in sentences) + "\n\n"
        
        result += "\nAgent Analysis: Compare the approaches above and choose the best."
        return result
    
    def _simple_merge(self, responses: List[ModelResponse]) -> str:
        """Simple concatenation of responses."""
        return "\n\n=== MERGED RESPONSE ===\n\n" + "\n\n---\n\n".join(
            f"{resp.model}:\n{resp.content}" for resp in responses if resp.content
        )
    
    def _calculate_confidence(self, responses: List[ModelResponse]) -> float:
        """Calculate confidence score based on response quality."""
        if not responses:
            return 0.0
        
        # Average of top scores
        valid_scores = [r.score for r in responses if r.score is not None and r.score > 0]
        if not valid_scores:
            return 0.0
        
        avg_score = sum(valid_scores) / len(valid_scores)
        
        # Boost confidence if multiple models agree
        similarities = self._calculate_similarities(responses)
        agreement = sum(similarities) / len(similarities) if similarities else 0.0
        
        confidence = avg_score * 0.7 + agreement * 0.3
        return min(confidence, 1.0)
    
    def _calculate_similarities(self, responses: List[ModelResponse]) -> List[float]:
        """Calculate pairwise similarities between responses."""
        similarities = []
        for i in range(len(responses)):
            for j in range(i+1, len(responses)):
                sim = self._sentence_similarity(responses[i].content, responses[j].content)
                similarities.append(sim)
        return similarities
    
    def _sentence_similarity(self, text1: str, text2: str) -> float:
        """Simple sentence similarity (Jaccard index on sentences)."""
        if not text1 or not text2:
            return 0.0
        
        sentences1 = set(s.strip().lower() for s in self._split_into_sentences(text1))
        sentences2 = set(s.strip().lower() for s in self._split_into_sentences(text2))
        
        if not sentences1 and not sentences2:
            return 0.0
        
        intersection = sentences1.intersection(sentences2)
        union = sentences1.union(sentences2)
        
        return len(intersection) / len(union)
    
    def _get_model_breakdown(self, responses: List[ModelResponse]) -> List[Dict[str, Any]]:
        """Get breakdown of contributions by model."""
        breakdown = []
        for resp in responses:
            if resp.score is not None:
                breakdown.append({
                    "model": resp.model,
                    "score": round(resp.score, 2),
                    "tokens": resp.tokens,
                    "latency": round(resp.latency, 2),
                    "contribution": int(self.model_weights.get(resp.model, 0.5) * 100)
                })
        return breakdown
    
    def _extract_key_sentences(self, text: str, max_sentences: int = 3) -> List[str]:
        """Extract key sentences from text."""
        if not text:
            return []
        
        sentences = self._split_into_sentences(text)
        # Simple heuristic: take first few sentences
        return [s.strip() for s in sentences[:max_sentences] if s.strip()]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_actions(self, text: str) -> List[str]:
        """Extract action items from text."""
        if not text:
            return []
        
        sentences = self._split_into_sentences(text)
        actions = []
        action_keywords = ['plan', 'step', 'action', 'research', 'write', 'create', 'analyze', 'design', 'build', 'test', 'implement']
        
        for s in sentences[:5]:  # Only first 5 sentences
            s_lower = s.lower()
            if any(kw in s_lower for kw in action_keywords) or s_lower.startswith(('step', 'action')):
                actions.append(s)
        
        return actions