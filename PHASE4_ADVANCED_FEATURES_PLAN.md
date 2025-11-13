# Phase 4: Advanced Features - IMPLEMENTATION PLAN

**Timeline**: Weeks 13-16 (4 weeks)  
**Status**: READY TO START  
**Dependencies**: Phase 3 complete (5/6 tasks)

---

## Overview

Phase 4 focuses on power-user features, advanced analytics, and enterprise capabilities. These features transform Dyocense from a proactive coach into a comprehensive business intelligence platform with collaboration, custom metrics, and predictive analytics.

**Strategic Goals**:

- Enable data-driven decision making with advanced analytics
- Support team collaboration and multi-user workflows
- Provide extensibility through custom metrics and integrations
- Deliver enterprise-ready features for larger SMBs

---

## Task 4.1: Advanced Analytics Dashboard

**Timeline**: Days 1-5 (1 week)  
**Priority**: HIGH  
**Complexity**: Medium

### Features

#### 1.1 Historical Trend Analysis

- **Multi-period comparison**: Compare metrics across custom date ranges
- **Trend visualization**: Line charts, area charts, sparklines
- **Seasonality detection**: Identify weekly/monthly patterns
- **Growth rate calculations**: MoM, QoQ, YoY growth rates
- **Moving averages**: 7-day, 30-day, 90-day SMAs

#### 1.2 Data Export System

- **CSV export**: All analytics data with metadata
- **PDF report generation**: Using weasyprint or headless Chrome
- **Excel export**: Multiple sheets with formatting
- **Scheduled exports**: Daily/weekly email delivery
- **Custom templates**: Branded report templates

#### 1.3 Interactive Drill-Down

- **Click-through navigation**: Click metric → see detailed breakdown
- **Filters & segments**: Filter by date, category, business type
- **Custom date ranges**: "Last 7/30/90 days", "This month", "Custom"
- **Comparison mode**: Side-by-side metric comparison
- **Cohort analysis**: Analyze user segments separately

#### 1.4 Dashboard Customization

- **Widget reordering**: Drag-and-drop dashboard layout
- **Widget visibility**: Show/hide specific metrics
- **Saved views**: Save custom dashboard configurations
- **Dashboard sharing**: Share views with team members
- **Mobile optimization**: Responsive dashboard for tablets/phones

### Implementation

**Backend (packages/agent/analytics.py)**:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Literal
import pandas as pd
import numpy as np
from enum import Enum

class TimeGranularity(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class ComparisonPeriod(str, Enum):
    PREVIOUS_PERIOD = "previous_period"
    PREVIOUS_YEAR = "previous_year"
    AVERAGE = "average"

@dataclass
class TrendData:
    """Historical trend data for a metric."""
    metric_name: str
    data_points: List[Dict[str, Any]]  # [{date, value, label}]
    trend_direction: Literal["up", "down", "stable"]
    change_percentage: float
    moving_average_7d: Optional[float] = None
    moving_average_30d: Optional[float] = None
    seasonality_detected: bool = False
    forecast_next_period: Optional[float] = None

@dataclass
class MetricComparison:
    """Comparison of metric across periods."""
    metric_name: str
    current_period: Dict[str, Any]  # {start_date, end_date, value}
    comparison_period: Dict[str, Any]
    absolute_change: float
    percentage_change: float
    is_improvement: bool
    context: str  # Human-readable explanation

class AdvancedAnalyticsEngine:
    """Advanced analytics and forecasting engine."""
    
    async def get_historical_trend(
        self,
        tenant_id: str,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        granularity: TimeGranularity = TimeGranularity.DAILY
    ) -> TrendData:
        """
        Calculate historical trend with moving averages and seasonality.
        
        Steps:
        1. Fetch raw metric data from database
        2. Aggregate by granularity (daily/weekly/monthly)
        3. Calculate moving averages (7-day, 30-day)
        4. Detect seasonality using FFT or autocorrelation
        5. Forecast next period using simple linear regression
        6. Determine trend direction
        """
        pass
    
    async def compare_periods(
        self,
        tenant_id: str,
        metric_name: str,
        current_start: datetime,
        current_end: datetime,
        comparison_type: ComparisonPeriod
    ) -> MetricComparison:
        """
        Compare metric across two time periods.
        
        Examples:
        - This week vs last week
        - This month vs same month last year
        - Current vs historical average
        """
        pass
    
    async def detect_anomalies(
        self,
        tenant_id: str,
        metric_name: str,
        threshold: float = 2.0  # Standard deviations
    ) -> List[Dict[str, Any]]:
        """
        Detect unusual spikes or drops in metrics.
        
        Uses Z-score method:
        - Calculate mean and std dev over historical period
        - Flag data points > threshold std devs from mean
        """
        pass
    
    async def calculate_cohort_metrics(
        self,
        tenant_id: str,
        cohort_definition: Dict[str, Any],  # e.g., {"business_type": "restaurant"}
        metrics: List[str],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate metrics for specific cohorts.
        
        Useful for:
        - Restaurant-specific analysis
        - Location-based analysis
        - Customer segment analysis
        """
        pass
    
    async def export_to_csv(
        self,
        tenant_id: str,
        metrics: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> bytes:
        """Generate CSV export of analytics data."""
        pass
    
    async def export_to_pdf(
        self,
        tenant_id: str,
        report_config: Dict[str, Any]
    ) -> bytes:
        """Generate PDF report with charts and tables."""
        pass

def create_analytics_engine() -> AdvancedAnalyticsEngine:
    return AdvancedAnalyticsEngine()
```

**Frontend (apps/smb/src/pages/AdvancedAnalytics.tsx)**:

```typescript
interface AnalyticsFilters {
  dateRange: { start: Date; end: Date };
  granularity: 'daily' | 'weekly' | 'monthly';
  metrics: string[];
  comparisonPeriod?: 'previous_period' | 'previous_year' | 'average';
}

interface TrendChartProps {
  data: TrendData;
  showMovingAverage?: boolean;
  showForecast?: boolean;
  interactive?: boolean;
}

function TrendChart({ data, showMovingAverage, showForecast, interactive }: TrendChartProps) {
  // Recharts line chart with:
  // - Main trend line
  // - 7-day moving average (dashed)
  // - 30-day moving average (dotted)
  // - Forecast line (different color)
  // - Anomaly markers (red dots)
  // - Interactive tooltips with drill-down
}

function MetricComparison({ comparison }: { comparison: MetricComparison }) {
  // Side-by-side comparison card:
  // - Current period value
  // - Comparison period value
  // - Change percentage (colored based on is_improvement)
  // - Context text
  // - Mini sparkline
}

export function AdvancedAnalytics() {
  const [filters, setFilters] = useState<AnalyticsFilters>({
    dateRange: { start: subDays(new Date(), 30), end: new Date() },
    granularity: 'daily',
    metrics: ['revenue', 'health_score', 'task_completion'],
  });
  
  // Fetch trend data
  const { data: trends } = useQuery({
    queryKey: ['analytics-trends', filters],
    queryFn: () => fetchTrends(filters),
  });
  
  // Export handlers
  const handleExportCSV = () => {
    // Download CSV file
  };
  
  const handleExportPDF = () => {
    // Generate and download PDF report
  };
  
  return (
    <Container>
      <AnalyticsFilters value={filters} onChange={setFilters} />
      
      <Grid>
        {trends?.map(trend => (
          <Grid.Col span={12} key={trend.metric_name}>
            <TrendChart data={trend} showMovingAverage showForecast interactive />
          </Grid.Col>
        ))}
      </Grid>
      
      <Group mt="xl">
        <Button onClick={handleExportCSV}>Export CSV</Button>
        <Button onClick={handleExportPDF}>Export PDF</Button>
      </Group>
    </Container>
  );
}
```

**API Endpoints**:

- `GET /v1/tenants/{tenant_id}/analytics/trends?metric=revenue&start_date=...&end_date=...&granularity=daily`
- `GET /v1/tenants/{tenant_id}/analytics/compare?metric=revenue&current_start=...&current_end=...&comparison_type=previous_period`
- `GET /v1/tenants/{tenant_id}/analytics/anomalies?metric=revenue&threshold=2.0`
- `POST /v1/tenants/{tenant_id}/analytics/export/csv` (returns file download)
- `POST /v1/tenants/{tenant_id}/analytics/export/pdf` (returns file download)

**Success Criteria**:

- [ ] Historical trends display correctly with moving averages
- [ ] Period comparisons show accurate percentage changes
- [ ] CSV export includes all selected metrics and date ranges
- [ ] PDF report generates with charts and branding
- [ ] Page load time < 2s for 90-day trend
- [ ] Anomaly detection flags unusual data points

---

## Task 4.2: Report Generation & Export System

**Timeline**: Days 6-8 (3 days)  
**Priority**: HIGH  
**Complexity**: Medium

### Features

#### 2.1 Automated Report Generation

- **Report templates**: Pre-built templates for common reports
  - Weekly business summary
  - Monthly performance report
  - Quarterly review
  - Custom ad-hoc reports
- **Dynamic sections**: Include/exclude sections based on data availability
- **Smart insights**: Automatically highlight key findings
- **Visual charts**: Embed charts and graphs in reports

#### 2.2 Scheduled Reports

- **Recurring schedules**: Daily, weekly, monthly, quarterly
- **Custom schedules**: "Every Monday at 8am", "1st of month"
- **Recipient lists**: Email to owner, managers, stakeholders
- **Conditional delivery**: Only send if certain conditions met
- **Timezone handling**: Deliver in recipient's local timezone

#### 2.3 Shareable Report Links

- **Public links**: Generate shareable URLs (no login required)
- **Expiration**: Links expire after 7/30/90 days
- **Access tracking**: See who viewed report and when
- **Password protection**: Optional password for sensitive reports
- **Revoke access**: Disable link anytime

#### 2.4 Report Branding

- **Custom logos**: Upload business logo
- **Color schemes**: Match business brand colors
- **Headers/footers**: Custom text, contact info
- **White-label**: Remove Dyocense branding (enterprise only)

### Implementation

**Backend (packages/agent/report_generator.py)**:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Literal
from jinja2 import Template
import io
from weasyprint import HTML  # For PDF generation

class ReportTemplate(str, Enum):
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_PERFORMANCE = "monthly_performance"
    QUARTERLY_REVIEW = "quarterly_review"
    CUSTOM = "custom"

@dataclass
class ReportConfig:
    """Configuration for report generation."""
    template: ReportTemplate
    title: str
    subtitle: Optional[str] = None
    include_sections: List[str] = None  # ["health_score", "goals", "metrics"]
    date_range: Dict[str, datetime] = None  # {start, end}
    branding: Optional[Dict[str, Any]] = None  # {logo_url, colors, footer}
    format: Literal["html", "pdf", "markdown"] = "html"

@dataclass
class ReportSchedule:
    """Scheduled report configuration."""
    id: str
    tenant_id: str
    config: ReportConfig
    frequency: Literal["daily", "weekly", "monthly", "quarterly"]
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    day_of_month: Optional[int] = None  # 1-31
    time: str = "08:00"  # HH:MM
    timezone: str = "UTC"
    recipients: List[str] = None  # Email addresses
    enabled: bool = True
    next_run: Optional[datetime] = None

@dataclass
class ShareableReport:
    """Shareable report link."""
    id: str
    report_id: str
    tenant_id: str
    share_token: str
    created_at: datetime
    expires_at: datetime
    password_hash: Optional[str] = None
    view_count: int = 0
    last_viewed_at: Optional[datetime] = None

class ReportGenerator:
    """Advanced report generation system."""
    
    async def generate_report(
        self,
        tenant_id: str,
        config: ReportConfig
    ) -> Dict[str, Any]:
        """
        Generate comprehensive business report.
        
        Steps:
        1. Fetch data for all included sections
        2. Calculate metrics and trends
        3. Generate insights using AI
        4. Render template with data
        5. Convert to requested format (HTML/PDF)
        6. Store report in database
        """
        pass
    
    async def create_schedule(
        self,
        tenant_id: str,
        schedule: ReportSchedule
    ) -> ReportSchedule:
        """Create recurring report schedule."""
        pass
    
    async def execute_scheduled_reports(self):
        """
        Background job to execute scheduled reports.
        
        Runs every hour:
        1. Find schedules due to run
        2. Generate reports
        3. Email to recipients
        4. Update next_run timestamp
        """
        pass
    
    async def create_shareable_link(
        self,
        tenant_id: str,
        report_id: str,
        expires_in_days: int = 7,
        password: Optional[str] = None
    ) -> ShareableReport:
        """
        Create shareable public link for report.
        
        Returns URL: /api/v1/public/reports/{share_token}
        """
        pass
    
    async def get_shared_report(
        self,
        share_token: str,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve report via share link.
        
        Validates:
        - Token exists
        - Not expired
        - Password matches (if set)
        
        Tracks view count and last viewed time.
        """
        pass
    
    async def revoke_share_link(
        self,
        tenant_id: str,
        share_token: str
    ) -> bool:
        """Revoke shareable link (delete from database)."""
        pass

def create_report_generator() -> ReportGenerator:
    return ReportGenerator()
```

**Database Schema**:

```sql
-- Table: report_schedules
CREATE TABLE report_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    template VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    config JSONB NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    day_of_week INT,
    day_of_month INT,
    time TIME NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    recipients TEXT[] NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    next_run TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: shareable_reports
CREATE TABLE shareable_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    share_token VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    view_count INT DEFAULT 0,
    last_viewed_at TIMESTAMPTZ,
    revoked BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_shareable_reports_token ON shareable_reports(share_token) WHERE NOT revoked;
CREATE INDEX idx_report_schedules_next_run ON report_schedules(next_run) WHERE enabled;
```

**API Endpoints**:

- `POST /v1/tenants/{tenant_id}/reports/generate` - Generate report on-demand
- `GET /v1/tenants/{tenant_id}/reports` - List all generated reports
- `GET /v1/tenants/{tenant_id}/reports/{report_id}` - Get specific report
- `POST /v1/tenants/{tenant_id}/reports/{report_id}/share` - Create shareable link
- `DELETE /v1/tenants/{tenant_id}/reports/share/{share_token}` - Revoke link
- `GET /v1/public/reports/{share_token}` - Public report access
- `POST /v1/tenants/{tenant_id}/reports/schedules` - Create schedule
- `GET /v1/tenants/{tenant_id}/reports/schedules` - List schedules
- `PUT /v1/tenants/{tenant_id}/reports/schedules/{schedule_id}` - Update schedule
- `DELETE /v1/tenants/{tenant_id}/reports/schedules/{schedule_id}` - Delete schedule

**Success Criteria**:

- [ ] Generate reports in HTML, PDF, and Markdown formats
- [ ] Scheduled reports execute on time (within 5 min window)
- [ ] Email delivery works reliably (>99% success rate)
- [ ] Shareable links expire correctly
- [ ] PDF reports render charts correctly
- [ ] Report generation < 10s for 90-day period

---

## Task 4.3: Multi-User Collaboration & RBAC

**Timeline**: Days 9-12 (4 days)  
**Priority**: HIGH (Deferred from Phase 3)  
**Complexity**: High

### Features

#### 3.1 User Roles & Permissions

- **Owner**: Full access, billing, user management
- **Manager**: Can view all data, create/edit goals/tasks, no billing access
- **Staff**: Task view only, limited metrics, no admin access
- **Custom roles**: Define custom permission sets (enterprise only)

#### 3.2 Team Management

- **Invite users**: Email invitations with role assignment
- **User directory**: List all team members with roles
- **Role changes**: Owner can change user roles
- **Remove users**: Deactivate access without deleting data
- **Audit log**: Track who did what and when

#### 3.3 Collaborative Features

- **Shared dashboards**: Team can see same dashboard
- **Task assignment**: Assign tasks to specific team members
- **Comments**: Team members can comment on goals/tasks
- **Mentions**: @mention users in comments for notifications
- **Activity feed**: See what team members are working on

#### 3.4 Data Access Control

- **Row-level security**: Users see only their assigned data
- **Column-level permissions**: Hide sensitive metrics from staff
- **Dashboard filtering**: Automatic filtering based on role
- **API enforcement**: All endpoints check permissions

### Implementation

**Backend (packages/trust/rbac.py)**:

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Set, Optional
from functools import wraps
from fastapi import HTTPException, Depends

class UserRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    STAFF = "staff"
    CUSTOM = "custom"

class Permission(str, Enum):
    # Goals
    VIEW_GOALS = "goals:view"
    CREATE_GOALS = "goals:create"
    EDIT_GOALS = "goals:edit"
    DELETE_GOALS = "goals:delete"
    
    # Tasks
    VIEW_TASKS = "tasks:view"
    CREATE_TASKS = "tasks:create"
    EDIT_TASKS = "tasks:edit"
    DELETE_TASKS = "tasks:delete"
    ASSIGN_TASKS = "tasks:assign"
    
    # Metrics
    VIEW_METRICS = "metrics:view"
    VIEW_FINANCIAL = "metrics:financial"
    VIEW_BENCHMARKS = "metrics:benchmarks"
    
    # Team
    INVITE_USERS = "team:invite"
    MANAGE_ROLES = "team:roles"
    REMOVE_USERS = "team:remove"
    
    # Billing
    VIEW_BILLING = "billing:view"
    MANAGE_BILLING = "billing:manage"
    
    # Reports
    VIEW_REPORTS = "reports:view"
    CREATE_REPORTS = "reports:create"
    SHARE_REPORTS = "reports:share"

# Permission sets by role
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.OWNER: {p for p in Permission},  # All permissions
    UserRole.MANAGER: {
        Permission.VIEW_GOALS,
        Permission.CREATE_GOALS,
        Permission.EDIT_GOALS,
        Permission.VIEW_TASKS,
        Permission.CREATE_TASKS,
        Permission.EDIT_TASKS,
        Permission.ASSIGN_TASKS,
        Permission.VIEW_METRICS,
        Permission.VIEW_FINANCIAL,
        Permission.VIEW_BENCHMARKS,
        Permission.VIEW_REPORTS,
        Permission.CREATE_REPORTS,
    },
    UserRole.STAFF: {
        Permission.VIEW_TASKS,
        Permission.EDIT_TASKS,  # Only their own
        Permission.VIEW_METRICS,  # Limited metrics
    },
}

@dataclass
class TenantUser:
    """User within a tenant context."""
    id: str
    tenant_id: str
    email: str
    role: UserRole
    custom_permissions: Optional[Set[Permission]] = None
    assigned_to: Optional[List[str]] = None  # Task IDs assigned to this user
    is_active: bool = True
    invited_at: datetime
    joined_at: Optional[datetime] = None

class RBACMiddleware:
    """Role-based access control middleware."""
    
    def has_permission(self, user: TenantUser, permission: Permission) -> bool:
        """Check if user has permission."""
        if user.role == UserRole.CUSTOM and user.custom_permissions:
            return permission in user.custom_permissions
        return permission in ROLE_PERMISSIONS.get(user.role, set())
    
    def can_view_task(self, user: TenantUser, task_id: str) -> bool:
        """Check if user can view specific task."""
        if not self.has_permission(user, Permission.VIEW_TASKS):
            return False
        
        # Staff can only see assigned tasks
        if user.role == UserRole.STAFF:
            return task_id in (user.assigned_to or [])
        
        return True
    
    def can_edit_task(self, user: TenantUser, task_id: str) -> bool:
        """Check if user can edit specific task."""
        if not self.has_permission(user, Permission.EDIT_TASKS):
            return False
        
        # Staff can only edit assigned tasks
        if user.role == UserRole.STAFF:
            return task_id in (user.assigned_to or [])
        
        return True

def require_permission(permission: Permission):
    """Decorator to enforce permission on endpoint."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: TenantUser = Depends(get_current_user), **kwargs):
            rbac = RBACMiddleware()
            if not rbac.has_permission(current_user, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission.value}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage in endpoints:
@router.post("/v1/tenants/{tenant_id}/goals")
@require_permission(Permission.CREATE_GOALS)
async def create_goal(
    tenant_id: str,
    goal_data: GoalCreate,
    current_user: TenantUser = Depends(get_current_user)
):
    # Create goal...
    pass
```

**Database Schema**:

```sql
-- Table: tenant_users
CREATE TABLE tenant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(20) NOT NULL DEFAULT 'staff',
    custom_permissions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    joined_at TIMESTAMPTZ,
    UNIQUE(tenant_id, user_id)
);

-- Table: task_assignments
CREATE TABLE task_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    assigned_by UUID NOT NULL REFERENCES users(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(task_id, user_id)
);

-- Table: audit_log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id) WHERE is_active;
CREATE INDEX idx_task_assignments_user ON task_assignments(user_id);
CREATE INDEX idx_audit_log_tenant ON audit_log(tenant_id, created_at DESC);
```

**Frontend (apps/smb/src/pages/TeamManagement.tsx)**:

```typescript
interface TeamMember {
  id: string;
  email: string;
  name: string;
  role: 'owner' | 'manager' | 'staff';
  avatar?: string;
  joinedAt: string;
  lastActive: string;
}

function TeamManagement() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'manager' | 'staff'>('staff');
  
  const handleInvite = async () => {
    await post(`/v1/tenants/${tenantId}/team/invite`, {
      email: inviteEmail,
      role: inviteRole,
    });
    // Refresh team list
  };
  
  const handleChangeRole = async (userId: string, newRole: string) => {
    await put(`/v1/tenants/${tenantId}/team/${userId}/role`, { role: newRole });
    // Refresh team list
  };
  
  return (
    <Container>
      <Title>Team Management</Title>
      
      <Card>
        <Title order={3}>Invite Team Member</Title>
        <Group>
          <TextInput
            placeholder="email@example.com"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
          />
          <Select
            data={[
              { value: 'manager', label: 'Manager' },
              { value: 'staff', label: 'Staff' },
            ]}
            value={inviteRole}
            onChange={setInviteRole}
          />
          <Button onClick={handleInvite}>Send Invite</Button>
        </Group>
      </Card>
      
      <Table>
        <thead>
          <tr>
            <th>Member</th>
            <th>Role</th>
            <th>Joined</th>
            <th>Last Active</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {members.map(member => (
            <tr key={member.id}>
              <td>
                <Group>
                  <Avatar src={member.avatar} />
                  <div>
                    <Text>{member.name}</Text>
                    <Text size="sm" c="dimmed">{member.email}</Text>
                  </div>
                </Group>
              </td>
              <td>
                <Select
                  value={member.role}
                  onChange={(role) => handleChangeRole(member.id, role)}
                  data={[
                    { value: 'owner', label: 'Owner', disabled: member.role === 'owner' },
                    { value: 'manager', label: 'Manager' },
                    { value: 'staff', label: 'Staff' },
                  ]}
                />
              </td>
              <td>{new Date(member.joinedAt).toLocaleDateString()}</td>
              <td>{formatRelativeTime(member.lastActive)}</td>
              <td>
                <Menu>
                  <Menu.Item onClick={() => handleRemove(member.id)}>Remove</Menu.Item>
                  <Menu.Item onClick={() => handleViewActivity(member.id)}>View Activity</Menu.Item>
                </Menu>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Container>
  );
}
```

**API Endpoints**:

- `POST /v1/tenants/{tenant_id}/team/invite` - Invite user to tenant
- `GET /v1/tenants/{tenant_id}/team` - List team members
- `PUT /v1/tenants/{tenant_id}/team/{user_id}/role` - Change user role
- `DELETE /v1/tenants/{tenant_id}/team/{user_id}` - Remove user from tenant
- `GET /v1/tenants/{tenant_id}/audit-log` - View audit log
- `POST /v1/tenants/{tenant_id}/tasks/{task_id}/assign` - Assign task to user
- `DELETE /v1/tenants/{tenant_id}/tasks/{task_id}/assign/{user_id}` - Unassign task

**Success Criteria**:

- [ ] User invitations sent via email with accept link
- [ ] Role changes take effect immediately
- [ ] Staff users see only their assigned tasks
- [ ] All API endpoints enforce RBAC
- [ ] Audit log captures all sensitive actions
- [ ] Team page loads < 1s for 50 members

---

## Task 4.4: Custom Metrics & KPI Builder

**Timeline**: Days 13-15 (3 days)  
**Priority**: MEDIUM  
**Complexity**: High

### Features

#### 4.1 Custom Metric Definition

- **Formula builder**: Define metrics using formulas (e.g., `revenue / costs`)
- **Data source selection**: Choose from available data tables
- **Aggregations**: SUM, AVG, COUNT, MIN, MAX, STDDEV
- **Filters**: Apply WHERE conditions
- **Time windows**: Rolling 7/30/90 days, MTD, QTD, YTD
- **Validation**: Syntax checking, type validation

#### 4.2 KPI Library

- **Pre-built templates**: 100+ common KPIs
  - Gross margin: `(revenue - COGS) / revenue * 100`
  - Inventory turnover: `COGS / avg_inventory`
  - Customer lifetime value: `avg_order_value * purchase_frequency * avg_lifespan`
  - Net promoter score: `% promoters - % detractors`
- **Industry-specific**: Curated KPIs per business type
- **Save custom KPIs**: Add to personal library
- **Share KPIs**: Share with team or community

#### 4.3 Thresholds & Alerts

- **Target values**: Set goal targets for KPIs
- **Warning thresholds**: Yellow alert if below target
- **Critical thresholds**: Red alert if severely off-target
- **Alert notifications**: Email/SMS when threshold breached
- **Trend alerts**: Alert if metric declining for N consecutive days

#### 4.4 Visualization Options

- **Chart types**: Line, bar, area, gauge, sparkline
- **Color coding**: Green/yellow/red based on thresholds
- **Dashboard placement**: Add custom metrics to dashboard
- **Report inclusion**: Include in automated reports

### Implementation

**Backend (packages/agent/custom_metrics.py)**:

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
import sqlparse
from simpleeval import simple_eval

class MetricAggregation(str, Enum):
    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"
    STDDEV = "STDDEV"

class TimeWindow(str, Enum):
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    MONTH_TO_DATE = "mtd"
    QUARTER_TO_DATE = "qtd"
    YEAR_TO_DATE = "ytd"

@dataclass
class CustomMetricDefinition:
    """User-defined metric."""
    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    formula: str  # e.g., "revenue / costs * 100"
    data_sources: List[str] = None  # Tables used
    aggregation: Optional[MetricAggregation] = None
    time_window: TimeWindow = TimeWindow.LAST_30_DAYS
    filters: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None  # "%", "$", "x", etc.
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    created_by: str = None
    created_at: datetime = None
    is_public: bool = False  # Shareable with community

@dataclass
class MetricValue:
    """Calculated metric value."""
    metric_id: str
    value: float
    formatted_value: str  # e.g., "42.5%", "$1,234"
    status: Literal["good", "warning", "critical", "unknown"]
    trend: Optional[Literal["up", "down", "stable"]] = None
    calculated_at: datetime = None
    metadata: Optional[Dict[str, Any]] = None  # Intermediate values, etc.

class CustomMetricEngine:
    """Engine for custom metric calculations."""
    
    SAFE_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'avg': lambda x: sum(x) / len(x) if x else 0,
    }
    
    async def validate_formula(
        self,
        formula: str,
        data_sources: List[str]
    ) -> Dict[str, Any]:
        """
        Validate metric formula.
        
        Checks:
        1. Syntax is valid Python expression
        2. Only safe functions used
        3. Referenced columns exist in data sources
        4. No SQL injection attempts
        
        Returns: {valid: bool, error: Optional[str], variables: List[str]}
        """
        pass
    
    async def calculate_metric(
        self,
        tenant_id: str,
        definition: CustomMetricDefinition
    ) -> MetricValue:
        """
        Calculate metric value.
        
        Steps:
        1. Fetch data from sources within time window
        2. Apply filters
        3. Apply aggregations
        4. Evaluate formula with simple_eval (safe eval)
        5. Determine status based on thresholds
        6. Calculate trend (compare to previous period)
        """
        pass
    
    async def get_metric_template(
        self,
        template_id: str
    ) -> CustomMetricDefinition:
        """Get pre-built metric template from library."""
        pass
    
    async def list_available_data_sources(
        self,
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        """
        List tables and columns available for custom metrics.
        
        Returns: [{table, columns, sample_count, last_updated}]
        """
        pass
    
    async def create_metric(
        self,
        tenant_id: str,
        definition: CustomMetricDefinition
    ) -> CustomMetricDefinition:
        """Save custom metric definition."""
        pass
    
    async def check_alerts(
        self,
        tenant_id: str,
        metric_id: str,
        current_value: float
    ) -> Optional[Dict[str, Any]]:
        """
        Check if metric breached thresholds.
        
        Returns alert details if threshold breached, else None.
        """
        pass

def create_custom_metric_engine() -> CustomMetricEngine:
    return CustomMetricEngine()
```

**Metric Template Library (packages/agent/metric_templates.py)**:

```python
METRIC_TEMPLATES = {
    "gross_margin": CustomMetricDefinition(
        id="template_gross_margin",
        name="Gross Margin",
        description="Percentage of revenue remaining after COGS",
        formula="(revenue - cogs) / revenue * 100",
        data_sources=["financial"],
        aggregation=MetricAggregation.SUM,
        time_window=TimeWindow.MONTH_TO_DATE,
        unit="%",
        target_value=40.0,
        warning_threshold=35.0,
        critical_threshold=30.0,
    ),
    "inventory_turnover": CustomMetricDefinition(
        id="template_inventory_turnover",
        name="Inventory Turnover",
        description="How many times inventory sold and replaced",
        formula="cogs / ((beginning_inventory + ending_inventory) / 2)",
        data_sources=["financial", "inventory"],
        aggregation=MetricAggregation.SUM,
        time_window=TimeWindow.YEAR_TO_DATE,
        unit="x",
        target_value=6.0,
        warning_threshold=4.0,
        critical_threshold=2.0,
    ),
    "customer_acquisition_cost": CustomMetricDefinition(
        id="template_cac",
        name="Customer Acquisition Cost (CAC)",
        description="Average cost to acquire a new customer",
        formula="marketing_spend / new_customers",
        data_sources=["expenses", "customers"],
        aggregation=MetricAggregation.SUM,
        time_window=TimeWindow.LAST_30_DAYS,
        unit="$",
        target_value=50.0,
        warning_threshold=75.0,
        critical_threshold=100.0,
    ),
    # ... 97 more templates
}
```

**Frontend (apps/smb/src/pages/CustomMetrics.tsx)**:

```typescript
interface FormulaBuilderProps {
  value: string;
  onChange: (formula: string) => void;
  dataSources: DataSource[];
}

function FormulaBuilder({ value, onChange, dataSources }: FormulaBuilderProps) {
  // Visual formula builder:
  // - Drag columns from data sources
  // - Select operators (+, -, *, /, etc.)
  // - Add functions (SUM, AVG, COUNT)
  // - Live validation
  // - Syntax highlighting
  
  return (
    <Box>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="revenue / costs * 100"
        minRows={3}
      />
      <Stack mt="sm">
        <Text size="sm" fw={600}>Available Variables:</Text>
        {dataSources.map(ds => (
          <Chip key={ds.name} onClick={() => insertVariable(ds.name)}>
            {ds.name}
          </Chip>
        ))}
      </Stack>
      <Stack mt="sm">
        <Text size="sm" fw={600}>Functions:</Text>
        {['SUM', 'AVG', 'COUNT', 'MIN', 'MAX'].map(fn => (
          <Button size="xs" key={fn} onClick={() => insertFunction(fn)}>
            {fn}
          </Button>
        ))}
      </Stack>
    </Box>
  );
}

function CustomMetricBuilder() {
  const [definition, setDefinition] = useState<CustomMetricDefinition>({
    name: '',
    formula: '',
    data_sources: [],
    time_window: '30d',
  });
  
  const handleSave = async () => {
    await post(`/v1/tenants/${tenantId}/metrics/custom`, definition);
    // Navigate to dashboard
  };
  
  return (
    <Container>
      <Title>Create Custom Metric</Title>
      
      <Stack>
        <TextInput
          label="Metric Name"
          placeholder="e.g., Gross Profit Margin"
          value={definition.name}
          onChange={(e) => setDefinition({ ...definition, name: e.target.value })}
        />
        
        <Textarea
          label="Description"
          placeholder="What does this metric measure?"
          value={definition.description}
          onChange={(e) => setDefinition({ ...definition, description: e.target.value })}
        />
        
        <FormulaBuilder
          value={definition.formula}
          onChange={(formula) => setDefinition({ ...definition, formula })}
          dataSources={availableDataSources}
        />
        
        <Select
          label="Time Window"
          data={[
            { value: '7d', label: 'Last 7 days' },
            { value: '30d', label: 'Last 30 days' },
            { value: 'mtd', label: 'Month to date' },
            { value: 'ytd', label: 'Year to date' },
          ]}
          value={definition.time_window}
          onChange={(tw) => setDefinition({ ...definition, time_window: tw })}
        />
        
        <NumberInput
          label="Target Value"
          placeholder="e.g., 40.0"
          value={definition.target_value}
          onChange={(val) => setDefinition({ ...definition, target_value: val })}
        />
        
        <Group>
          <Button onClick={handleSave}>Save Metric</Button>
          <Button variant="default" onClick={() => navigate('/metrics')}>
            Cancel
          </Button>
        </Group>
      </Stack>
    </Container>
  );
}
```

**API Endpoints**:

- `POST /v1/tenants/{tenant_id}/metrics/custom` - Create custom metric
- `GET /v1/tenants/{tenant_id}/metrics/custom` - List custom metrics
- `GET /v1/tenants/{tenant_id}/metrics/custom/{metric_id}` - Get metric definition
- `PUT /v1/tenants/{tenant_id}/metrics/custom/{metric_id}` - Update metric
- `DELETE /v1/tenants/{tenant_id}/metrics/custom/{metric_id}` - Delete metric
- `POST /v1/tenants/{tenant_id}/metrics/custom/{metric_id}/calculate` - Calculate value
- `GET /v1/tenants/{tenant_id}/metrics/templates` - List metric templates
- `GET /v1/tenants/{tenant_id}/metrics/data-sources` - List available data sources

**Success Criteria**:

- [ ] Formula validation catches syntax errors
- [ ] Metric calculations return accurate values
- [ ] Thresholds trigger alerts correctly
- [ ] Custom metrics display on dashboard
- [ ] Metric templates library has 100+ options
- [ ] Calculation performance < 2s for complex formulas

---

## Task 4.5: Advanced Forecasting Engine

**Timeline**: Days 16-18 (3 days)  
**Priority**: MEDIUM  
**Complexity**: High

### Features

#### 5.1 Predictive Analytics

- **Trend forecasting**: Predict next 7/30/90 days based on historical trends
- **Seasonality detection**: Identify weekly/monthly/yearly patterns
- **Confidence intervals**: Show prediction range (low, high, likely)
- **What-if scenarios**: "What if revenue drops 10%?"
- **Goal projections**: "Will I hit my revenue goal by end of quarter?"

#### 5.2 Anomaly Detection

- **Statistical methods**: Z-score, IQR, moving average deviation
- **ML-based detection**: Isolation Forest, DBSCAN
- **Real-time alerts**: Notify immediately on anomaly
- **Anomaly explanations**: "Revenue 30% below normal for Tuesday"
- **False positive reduction**: Learn from user feedback

#### 5.3 Scenario Modeling

- **Best/worst/likely cases**: Model multiple scenarios
- **Sensitivity analysis**: How sensitive is outcome to input changes?
- **Resource optimization**: Optimal staffing, inventory levels
- **Risk assessment**: Probability of missing goals

### Implementation

**Backend (packages/agent/forecasting.py)**:

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Literal
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.ensemble import IsolationForest

@dataclass
class Forecast:
    """Forecast prediction."""
    metric_name: str
    forecast_date: datetime
    predicted_value: float
    confidence_interval: Dict[str, float]  # {low, high}
    confidence_level: float  # 0.95 = 95% confidence
    method: str  # "linear", "exponential_smoothing", "arima"
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Anomaly:
    """Detected anomaly."""
    metric_name: str
    detected_at: datetime
    value: float
    expected_value: float
    deviation_pct: float
    severity: Literal["low", "medium", "high"]
    explanation: str
    confidence: float

@dataclass
class Scenario:
    """What-if scenario."""
    name: str
    assumptions: Dict[str, Any]  # {revenue_growth: -0.10}
    projections: Dict[str, float]  # {revenue: 45000, profit: 12000}
    probability: Optional[float] = None
    risk_level: Optional[Literal["low", "medium", "high"]] = None

class ForecastingEngine:
    """Advanced forecasting and prediction engine."""
    
    async def forecast_metric(
        self,
        tenant_id: str,
        metric_name: str,
        forecast_days: int = 30,
        method: Literal["auto", "linear", "exponential", "arima"] = "auto"
    ) -> List[Forecast]:
        """
        Forecast metric for next N days.
        
        Methods:
        - linear: Simple linear regression on historical data
        - exponential: Exponential smoothing (Holt-Winters)
        - arima: ARIMA model for complex patterns
        - auto: Automatically select best method
        
        Steps:
        1. Fetch historical data (90-365 days)
        2. Decompose into trend, seasonality, residual
        3. Fit model based on method
        4. Generate predictions with confidence intervals
        5. Validate predictions against holdout set
        """
        pass
    
    async def detect_seasonality(
        self,
        tenant_id: str,
        metric_name: str
    ) -> Dict[str, Any]:
        """
        Detect seasonal patterns.
        
        Returns:
        - has_weekly_seasonality: bool
        - has_monthly_seasonality: bool
        - has_yearly_seasonality: bool
        - seasonal_strength: float (0-1)
        - peak_days: List[int] (days of week with peaks)
        - peak_dates: List[int] (days of month with peaks)
        """
        pass
    
    async def detect_anomalies(
        self,
        tenant_id: str,
        metric_name: str,
        method: Literal["zscore", "iqr", "isolation_forest"] = "isolation_forest"
    ) -> List[Anomaly]:
        """
        Detect anomalies in metric time series.
        
        Methods:
        - zscore: Flag values >2-3 standard deviations from mean
        - iqr: Flag values outside 1.5 * IQR
        - isolation_forest: ML-based outlier detection
        """
        pass
    
    async def run_scenario(
        self,
        tenant_id: str,
        scenario: Scenario
    ) -> Scenario:
        """
        Run what-if scenario.
        
        Example:
        scenario = {
            "name": "10% Revenue Drop",
            "assumptions": {"revenue_growth": -0.10},
        }
        
        Returns scenario with projections filled in.
        """
        pass
    
    async def predict_goal_achievement(
        self,
        tenant_id: str,
        goal_id: str
    ) -> Dict[str, Any]:
        """
        Predict likelihood of achieving goal by deadline.
        
        Returns:
        - probability: float (0-1)
        - projected_value: float
        - target_value: float
        - days_remaining: int
        - on_track: bool
        - recommendation: str
        """
        pass

def create_forecasting_engine() -> ForecastingEngine:
    return ForecastingEngine()
```

**API Endpoints**:

- `GET /v1/tenants/{tenant_id}/forecast?metric=revenue&days=30&method=auto`
- `GET /v1/tenants/{tenant_id}/forecast/seasonality?metric=revenue`
- `GET /v1/tenants/{tenant_id}/forecast/anomalies?metric=revenue&method=isolation_forest`
- `POST /v1/tenants/{tenant_id}/forecast/scenario` - Run what-if scenario
- `GET /v1/tenants/{tenant_id}/goals/{goal_id}/predict` - Predict goal achievement

**Success Criteria**:

- [ ] Forecasts within 15% MAPE (Mean Absolute Percentage Error)
- [ ] Seasonality detection accuracy >80%
- [ ] Anomaly detection <10% false positive rate
- [ ] Scenario modeling returns results < 3s
- [ ] Goal predictions update daily

---

## Task 4.6: Integration Hub & API Access

**Timeline**: Days 19-20 (2 days)  
**Priority**: LOW  
**Complexity**: Medium

### Features

#### 6.1 External Integrations

- **Accounting**: QuickBooks, Xero, FreshBooks
- **Payments**: Stripe, Square, PayPal
- **POS**: Toast, Clover, Lightspeed
- **Inventory**: TradeGecko, Cin7
- **CRM**: HubSpot, Salesforce
- **OAuth flow**: Secure authentication

#### 6.2 Webhook System

- **Event triggers**: Goal completed, alert triggered, report generated
- **Custom webhooks**: User-defined webhook URLs
- **Payload customization**: Select fields to include
- **Retry logic**: Exponential backoff on failures
- **Webhook logs**: Track deliveries and failures

#### 6.3 REST API for Power Users

- **API keys**: Generate and manage API keys
- **Rate limiting**: 1000 req/hour for basic, 10000 for enterprise
- **Documentation**: OpenAPI/Swagger docs
- **SDKs**: Python, Node.js, curl examples
- **Scoped permissions**: API keys with specific permissions

### Implementation

**Backend (packages/connectors/integration_hub.py)**:

```python
@dataclass
class Integration:
    """External integration configuration."""
    id: str
    tenant_id: str
    provider: str  # "quickbooks", "stripe", "square"
    auth_type: Literal["oauth", "api_key", "basic"]
    credentials: Dict[str, str]  # Encrypted
    enabled: bool = True
    last_sync: Optional[datetime] = None
    sync_frequency: str = "hourly"  # "realtime", "hourly", "daily"

@dataclass
class WebhookConfig:
    """Webhook configuration."""
    id: str
    tenant_id: str
    url: str
    events: List[str]  # ["goal.completed", "alert.triggered"]
    secret: str  # For signature verification
    enabled: bool = True
    retry_count: int = 3
    last_triggered: Optional[datetime] = None
    failure_count: int = 0

class IntegrationHub:
    """Manage external integrations."""
    
    async def connect_integration(
        self,
        tenant_id: str,
        provider: str,
        credentials: Dict[str, str]
    ) -> Integration:
        """
        Connect external integration.
        
        Steps for OAuth:
        1. Redirect user to provider's OAuth page
        2. User authorizes access
        3. Receive callback with auth code
        4. Exchange code for access token
        5. Store encrypted credentials
        """
        pass
    
    async def sync_data(
        self,
        tenant_id: str,
        integration_id: str
    ) -> Dict[str, Any]:
        """
        Sync data from integration.
        
        Returns: {records_synced, last_sync, next_sync}
        """
        pass
    
    async def trigger_webhook(
        self,
        tenant_id: str,
        event: str,
        payload: Dict[str, Any]
    ):
        """
        Trigger webhooks for event.
        
        Steps:
        1. Find all webhooks listening for event
        2. Build payload
        3. Sign payload with secret
        4. POST to webhook URL
        5. Retry on failure with exponential backoff
        6. Log result
        """
        pass

@router.post("/v1/integrations/{provider}/connect")
async def connect_integration(
    provider: str,
    credentials: Dict[str, str],
    current_user: TenantUser = Depends(get_current_user)
):
    """Connect external integration."""
    pass
```

**API Key Management (packages/trust/api_keys.py)**:

```python
@dataclass
class APIKey:
    """API key for programmatic access."""
    id: str
    tenant_id: str
    name: str
    key_hash: str  # Never store plain key
    key_prefix: str  # First 8 chars for identification
    permissions: List[Permission]
    rate_limit: int = 1000  # Requests per hour
    expires_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    last_used: Optional[datetime] = None

class APIKeyManager:
    """Manage API keys."""
    
    async def create_api_key(
        self,
        tenant_id: str,
        name: str,
        permissions: List[Permission],
        expires_in_days: Optional[int] = None
    ) -> Tuple[str, APIKey]:
        """
        Create API key.
        
        Returns: (plain_key, api_key_record)
        Plain key shown only once at creation.
        """
        # Generate random key
        plain_key = f"dk_{''.join(random.choices(string.ascii_letters + string.digits, k=32))}"
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        
        # Store hashed key
        api_key = APIKey(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            key_hash=key_hash,
            key_prefix=plain_key[:8],
            permissions=permissions,
            created_at=datetime.now(),
        )
        
        return plain_key, api_key
    
    async def verify_api_key(
        self,
        plain_key: str
    ) -> Optional[APIKey]:
        """Verify API key and return associated record."""
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        # Fetch from database
        return api_key_record

# Dependency for API key auth
async def get_api_key(
    api_key: str = Header(..., alias="X-API-Key")
) -> APIKey:
    manager = APIKeyManager()
    key_record = await manager.verify_api_key(api_key)
    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key_record
```

**API Endpoints**:

- `POST /v1/integrations/{provider}/connect` - Connect integration
- `GET /v1/integrations` - List connected integrations
- `DELETE /v1/integrations/{integration_id}` - Disconnect integration
- `POST /v1/integrations/{integration_id}/sync` - Trigger manual sync
- `POST /v1/webhooks` - Create webhook
- `GET /v1/webhooks` - List webhooks
- `DELETE /v1/webhooks/{webhook_id}` - Delete webhook
- `POST /v1/api-keys` - Create API key
- `GET /v1/api-keys` - List API keys
- `DELETE /v1/api-keys/{key_id}` - Revoke API key

**Success Criteria**:

- [ ] OAuth flow works for QuickBooks and Stripe
- [ ] Data sync imports records correctly
- [ ] Webhooks deliver within 5 seconds
- [ ] Webhook retry logic works on failures
- [ ] API key auth works on all endpoints
- [ ] Rate limiting enforces limits correctly
- [ ] OpenAPI docs auto-generated and accurate

---

## Phase 4 Summary

### Code Estimates

- **Total Lines**: ~6,000 lines
  - Backend Python: ~4,500 lines
  - Frontend TypeScript/React: ~1,500 lines
- **New Files**: ~20
- **API Endpoints**: ~35 new endpoints
- **Database Tables**: 8 new tables

### Technology Stack

- **Analytics**: pandas, numpy, statsmodels
- **Forecasting**: ARIMA, Exponential Smoothing, scikit-learn
- **PDF Generation**: weasyprint or puppeteer
- **Formula Evaluation**: simpleeval (safe eval)
- **Webhooks**: aiohttp for async HTTP
- **OAuth**: authlib for OAuth flows

### Key Achievements

✅ Advanced analytics with forecasting  
✅ Automated report generation and scheduling  
✅ Multi-user collaboration with RBAC (completes Phase 3)  
✅ Custom metrics and KPI builder  
✅ Predictive analytics with anomaly detection  
✅ Integration framework and API access  

### Enterprise-Ready Features

- Role-based access control
- Team collaboration
- Custom metrics
- API access
- Scheduled reports
- Advanced forecasting

### Next Steps After Phase 4

- **Phase 5: Mobile App** (iOS/Android native apps)
- **Phase 6: Multi-Location Support** (Franchise management)
- **Phase 7: AI Copilot** (Voice assistant, conversational AI)
- **Security Hardening** (Complete Task 3.5, penetration testing, compliance)

---

**Phase 4 Start Date**: Week 13  
**Phase 4 End Date**: Week 16  
**Ready for**: Enterprise beta testing, security audit
