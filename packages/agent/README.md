# Coach V6 Enhanced AI Templates

Comprehensive recommendation template system with GPT-4 integration for generating contextual, actionable business recommendations.

## Overview

The enhanced template system provides 25+ recommendation templates across 6 business domains:

1. **Cash Flow & Liquidity** (5 templates)
2. **Inventory Management** (3 templates)
3. **Revenue Growth** (3 templates)
4. **Profitability** (2 templates)
5. **Operations Efficiency** (2 templates)
6. **Strategic Growth** (2 templates)

## Architecture

```
packages/agent/
├── coach_templates.py          # Template definitions and triggers
├── gpt4_recommendations.py     # GPT-4 integration layer
└── __init__.py                 # Package exports

services/smb_gateway/
└── recommendations_service.py  # Service using templates
```

## Components

### 1. Template System (`coach_templates.py`)

**RecommendationTemplate** - Core template structure:

```python
class RecommendationTemplate:
    trigger: TemplateTrigger           # What triggers this recommendation
    category: RecommendationCategory   # Business domain
    priority_logic: str                # Python expression for priority
    title_template: str                # Template for title
    description_template: str          # Template for description
    reasoning_template: str            # Template for reasoning
    actions: List[Dict]                # Action templates
    data_requirements: List[str]       # Required data fields
```

**Key Features:**

- Declarative template definitions
- Data-driven trigger evaluation
- Dynamic priority calculation
- Template string formatting with business data
- 25+ pre-built templates covering common scenarios

### 2. GPT-4 Integration (`gpt4_recommendations.py`)

**GPT4RecommendationGenerator** - Natural language generation:

- Contextual recommendation generation
- Business-specific insights
- Personalized tone and language
- Falls back to templates if GPT-4 unavailable

**RecommendationEnricher** - Enhance recommendations:

- Enrich template-based recommendations with GPT-4
- Generate follow-up insights for chat conversations
- Maintain consistency while adding personality

### 3. Recommendations Service (`recommendations_service.py`)

Enhanced service with template support:

```python
service = CoachRecommendationsService(
    tenant_id="tenant-123",
    use_gpt4=True  # Enable GPT-4 enhancement
)

recommendations = await service.generate_recommendations(
    health_score=65,
    health_breakdown={...},
    connector_data={...}
)
```

## Template Categories

### Cash Flow & Liquidity

1. **Negative Cash Flow Projection** (Critical)
   - Triggers: `days_until_negative < 21`
   - Actions: Accelerate collections, delay expenses, explore financing

2. **Low Cash Balance** (Critical/Important)
   - Triggers: `cash_balance < min_safe_balance`
   - Actions: Transfer funds, reduce spending

3. **Overdue Receivables** (Important)
   - Triggers: `overdue_amount > 5000 and overdue_days_avg > 30`
   - Actions: Send reminders, offer discounts, call customers

4. **High Burn Rate** (Important)
   - Actions: Audit expenses, renegotiate contracts

5. **Payment Delays** (Suggestion)
   - Actions: Improve invoicing, automate reminders

### Inventory Management

1. **Aging Inventory** (Important)
   - Triggers: `aging_items_count > 10 and aging_days > 90`
   - Actions: Run clearance, create bundles, write off

2. **Stockout Risk** (Critical)
   - Triggers: `at_risk_items_count > 0`
   - Actions: Place urgent reorder, enable backorders

3. **Slow-Moving Items** (Suggestion)
   - Triggers: `slow_moving_count > 5`
   - Actions: Reduce reorder quantities, discontinue items

### Revenue Growth

1. **Revenue Decline** (Important/Critical)
   - Triggers: `revenue_change_percent < -10`
   - Actions: Win-back campaign, analyze losses, launch promotion

2. **Average Order Value Decline** (Important)
   - Triggers: `aov_change_percent < -5`
   - Actions: Free shipping threshold, bundles, upsells

3. **Seasonal Opportunity** (Suggestion)
   - Triggers: `seasonal_uplift_potential > 20`
   - Actions: Stock bestsellers, marketing campaign, seasonal bundles

### Profitability

1. **Margin Erosion** (Important/Critical)
   - Triggers: `margin_change < -3`
   - Actions: Review supplier pricing, adjust pricing, discontinue low-margin items

2. **Cost Spike** (Important)
   - Triggers: `cost_increase_percent > 15`
   - Actions: Audit expenses, negotiate rates

### Operations Efficiency

1. **Task Backlog** (Important)
   - Triggers: `overdue_tasks > 10`
   - Actions: Prioritize critical tasks, delegate, automate

2. **Capacity Constraint** (Important)
   - Triggers: `capacity_utilization > 90`
   - Actions: Hire part-time help, defer projects

### Strategic Growth

1. **Expansion Ready** (Suggestion)
   - Triggers: `growth_readiness_score > 75`
   - Actions: Explore markets, expand channels, invest in marketing

2. **Product Line Extension** (Suggestion)
   - Triggers: `product_opportunity_score > 60`
   - Actions: Survey customers, research competitors, calculate ROI

## Usage

### Basic Usage (Templates Only)

```python
from services.smb_gateway.recommendations_service import CoachRecommendationsService

service = CoachRecommendationsService(tenant_id="tenant-123")

recommendations = await service.generate_recommendations(
    health_score=65,
    health_breakdown={
        "cash_flow": 55,
        "operations": 68,
        "revenue": 72,
        "profitability": 65,
    },
    connector_data={
        "cash_balance": 12000,
        "burn_rate": 800,
        "outstanding_receivables": 15000,
    }
)

for rec in recommendations:
    print(f"{rec.priority}: {rec.title}")
    print(f"  {rec.description}")
    print(f"  Reasoning: {rec.reasoning}")
    for action in rec.actions:
        print(f"  - {action.label}")
```

### Enhanced with GPT-4

```python
import os

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = "sk-..."

service = CoachRecommendationsService(
    tenant_id="tenant-123",
    use_gpt4=True  # Enable GPT-4 enhancement
)

# GPT-4 will enhance titles, descriptions, and reasoning
recommendations = await service.generate_recommendations(
    health_score=65,
    health_breakdown={...},
    connector_data={...}
)
```

### Custom Template

```python
from packages.agent.coach_templates import (
    RecommendationTemplate,
    TemplateTrigger,
    RecommendationCategory,
)

custom_template = RecommendationTemplate(
    trigger=TemplateTrigger.CUSTOM,
    category=RecommendationCategory.CASH_FLOW,
    priority_logic="data.get('custom_metric', 0) > 100",
    title_template="Custom alert: {custom_metric}",
    description_template="Your custom metric is {custom_metric}",
    reasoning_template="Based on {data_source} analysis",
    actions=[
        {
            "label": "Take action on {item_count} items",
            "description": "Review and address items",
            "buttonText": "Review Items",
        }
    ],
    data_requirements=["custom_metric", "data_source", "item_count"],
)
```

## Data Requirements

Each template specifies required data fields. The service maps connector data to these fields:

### Cash Flow Data

- `cash_balance`: Current bank balance
- `burn_rate`: Daily/weekly burn rate
- `days_until_negative`: Projected days until negative balance
- `outstanding_receivables`: Total AR
- `overdue_count`: Number of overdue invoices
- `overdue_amount`: Dollar amount overdue
- `overdue_days_avg`: Average days overdue

### Inventory Data

- `aging_items_count`: Number of aging items
- `aging_days`: Days in inventory threshold
- `capital_tied`: Dollar value in aging inventory
- `turnover_ratio`: Inventory turnover ratio
- `at_risk_items_count`: Items at risk of stockout
- `slow_moving_count`: Number of slow-moving items

### Revenue Data

- `current_revenue`: Current period revenue
- `previous_revenue`: Previous period revenue
- `revenue_change_percent`: Percent change
- `aov_change_percent`: Average order value change
- `seasonal_uplift_potential`: Seasonal growth opportunity

### Operations Data

- `overdue_tasks`: Number of overdue tasks
- `completion_rate`: Task completion percentage
- `capacity_utilization`: Percent of capacity used
- `backlog_growth_rate`: Rate of backlog growth

## GPT-4 Configuration

Set environment variable for GPT-4:

```bash
export OPENAI_API_KEY="sk-your-key"
```

Or pass directly:

```python
from packages.agent.gpt4_recommendations import GPT4RecommendationGenerator

generator = GPT4RecommendationGenerator(
    api_key="sk-your-key",
    model="gpt-4"  # or "gpt-4-turbo"
)
```

## Priority Logic

Templates use Python expressions for priority calculation:

- **Critical**: `days_until_negative < 14` or `severity_score > 7`
- **Important**: `days_until_negative < 30` or `severity_score > 4`
- **Suggestion**: Default for growth opportunities

## Testing

Test template matching:

```python
from packages.agent.coach_templates import get_triggered_templates

data = {
    "days_until_negative": 12,
    "cash_balance": 8000,
    "overdue_amount": 15000,
    "severity_score": 8,
}

templates = get_triggered_templates(data)
print(f"Triggered {len(templates)} templates")
for template in templates:
    print(f"  - {template.trigger.value} ({template.category.value})")
```

## Extending Templates

### Add New Template

1. Define trigger in `TemplateTrigger` enum
2. Create `RecommendationTemplate` instance
3. Add to appropriate template list (e.g., `CASH_FLOW_TEMPLATES`)
4. Template automatically included in `ALL_TEMPLATES`

### Add New Category

1. Add to `RecommendationCategory` enum
2. Create new template list (e.g., `MARKETING_TEMPLATES`)
3. Add to `ALL_TEMPLATES` concatenation

## Performance

- Template evaluation: O(n) where n = number of templates
- Typical: 25-30 templates evaluated in <1ms
- GPT-4 generation: ~1-2 seconds per recommendation
- Recommendation: Use templates for real-time, GPT-4 for batch/background

## Future Enhancements

1. **Machine Learning Priority**: Learn from feedback to adjust priorities
2. **A/B Testing**: Test different phrasings and actions
3. **Industry-Specific Templates**: Restaurants, retail, services
4. **Multi-Language**: Generate recommendations in multiple languages
5. **Historical Context**: Reference past recommendations and outcomes

## Dependencies

```python
# Required
pydantic>=2.0.0

# Optional (for GPT-4)
openai>=1.0.0
```

Install:

```bash
pip install pydantic
pip install openai  # Optional
```

## License

Part of Dyocense platform - Internal use only
