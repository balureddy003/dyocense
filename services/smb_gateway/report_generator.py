"""
Report Generator

Creates downloadable business reports with charts, graphs, and structured data
Supports multiple output formats: JSON, PDF, HTML, Excel
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging
import json
import uuid

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"
    MARKDOWN = "markdown"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    GAUGE = "gauge"


class AgentThought:
    """Represents an agent's reasoning step"""
    def __init__(
        self,
        agent_name: str,
        thought: str,
        action: str,
        observation: str,
        data_source: str,
        timestamp: Optional[datetime] = None
    ):
        self.agent_name = agent_name
        self.thought = thought
        self.action = action
        self.observation = observation
        self.data_source = data_source
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "data_source": self.data_source,
            "timestamp": self.timestamp.isoformat()
        }


class Evidence:
    """Evidence supporting a claim"""
    def __init__(
        self,
        claim: str,
        data_source: str,
        calculation: str,
        raw_value: Any,
        confidence: float = 1.0
    ):
        self.claim = claim
        self.data_source = data_source
        self.calculation = calculation
        self.raw_value = raw_value
        self.confidence = confidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "data_source": self.data_source,
            "calculation": self.calculation,
            "raw_value": self.raw_value,
            "confidence": self.confidence
        }


class ReportSection:
    """A section of the report with data and optional visualization"""
    
    def __init__(
        self,
        title: str,
        content: str,
        data: Optional[Dict[str, Any]] = None,
        chart: Optional[Dict[str, Any]] = None,
        table: Optional[List[Dict[str, Any]]] = None,
        insights: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
        agent_thoughts: Optional[List[AgentThought]] = None,
        evidence: Optional[List[Evidence]] = None
    ):
        self.title = title
        self.content = content
        self.data = data or {}
        self.chart = chart
        self.table = table
        self.insights = insights or []
        self.recommendations = recommendations or []
        self.agent_thoughts = agent_thoughts or []
        self.evidence = evidence or []
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "title": self.title,
            "content": self.content,
            "data": self.data,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "agent_thoughts": [t.to_dict() for t in self.agent_thoughts],
            "evidence": [e.to_dict() for e in self.evidence]
        }
        if self.chart:
            result["chart"] = self.chart
        if self.table:
            result["table"] = self.table
        return result


class BusinessReport:
    """Complete business report with metadata and sections"""
    
    def __init__(
        self,
        title: str,
        business_name: str,
        report_type: str,
        generated_at: Optional[datetime] = None,
        report_id: Optional[str] = None
    ):
        self.report_id = report_id or f"RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        self.title = title
        self.business_name = business_name
        self.report_type = report_type
        self.generated_at = generated_at or datetime.now()
        self.sections: List[ReportSection] = []
        self.metadata: Dict[str, Any] = {}
        self.summary: str = ""
    
    def add_section(self, section: ReportSection):
        """Add a section to the report"""
        self.sections.append(section)
    
    def set_summary(self, summary: str):
        """Set executive summary"""
        self.summary = summary
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """Set report metadata"""
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "report_id": self.report_id,
            "title": self.title,
            "business_name": self.business_name,
            "report_type": self.report_type,
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary,
            "metadata": self.metadata,
            "sections": [s.to_dict() for s in self.sections]
        }
    
    def to_json(self) -> str:
        """Export report as JSON"""
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Export report as Markdown"""
        lines = []
        
        # Title and metadata
        lines.append(f"# {self.title}")
        lines.append(f"**Business:** {self.business_name}")
        lines.append(f"**Report Type:** {self.report_type}")
        lines.append(f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Executive summary
        if self.summary:
            lines.append("## Executive Summary")
            lines.append(self.summary)
            lines.append("")
        
        # Sections
        for section in self.sections:
            lines.append(f"## {section.title}")
            lines.append(section.content)
            lines.append("")
            
            # Agent Thinking Process
            if section.agent_thoughts:
                lines.append("### 🤖 Agent Analysis Process")
                for thought in section.agent_thoughts:
                    lines.append(f"\n**Agent: {thought.agent_name}**")
                    lines.append(f"- 💭 **Thought:** {thought.thought}")
                    lines.append(f"- ⚡ **Action:** {thought.action}")
                    lines.append(f"- 👁️ **Observation:** {thought.observation}")
                    lines.append(f"- 📊 **Data Source:** `{thought.data_source}`")
                lines.append("")
            
            # Evidence and Facts
            if section.evidence:
                lines.append("### 📊 Evidence & Data Points")
                for ev in section.evidence:
                    lines.append(f"\n**{ev.claim}**")
                    lines.append(f"- Source: `{ev.data_source}`")
                    lines.append(f"- Calculation: `{ev.calculation}`")
                    lines.append(f"- Value: `{ev.raw_value}`")
                    lines.append(f"- Confidence: {ev.confidence * 100:.0f}%")
                lines.append("")
            
            # Insights
            if section.insights:
                lines.append("### 💡 Key Insights")
                for insight in section.insights:
                    lines.append(f"- {insight}")
                lines.append("")
            
            # Table
            if section.table and len(section.table) > 0:
                lines.append("### 📋 Data")
                headers = list(section.table[0].keys())
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for row in section.table[:10]:  # Limit to first 10 rows
                    values = [str(row.get(h, "")) for h in headers]
                    lines.append("| " + " | ".join(values) + " |")
                lines.append("")
            
            # Recommendations
            if section.recommendations:
                lines.append("### ✅ Recommendations")
                for i, rec in enumerate(section.recommendations, 1):
                    lines.append(f"{i}. {rec}")
                lines.append("")
        
        return "\n".join(lines)
    
    def to_html(self, include_thinking: bool = True, include_evidence: bool = True) -> str:
        """Export report as rich HTML with agent thinking and evidence"""
        html_parts = []
        
        # HTML header
        html_parts.append("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {business_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px 12px 0 0;
        }}
        .header h1 {{ font-size: 36px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .summary {{
            background: #f0f4ff;
            padding: 30px 40px;
            border-left: 4px solid #667eea;
            margin: 20px 40px;
            border-radius: 8px;
        }}
        .summary h2 {{ color: #667eea; margin-bottom: 15px; }}
        .section {{ padding: 30px 40px; border-bottom: 1px solid #e5e7eb; }}
        .section:last-child {{ border-bottom: none; }}
        .section h2 {{ color: #1f2937; margin-bottom: 20px; font-size: 28px; }}
        .agent-thoughts {{
            background: #fffbeb;
            border: 1px solid #fbbf24;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .agent-thoughts h3 {{ color: #d97706; margin-bottom: 15px; }}
        .thought-item {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 12px;
            border-left: 3px solid #fbbf24;
        }}
        .thought-item .agent-name {{ font-weight: bold; color: #d97706; margin-bottom: 8px; }}
        .thought-step {{ margin: 6px 0; padding-left: 20px; }}
        .thought-step .label {{ font-weight: 600; color: #92400e; }}
        .evidence {{
            background: #ecfdf5;
            border: 1px solid #10b981;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .evidence h3 {{ color: #047857; margin-bottom: 15px; }}
        .evidence-item {{
            background: white;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
            border-left: 3px solid #10b981;
        }}
        .evidence-item .claim {{ font-weight: bold; color: #047857; margin-bottom: 6px; }}
        .evidence-item .detail {{ font-size: 13px; color: #065f46; font-family: 'Monaco', monospace; }}
        .insights {{ background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .insights h3 {{ color: #374151; margin-bottom: 12px; }}
        .insights li {{ margin: 8px 0; }}
        .recommendations {{
            background: #e0f2fe;
            border: 1px solid #0284c7;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .recommendations h3 {{ color: #075985; margin-bottom: 12px; }}
        .recommendations li {{ margin: 10px 0; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}
        tr:hover {{ background: #f9fafb; }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: #6b7280;
            font-size: 14px;
        }}
        .download-buttons {{
            padding: 20px 40px;
            background: #f9fafb;
            border-top: 1px solid #e5e7eb;
        }}
        .download-buttons button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-right: 10px;
            transition: background 0.2s;
        }}
        .download-buttons button:hover {{ background: #5568d3; }}
        @media print {{
            body {{ background: white; }}
            .download-buttons {{ display: none; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <div class="meta">
                <strong>{business_name}</strong> | 
                Generated: {generated_at} | 
                Report Type: {report_type}
            </div>
        </div>
""".format(
            title=self.title,
            business_name=self.business_name,
            generated_at=self.generated_at.strftime('%B %d, %Y at %I:%M %p'),
            report_type=self.report_type
        ))
        
        # Summary
        if self.summary:
            html_parts.append(f"""
        <div class="summary">
            <h2>📋 Executive Summary</h2>
            <p>{self.summary}</p>
        </div>
""")
        
        # Sections
        for section in self.sections:
            html_parts.append(f"""
        <div class="section">
            <h2>{section.title}</h2>
            {section.content}
""")
            
            # Agent Thinking
            if include_thinking and section.agent_thoughts:
                html_parts.append("""
            <div class="agent-thoughts">
                <h3>🤖 How Our Agents Analyzed This</h3>
""")
                for thought in section.agent_thoughts:
                    html_parts.append(f"""
                <div class="thought-item">
                    <div class="agent-name">Agent: {thought.agent_name}</div>
                    <div class="thought-step"><span class="label">💭 Thought:</span> {thought.thought}</div>
                    <div class="thought-step"><span class="label">⚡ Action:</span> {thought.action}</div>
                    <div class="thought-step"><span class="label">👁️ Observation:</span> {thought.observation}</div>
                    <div class="thought-step"><span class="label">📊 Data Source:</span> <code>{thought.data_source}</code></div>
                </div>
""")
                html_parts.append("""
            </div>
""")
            
            # Evidence
            if include_evidence and section.evidence:
                html_parts.append("""
            <div class="evidence">
                <h3>📊 Evidence & Calculations</h3>
""")
                for ev in section.evidence:
                    html_parts.append(f"""
                <div class="evidence-item">
                    <div class="claim">{ev.claim}</div>
                    <div class="detail">Source: {ev.data_source} | Calculation: {ev.calculation}</div>
                    <div class="detail">Raw Value: {ev.raw_value} | Confidence: {ev.confidence * 100:.0f}%</div>
                </div>
""")
                html_parts.append("""
            </div>
""")
            
            # Insights
            if section.insights:
                html_parts.append("""
            <div class="insights">
                <h3>💡 Key Insights</h3>
                <ul>
""")
                for insight in section.insights:
                    html_parts.append(f"                    <li>{insight}</li>\n")
                html_parts.append("""
                </ul>
            </div>
""")
            
            # Recommendations
            if section.recommendations:
                html_parts.append("""
            <div class="recommendations">
                <h3>✅ Recommended Actions</h3>
                <ol>
""")
                for rec in section.recommendations:
                    html_parts.append(f"                    <li>{rec}</li>\n")
                html_parts.append("""
                </ol>
            </div>
""")
            
            html_parts.append("""
        </div>
""")
        
        # Footer
        html_parts.append("""
        <div class="footer">
            Generated by Dyocense AI Business Coach | All rights reserved
        </div>
    </div>
</body>
</html>
""")
        
        return "".join(html_parts)


class ReportGenerator:
    """Generate business reports from analysis results"""
    
    @staticmethod
    def create_inventory_report(
        business_name: str,
        analysis_result: Dict[str, Any],
        business_profile: Any
    ) -> BusinessReport:
        """
        Create inventory analysis report with charts
        
        Args:
            business_name: Name of the business
            analysis_result: Results from analyze_inventory tool
            business_profile: BusinessProfile object with terminology
        """
        terminology = business_profile.terminology
        items_term = terminology.get("items", "items")
        
        report = BusinessReport(
            title=f"{items_term.title()} Stock Analysis Report",
            business_name=business_name,
            report_type="inventory_analysis"
        )
        
        # Executive Summary
        total_items = analysis_result.get("total_items", 0)
        total_value = analysis_result.get("total_value", 0)
        stock_health = analysis_result.get("stock_health", {})
        
        summary = (
            f"The current inventory consists of **{total_items:,} {items_term}** "
            f"with a total valuation of **${total_value:,.2f}**. "
        )
        
        in_stock_pct = stock_health.get("in_stock", {}).get("percentage", 0)
        low_stock_pct = stock_health.get("low_stock", {}).get("percentage", 0)
        out_of_stock_pct = stock_health.get("out_of_stock", {}).get("percentage", 0)
        
        if out_of_stock_pct > 0:
            summary += f"**{out_of_stock_pct:.1f}%** are currently out of stock, requiring immediate attention. "
        else:
            summary += "All items are currently in stock. "
        
        report.set_summary(summary)
        
        # Section 1: Stock Health Distribution
        stock_health_section = ReportSection(
            title="Stock Health Distribution",
            content=f"Analysis of stock availability across all {items_term}:",
            data=stock_health,
            chart={
                "type": ChartType.DONUT.value,
                "data": {
                    "labels": ["In Stock", "Low Stock", "Out of Stock"],
                    "values": [
                        in_stock_pct,
                        low_stock_pct,
                        out_of_stock_pct
                    ],
                    "colors": ["#10b981", "#f59e0b", "#ef4444"]
                },
                "options": {
                    "title": "Stock Distribution by Status",
                    "valueFormat": "percentage"
                }
            },
            insights=[
                f"{in_stock_pct:.1f}% of {items_term} are adequately stocked",
                f"{low_stock_pct:.1f}% need reordering soon" if low_stock_pct > 0 else "No items running low",
                f"{out_of_stock_pct:.1f}% are currently unavailable" if out_of_stock_pct > 0 else "No stockouts"
            ]
        )
        report.add_section(stock_health_section)
        
        # Section 2: Valuation Metrics
        avg_value = analysis_result.get("avg_value_per_sku", 0)
        total_qty = analysis_result.get("total_quantity", 0)
        
        valuation_section = ReportSection(
            title="Inventory Valuation",
            content=f"Financial analysis of {items_term} inventory:",
            data={
                "total_value": total_value,
                "total_quantity": total_qty,
                "avg_value_per_item": avg_value,
                "total_items": total_items
            },
            chart={
                "type": ChartType.BAR.value,
                "data": {
                    "labels": ["Total Value", "Avg Value/Item", "Total Quantity"],
                    "values": [total_value, avg_value, total_qty],
                    "colors": ["#3b82f6", "#8b5cf6", "#06b6d4"]
                },
                "options": {
                    "title": "Inventory Metrics",
                    "yAxisLabel": "Value ($)"
                }
            },
            insights=[
                f"Total inventory value: ${total_value:,.2f}",
                f"Average value per item: ${avg_value:,.2f}",
                f"Total quantity in stock: {total_qty:,} units"
            ]
        )
        report.add_section(valuation_section)
        
        # Section 3: Recommendations
        recommendations = analysis_result.get("recommendations", [])
        critical_issues = analysis_result.get("critical_issues", [])
        
        action_section = ReportSection(
            title="Action Items",
            content="Recommended actions based on current stock levels:",
            insights=critical_issues,
            recommendations=recommendations if recommendations else [
                f"Continue monitoring stock levels for all {items_term}",
                "Review reorder points for seasonal fluctuations",
                "Consider implementing automated reorder triggers"
            ]
        )
        report.add_section(action_section)
        
        # Set metadata
        report.set_metadata({
            "data_source": "inventory_system",
            "items_analyzed": total_items,
            "industry": business_profile.industry,
            "business_type": business_profile.business_type
        })
        
        return report
    
    @staticmethod
    def create_revenue_report(
        business_name: str,
        analysis_result: Dict[str, Any],
        business_profile: Any
    ) -> BusinessReport:
        """Create revenue analysis report with trend charts"""
        terminology = business_profile.terminology
        transaction_term = terminology.get("transaction", "transaction")
        value_term = terminology.get("value", "revenue")
        
        report = BusinessReport(
            title=f"{value_term.title()} Analysis Report",
            business_name=business_name,
            report_type="revenue_analysis"
        )
        
        revenue_30d = analysis_result.get("revenue_30d", 0)
        orders_30d = analysis_result.get("orders_30d", 0)
        avg_order_value = analysis_result.get("avg_order_value", 0)
        
        summary = (
            f"Generated **${revenue_30d:,.2f}** in {value_term} "
            f"from **{orders_30d:,} {transaction_term}s** over the last 30 days. "
            f"Average {transaction_term} value is **${avg_order_value:,.2f}**."
        )
        
        report.set_summary(summary)
        
        # Revenue metrics section
        metrics_section = ReportSection(
            title=f"{value_term.title()} Metrics (Last 30 Days)",
            content=f"Key performance indicators for {transaction_term}s:",
            data={
                "revenue_30d": revenue_30d,
                "orders_30d": orders_30d,
                "avg_order_value": avg_order_value
            },
            chart={
                "type": ChartType.BAR.value,
                "data": {
                    "labels": [f"Total {value_term.title()}", f"{transaction_term.title()}s", "Avg Value"],
                    "values": [revenue_30d, orders_30d, avg_order_value],
                    "colors": ["#10b981", "#3b82f6", "#8b5cf6"]
                },
                "options": {
                    "title": f"{value_term.title()} Performance"
                }
            }
        )
        report.add_section(metrics_section)
        
        report.set_metadata({
            "period": "30_days",
            "industry": business_profile.industry
        })
        
        return report


# Global singleton
_report_generator: Optional['ReportGenerator'] = None


def get_report_generator() -> ReportGenerator:
    """Get or create report generator singleton"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
