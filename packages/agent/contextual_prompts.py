"""
Contextual Prompt System

Generates time-based, context-aware proactive messages for users:
- Morning kickoff (8-10am): Daily priorities, overnight insights
- Midday check-in (12-2pm): Lunch rush updates, service reminders
- End-of-day wrap-up (5-7pm): Summary, tomorrow prep
- Critical alerts: Immediate notifications for urgent issues

Features:
- Business hours awareness (different schedules for restaurants vs offices)
- Timezone support for multi-location businesses
- Industry-specific messaging (restaurant vs retail vs services)
- Delivery via WebSocket for real-time updates
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, time, timedelta
from enum import Enum
from dataclasses import dataclass
import pytz


class PromptType(str, Enum):
    """Types of contextual prompts"""
    MORNING_KICKOFF = "morning_kickoff"
    MIDDAY_CHECKIN = "midday_checkin"
    EOD_WRAPUP = "eod_wrapup"
    CRITICAL_ALERT = "critical_alert"
    MILESTONE_CELEBRATION = "milestone_celebration"
    RECOMMENDATION = "recommendation"


class MessageTone(str, Enum):
    """Tone of the message"""
    MOTIVATIONAL = "motivational"
    INFORMATIVE = "informative"
    URGENT = "urgent"
    CELEBRATORY = "celebratory"
    ADVISORY = "advisory"


@dataclass
class BusinessHours:
    """Business operating hours configuration"""
    timezone: str  # e.g., "America/New_York"
    open_time: time  # e.g., time(8, 0) for 8am
    close_time: time  # e.g., time(22, 0) for 10pm
    business_type: str
    
    def is_open_now(self) -> bool:
        """Check if business is currently open"""
        tz = pytz.timezone(self.timezone)
        now = datetime.now(tz).time()
        
        if self.open_time < self.close_time:
            # Normal hours (e.g., 9am-5pm)
            return self.open_time <= now <= self.close_time
        else:
            # Overnight hours (e.g., 6pm-2am)
            return now >= self.open_time or now <= self.close_time
    
    def time_until_open(self) -> Optional[timedelta]:
        """Time until business opens"""
        tz = pytz.timezone(self.timezone)
        now = datetime.now(tz)
        
        if self.is_open_now():
            return None
        
        # Calculate next opening
        next_open = datetime.combine(now.date(), self.open_time)
        next_open = tz.localize(next_open)
        
        if next_open < now:
            # Opening is tomorrow
            next_open += timedelta(days=1)
        
        return next_open - now
    
    def time_until_close(self) -> Optional[timedelta]:
        """Time until business closes"""
        tz = pytz.timezone(self.timezone)
        now = datetime.now(tz)
        
        if not self.is_open_now():
            return None
        
        # Calculate closing time
        close_dt = datetime.combine(now.date(), self.close_time)
        close_dt = tz.localize(close_dt)
        
        if close_dt < now:
            # Closing is tomorrow (overnight business)
            close_dt += timedelta(days=1)
        
        return close_dt - now


@dataclass
class ContextualPrompt:
    """A contextual prompt message"""
    id: str
    type: PromptType
    tone: MessageTone
    title: str
    message: str
    actions: List[Dict[str, Any]]
    priority: int  # 1=highest
    scheduled_time: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ContextualPromptGenerator:
    """
    Generates contextual prompts based on:
    - Time of day
    - Business type
    - Business hours
    - Recent data/metrics
    - User behavior patterns
    """
    
    # Default business hours by industry
    DEFAULT_HOURS = {
        "restaurant": BusinessHours("America/New_York", time(10, 0), time(22, 0), "restaurant"),
        "retail": BusinessHours("America/New_York", time(9, 0), time(20, 0), "retail"),
        "services": BusinessHours("America/New_York", time(9, 0), time(17, 0), "services"),
        "contractor": BusinessHours("America/New_York", time(7, 0), time(17, 0), "contractor"),
        "other": BusinessHours("America/New_York", time(9, 0), time(17, 0), "other"),
    }
    
    def __init__(
        self,
        business_type: str,
        timezone: str = "America/New_York",
        custom_hours: Optional[BusinessHours] = None,
    ):
        self.business_type = business_type
        self.timezone = timezone
        self.business_hours = custom_hours or self.DEFAULT_HOURS.get(
            business_type,
            self.DEFAULT_HOURS["other"]
        )
    
    async def generate_prompts(
        self,
        tenant_id: str,
        current_data: Dict[str, Any],
    ) -> List[ContextualPrompt]:
        """
        Generate contextual prompts based on current time and data
        
        Args:
            tenant_id: Tenant identifier
            current_data: Current metrics, health score, etc.
        
        Returns:
            List of prompts to deliver
        """
        prompts = []
        
        tz = pytz.timezone(self.timezone)
        now = datetime.now(tz)
        current_hour = now.hour
        
        # Morning kickoff (8-10am)
        if 8 <= current_hour < 10:
            morning_prompt = self._generate_morning_kickoff(tenant_id, current_data, now)
            if morning_prompt:
                prompts.append(morning_prompt)
        
        # Midday check-in (12-2pm)
        elif 12 <= current_hour < 14:
            midday_prompt = self._generate_midday_checkin(tenant_id, current_data, now)
            if midday_prompt:
                prompts.append(midday_prompt)
        
        # End-of-day wrap-up (5-7pm)
        elif 17 <= current_hour < 19:
            eod_prompt = self._generate_eod_wrapup(tenant_id, current_data, now)
            if eod_prompt:
                prompts.append(eod_prompt)
        
        # Critical alerts (anytime)
        critical_prompts = self._check_critical_alerts(tenant_id, current_data, now)
        prompts.extend(critical_prompts)
        
        # Milestone celebrations
        milestone_prompts = self._check_milestones(tenant_id, current_data, now)
        prompts.extend(milestone_prompts)
        
        return prompts
    
    def _generate_morning_kickoff(
        self,
        tenant_id: str,
        data: Dict[str, Any],
        now: datetime,
    ) -> Optional[ContextualPrompt]:
        """Generate morning kickoff message"""
        
        # Industry-specific morning messages
        messages = {
            "restaurant": [
                "Good morning! Ready for another great day of service?",
                "Morning! Let's prep for today's rush.",
                "Rise and shine! Time to check today's reservations and prep.",
            ],
            "retail": [
                "Good morning! Let's make today a strong sales day.",
                "Morning! Time to open up and serve customers.",
                "New day, new opportunities! Let's boost those conversions.",
            ],
            "services": [
                "Good morning! Let's maximize billable hours today.",
                "Morning! Time to check your project pipeline.",
                "New day! Let's keep those utilization rates high.",
            ],
            "contractor": [
                "Good morning! Let's get those jobs moving.",
                "Morning! Time to check job sites and schedules.",
                "New day! Let's keep projects on track and on budget.",
            ],
        }
        
        base_message = messages.get(self.business_type, ["Good morning! Let's make today count."])[0]
        
        # Add data-driven insights
        insights = []
        health_score = data.get("health_score", 0)
        
        if health_score > 80:
            insights.append("Your business health score is looking strong at {score}!".format(score=health_score))
        elif health_score < 60:
            insights.append("Let's work on improving your health score (currently {score}).".format(score=health_score))
        
        # Check pending tasks
        pending_tasks = data.get("pending_tasks", 0)
        if pending_tasks > 0:
            insights.append("You have {count} tasks to tackle today.".format(count=pending_tasks))
        
        message = base_message
        if insights:
            message += "\n\n" + "\n".join("• " + i for i in insights)
        
        return ContextualPrompt(
            id=f"morning-{tenant_id}-{now.date()}",
            type=PromptType.MORNING_KICKOFF,
            tone=MessageTone.MOTIVATIONAL,
            title="Good Morning!",
            message=message,
            actions=[
                {"label": "View Today's Tasks", "action": "navigate", "target": "/tasks"},
                {"label": "Check Metrics", "action": "navigate", "target": "/metrics"},
            ],
            priority=2,
            scheduled_time=now,
            expires_at=now + timedelta(hours=2),
        )
    
    def _generate_midday_checkin(
        self,
        tenant_id: str,
        data: Dict[str, Any],
        now: datetime,
    ) -> Optional[ContextualPrompt]:
        """Generate midday check-in message"""
        
        # Industry-specific midday messages
        if self.business_type == "restaurant":
            title = "Lunch Rush Update"
            message = "How's the lunch service going? Check your covers and kitchen times."
        elif self.business_type == "retail":
            title = "Midday Sales Check"
            message = "Halfway through the day! Let's check how sales are tracking."
        elif self.business_type == "services":
            title = "Midday Progress"
            message = "How are your billable hours looking today?"
        else:
            title = "Midday Check-In"
            message = "Quick check: How's your day progressing?"
        
        # Add performance data
        daily_progress = data.get("daily_progress", {})
        if daily_progress:
            revenue_today = daily_progress.get("revenue", 0)
            if revenue_today > 0:
                message += f"\n\nRevenue so far: ${revenue_today:,.2f}"
        
        return ContextualPrompt(
            id=f"midday-{tenant_id}-{now.date()}",
            type=PromptType.MIDDAY_CHECKIN,
            tone=MessageTone.INFORMATIVE,
            title=title,
            message=message,
            actions=[
                {"label": "View Today's Performance", "action": "navigate", "target": "/analytics?period=today"},
            ],
            priority=3,
            scheduled_time=now,
            expires_at=now + timedelta(hours=2),
        )
    
    def _generate_eod_wrapup(
        self,
        tenant_id: str,
        data: Dict[str, Any],
        now: datetime,
    ) -> Optional[ContextualPrompt]:
        """Generate end-of-day wrap-up message"""
        
        title = "End of Day Summary"
        message = "Great work today! Here's how things went:\n\n"
        
        # Add daily summary
        daily_summary = data.get("daily_summary", {})
        
        if self.business_type == "restaurant":
            covers = daily_summary.get("covers", 0)
            revenue = daily_summary.get("revenue", 0)
            message += f"• Served {covers} customers\n"
            message += f"• Revenue: ${revenue:,.2f}\n"
        elif self.business_type == "retail":
            transactions = daily_summary.get("transactions", 0)
            revenue = daily_summary.get("revenue", 0)
            message += f"• {transactions} transactions\n"
            message += f"• Revenue: ${revenue:,.2f}\n"
        else:
            revenue = daily_summary.get("revenue", 0)
            message += f"• Revenue: ${revenue:,.2f}\n"
        
        # Tasks completed
        tasks_completed = daily_summary.get("tasks_completed", 0)
        if tasks_completed > 0:
            message += f"• {tasks_completed} tasks completed\n"
        
        message += "\nSee you tomorrow!"
        
        return ContextualPrompt(
            id=f"eod-{tenant_id}-{now.date()}",
            type=PromptType.EOD_WRAPUP,
            tone=MessageTone.CELEBRATORY,
            title=title,
            message=message,
            actions=[
                {"label": "View Full Report", "action": "navigate", "target": "/analytics?period=today"},
                {"label": "Plan Tomorrow", "action": "navigate", "target": "/tasks?view=tomorrow"},
            ],
            priority=2,
            scheduled_time=now,
            expires_at=now + timedelta(hours=3),
        )
    
    def _check_critical_alerts(
        self,
        tenant_id: str,
        data: Dict[str, Any],
        now: datetime,
    ) -> List[ContextualPrompt]:
        """Check for critical alerts requiring immediate attention"""
        alerts = []
        
        # Health score dropped significantly
        health_score = data.get("health_score", 0)
        previous_score = data.get("previous_health_score", health_score)
        
        if health_score < 50 and previous_score >= 60:
            alerts.append(ContextualPrompt(
                id=f"alert-health-{tenant_id}-{now.timestamp()}",
                type=PromptType.CRITICAL_ALERT,
                tone=MessageTone.URGENT,
                title="⚠️ Business Health Alert",
                message=f"Your health score dropped from {previous_score} to {health_score}. Let's investigate and take action.",
                actions=[
                    {"label": "View Breakdown", "action": "navigate", "target": "/health"},
                    {"label": "Get Recommendations", "action": "navigate", "target": "/recommendations"},
                ],
                priority=1,
                scheduled_time=now,
                expires_at=now + timedelta(days=1),
            ))
        
        # Cash flow warning
        cash_balance = data.get("cash_balance", 0)
        if cash_balance < 5000:
            alerts.append(ContextualPrompt(
                id=f"alert-cash-{tenant_id}-{now.timestamp()}",
                type=PromptType.CRITICAL_ALERT,
                tone=MessageTone.URGENT,
                title="💰 Low Cash Balance",
                message=f"Cash balance is ${cash_balance:,.2f}. Consider reviewing receivables and upcoming expenses.",
                actions=[
                    {"label": "View Cash Flow", "action": "navigate", "target": "/cashflow"},
                ],
                priority=1,
                scheduled_time=now,
            ))
        
        return alerts
    
    def _check_milestones(
        self,
        tenant_id: str,
        data: Dict[str, Any],
        now: datetime,
    ) -> List[ContextualPrompt]:
        """Check for milestone achievements to celebrate"""
        milestones = []
        
        # Revenue milestones
        monthly_revenue = data.get("monthly_revenue", 0)
        if monthly_revenue >= 100000 and monthly_revenue < 100500:
            milestones.append(ContextualPrompt(
                id=f"milestone-revenue-100k-{tenant_id}",
                type=PromptType.MILESTONE_CELEBRATION,
                tone=MessageTone.CELEBRATORY,
                title="🎉 Milestone Achieved!",
                message="Congratulations! You've hit $100K in monthly revenue!",
                actions=[
                    {"label": "Share Achievement", "action": "share"},
                    {"label": "View Report", "action": "navigate", "target": "/analytics"},
                ],
                priority=1,
                scheduled_time=now,
                expires_at=now + timedelta(days=7),
            ))
        
        # Goal completions
        goals_completed = data.get("recently_completed_goals", [])
        for goal in goals_completed:
            milestones.append(ContextualPrompt(
                id=f"milestone-goal-{goal['id']}",
                type=PromptType.MILESTONE_CELEBRATION,
                tone=MessageTone.CELEBRATORY,
                title="🎯 Goal Completed!",
                message=f"You completed your goal: {goal['title']}",
                actions=[
                    {"label": "Set Next Goal", "action": "navigate", "target": "/goals/new"},
                ],
                priority=2,
                scheduled_time=now,
                expires_at=now + timedelta(days=3),
            ))
        
        return milestones


def create_prompt_generator(
    business_type: str,
    timezone: str = "America/New_York",
    custom_hours: Optional[BusinessHours] = None,
) -> ContextualPromptGenerator:
    """Factory function for creating prompt generator"""
    return ContextualPromptGenerator(business_type, timezone, custom_hours)
