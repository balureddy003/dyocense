"""
Coach Orchestrator - Dynamic Multi-Agent Task Planning

This module analyzes user intent and available data to dynamically determine:
1. What analysis is needed
2. Which tools/agents should be invoked
3. What order to execute tasks
4. How to synthesize results into a coherent response
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Types of analysis tasks"""
    INVENTORY_ANALYSIS = "inventory_analysis"
    REVENUE_ANALYSIS = "revenue_analysis"
    CUSTOMER_ANALYSIS = "customer_analysis"
    FORECAST = "forecast"
    OPTIMIZATION = "optimization"
    HEALTH_DIAGNOSIS = "health_diagnosis"
    GOAL_PLANNING = "goal_planning"
    GENERAL_ADVICE = "general_advice"


class ToolRequirement(BaseModel):
    """Specification for a tool/agent to invoke"""
    tool_name: str
    tool_type: str  # "mcp_tool", "internal_function", "external_agent"
    parameters: Dict[str, Any] = {}
    required: bool = True
    fallback: Optional[str] = None


class TaskPlan(BaseModel):
    """Plan for executing a user request"""
    task_type: TaskType
    description: str
    required_tools: List[ToolRequirement]
    data_requirements: List[str]  # e.g., ["orders", "inventory", "customers"]
    can_execute: bool
    missing_data: List[str] = []
    execution_order: List[str] = []  # Tool names in order
    report_structure: Dict[str, Any] = {}


class CoachOrchestrator:
    """
    Orchestrates multi-agent analysis based on:
    1. User intent (what they're asking for)
    2. Available data (what we have)
    3. Available tools (what we can do)
    """
    
    def __init__(self):
        self.tool_registry = self._build_tool_registry()
        self.intent_patterns = self._build_intent_patterns()
    
    def _build_tool_registry(self) -> Dict[str, Dict[str, Any]]:
        """Registry of available tools and their capabilities"""
        return {
            # MCP Tools (CSV Data Access)
            "list_csv_files": {
                "type": "mcp_tool",
                "capability": "list_available_datasets",
                "required_data": [],
                "output": "List of CSV files with metadata"
            },
            "read_csv_file": {
                "type": "mcp_tool",
                "capability": "load_raw_data",
                "required_data": ["csv_file_name"],
                "output": "CSV data as JSON/records"
            },
            "query_csv_data": {
                "type": "mcp_tool",
                "capability": "filter_aggregate_data",
                "required_data": ["csv_file_name"],
                "output": "Filtered/aggregated results"
            },
            
            # Internal Analysis Functions
            "analyze_inventory": {
                "type": "internal_function",
                "capability": "inventory_health_analysis",
                "required_data": ["inventory"],
                "output": "Stock levels, valuations, ABC analysis"
            },
            "analyze_revenue": {
                "type": "internal_function",
                "capability": "revenue_trend_analysis",
                "required_data": ["orders"],
                "output": "Revenue metrics, trends, growth rates"
            },
            "analyze_customers": {
                "type": "internal_function",
                "capability": "customer_segmentation",
                "required_data": ["customers", "orders"],
                "output": "Customer segments, LTV, churn risk"
            },
            "forecast_demand": {
                "type": "internal_function",
                "capability": "time_series_forecasting",
                "required_data": ["orders"],
                "output": "Future demand predictions with confidence intervals"
            },
            "optimize_inventory": {
                "type": "internal_function",
                "capability": "inventory_optimization",
                "required_data": ["inventory", "orders"],
                "output": "Reorder recommendations, safety stock levels"
            },
            
            # External Agents (if available)
            "diagnostician_agent": {
                "type": "external_agent",
                "capability": "health_score_diagnosis",
                "required_data": ["health_score"],
                "output": "Root cause analysis and recommendations"
            },
        }
    
    def _build_intent_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Map keywords to task types and tool requirements"""
        return {
            "inventory_analysis": {
                "keywords": ["inventory", "stock", "sku", "product", "catalog", "warehouse"],
                "task_type": TaskType.INVENTORY_ANALYSIS,
                "primary_tools": ["analyze_inventory", "read_csv_file"],
                "optional_tools": ["optimize_inventory"],
                "report_sections": ["executive_summary", "stock_health", "valuations", "recommendations"]
            },
            "revenue_analysis": {
                "keywords": ["revenue", "sales", "order", "income", "earnings"],
                "task_type": TaskType.REVENUE_ANALYSIS,
                "primary_tools": ["analyze_revenue", "read_csv_file"],
                "optional_tools": ["forecast_demand"],
                "report_sections": ["executive_summary", "revenue_metrics", "trends", "forecast"]
            },
            "customer_analysis": {
                "keywords": ["customer", "client", "buyer", "segment", "churn", "retention"],
                "task_type": TaskType.CUSTOMER_ANALYSIS,
                "primary_tools": ["analyze_customers", "read_csv_file"],
                "optional_tools": [],
                "report_sections": ["executive_summary", "segments", "ltv_analysis", "recommendations"]
            },
            "forecast": {
                "keywords": ["forecast", "predict", "future", "next month", "trend", "projection", "demand"],
                "task_type": TaskType.FORECAST,
                "primary_tools": ["forecast_demand", "read_csv_file"],
                "optional_tools": [],
                "report_sections": ["executive_summary", "historical_trends", "predictions", "confidence"]
            },
            "optimization": {
                "keywords": ["optimize", "optimiz", "improve", "efficiency", "reduce cost", "maximize"],
                "task_type": TaskType.OPTIMIZATION,
                "primary_tools": ["optimize_inventory", "read_csv_file"],
                "optional_tools": ["analyze_inventory", "forecast_demand"],
                "report_sections": ["executive_summary", "current_state", "optimization_strategy", "expected_outcomes"]
            },
            "health_diagnosis": {
                "keywords": ["health", "diagnose", "problem", "issue", "what's wrong"],
                "task_type": TaskType.HEALTH_DIAGNOSIS,
                "primary_tools": ["diagnostician_agent"],
                "optional_tools": ["analyze_inventory", "analyze_revenue"],
                "report_sections": ["executive_summary", "root_causes", "impact_analysis", "action_plan"]
            },
        }
    
    def analyze_intent(self, user_message: str, available_data: Dict[str, int]) -> TaskPlan:
        """
        Analyze user intent and create execution plan
        
        Args:
            user_message: What the user is asking for
            available_data: Dict of data_type -> record_count (e.g., {"orders": 150, "inventory": 541909})
        
        Returns:
            TaskPlan with tools to invoke and execution order
        """
        message_lower = user_message.lower()
        
        logger.info(f"[Orchestrator] Analyzing message: '{user_message}'")
        logger.info(f"[Orchestrator] Message (lowercase): '{message_lower}'")
        logger.info(f"[Orchestrator] Available data: {available_data}")
        
        # Detect ALL matching intents (user might ask for multiple things)
        matched_intents = []
        
        for intent_name, config in self.intent_patterns.items():
            keywords_found = [kw for kw in config["keywords"] if kw in message_lower]
            if keywords_found:
                logger.info(f"[Orchestrator] Intent '{intent_name}' matched keywords: {keywords_found}")
                matched_intents.append((intent_name, config, len(keywords_found)))
            else:
                logger.debug(f"[Orchestrator] Intent '{intent_name}' - no match")
        
        # Fallback to general advice if no specific intent detected
        if not matched_intents:
            logger.warning(f"[Orchestrator] No specific intent detected - falling back to GENERAL_ADVICE")
            return self._create_general_advice_plan(user_message)
        
        # Sort by number of keywords matched (most relevant first)
        matched_intents.sort(key=lambda x: x[2], reverse=True)
        
        # If multiple intents detected, merge them into a compound task
        if len(matched_intents) > 1:
            logger.info(f"[Orchestrator] Multiple intents detected: {[name for name, _, _ in matched_intents]}")
            return self._create_compound_task_plan(matched_intents, available_data, user_message)
        
        # Single intent - use standard plan
        intent_name, intent_config, _ = matched_intents[0]
        logger.info(f"[Orchestrator] Selected intent: {intent_name}")
        
        # Build task plan based on detected intent and available data
        task_plan = self._create_task_plan(
            intent_config,
            available_data,
            user_message
        )
        
        logger.info(f"[Orchestrator] Task plan created: {task_plan.task_type.value}")
        return task_plan
    
    def _create_compound_task_plan(
        self,
        matched_intents: List[tuple],
        available_data: Dict[str, int],
        user_message: str
    ) -> TaskPlan:
        """
        Create a compound task plan when multiple intents are detected
        
        Example: "inventory optimization report with demand forecast"
        → Combines inventory_analysis + optimization + forecast
        """
        intent_names = [name for name, _, _ in matched_intents]
        logger.info(f"[Orchestrator] Creating compound plan for: {intent_names}")
        
        # Merge all tools from matched intents
        all_tools = set()
        all_optional_tools = set()
        primary_task_type = matched_intents[0][1]["task_type"]  # Use first as primary
        
        for intent_name, config, _ in matched_intents:
            all_tools.update(config["primary_tools"])
            all_optional_tools.update(config.get("optional_tools", []))
        
        # Determine execution order based on dependencies
        # Analysis → Forecast → Optimization
        ordered_tools = []
        tool_order_priority = {
            "analyze_inventory": 1,
            "analyze_revenue": 1,
            "analyze_customers": 1,
            "forecast_demand": 2,
            "forecast_revenue": 2,
            "optimize_inventory": 3,
            "optimize_pricing": 3,
        }
        
        for tool in sorted(all_tools, key=lambda t: tool_order_priority.get(t, 99)):
            ordered_tools.append(tool)
        
        # Add optional tools if data available
        for tool in all_optional_tools:
            if tool not in ordered_tools:
                ordered_tools.append(tool)
        
        logger.info(f"[Orchestrator] Compound plan tools: {ordered_tools}")
        
        # Build tool requirements
        required_tools = []
        execution_order = []
        
        for tool_name in ordered_tools:
            tool_info = self.tool_registry.get(tool_name, {})
            if not tool_info:
                logger.warning(f"[Orchestrator] Tool '{tool_name}' not in registry")
                continue
            
            execution_order.append(tool_name)
            required_tools.append(ToolRequirement(
                tool_name=tool_name,
                tool_type=tool_info["type"],
                required=True
            ))
        
        # Determine data requirements
        data_requirements = self._determine_data_requirements(ordered_tools)
        missing_data = [
            data_type for data_type in data_requirements
            if available_data.get(data_type, 0) == 0
        ]
        
        can_execute = len(missing_data) == 0
        
        return TaskPlan(
            task_type=primary_task_type,
            description=f"Compound analysis: {', '.join(intent_names)}",
            required_tools=required_tools,
            data_requirements=data_requirements,
            can_execute=can_execute,
            missing_data=missing_data,
            execution_order=execution_order,
            report_structure={"sections": ["analysis", "forecast", "optimization", "recommendations"]}
        )
    
    def _create_task_plan(
        self,
        intent_config: Dict[str, Any],
        available_data: Dict[str, int],
        user_message: str
    ) -> TaskPlan:
        """Create a specific task plan with tool requirements"""
        
        task_type = intent_config["task_type"]
        primary_tools = intent_config["primary_tools"]
        optional_tools = intent_config.get("optional_tools", [])
        
        # Determine data requirements
        data_requirements = self._determine_data_requirements(primary_tools)
        
        # Check if we have required data
        missing_data = [
            data_type for data_type in data_requirements
            if available_data.get(data_type, 0) == 0
        ]
        
        can_execute = len(missing_data) == 0
        
        # Build tool requirements
        required_tools = []
        execution_order = []
        
        # Add primary tools
        for tool_name in primary_tools:
            tool_info = self.tool_registry.get(tool_name, {})
            if tool_info.get("type") == "mcp_tool":
                # For MCP tools, we need to list files first
                if "list_csv_files" not in execution_order:
                    execution_order.append("list_csv_files")
                    required_tools.append(ToolRequirement(
                        tool_name="list_csv_files",
                        tool_type="mcp_tool",
                        required=True
                    ))
                
                execution_order.append(tool_name)
                required_tools.append(ToolRequirement(
                    tool_name=tool_name,
                    tool_type=tool_info["type"],
                    required=True
                ))
            else:
                execution_order.append(tool_name)
                required_tools.append(ToolRequirement(
                    tool_name=tool_name,
                    tool_type=tool_info["type"],
                    required=True
                ))
        
        # Add optional tools if data is available
        for tool_name in optional_tools:
            tool_info = self.tool_registry.get(tool_name, {})
            tool_data_reqs = tool_info.get("required_data", [])
            if all(available_data.get(req, 0) > 0 for req in tool_data_reqs):
                execution_order.append(tool_name)
                required_tools.append(ToolRequirement(
                    tool_name=tool_name,
                    tool_type=tool_info["type"],
                    required=False
                ))
        
        return TaskPlan(
            task_type=task_type,
            description=f"{task_type.value.replace('_', ' ').title()} based on user request",
            required_tools=required_tools,
            data_requirements=data_requirements,
            can_execute=can_execute,
            missing_data=missing_data,
            execution_order=execution_order,
            report_structure={"sections": intent_config.get("report_sections", [])}
        )
    
    def _determine_data_requirements(self, tool_names: List[str]) -> List[str]:
        """Determine what data is needed for the given tools"""
        data_reqs = set()
        for tool_name in tool_names:
            tool_info = self.tool_registry.get(tool_name, {})
            data_reqs.update(tool_info.get("required_data", []))
        # Filter out generic requirements like "csv_file_name"
        return [req for req in data_reqs if req in ["orders", "inventory", "customers", "health_score"]]
    
    def _create_general_advice_plan(self, user_message: str) -> TaskPlan:
        """Create a plan for general advice (no specific tools needed)"""
        return TaskPlan(
            task_type=TaskType.GENERAL_ADVICE,
            description="General business coaching advice",
            required_tools=[],
            data_requirements=[],
            can_execute=True,
            missing_data=[],
            execution_order=[],
            report_structure={}
        )
    
    def generate_system_prompt_for_plan(
        self,
        task_plan: TaskPlan,
        available_data: Dict[str, int],
        persona: str = "business_analyst",
        analysis_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a dynamic system prompt based on the task plan
        
        Args:
            task_plan: The execution plan
            available_data: Available data counts
            persona: User-selected persona
            analysis_results: Results from tool execution (e.g., inventory_analysis)
        
        This replaces hardcoded prompts with intelligent, context-aware instructions
        """
        if not task_plan.can_execute:
            return self._generate_missing_data_prompt(task_plan, available_data)
        
        prompt_parts = [
            f"# Task: {task_plan.description}",
            f"# Persona: {persona.replace('_', ' ').title()}",
            "",
            "## Execution Plan",
            f"You will perform {task_plan.task_type.value.replace('_', ' ')} using the following tools:",
            ""
        ]
        
        # List tools and their purpose
        for i, tool_req in enumerate(task_plan.required_tools, 1):
            tool_info = self.tool_registry.get(tool_req.tool_name, {})
            capability = tool_info.get("capability", "Unknown")
            tool_type = tool_req.tool_type
            required_marker = "REQUIRED" if tool_req.required else "OPTIONAL"
            
            prompt_parts.append(
                f"{i}. **{tool_req.tool_name}** ({tool_type}) - {required_marker}"
            )
            prompt_parts.append(f"   Purpose: {capability}")
            prompt_parts.append(f"   Output: {tool_info.get('output', 'N/A')}")
            prompt_parts.append("")
        
        # Add execution workflow
        prompt_parts.extend([
            "## Workflow",
            "Execute tools in this order:",
            ""
        ])
        
        for i, tool_name in enumerate(task_plan.execution_order, 1):
            prompt_parts.append(f"{i}. {tool_name}")
        
        prompt_parts.extend([
            "",
            "## Report Structure",
            "Generate your response with these sections:",
            ""
        ])
        
        sections = task_plan.report_structure.get("sections", [])
        for section in sections:
            prompt_parts.append(f"- {section.replace('_', ' ').title()}")
        
        # Add data context
        prompt_parts.extend([
            "",
            "## Available Data",
            ""
        ])
        
        for data_type, count in available_data.items():
            if count > 0:
                prompt_parts.append(f"- {data_type.title()}: {count:,} records")
        
        # Add analysis results if available
        if analysis_results:
            prompt_parts.extend([
                "",
                "## Analysis Results from Tool Execution",
                "The following tools have been executed and their results are below.",
                "YOU MUST USE THESE ACTUAL NUMBERS in your response:",
                ""
            ])
            
            # Inventory analysis results
            if "inventory_analysis" in analysis_results:
                inv = analysis_results["inventory_analysis"]
                stock_health = inv.get("stock_health", {})
                
                prompt_parts.extend([
                    "### Inventory Analysis Tool Results:",
                    f"- Total SKUs: **{inv['total_items']:,}**",
                    f"- Total Units: **{inv['total_quantity']:,}**",
                    f"- Total Value: **${inv['total_value']:,.2f}**",
                    f"- Avg Value per SKU: **${inv['avg_value_per_sku']:,.2f}**",
                    "",
                    "Stock Health Breakdown:",
                    f"- In Stock: **{stock_health['in_stock']['count']:,} items ({stock_health['in_stock']['percentage']}%)**",
                    f"- Low Stock: **{stock_health['low_stock']['count']:,} items ({stock_health['low_stock']['percentage']}%)**",
                    f"- Out of Stock: **{stock_health['out_of_stock']['count']:,} items ({stock_health['out_of_stock']['percentage']}%)**",
                    "",
                    "**IMPORTANT**: Use these exact numbers in your Executive Summary and Stock Health table.",
                    ""
                ])
            
            # Revenue forecast results
            if "forecast_insight" in analysis_results:
                forecast = analysis_results["forecast_insight"]
                prompt_parts.extend([
                    "### Demand Forecast Tool Results:",
                    f"- Model: {forecast.get('model', 'N/A')}",
                    f"- Confidence: {forecast.get('confidence', 'N/A')}",
                    "- Predictions:",
                ])
                for fc in forecast.get("forecasts", []):
                    prompt_parts.append(
                        f"  - Period {fc['period']}: ${fc['point']:.2f} (range: ${fc['low']:.2f} - ${fc['high']:.2f})"
                    )
                prompt_parts.append("")
        
        prompt_parts.extend([
            "",
            "## Output Requirements",
            "- Use professional Markdown formatting with tables",
            "- Include the ACTUAL numbers from Analysis Results above",
            "- Cite data sources for all claims [Source: Tool Name]",
            "- Provide actionable recommendations based on the data",
            "- DO NOT give generic advice - analyze the specific numbers provided",
            "- Create tables for the Stock Health Breakdown using the exact percentages",
            ""
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_missing_data_prompt(
        self,
        task_plan: TaskPlan,
        available_data: Dict[str, int]
    ) -> str:
        """Generate prompt when required data is missing"""
        prompt_parts = [
            f"# Cannot Execute: {task_plan.description}",
            "",
            "## Missing Data",
            "The following data is required but not available:",
            ""
        ]
        
        for missing in task_plan.missing_data:
            prompt_parts.append(f"- {missing.title()}")
        
        prompt_parts.extend([
            "",
            "## Available Data",
            ""
        ])
        
        for data_type, count in available_data.items():
            if count > 0:
                prompt_parts.append(f"- {data_type.title()}: {count:,} records ✓")
        
        prompt_parts.extend([
            "",
            "## Response Instructions",
            "Explain to the user:",
            "1. What data is missing and why it's needed",
            "2. What analysis you CAN do with available data",
            "3. How to connect the missing data sources",
            "4. What insights they'll get once data is connected",
            ""
        ])
        
        return "\n".join(prompt_parts)
