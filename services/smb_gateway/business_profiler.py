"""
Dynamic Business Profiler

Automatically detects business type and industry from:
1. Tenant profile metadata
2. Connected data patterns
3. Data schema analysis
"""
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class BusinessProfile:
    """Detected business profile with industry-specific terminology"""
    
    def __init__(
        self,
        industry: str,
        business_type: str,
        terminology: Dict[str, str],
        metrics_focus: List[str],
        recommended_analyses: List[str]
    ):
        self.industry = industry
        self.business_type = business_type
        self.terminology = terminology
        self.metrics_focus = metrics_focus
        self.recommended_analyses = recommended_analyses
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "industry": self.industry,
            "business_type": self.business_type,
            "terminology": self.terminology,
            "metrics_focus": self.metrics_focus,
            "recommended_analyses": self.recommended_analyses
        }


class BusinessProfiler:
    """Detect and profile business type dynamically"""
    
    # Industry profiles with terminology mappings
    INDUSTRY_PROFILES = {
        "retail": {
            "keywords": ["product", "sku", "inventory", "store", "shop", "retail", "merchandise"],
            "terminology": {
                "items": "products",
                "transaction": "sale",
                "customer": "shopper",
                "value": "revenue"
            },
            "metrics_focus": ["inventory_turnover", "sales_velocity", "basket_size"],
            "recommended_analyses": ["inventory_optimization", "demand_forecasting", "abc_analysis"]
        },
        "ecommerce": {
            "keywords": ["order", "cart", "shipping", "online", "ecommerce", "marketplace"],
            "terminology": {
                "items": "products",
                "transaction": "order",
                "customer": "buyer",
                "value": "gmv"
            },
            "metrics_focus": ["conversion_rate", "cart_abandonment", "shipping_efficiency"],
            "recommended_analyses": ["funnel_analysis", "cohort_retention", "pricing_optimization"]
        },
        "saas": {
            "keywords": ["subscription", "mrr", "arr", "churn", "trial", "user", "license"],
            "terminology": {
                "items": "subscriptions",
                "transaction": "renewal",
                "customer": "subscriber",
                "value": "mrr"
            },
            "metrics_focus": ["mrr_growth", "churn_rate", "ltv_cac_ratio"],
            "recommended_analyses": ["cohort_retention", "expansion_revenue", "churn_prediction"]
        },
        "restaurant": {
            "keywords": ["menu", "dish", "ingredient", "table", "reservation", "kitchen", "food"],
            "terminology": {
                "items": "menu items",
                "transaction": "order",
                "customer": "diner",
                "value": "check_average"
            },
            "metrics_focus": ["table_turnover", "food_cost_percentage", "labor_cost"],
            "recommended_analyses": ["menu_engineering", "ingredient_optimization", "demand_forecasting"]
        },
        "healthcare": {
            "keywords": ["patient", "appointment", "medical", "clinic", "hospital", "treatment"],
            "terminology": {
                "items": "services",
                "transaction": "appointment",
                "customer": "patient",
                "value": "billing"
            },
            "metrics_focus": ["patient_satisfaction", "wait_times", "utilization_rate"],
            "recommended_analyses": ["capacity_planning", "patient_flow", "resource_allocation"]
        },
        "manufacturing": {
            "keywords": ["production", "raw_material", "assembly", "batch", "factory", "plant"],
            "terminology": {
                "items": "components",
                "transaction": "production_run",
                "customer": "client",
                "value": "output_value"
            },
            "metrics_focus": ["oee", "yield_rate", "defect_rate"],
            "recommended_analyses": ["production_optimization", "quality_control", "supply_chain"]
        },
        "services": {
            "keywords": ["project", "billable", "consulting", "service", "client", "engagement"],
            "terminology": {
                "items": "services",
                "transaction": "engagement",
                "customer": "client",
                "value": "revenue"
            },
            "metrics_focus": ["utilization_rate", "billable_ratio", "project_margin"],
            "recommended_analyses": ["resource_planning", "profitability_analysis", "capacity_forecasting"]
        }
    }
    
    @classmethod
    def detect_from_metadata(cls, tenant_metadata: Dict[str, Any]) -> Optional[BusinessProfile]:
        """
        Detect business profile from tenant metadata
        
        Args:
            tenant_metadata: Tenant profile data with industry, business_type, etc.
        
        Returns:
            BusinessProfile or None if cannot detect
        """
        # Check explicit industry/business_type in metadata
        explicit_industry = tenant_metadata.get("industry", "").lower()
        explicit_type = tenant_metadata.get("business_type", "").lower()
        
        # Try explicit match first
        for industry, profile in cls.INDUSTRY_PROFILES.items():
            if industry in explicit_industry or industry in explicit_type:
                return BusinessProfile(
                    industry=industry,
                    business_type=explicit_type or industry,
                    terminology=profile["terminology"],
                    metrics_focus=profile["metrics_focus"],
                    recommended_analyses=profile["recommended_analyses"]
                )
        
        return None
    
    @classmethod
    def detect_from_data_patterns(cls, data_samples: Dict[str, List[Dict[str, Any]]]) -> Optional[BusinessProfile]:
        """
        Detect business profile by analyzing data schema and field names
        
        Args:
            data_samples: Sample records from orders, inventory, customers, etc.
        
        Returns:
            BusinessProfile or None if cannot detect
        """
        # Collect all field names from data
        all_fields = set()
        
        for data_type, records in data_samples.items():
            if records and len(records) > 0:
                all_fields.update(records[0].keys())
        
        # Score each industry based on keyword matches
        industry_scores = {}
        
        for industry, profile in cls.INDUSTRY_PROFILES.items():
            score = 0
            for keyword in profile["keywords"]:
                # Check if keyword appears in any field name
                for field in all_fields:
                    if keyword in field.lower():
                        score += 1
            
            if score > 0:
                industry_scores[industry] = score
        
        # Select industry with highest score
        if industry_scores:
            detected_industry = max(industry_scores, key=industry_scores.get)
            profile = cls.INDUSTRY_PROFILES[detected_industry]
            
            logger.info(f"[BusinessProfiler] Detected industry: {detected_industry} (score: {industry_scores[detected_industry]})")
            
            return BusinessProfile(
                industry=detected_industry,
                business_type=detected_industry,
                terminology=profile["terminology"],
                metrics_focus=profile["metrics_focus"],
                recommended_analyses=profile["recommended_analyses"]
            )
        
        return None
    
    @classmethod
    def get_profile(
        cls,
        tenant_metadata: Optional[Dict[str, Any]] = None,
        data_samples: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> BusinessProfile:
        """
        Get business profile using multiple detection methods
        
        Falls back to generic "general" profile if cannot detect specific industry
        """
        # Try metadata first
        if tenant_metadata:
            profile = cls.detect_from_metadata(tenant_metadata)
            if profile:
                logger.info(f"[BusinessProfiler] Profile from metadata: {profile.industry}")
                return profile
        
        # Try data pattern detection
        if data_samples:
            profile = cls.detect_from_data_patterns(data_samples)
            if profile:
                logger.info(f"[BusinessProfiler] Profile from data patterns: {profile.industry}")
                return profile
        
        # Fallback to generic profile
        logger.info("[BusinessProfiler] Using generic business profile")
        return BusinessProfile(
            industry="general",
            business_type="general",
            terminology={
                "items": "items",
                "transaction": "transaction",
                "customer": "customer",
                "value": "value"
            },
            metrics_focus=["growth_rate", "efficiency", "customer_satisfaction"],
            recommended_analyses=["trend_analysis", "performance_metrics", "forecasting"]
        )
