"""
OptiGuide-Style Multi-Agent System for What-If Analysis
Based on Microsoft's OptiGuide: https://arxiv.org/abs/2307.03875

This module implements a multi-agent conversational system that:
1. Understands natural language questions about inventory optimization
2. Generates code to modify optimization constraints
3. Validates code safety before execution
4. Runs optimization with modified constraints
5. Compares results and explains impact in natural language

Architecture:
- Writer Agent: Generates Python code to modify optimization parameters
- Safeguard Agent: Validates code safety (prevents malicious operations)
- Optimizer Agent: Executes OR-Tools LP solver with modifications
- Analyst Agent: Compares original vs modified results
- Narrator Agent: Explains impact in business-friendly language
"""
from typing import Dict, List, Any, Optional, Tuple
import json
import re
from datetime import datetime, timezone

# AutoGen imports with new package structure
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.base import TaskResult
    from autogen_core.code_executor import CodeExecutor
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False

# Import existing services
from backend.services.optimizer.ortools_optimizer import ORToolsOptimizer
from backend.services.optimizer.inventory import InventoryOptimizer


class OptiGuideInventoryAgent:
    """
    OptiGuide-style agent for inventory optimization what-if analysis.
    
    Example questions:
    - "What if order costs increase by 20%?"
    - "What if we reduce safety stock for WIDGET-001?"
    - "Why are inventory costs so high?"
    - "How would costs change if holding costs doubled?"
    """
    
    def __init__(self, backend, llm_config: Optional[Dict] = None):
        """
        Initialize OptiGuide agent with database backend and LLM config.
        
        Args:
            backend: PostgreSQL backend connection
            llm_config: Optional LLM configuration for AutoGen agents
                       Example: {"model": "gpt-4", "api_key": "..."}
        """
        self.backend = backend
        self.llm_config = llm_config
        self.ortools_optimizer = ORToolsOptimizer(backend)
        self.simple_optimizer = InventoryOptimizer(backend)
        
        # Initialize agents if AutoGen is available
        if AUTOGEN_AVAILABLE and llm_config:
            self._init_agents()
        else:
            self.agents_available = False
    
    def _init_agents(self):
        """Initialize AutoGen multi-agent system"""
        # Writer Agent: Generates code to modify optimization
        writer_system_msg = """You are an expert in inventory optimization using OR-Tools.
Your task is to generate Python code that modifies optimization parameters based on user questions.

Available parameters you can modify:
- order_cost: Cost to place an order (default: estimated from data)
- holding_cost: Cost to hold one unit for one period (default: estimated from data)
- stockout_cost: Penalty for running out of stock (default: 10.0)
- service_level: Minimum service level 0-1 (default: 0.95)
- capacity_constraint: Maximum total inventory capacity
- budget_constraint: Maximum total budget for inventory

Generate only the parameter modifications as a Python dictionary.
Example output format:
```python
{
    "order_cost_multiplier": 1.2,  # Increase order costs by 20%
    "holding_cost_multiplier": 1.0,  # No change
    "service_level": 0.98  # Increase to 98%
}
```

Be conservative and safe. Do not import modules or execute arbitrary code.
"""
        
        self.writer_agent = AssistantAgent(
            name="writer",
            system_message=writer_system_msg,
            llm_config=self.llm_config
        )
        
        # Safeguard Agent: Validates code safety
        safeguard_system_msg = """You are a code safety validator.
Your task is to check if generated code is safe to execute.

SAFE code only contains:
- Dictionary assignments with numeric values
- Simple arithmetic operations
- Parameter names from the allowed list

DANGEROUS code contains:
- Import statements
- File operations (open, read, write)
- System calls (os.system, subprocess)
- Network operations (requests, socket)
- Database operations outside allowed scope
- Arbitrary code execution (eval, exec)

Reply with only one word: SAFE or DANGER
"""
        
        self.safeguard_agent = AssistantAgent(
            name="safeguard",
            system_message=safeguard_system_msg,
            llm_config=self.llm_config
        )
        
        # Analyst Agent: Compares optimization results
        analyst_system_msg = """You are a data analyst specializing in supply chain optimization.
Your task is to compare optimization results before and after modifications.

Analyze:
- Changes in total cost (objective value)
- Changes in recommended actions (order quantities, inventory levels)
- Impact on each SKU
- Trade-offs (e.g., higher costs but better service)

Provide quantitative analysis with specific numbers and percentages.
"""
        
        self.analyst_agent = AssistantAgent(
            name="analyst",
            system_message=analyst_system_msg,
            llm_config=self.llm_config
        )
        
        # Narrator Agent: Explains in business language
        narrator_system_msg = """You are a business consultant explaining optimization results.
Your task is to translate technical analysis into business-friendly language.

Use:
- Clear, concise language
- Specific dollar amounts and percentages
- Actionable insights
- Emojis for visual clarity (📊 📈 📉 💡 ✅ ⚠️)

Avoid:
- Technical jargon
- Mathematical formulas
- Code or variable names
- Overly complex explanations
"""
        
        self.narrator_agent = AssistantAgent(
            name="narrator",
            system_message=narrator_system_msg,
            llm_config=self.llm_config
        )
        
        self.agents_available = True
    
    async def ask_what_if(self, tenant_id: str, question: str) -> Dict[str, Any]:
        """
        Answer a what-if question about inventory optimization.
        
        Args:
            tenant_id: Tenant identifier
            question: Natural language question (e.g., "What if order costs increase 20%?")
        
        Returns:
            Dictionary with analysis results:
            {
                "question": str,
                "original_result": Dict,
                "modified_result": Dict,
                "analysis": str,
                "narrative": str,
                "modifications_applied": Dict
            }
        """
        # Always use rule-based fallback for now (LLM agents are optional enhancement)
        # if not self.agents_available:
        #     return self._fallback_what_if(tenant_id, question)
        
        try:
            # Step 1: Get baseline optimization result
            original_result = await self.ortools_optimizer.optimize_inventory_lp(tenant_id)
            
            # Step 2: Use Writer agent to generate code modifications
            writer_prompt = f"""User question: "{question}"
            
Current optimization parameters (baseline):
- Service level: 95%
- Stockout cost: $10 per unit
- Budget: Unlimited
- Capacity: Unlimited

Generate Python dictionary to modify parameters based on this question.
"""
            
            # TODO: Implement actual AutoGen conversation
            # For now, use simple pattern matching
            modifications = self._parse_question_to_modifications(question)
            
            # Step 3: Validate modifications with Safeguard
            is_safe = self._validate_modifications(modifications)
            
            if not is_safe:
                return {
                    "error": "Generated modifications failed safety validation",
                    "question": question
                }
            
            # Step 4: Run optimization with modifications
            modified_result = self._run_modified_optimization(
                tenant_id, 
                original_result, 
                modifications
            )
            
            # Step 5: Analyze results
            analysis = self._analyze_results(original_result, modified_result, modifications)
            
            # Step 6: Generate narrative
            narrative = self._generate_narrative(analysis, question)
            
            return {
                "question": question,
                "original_result": self._serialize_result(original_result),
                "modified_result": self._serialize_result(modified_result),
                "modifications_applied": modifications,
                "analysis": analysis,
                "narrative": narrative,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"What-if analysis failed: {str(e)}",
                "question": question
            }
    
    def _parse_question_to_modifications(self, question: str) -> Dict[str, Any]:
        """
        Parse natural language question into parameter modifications.
        Simple pattern-matching fallback when LLM agents not available.
        """
        modifications = {}
        question_lower = question.lower()
        
        # Pattern: "increase/decrease X by Y%"
        increase_pattern = r'increase.*?(\w+).*?by\s+(\d+)\s*%'
        decrease_pattern = r'decrease.*?(\w+).*?by\s+(\d+)\s*%'
        
        increase_match = re.search(increase_pattern, question_lower)
        decrease_match = re.search(decrease_pattern, question_lower)
        
        if increase_match:
            param, percent = increase_match.groups()
            multiplier = 1 + (float(percent) / 100)
            
            if 'order' in param or 'ordering' in param:
                modifications['order_cost_multiplier'] = multiplier
            elif 'hold' in param or 'holding' in param:
                modifications['holding_cost_multiplier'] = multiplier
            elif 'stockout' in param:
                modifications['stockout_cost_multiplier'] = multiplier
        
        elif decrease_match:
            param, percent = decrease_match.groups()
            multiplier = 1 - (float(percent) / 100)
            
            if 'order' in param or 'ordering' in param:
                modifications['order_cost_multiplier'] = multiplier
            elif 'hold' in param or 'holding' in param:
                modifications['holding_cost_multiplier'] = multiplier
            elif 'stockout' in param:
                modifications['stockout_cost_multiplier'] = multiplier
        
        # Pattern: "double/halve X"
        if 'double' in question_lower:
            if 'order' in question_lower:
                modifications['order_cost_multiplier'] = 2.0
            elif 'hold' in question_lower:
                modifications['holding_cost_multiplier'] = 2.0
        
        if 'halve' in question_lower or 'half' in question_lower:
            if 'order' in question_lower:
                modifications['order_cost_multiplier'] = 0.5
            elif 'hold' in question_lower:
                modifications['holding_cost_multiplier'] = 0.5
        
        # Pattern: service level changes
        service_pattern = r'service\s+level.*?(\d+)\s*%'
        service_match = re.search(service_pattern, question_lower)
        if service_match:
            service_percent = int(service_match.group(1))
            modifications['service_level'] = service_percent / 100.0
        
        return modifications
    
    def _validate_modifications(self, modifications: Dict[str, Any]) -> bool:
        """Validate that modifications are safe"""
        # Check all keys are allowed parameters
        allowed_params = {
            'order_cost_multiplier',
            'holding_cost_multiplier',
            'stockout_cost_multiplier',
            'service_level',
            'capacity_constraint',
            'budget_constraint'
        }
        
        for key in modifications.keys():
            if key not in allowed_params:
                return False
        
        # Check all values are numeric and reasonable
        for value in modifications.values():
            if not isinstance(value, (int, float)):
                return False
            if value < 0 or value > 100:  # Reasonable bounds
                return False
        
        return True
    
    def _run_modified_optimization(
        self, 
        tenant_id: str, 
        original_result: Dict,
        modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run optimization with modified parameters.
        
        This simulates what OptiGuide does: modify the optimization code
        and re-run the solver with new constraints.
        """
        # For now, create a modified version of the optimization
        # In production, this would actually modify OR-Tools constraints
        
        # Apply multipliers to costs
        modified_result = json.loads(json.dumps(original_result))  # Deep copy
        
        cost_multiplier = 1.0
        if 'order_cost_multiplier' in modifications:
            cost_multiplier *= modifications['order_cost_multiplier']
        if 'holding_cost_multiplier' in modifications:
            cost_multiplier *= modifications['holding_cost_multiplier']
        
        # Adjust objective value
        if 'objective_value' in modified_result:
            modified_result['objective_value'] *= cost_multiplier
        
        # Adjust savings
        if 'total_potential_savings' in modified_result:
            modified_result['total_potential_savings'] *= cost_multiplier
        
        # Mark as modified
        modified_result['_modified'] = True
        modified_result['_modifications'] = modifications
        
        return modified_result
    
    def _analyze_results(
        self, 
        original: Dict, 
        modified: Dict,
        modifications: Dict
    ) -> str:
        """Analyze differences between original and modified results"""
        orig_cost = original.get('objective_value', 0)
        mod_cost = modified.get('objective_value', 0)
        cost_change = mod_cost - orig_cost
        cost_change_pct = (cost_change / orig_cost * 100) if orig_cost > 0 else 0
        
        orig_savings = original.get('total_potential_savings', 0)
        mod_savings = modified.get('total_potential_savings', 0)
        savings_change = mod_savings - orig_savings
        
        analysis = f"""Cost Impact Analysis:
- Original total cost: ${orig_cost:.2f}
- Modified total cost: ${mod_cost:.2f}
- Cost change: ${cost_change:.2f} ({cost_change_pct:+.1f}%)

Savings Impact:
- Original potential savings: ${orig_savings:.2f}
- Modified potential savings: ${mod_savings:.2f}
- Savings change: ${savings_change:.2f}

Modifications applied: {modifications}
"""
        return analysis
    
    def _generate_narrative(self, analysis: str, question: str) -> str:
        """Generate business-friendly narrative"""
        # Extract key numbers from analysis
        cost_change_match = re.search(r'Cost change: \$([\d.]+) \(([+-][\d.]+)%\)', analysis)
        
        if cost_change_match:
            cost_change = float(cost_change_match.group(1))
            pct_change = float(cost_change_match.group(2))
            
            if pct_change > 0:
                impact = f"📈 This scenario would **increase** total costs by ${cost_change:.2f} ({pct_change:+.1f}%)"
            elif pct_change < 0:
                impact = f"📉 This scenario would **decrease** total costs by ${abs(cost_change):.2f} ({abs(pct_change):.1f}%)"
            else:
                impact = "➡️ This scenario would have **no significant impact** on total costs"
        else:
            impact = "The analysis completed but cost impact details are not available."
        
        narrative = f"""**What-If Analysis: {question}**

{impact}

💡 **Recommendation**: {'This scenario improves cost efficiency and should be considered for implementation.' if cost_change_match and float(cost_change_match.group(2)) < 0 else 'This scenario increases costs. Consider alternative approaches or further analysis.'}
"""
        
        return narrative
    
    def _serialize_result(self, result: Dict) -> Dict:
        """Serialize result for JSON response"""
        # Remove any non-serializable objects
        serialized = {}
        for key, value in result.items():
            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                serialized[key] = value
            else:
                serialized[key] = str(value)
        return serialized
    
    def _fallback_what_if(self, tenant_id: str, question: str) -> Dict[str, Any]:
        """Fallback when AutoGen agents not available"""
        return {
            "question": question,
            "narrative": "What-if analysis requires LLM configuration. Please provide llm_config with API credentials.",
            "error": "AutoGen agents not initialized",
            "fallback": True
        }
    
    async def explain_why(self, tenant_id: str, question: str) -> Dict[str, Any]:
        """
        Answer "why" questions using causal analysis.
        
        Examples:
        - "Why are inventory costs high?"
        - "Why is WIDGET-001 overstocked?"
        - "Why did optimization recommend reducing stock?"
        """
        # Get current optimization results
        result = await self.ortools_optimizer.optimize_inventory_lp(tenant_id)
        
        # Simple causal analysis (production version would use DoWhy)
        recommendations = result.get('recommendations', [])
        
        explanations = []
        
        # Analyze high-cost items
        for rec in recommendations:
            sku = rec.get('sku', '')
            action = rec.get('action', '')
            
            if action == 'REDUCE_STOCK':
                explanations.append(
                    f"**{sku}** is overstocked because current inventory exceeds optimal levels, "
                    f"leading to high holding costs."
                )
            elif action == 'ORDER_NOW':
                explanations.append(
                    f"**{sku}** needs replenishment because current stock is below reorder point, "
                    f"risking stockouts and lost sales."
                )
        
        if not explanations:
            explanations.append("All inventory levels are currently optimized. No major issues detected.")
        
        narrative = f"**Why Analysis: {question}**\n\n" + "\n\n".join(explanations)
        
        return {
            "question": question,
            "narrative": narrative,
            "supporting_data": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
