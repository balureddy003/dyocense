"""
GPT-4 Integration for Coach Recommendations

Uses GPT-4 to generate natural, contextual recommendations with:
- Business-specific insights
- Personalized tone
- Data-driven reasoning
- Actionable recommendations
"""
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime


# Default system prompt for coach recommendations
COACH_SYSTEM_PROMPT = """You are an expert business advisor for small and medium businesses. 
You help business owners make better decisions by analyzing their data and providing 
actionable recommendations.

Your recommendations should be:
- Data-driven and specific
- Actionable with clear next steps
- Empathetic to the business owner's challenges
- Realistic and achievable
- Prioritized by impact and urgency

Use a supportive, encouraging tone. Focus on opportunities, not just problems.
When presenting numbers, use clear formatting (e.g., $1,234 not 1234).
Keep recommendations concise but comprehensive."""


class GPT4RecommendationGenerator:
    """Generate recommendations using GPT-4"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize GPT-4 generator
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (gpt-4, gpt-4-turbo, etc.)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("Warning: openai package not installed. Install with: pip install openai")
    
    def generate_recommendation(
        self,
        template_data: Dict[str, Any],
        business_context: Dict[str, Any],
        use_gpt4: bool = True,
    ) -> Dict[str, str]:
        """
        Generate a recommendation using GPT-4 or template fallback
        
        Args:
            template_data: Template with placeholders and structure
            business_context: Business-specific data for contextualization
            use_gpt4: If True and client available, use GPT-4; else use templates
        
        Returns:
            Dict with title, description, reasoning keys
        """
        if use_gpt4 and self.client:
            return self._generate_with_gpt4(template_data, business_context)
        else:
            return self._generate_from_template(template_data)
    
    def _generate_with_gpt4(
        self,
        template_data: Dict[str, Any],
        business_context: Dict[str, Any],
    ) -> Dict[str, str]:
        """Generate recommendation using GPT-4"""
        prompt = self._build_prompt(template_data, business_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": COACH_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            
            result = response.choices[0].message.content
            return self._parse_gpt4_response(result)
            
        except Exception as e:
            print(f"GPT-4 generation failed: {e}. Falling back to template.")
            return self._generate_from_template(template_data)
    
    def _build_prompt(
        self,
        template_data: Dict[str, Any],
        business_context: Dict[str, Any],
    ) -> str:
        """Build prompt for GPT-4"""
        category = template_data.get("category", "general")
        trigger = template_data.get("trigger", "unknown")
        data = template_data.get("data", {})
        
        # Build context string
        context_str = "\n".join([
            f"- {k}: {v}" for k, v in business_context.items()
        ])
        
        # Build data string
        data_str = "\n".join([
            f"- {k}: {v}" for k, v in data.items()
        ])
        
        prompt = f"""Generate a business recommendation for this scenario:

SITUATION:
Category: {category}
Trigger: {trigger}

BUSINESS CONTEXT:
{context_str}

DATA POINTS:
{data_str}

Generate a recommendation with:
1. Title (concise, 8-12 words)
2. Description (what's happening, 1-2 sentences)
3. Reasoning (why this matters, 1-2 sentences)

Format your response as JSON:
{{
  "title": "...",
  "description": "...",
  "reasoning": "..."
}}"""
        
        return prompt
    
    def _parse_gpt4_response(self, response: str) -> Dict[str, str]:
        """Parse GPT-4 JSON response"""
        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except Exception:
            pass
        
        # Fallback: return raw response
        return {
            "title": "Recommendation",
            "description": response[:200],
            "reasoning": "Generated by AI analysis",
        }
    
    def _generate_from_template(self, template_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate recommendation from template (fallback)"""
        template = template_data.get("template")
        data = template_data.get("data", {})
        
        if not template:
            return {
                "title": "Business Recommendation",
                "description": "Review your business metrics",
                "reasoning": "Based on current data analysis",
            }
        
        return {
            "title": template.format_template(template.title_template, data),
            "description": template.format_template(template.description_template, data),
            "reasoning": template.format_template(template.reasoning_template, data),
        }
    
    def generate_action_labels(
        self,
        actions: List[Dict[str, Any]],
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Format action labels with data
        
        Args:
            actions: List of action templates
            data: Data for formatting
        
        Returns:
            List of formatted actions
        """
        formatted_actions = []
        
        for action in actions:
            try:
                formatted = {
                    "label": action["label"].format(**data),
                    "description": action.get("description", "").format(**data),
                    "buttonText": action.get("buttonText", "Take Action").format(**data),
                    "variant": action.get("variant", "primary"),
                }
                formatted_actions.append(formatted)
            except KeyError:
                # If data is missing, use template as-is
                formatted_actions.append(action)
        
        return formatted_actions


class RecommendationEnricher:
    """Enrich recommendations with GPT-4 insights"""
    
    def __init__(self, gpt4_generator: Optional[GPT4RecommendationGenerator] = None):
        self.generator = gpt4_generator or GPT4RecommendationGenerator()
    
    def enrich_recommendation(
        self,
        recommendation: Dict[str, Any],
        business_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enrich recommendation with GPT-4 insights
        
        Args:
            recommendation: Base recommendation from template
            business_context: Business-specific context
        
        Returns:
            Enriched recommendation
        """
        # If GPT-4 is available, enhance the reasoning
        if self.generator.client:
            enhanced = self.generator.generate_recommendation(
                template_data={
                    "category": recommendation.get("category"),
                    "trigger": recommendation.get("trigger"),
                    "data": recommendation.get("metadata", {}),
                    "template": None,  # Force GPT-4 generation
                },
                business_context=business_context,
                use_gpt4=True,
            )
            
            # Merge GPT-4 enhancements
            recommendation["title"] = enhanced.get("title", recommendation["title"])
            recommendation["description"] = enhanced.get("description", recommendation["description"])
            recommendation["reasoning"] = enhanced.get("reasoning", recommendation["reasoning"])
        
        return recommendation
    
    def generate_follow_up_insights(
        self,
        recommendation: Dict[str, Any],
        user_question: str,
    ) -> str:
        """
        Generate follow-up insights for "Tell Me More" conversations
        
        Args:
            recommendation: The recommendation being discussed
            user_question: User's question
        
        Returns:
            AI-generated response
        """
        if not self.generator.client:
            return "I'd be happy to provide more details, but GPT-4 is not configured."
        
        prompt = f"""The business owner has a question about this recommendation:

RECOMMENDATION:
Title: {recommendation.get('title')}
Description: {recommendation.get('description')}

USER QUESTION:
{user_question}

Provide a helpful, specific answer that:
- Addresses their question directly
- Provides actionable guidance
- Uses a supportive tone
- Is concise (2-3 sentences)"""
        
        try:
            response = self.generator.client.chat.completions.create(
                model=self.generator.model,
                messages=[
                    {"role": "system", "content": COACH_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=200,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Failed to generate follow-up: {e}")
            return "I can help with that. Could you provide more specific details about what you'd like to know?"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_recommendation_generator(
    api_key: Optional[str] = None,
    model: str = "gpt-4",
) -> GPT4RecommendationGenerator:
    """
    Factory function for creating recommendation generator
    
    Args:
        api_key: OpenAI API key (defaults to env var)
        model: GPT-4 model to use
    
    Returns:
        GPT4RecommendationGenerator instance
    """
    return GPT4RecommendationGenerator(api_key=api_key, model=model)


def create_recommendation_enricher(
    api_key: Optional[str] = None,
    model: str = "gpt-4",
) -> RecommendationEnricher:
    """
    Factory function for creating recommendation enricher
    
    Args:
        api_key: OpenAI API key (defaults to env var)
        model: GPT-4 model to use
    
    Returns:
        RecommendationEnricher instance
    """
    generator = create_recommendation_generator(api_key=api_key, model=model)
    return RecommendationEnricher(gpt4_generator=generator)
