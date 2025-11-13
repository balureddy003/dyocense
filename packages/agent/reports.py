"""
Report Generation & Export System

Provides automated report generation with PDF export, scheduled reports,
and shareable links.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import secrets
import hashlib
from io import BytesIO
import json


class ReportFormat(str, Enum):
    """Supported report output formats."""
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


class ReportTemplate(str, Enum):
    """Pre-built report templates."""
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_PERFORMANCE = "weekly_performance"
    MONTHLY_OVERVIEW = "monthly_overview"
    CUSTOM = "custom"


class ReportFrequency(str, Enum):
    """Report schedule frequencies."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ONE_TIME = "one_time"


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    metrics: List[str]
    start_date: datetime
    end_date: datetime
    include_charts: bool = True
    include_insights: bool = True
    include_comparisons: bool = True
    comparison_period: str = "previous_period"
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    """Generated report."""
    id: str
    tenant_id: str
    template: ReportTemplate
    title: str
    config: ReportConfig
    format: ReportFormat
    content: str
    file_size: int
    generated_at: datetime
    generated_by: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportSchedule:
    """Scheduled report configuration."""
    id: Optional[str]
    tenant_id: str
    template: ReportTemplate
    title: str
    config: ReportConfig
    frequency: ReportFrequency
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    day_of_month: Optional[int] = None  # 1-31
    time: str = "09:00"  # HH:MM format
    timezone: str = "UTC"
    recipients: List[str] = field(default_factory=list)
    enabled: bool = True
    next_run: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ShareableReport:
    """Shareable report link."""
    id: str
    report_id: str
    tenant_id: str
    share_token: str
    password_hash: Optional[str]
    created_at: datetime
    expires_at: datetime
    view_count: int = 0
    last_viewed_at: Optional[datetime] = None
    revoked: bool = False


class ReportGenerator:
    """Handles report generation and management."""
    
    def __init__(self):
        """Initialize report generator."""
        self.reports_cache: Dict[str, Report] = {}
        self.schedules_cache: Dict[str, ReportSchedule] = {}
        self.shareable_links: Dict[str, ShareableReport] = {}
    
    async def generate_report(
        self,
        tenant_id: str,
        template: ReportTemplate,
        title: str,
        config: ReportConfig,
        format: ReportFormat = ReportFormat.HTML,
        generated_by: str = "system"
    ) -> Report:
        """
        Generate a report based on template and configuration.
        
        Steps:
        1. Fetch data based on config (metrics, date range, filters)
        2. Calculate metrics and trends
        3. Generate insights using AI (if enabled)
        4. Render template with data
        5. Convert to requested format (HTML/PDF)
        6. Store report in cache
        
        Args:
            tenant_id: Tenant identifier
            template: Report template to use
            title: Report title
            config: Report configuration
            format: Output format
            generated_by: User who generated the report
        
        Returns:
            Generated Report object
        """
        # Generate report ID
        report_id = f"rpt_{secrets.token_hex(16)}"
        
        # Fetch data for report
        data = await self._fetch_report_data(tenant_id, config)
        
        # Calculate metrics
        metrics = await self._calculate_metrics(data, config)
        
        # Generate insights (if enabled)
        insights = []
        if config.include_insights:
            insights = await self._generate_insights(metrics, config)
        
        # Render HTML content
        html_content = await self._render_html(
            template=template,
            title=title,
            metrics=metrics,
            insights=insights,
            config=config
        )
        
        # Convert to requested format
        if format == ReportFormat.PDF:
            content = await self._convert_to_pdf(html_content)
        elif format == ReportFormat.MARKDOWN:
            content = await self._convert_to_markdown(metrics, insights, config)
        else:
            content = html_content
        
        # Create report object
        report = Report(
            id=report_id,
            tenant_id=tenant_id,
            template=template,
            title=title,
            config=config,
            format=format,
            content=content,
            file_size=len(content.encode('utf-8')),
            generated_at=datetime.utcnow(),
            generated_by=generated_by,
            metadata={
                "metrics_count": len(metrics),
                "insights_count": len(insights),
                "date_range": f"{config.start_date.date()} to {config.end_date.date()}"
            }
        )
        
        # Store in cache
        self.reports_cache[report_id] = report
        
        return report
    
    async def _fetch_report_data(
        self,
        tenant_id: str,
        config: ReportConfig
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch raw data for report generation."""
        # MVP: Generate sample data
        data = {}
        
        for metric in config.metrics:
            days = (config.end_date - config.start_date).days + 1
            metric_data = []
            
            current_date = config.start_date
            base_value = 1000 if metric == "revenue" else 80
            
            for i in range(days):
                value = base_value + (i * 10) + (i % 7 * 20)  # Trend + weekly pattern
                metric_data.append({
                    "date": current_date.isoformat(),
                    "value": value,
                    "metric": metric
                })
                current_date += timedelta(days=1)
            
            data[metric] = metric_data
        
        return data
    
    async def _calculate_metrics(
        self,
        data: Dict[str, List[Dict[str, Any]]],
        config: ReportConfig
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate summary metrics from raw data."""
        metrics = {}
        
        for metric_name, metric_data in data.items():
            values = [point["value"] for point in metric_data]
            
            if not values:
                continue
            
            # Calculate summary statistics
            total = sum(values)
            average = total / len(values)
            minimum = min(values)
            maximum = max(values)
            
            # Calculate trend
            if len(values) >= 2:
                recent_avg = sum(values[-7:]) / min(7, len(values))
                earlier_avg = sum(values[:7]) / min(7, len(values))
                trend_pct = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
            else:
                trend_pct = 0
            
            metrics[metric_name] = {
                "total": round(total, 2),
                "average": round(average, 2),
                "minimum": round(minimum, 2),
                "maximum": round(maximum, 2),
                "trend_percentage": round(trend_pct, 2),
                "data_points": len(values),
                "data": metric_data
            }
        
        return metrics
    
    async def _generate_insights(
        self,
        metrics: Dict[str, Dict[str, Any]],
        config: ReportConfig
    ) -> List[Dict[str, str]]:
        """Generate AI-powered insights from metrics."""
        insights = []
        
        # MVP: Rule-based insights
        for metric_name, metric_data in metrics.items():
            trend_pct = metric_data.get("trend_percentage", 0)
            
            if abs(trend_pct) > 15:
                direction = "increased" if trend_pct > 0 else "decreased"
                insights.append({
                    "type": "trend",
                    "severity": "high" if abs(trend_pct) > 25 else "medium",
                    "title": f"{metric_name.replace('_', ' ').title()} {direction} significantly",
                    "description": f"Your {metric_name.replace('_', ' ')} has {direction} by {abs(trend_pct):.1f}% over the reporting period.",
                    "recommendation": f"{'Maintain' if trend_pct > 0 else 'Review'} your current strategies for {metric_name.replace('_', ' ')}."
                })
            
            # Check for anomalies (values > 2 std dev from mean)
            values = [point["value"] for point in metric_data.get("data", [])]
            if len(values) > 10:
                avg = sum(values) / len(values)
                variance = sum((x - avg) ** 2 for x in values) / len(values)
                std_dev = variance ** 0.5
                
                anomalies = [v for v in values if abs(v - avg) > 2 * std_dev]
                if anomalies:
                    insights.append({
                        "type": "anomaly",
                        "severity": "medium",
                        "title": f"Unusual {metric_name.replace('_', ' ').title()} detected",
                        "description": f"Found {len(anomalies)} data points that significantly deviate from normal patterns.",
                        "recommendation": f"Investigate these unusual {metric_name.replace('_', ' ')} values for potential issues or opportunities."
                    })
        
        return insights
    
    async def _render_html(
        self,
        template: ReportTemplate,
        title: str,
        metrics: Dict[str, Dict[str, Any]],
        insights: List[Dict[str, str]],
        config: ReportConfig
    ) -> str:
        """Render report as HTML."""
        # Build HTML content
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{title}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; color: #333; }",
            "h1 { color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }",
            "h2 { color: #1e40af; margin-top: 30px; }",
            ".metric { background: #f8fafc; padding: 15px; margin: 10px 0; border-radius: 8px; }",
            ".metric-name { font-weight: bold; font-size: 18px; color: #334155; }",
            ".metric-value { font-size: 32px; color: #2563eb; font-weight: bold; }",
            ".metric-stats { display: flex; gap: 20px; margin-top: 10px; }",
            ".stat { flex: 1; }",
            ".stat-label { color: #64748b; font-size: 12px; }",
            ".stat-value { font-size: 18px; font-weight: 600; }",
            ".insight { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 10px 0; }",
            ".insight-high { background: #fee2e2; border-left-color: #dc2626; }",
            ".insight-title { font-weight: bold; margin-bottom: 5px; }",
            ".trend-up { color: #16a34a; }",
            ".trend-down { color: #dc2626; }",
            ".footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{title}</h1>",
            f"<p><strong>Period:</strong> {config.start_date.strftime('%B %d, %Y')} to {config.end_date.strftime('%B %d, %Y')}</p>",
            f"<p><strong>Generated:</strong> {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</p>",
        ]
        
        # Add metrics section
        html_parts.append("<h2>📊 Key Metrics</h2>")
        for metric_name, metric_data in metrics.items():
            trend_class = "trend-up" if metric_data["trend_percentage"] > 0 else "trend-down"
            trend_arrow = "↑" if metric_data["trend_percentage"] > 0 else "↓"
            
            html_parts.extend([
                '<div class="metric">',
                f'<div class="metric-name">{metric_name.replace("_", " ").title()}</div>',
                f'<div class="metric-value">{metric_data["total"]:,.2f}</div>',
                '<div class="metric-stats">',
                f'<div class="stat"><div class="stat-label">Average</div><div class="stat-value">{metric_data["average"]:,.2f}</div></div>',
                f'<div class="stat"><div class="stat-label">Min / Max</div><div class="stat-value">{metric_data["minimum"]:,.2f} / {metric_data["maximum"]:,.2f}</div></div>',
                f'<div class="stat"><div class="stat-label">Trend</div><div class="stat-value {trend_class}">{trend_arrow} {abs(metric_data["trend_percentage"]):.1f}%</div></div>',
                '</div>',
                '</div>'
            ])
        
        # Add insights section
        if insights:
            html_parts.append("<h2>💡 Key Insights</h2>")
            for insight in insights:
                severity_class = f'insight-{insight["severity"]}' if insight["severity"] == "high" else "insight"
                html_parts.extend([
                    f'<div class="insight {severity_class}">',
                    f'<div class="insight-title">{insight["title"]}</div>',
                    f'<p>{insight["description"]}</p>',
                    f'<p><strong>Recommendation:</strong> {insight["recommendation"]}</p>',
                    '</div>'
                ])
        
        # Add footer
        html_parts.extend([
            '<div class="footer">',
            '<p>This report was automatically generated by your AI Business Coach.</p>',
            '<p>For questions or support, contact your account manager.</p>',
            '</div>',
            '</body>',
            '</html>'
        ])
        
        return "\n".join(html_parts)
    
    async def _convert_to_pdf(self, html_content: str) -> str:
        """Convert HTML to PDF (stub for MVP)."""
        # MVP: Return HTML with PDF header
        # Production: Use weasyprint or puppeteer
        return f"[PDF Content - {len(html_content)} bytes]\n\n{html_content}"
    
    async def _convert_to_markdown(
        self,
        metrics: Dict[str, Dict[str, Any]],
        insights: List[Dict[str, str]],
        config: ReportConfig
    ) -> str:
        """Convert report data to Markdown format."""
        md_parts = [
            "# Business Performance Report",
            "",
            f"**Period:** {config.start_date.strftime('%B %d, %Y')} to {config.end_date.strftime('%B %d, %Y')}",
            f"**Generated:** {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}",
            "",
            "## 📊 Key Metrics",
            ""
        ]
        
        for metric_name, metric_data in metrics.items():
            trend_arrow = "↑" if metric_data["trend_percentage"] > 0 else "↓"
            md_parts.extend([
                f"### {metric_name.replace('_', ' ').title()}",
                "",
                f"- **Total:** {metric_data['total']:,.2f}",
                f"- **Average:** {metric_data['average']:,.2f}",
                f"- **Range:** {metric_data['minimum']:,.2f} - {metric_data['maximum']:,.2f}",
                f"- **Trend:** {trend_arrow} {abs(metric_data['trend_percentage']):.1f}%",
                ""
            ])
        
        if insights:
            md_parts.extend([
                "## 💡 Key Insights",
                ""
            ])
            
            for insight in insights:
                md_parts.extend([
                    f"### {insight['title']}",
                    "",
                    insight['description'],
                    "",
                    f"**Recommendation:** {insight['recommendation']}",
                    ""
                ])
        
        return "\n".join(md_parts)
    
    async def list_reports(
        self,
        tenant_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List all reports for a tenant."""
        reports = [
            {
                "id": report.id,
                "title": report.title,
                "template": report.template,
                "format": report.format,
                "file_size": report.file_size,
                "generated_at": report.generated_at.isoformat(),
                "generated_by": report.generated_by,
                "metadata": report.metadata
            }
            for report in self.reports_cache.values()
            if report.tenant_id == tenant_id
        ]
        
        # Sort by generated_at descending
        reports.sort(key=lambda x: x["generated_at"], reverse=True)
        
        return reports[:limit]
    
    async def get_report(
        self,
        tenant_id: str,
        report_id: str
    ) -> Optional[Report]:
        """Get specific report by ID."""
        report = self.reports_cache.get(report_id)
        
        if report and report.tenant_id == tenant_id:
            return report
        
        return None
    
    async def create_schedule(
        self,
        tenant_id: str,
        schedule: ReportSchedule
    ) -> ReportSchedule:
        """Create recurring report schedule."""
        # Generate schedule ID
        schedule_id = f"sch_{secrets.token_hex(16)}"
        schedule.id = schedule_id
        schedule.tenant_id = tenant_id
        
        # Calculate next run time
        schedule.next_run = self._calculate_next_run(schedule)
        
        # Store in cache
        self.schedules_cache[schedule_id] = schedule
        
        return schedule
    
    def _calculate_next_run(self, schedule: ReportSchedule) -> datetime:
        """Calculate next scheduled run time."""
        now = datetime.utcnow()
        
        # Parse time
        hour, minute = map(int, schedule.time.split(':'))
        
        if schedule.frequency == ReportFrequency.DAILY:
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif schedule.frequency == ReportFrequency.WEEKLY:
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            day_of_week = schedule.day_of_week or 0
            days_ahead = (day_of_week - now.weekday()) % 7
            if days_ahead == 0 and next_run <= now:
                days_ahead = 7
            next_run += timedelta(days=days_ahead)
        
        elif schedule.frequency == ReportFrequency.MONTHLY:
            day_of_month = schedule.day_of_month or 1
            next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                # Move to next month
                if next_run.month == 12:
                    next_run = next_run.replace(year=next_run.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=next_run.month + 1)
        
        else:  # ONE_TIME
            next_run = now
        
        return next_run
    
    async def list_schedules(
        self,
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        """List all schedules for a tenant."""
        schedules = [
            {
                "id": schedule.id,
                "title": schedule.title,
                "template": schedule.template,
                "frequency": schedule.frequency,
                "recipients": schedule.recipients,
                "enabled": schedule.enabled,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None
            }
            for schedule in self.schedules_cache.values()
            if schedule.tenant_id == tenant_id
        ]
        
        return schedules
    
    async def update_schedule(
        self,
        tenant_id: str,
        schedule_id: str,
        updates: Dict[str, Any]
    ) -> Optional[ReportSchedule]:
        """Update existing schedule."""
        schedule = self.schedules_cache.get(schedule_id)
        
        if not schedule or schedule.tenant_id != tenant_id:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        
        schedule.updated_at = datetime.utcnow()
        
        # Recalculate next run if frequency/time changed
        if any(k in updates for k in ['frequency', 'time', 'day_of_week', 'day_of_month']):
            schedule.next_run = self._calculate_next_run(schedule)
        
        return schedule
    
    async def delete_schedule(
        self,
        tenant_id: str,
        schedule_id: str
    ) -> bool:
        """Delete schedule."""
        schedule = self.schedules_cache.get(schedule_id)
        
        if schedule and schedule.tenant_id == tenant_id:
            del self.schedules_cache[schedule_id]
            return True
        
        return False
    
    async def create_shareable_link(
        self,
        tenant_id: str,
        report_id: str,
        expires_in_days: int = 7,
        password: Optional[str] = None
    ) -> ShareableReport:
        """Create shareable public link for report."""
        # Generate secure token
        share_token = secrets.token_urlsafe(32)
        
        # Hash password if provided
        password_hash = None
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create shareable report
        shareable = ShareableReport(
            id=f"shr_{secrets.token_hex(16)}",
            report_id=report_id,
            tenant_id=tenant_id,
            share_token=share_token,
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )
        
        # Store in cache
        self.shareable_links[share_token] = shareable
        
        return shareable
    
    async def get_shared_report(
        self,
        share_token: str,
        password: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve report via share link."""
        shareable = self.shareable_links.get(share_token)
        
        if not shareable:
            return None
        
        # Check if revoked
        if shareable.revoked:
            return None
        
        # Check if expired
        if datetime.utcnow() > shareable.expires_at:
            return None
        
        # Verify password if required
        if shareable.password_hash:
            if not password:
                return {"error": "password_required"}
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != shareable.password_hash:
                return {"error": "invalid_password"}
        
        # Get the actual report
        report = self.reports_cache.get(shareable.report_id)
        
        if not report:
            return None
        
        # Update view tracking
        shareable.view_count += 1
        shareable.last_viewed_at = datetime.utcnow()
        
        return {
            "report": {
                "id": report.id,
                "title": report.title,
                "content": report.content,
                "format": report.format,
                "generated_at": report.generated_at.isoformat()
            },
            "share_info": {
                "expires_at": shareable.expires_at.isoformat(),
                "view_count": shareable.view_count
            }
        }
    
    async def revoke_share_link(
        self,
        tenant_id: str,
        share_token: str
    ) -> bool:
        """Revoke shareable link."""
        shareable = self.shareable_links.get(share_token)
        
        if shareable and shareable.tenant_id == tenant_id:
            shareable.revoked = True
            return True
        
        return False
    
    async def execute_scheduled_reports(self):
        """
        Background job to execute scheduled reports.
        
        Should be called periodically (e.g., every hour) to:
        1. Find schedules due to run
        2. Generate reports
        3. Email to recipients
        4. Update next_run timestamp
        """
        now = datetime.utcnow()
        
        for schedule in self.schedules_cache.values():
            if not schedule.enabled:
                continue
            
            if schedule.next_run and schedule.next_run <= now:
                # Generate report
                try:
                    report = await self.generate_report(
                        tenant_id=schedule.tenant_id,
                        template=schedule.template,
                        title=schedule.title,
                        config=schedule.config,
                        format=ReportFormat.PDF,
                        generated_by="scheduled_job"
                    )
                    
                    # TODO: Send email to recipients
                    # await send_email(schedule.recipients, report)
                    
                    # Update next run
                    schedule.next_run = self._calculate_next_run(schedule)
                    schedule.updated_at = datetime.utcnow()
                    
                except Exception as e:
                    # Log error but continue with other schedules
                    print(f"Error executing schedule {schedule.id}: {e}")


def create_report_generator() -> ReportGenerator:
    """Factory function to create ReportGenerator instance."""
    return ReportGenerator()
