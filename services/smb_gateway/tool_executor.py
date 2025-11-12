"""
Tool Executor - Decoupled Business Logic Execution

This module provides a plugin-based architecture for executing analysis tools
without hardcoding business-specific logic into the coach.

Benefits:
- Scale to any business domain (retail, healthcare, manufacturing, etc.)
- Add new analysis tools without modifying coach code
- Swap implementations per tenant/industry
- Test tools independently
"""
from typing import Dict, Any, Optional, Callable, Protocol, List
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class AnalysisTool(Protocol):
    """Protocol for analysis tools - any callable that matches this signature"""
    def __call__(self, business_context: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """Execute analysis and return results"""
        ...


class ToolExecutor:
    """
    Executes tools dynamically based on registry without hardcoding business logic
    
    Usage:
        executor = ToolExecutor()
        executor.register_tool("analyze_inventory", inventory_analysis_function)
        result = executor.execute("analyze_inventory", business_context)
    """
    
    def __init__(self):
        self.tools: Dict[str, AnalysisTool] = {}
        self._register_default_tools()
    
    def register_tool(self, tool_name: str, tool_function: AnalysisTool):
        """Register a tool for execution"""
        self.tools[tool_name] = tool_function
        logger.info(f"✅ Registered tool: {tool_name}")
    
    def _register_default_tools(self):
        """Register default analysis tools"""
        # Import tool implementations
        from .analysis_tools import (
            analyze_inventory_data,
            analyze_revenue_data,
            analyze_customer_data,
            analyze_health_metrics,
        )
        from .forecast_tools import (
            forecast_demand,
            forecast_revenue,
        )
        from .optimization_tools import (
            optimize_inventory_levels,
            optimize_pricing,
        )
        
        # Register analysis tools
        self.register_tool("analyze_inventory", analyze_inventory_data)
        self.register_tool("analyze_revenue", analyze_revenue_data)
        self.register_tool("analyze_customers", analyze_customer_data)
        self.register_tool("analyze_health", analyze_health_metrics)
        
        # Register forecasting tools
        self.register_tool("forecast_demand", forecast_demand)
        self.register_tool("forecast_revenue", forecast_revenue)
        
        # Register optimization tools
        self.register_tool("optimize_inventory", optimize_inventory_levels)
        self.register_tool("optimize_pricing", optimize_pricing)
        
        logger.info(f"📦 Registered {len(self.tools)} default tools (analysis + forecasting + optimization)")
    
    def execute(
        self,
        tool_name: str,
        business_context: Dict[str, Any],
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a tool dynamically
        
        Args:
            tool_name: Name of the tool to execute (e.g., "analyze_inventory")
            business_context: Business context with metrics and data
            **kwargs: Additional parameters for the tool
        
        Returns:
            Analysis results or None if execution fails
        """
        if tool_name not in self.tools:
            logger.error(f"❌ Tool '{tool_name}' not registered")
            return None
        
        try:
            logger.info(f"🔧 Executing tool: {tool_name}")
            tool = self.tools[tool_name]
            result = tool(business_context, **kwargs)
            
            if result:
                logger.info(f"✅ Tool '{tool_name}' completed successfully")
            else:
                logger.warning(f"⚠️ Tool '{tool_name}' returned no results")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Tool '{tool_name}' execution failed: {e}", exc_info=True)
            return {"error": str(e), "tool": tool_name}
    
    def is_available(self, tool_name: str) -> bool:
        """Check if a tool is available"""
        return tool_name in self.tools
    
    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return list(self.tools.keys())


# Global singleton
_tool_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """Get global tool executor instance"""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
    return _tool_executor
