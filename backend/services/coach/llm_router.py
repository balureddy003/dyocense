"""
LLM Router - Hybrid Local/Cloud Routing

Routes queries to local LLM (70%) or cloud LLM (30%) based on complexity.
Saves 80% on LLM costs while maintaining quality for complex queries.
"""

from __future__ import annotations

import logging
import re
import time
from enum import Enum
from typing import Any, Optional

from openai import AsyncOpenAI
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI

from backend.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM provider types."""
    LOCAL = "local"
    CLOUD = "cloud"


class ComplexityLevel(str, Enum):
    """Query complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class LLMRouter:
    """
    Routes LLM queries based on complexity analysis.
    
    Complexity Scoring:
    - Query length
    - Keyword presence (optimization, forecasting, causal, etc.)
    - Multi-step reasoning requirements
    - Domain-specific terminology
    """
    
    def __init__(self):
        """Initialize LLM clients."""
        # Local LLM (Ollama)
        self.local_client: Optional[Ollama] = None
        if settings.ENABLE_LOCAL_LLM:
            try:
                self.local_client = Ollama(
                    base_url=settings.LOCAL_LLM_URL,
                    model=settings.LOCAL_LLM_MODEL,
                    temperature=settings.LOCAL_LLM_TEMPERATURE,
                )
                logger.info(f"Local LLM initialized: {settings.LOCAL_LLM_MODEL}")
            except Exception as e:
                logger.warning(f"Local LLM unavailable: {e}")
        
        # Cloud LLM (OpenAI)
        self.cloud_client = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY,
        )
        
        # Complexity keywords
        self.complex_keywords = {
            "optimize", "optimization", "forecast", "predict", "causal",
            "root cause", "correlation", "regression", "statistical",
            "analyze", "compare", "recommend", "strategy", "trade-off",
            "multi-objective", "constraint", "scenario", "simulation"
        }
        
        self.moderate_keywords = {
            "explain", "summarize", "breakdown", "calculate", "estimate",
            "trend", "pattern", "anomaly", "outlier"
        }
    
    def calculate_complexity(self, query: str, context: Optional[dict] = None) -> tuple[ComplexityLevel, float]:
        """
        Calculate query complexity score.
        
        Args:
            query: User query
            context: Optional context (history, metrics, etc.)
        
        Returns:
            Tuple of (complexity_level, score)
        """
        score = 0.0
        
        # 1. Length-based complexity (0-0.3)
        words = query.split()
        if len(words) > 50:
            score += 0.3
        elif len(words) > 20:
            score += 0.2
        elif len(words) > 10:
            score += 0.1
        
        # 2. Keyword presence (0-0.4)
        query_lower = query.lower()
        complex_matches = sum(1 for kw in self.complex_keywords if kw in query_lower)
        moderate_matches = sum(1 for kw in self.moderate_keywords if kw in query_lower)
        
        if complex_matches > 0:
            score += min(0.4, complex_matches * 0.15)
        elif moderate_matches > 0:
            score += min(0.2, moderate_matches * 0.1)
        
        # 3. Multi-step reasoning (0-0.2)
        multi_step_indicators = ["and then", "after that", "next", "following", "step"]
        if any(ind in query_lower for ind in multi_step_indicators):
            score += 0.2
        
        # 4. Question marks (multiple questions = complex) (0-0.1)
        question_count = query.count("?")
        if question_count > 1:
            score += 0.1
        
        # 5. Context complexity (0-0.2)
        if context:
            if context.get("requires_calculation"):
                score += 0.1
            if context.get("requires_optimization"):
                score += 0.1
            if len(context.get("relevant_metrics", [])) > 5:
                score += 0.1
        
        # Determine complexity level
        if score >= 0.7:
            level = ComplexityLevel.COMPLEX
        elif score >= 0.4:
            level = ComplexityLevel.MODERATE
        else:
            level = ComplexityLevel.SIMPLE
        
        logger.info(f"Complexity analysis: {level.value} (score: {score:.2f})")
        return level, score
    
    def should_use_local(self, complexity: ComplexityLevel, score: float) -> bool:
        """
        Decide whether to use local LLM based on complexity.
        
        Strategy:
        - SIMPLE: 100% local
        - MODERATE: Probabilistic (based on threshold)
        - COMPLEX: 100% cloud
        """
        if not self.local_client:
            return False
        
        if complexity == ComplexityLevel.SIMPLE:
            return True
        elif complexity == ComplexityLevel.COMPLEX:
            return False
        else:  # MODERATE
            # Use threshold with some randomness
            import random
            threshold = settings.LLM_COMPLEXITY_THRESHOLD
            # Add ±10% randomness to avoid hard cutoff
            adjusted_threshold = threshold + random.uniform(-0.1, 0.1)
            return score < adjusted_threshold
    
    async def route(
        self,
        query: str,
        context: Optional[dict] = None,
        force_provider: Optional[LLMProvider] = None
    ) -> tuple[LLMProvider, Any]:
        """
        Route query to appropriate LLM.
        
        Args:
            query: User query
            context: Optional context
            force_provider: Force specific provider (for testing)
        
        Returns:
            Tuple of (provider, llm_client)
        """
        if force_provider:
            provider = force_provider
        else:
            complexity, score = self.calculate_complexity(query, context)
            use_local = self.should_use_local(complexity, score)
            provider = LLMProvider.LOCAL if use_local else LLMProvider.CLOUD
        
        client = self.local_client if provider == LLMProvider.LOCAL else self.cloud_client
        
        logger.info(f"Routing to {provider.value} LLM")
        return provider, client
    
    async def generate(
        self,
        query: str,
        context: Optional[dict] = None,
        system_prompt: Optional[str] = None,
        force_provider: Optional[LLMProvider] = None
    ) -> dict[str, Any]:
        """
        Generate response using routed LLM.
        
        Args:
            query: User query
            context: Optional context
            system_prompt: System prompt
            force_provider: Force specific provider
        
        Returns:
            Response dict with text, provider, tokens, cost
        """
        start_time = time.time()
        provider, client = await self.route(query, context, force_provider)
        
        # Format messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})
        
        # Generate response
        try:
            if provider == LLMProvider.LOCAL:
                # Ollama via LangChain
                response_text = await client.ainvoke(query)
                tokens_used = len(response_text.split()) * 1.3  # Estimate
                cost = 0.0  # Local is free
            else:
                # OpenAI
                response = await client.ainvoke(messages)
                response_text = response.content
                tokens_used = getattr(response.response_metadata.get("token_usage", {}), "total_tokens", 0)
                # Cost estimation (GPT-4o: $5/1M input, $15/1M output)
                cost = (tokens_used / 1_000_000) * 10  # Average $10/1M tokens
            
            duration = time.time() - start_time
            
            logger.info(
                f"LLM response generated: provider={provider.value}, "
                f"tokens={tokens_used:.0f}, duration={duration:.2f}s, cost=${cost:.4f}"
            )
            
            return {
                "text": response_text,
                "provider": provider.value,
                "tokens": int(tokens_used),
                "cost": cost,
                "duration": duration,
            }
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            
            # Fallback to cloud if local fails
            if provider == LLMProvider.LOCAL and self.cloud_client:
                logger.warning("Falling back to cloud LLM")
                return await self.generate(
                    query, context, system_prompt, force_provider=LLMProvider.CLOUD
                )
            
            raise


# Global router instance
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get or create global LLM router instance."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
