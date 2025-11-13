"""
Business Type Classification System

Automatically detects business industry type from tenant data:
- Transaction patterns and volumes
- Inventory characteristics
- Customer patterns (B2B vs B2C)
- Industry keywords in description
- Chart of accounts structure

Supported Business Types:
- Restaurant/Food Service
- Retail/E-commerce
- Professional Services
- Contractor/Construction
- Healthcare/Wellness
- Manufacturing
- Wholesale/Distribution
- Other/General
"""
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
import re


class BusinessType(str, Enum):
    """Supported business types for personalization"""
    RESTAURANT = "restaurant"
    RETAIL = "retail"
    SERVICES = "services"
    CONTRACTOR = "contractor"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    WHOLESALE = "wholesale"
    OTHER = "other"


class ClassificationConfidence(str, Enum):
    """Confidence level in classification"""
    HIGH = "high"      # 80%+ confidence
    MEDIUM = "medium"  # 60-80% confidence
    LOW = "low"        # <60% confidence


@dataclass
class ClassificationResult:
    """Result of business type classification"""
    business_type: BusinessType
    confidence: ClassificationConfidence
    confidence_score: float  # 0-100
    reasoning: List[str]  # Why this classification was chosen
    signals: Dict[str, Any]  # Data points used in classification
    alternative_types: List[Tuple[BusinessType, float]]  # Other possibilities


class BusinessTypeClassifier:
    """
    ML-powered business type classifier
    
    Uses multiple signals:
    1. Industry keywords from tenant profile
    2. Transaction patterns (frequency, amounts, seasonality)
    3. Inventory characteristics (SKUs, turnover)
    4. Customer patterns (B2B vs B2C, repeat rate)
    5. Chart of accounts (expense categories)
    6. Revenue streams (product vs service)
    """
    
    # Industry keywords for text analysis
    INDUSTRY_KEYWORDS = {
        BusinessType.RESTAURANT: [
            "restaurant", "cafe", "coffee", "bar", "grill", "bistro", "diner",
            "food service", "catering", "bakery", "pizzeria", "tavern", "pub",
            "eatery", "dining", "kitchen", "menu", "chef", "culinary"
        ],
        BusinessType.RETAIL: [
            "retail", "store", "shop", "boutique", "mart", "market", "outlet",
            "merchandise", "clothing", "apparel", "fashion", "electronics",
            "furniture", "gifts", "books", "toys", "sporting goods"
        ],
        BusinessType.SERVICES: [
            "consulting", "professional services", "agency", "firm", "advisors",
            "marketing", "design", "accounting", "legal", "insurance", "financial",
            "it services", "software", "consulting", "coaching", "training"
        ],
        BusinessType.CONTRACTOR: [
            "construction", "contractor", "builder", "remodeling", "renovation",
            "plumbing", "electrical", "hvac", "roofing", "carpentry", "masonry",
            "landscaping", "painting", "flooring", "general contractor"
        ],
        BusinessType.HEALTHCARE: [
            "medical", "dental", "healthcare", "clinic", "practice", "doctor",
            "dentist", "therapist", "chiropractor", "pharmacy", "veterinary",
            "wellness", "fitness", "gym", "spa", "massage", "health"
        ],
        BusinessType.MANUFACTURING: [
            "manufacturing", "factory", "production", "assembly", "fabrication",
            "industrial", "machinery", "equipment", "processing", "packaging"
        ],
        BusinessType.WHOLESALE: [
            "wholesale", "distributor", "distribution", "supplier", "import",
            "export", "bulk", "warehouse", "logistics"
        ],
    }
    
    # Expense category patterns by industry
    EXPENSE_PATTERNS = {
        BusinessType.RESTAURANT: ["food cost", "cogs food", "supplies food", "kitchen"],
        BusinessType.RETAIL: ["inventory", "merchandise", "cogs"],
        BusinessType.SERVICES: ["professional fees", "consulting", "subcontractors"],
        BusinessType.CONTRACTOR: ["materials", "labor", "equipment rental", "permits"],
        BusinessType.HEALTHCARE: ["medical supplies", "pharmaceuticals", "lab fees"],
        BusinessType.MANUFACTURING: ["raw materials", "production", "factory"],
        BusinessType.WHOLESALE: ["inventory", "freight", "warehouse"],
    }
    
    def __init__(self):
        self.classification_cache = {}
    
    async def classify_tenant(
        self,
        tenant_id: str,
        tenant_data: Dict[str, Any],
        transaction_data: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False,
    ) -> ClassificationResult:
        """
        Classify business type for a tenant
        
        Args:
            tenant_id: Tenant identifier
            tenant_data: Tenant profile data
            transaction_data: Optional transaction history
            force_refresh: Skip cache and reclassify
        
        Returns:
            ClassificationResult with type, confidence, reasoning
        """
        # Check cache
        if not force_refresh and tenant_id in self.classification_cache:
            return self.classification_cache[tenant_id]
        
        # Extract signals from data
        signals = self._extract_signals(tenant_data, transaction_data)
        
        # Score each business type
        scores = {}
        reasoning_by_type = {}
        
        for business_type in BusinessType:
            score, reasoning = self._score_business_type(
                business_type,
                signals,
            )
            scores[business_type] = score
            reasoning_by_type[business_type] = reasoning
        
        # Get top classification
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_type, top_score = sorted_types[0]
        
        # Calculate confidence
        confidence_score = top_score
        if confidence_score >= 80:
            confidence = ClassificationConfidence.HIGH
        elif confidence_score >= 60:
            confidence = ClassificationConfidence.MEDIUM
        else:
            confidence = ClassificationConfidence.LOW
        
        # Get alternative types (top 3)
        alternatives = [(t, s) for t, s in sorted_types[1:4]]
        
        result = ClassificationResult(
            business_type=top_type,
            confidence=confidence,
            confidence_score=confidence_score,
            reasoning=reasoning_by_type[top_type],
            signals=signals,
            alternative_types=alternatives,
        )
        
        # Cache result
        self.classification_cache[tenant_id] = result
        
        return result
    
    def _extract_signals(
        self,
        tenant_data: Dict[str, Any],
        transaction_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract classification signals from raw data"""
        signals = {}
        
        # Text signals from tenant profile
        business_name = tenant_data.get("business_name", "").lower()
        industry = tenant_data.get("industry", "").lower()
        description = tenant_data.get("description", "").lower()
        
        signals["text"] = f"{business_name} {industry} {description}"
        
        # Transaction patterns
        if transaction_data:
            signals["transaction_frequency"] = transaction_data.get("avg_daily_transactions", 0)
            signals["avg_transaction_amount"] = transaction_data.get("avg_transaction_amount", 0)
            signals["transaction_volume"] = transaction_data.get("total_transactions", 0)
            signals["customer_count"] = transaction_data.get("unique_customers", 0)
            signals["repeat_customer_rate"] = transaction_data.get("repeat_customer_rate", 0)
        
        # Inventory signals
        inventory = tenant_data.get("inventory_data", {})
        signals["has_inventory"] = inventory.get("total_items", 0) > 0
        signals["inventory_sku_count"] = inventory.get("total_items", 0)
        signals["inventory_turnover"] = inventory.get("turnover_ratio", 0)
        
        # Revenue patterns
        revenue = tenant_data.get("revenue_data", {})
        signals["revenue_monthly"] = revenue.get("monthly_avg", 0)
        signals["revenue_seasonality"] = revenue.get("seasonality_score", 0)
        
        # Expense patterns
        expenses = tenant_data.get("expense_breakdown", {})
        signals["expense_categories"] = list(expenses.keys())
        signals["cogs_percentage"] = expenses.get("cogs", 0) / max(signals.get("revenue_monthly", 1), 1) * 100
        
        # Customer patterns
        signals["b2b_percentage"] = tenant_data.get("b2b_percentage", 0)
        
        return signals
    
    def _score_business_type(
        self,
        business_type: BusinessType,
        signals: Dict[str, Any],
    ) -> Tuple[float, List[str]]:
        """
        Score how well signals match a business type
        
        Returns:
            (score 0-100, list of reasoning statements)
        """
        score = 0.0
        reasoning = []
        
        # Text analysis (40 points max)
        text_score, text_reasoning = self._score_text_match(
            business_type,
            signals.get("text", ""),
        )
        score += text_score
        reasoning.extend(text_reasoning)
        
        # Transaction patterns (30 points max)
        transaction_score, transaction_reasoning = self._score_transaction_patterns(
            business_type,
            signals,
        )
        score += transaction_score
        reasoning.extend(transaction_reasoning)
        
        # Inventory characteristics (15 points max)
        inventory_score, inventory_reasoning = self._score_inventory_patterns(
            business_type,
            signals,
        )
        score += inventory_score
        reasoning.extend(inventory_reasoning)
        
        # Expense patterns (15 points max)
        expense_score, expense_reasoning = self._score_expense_patterns(
            business_type,
            signals,
        )
        score += expense_score
        reasoning.extend(expense_reasoning)
        
        return score, reasoning
    
    def _score_text_match(
        self,
        business_type: BusinessType,
        text: str,
    ) -> Tuple[float, List[str]]:
        """Score based on keyword matching"""
        if business_type not in self.INDUSTRY_KEYWORDS:
            return 0.0, []
        
        keywords = self.INDUSTRY_KEYWORDS[business_type]
        matches = [kw for kw in keywords if kw in text]
        
        if not matches:
            return 0.0, []
        
        # Score based on number of matches
        score = min(len(matches) * 10, 40)
        reasoning = [f"Business description contains {len(matches)} {business_type.value} keywords: {', '.join(matches[:3])}"]
        
        return score, reasoning
    
    def _score_transaction_patterns(
        self,
        business_type: BusinessType,
        signals: Dict[str, Any],
    ) -> Tuple[float, List[str]]:
        """Score based on transaction characteristics"""
        score = 0.0
        reasoning = []
        
        freq = signals.get("transaction_frequency", 0)
        avg_amount = signals.get("avg_transaction_amount", 0)
        repeat_rate = signals.get("repeat_customer_rate", 0)
        
        # Restaurant: High frequency, low-medium amounts, high repeat
        if business_type == BusinessType.RESTAURANT:
            if freq > 50:  # 50+ transactions/day
                score += 10
                reasoning.append(f"High transaction frequency ({freq}/day) typical of restaurants")
            if 10 < avg_amount < 100:
                score += 10
                reasoning.append(f"Average transaction ${avg_amount:.0f} in restaurant range")
            if repeat_rate > 0.4:
                score += 10
                reasoning.append(f"{repeat_rate*100:.0f}% repeat customer rate typical of local restaurants")
        
        # Retail: Medium frequency, varied amounts
        elif business_type == BusinessType.RETAIL:
            if 20 < freq < 200:
                score += 10
                reasoning.append(f"Transaction frequency ({freq}/day) typical of retail")
            if 20 < avg_amount < 200:
                score += 10
                reasoning.append(f"Average transaction ${avg_amount:.0f} in retail range")
        
        # Services: Low frequency, high amounts, B2B
        elif business_type == BusinessType.SERVICES:
            if freq < 10:
                score += 10
                reasoning.append(f"Low transaction frequency ({freq}/day) typical of B2B services")
            if avg_amount > 500:
                score += 10
                reasoning.append(f"High average transaction ${avg_amount:.0f} typical of professional services")
            if signals.get("b2b_percentage", 0) > 0.7:
                score += 10
                reasoning.append("Primarily B2B customers typical of services")
        
        # Contractor: Project-based, high amounts
        elif business_type == BusinessType.CONTRACTOR:
            if freq < 20:
                score += 10
                reasoning.append(f"Project-based transaction pattern ({freq}/day)")
            if avg_amount > 1000:
                score += 10
                reasoning.append(f"High average transaction ${avg_amount:.0f} typical of construction projects")
        
        return score, reasoning
    
    def _score_inventory_patterns(
        self,
        business_type: BusinessType,
        signals: Dict[str, Any],
    ) -> Tuple[float, List[str]]:
        """Score based on inventory characteristics"""
        score = 0.0
        reasoning = []
        
        has_inventory = signals.get("has_inventory", False)
        sku_count = signals.get("inventory_sku_count", 0)
        turnover = signals.get("inventory_turnover", 0)
        
        # Restaurant: Inventory with high turnover, perishable
        if business_type == BusinessType.RESTAURANT:
            if has_inventory and turnover > 15:  # 15+ turns/year = ~24 days
                score += 15
                reasoning.append(f"High inventory turnover ({turnover:.1f}x/year) typical of food service")
        
        # Retail: Large SKU count, moderate turnover
        elif business_type == BusinessType.RETAIL:
            if sku_count > 100:
                score += 10
                reasoning.append(f"Large product catalog ({sku_count} SKUs) typical of retail")
            if 4 < turnover < 12:
                score += 5
                reasoning.append(f"Moderate inventory turnover ({turnover:.1f}x/year)")
        
        # Services: Little to no inventory
        elif business_type == BusinessType.SERVICES:
            if not has_inventory or sku_count < 10:
                score += 15
                reasoning.append("Minimal inventory typical of professional services")
        
        # Contractor: Project-specific materials
        elif business_type == BusinessType.CONTRACTOR:
            if has_inventory and sku_count < 50:
                score += 10
                reasoning.append("Small inventory of materials typical of contractors")
        
        return score, reasoning
    
    def _score_expense_patterns(
        self,
        business_type: BusinessType,
        signals: Dict[str, Any],
    ) -> Tuple[float, List[str]]:
        """Score based on expense categories"""
        score = 0.0
        reasoning = []
        
        expense_categories = [cat.lower() for cat in signals.get("expense_categories", [])]
        cogs_percentage = signals.get("cogs_percentage", 0)
        
        if business_type not in self.EXPENSE_PATTERNS:
            return 0.0, []
        
        # Check for industry-specific expense categories
        pattern_keywords = self.EXPENSE_PATTERNS[business_type]
        matches = []
        for keyword in pattern_keywords:
            if any(keyword in cat for cat in expense_categories):
                matches.append(keyword)
        
        if matches:
            score += min(len(matches) * 5, 10)
            reasoning.append(f"Expense categories include {', '.join(matches)}")
        
        # COGS percentage analysis
        if business_type == BusinessType.RESTAURANT:
            if 25 < cogs_percentage < 40:  # Typical food cost
                score += 5
                reasoning.append(f"Food cost {cogs_percentage:.0f}% in typical restaurant range")
        elif business_type == BusinessType.RETAIL:
            if 40 < cogs_percentage < 70:
                score += 5
                reasoning.append(f"COGS {cogs_percentage:.0f}% typical of retail")
        elif business_type == BusinessType.SERVICES:
            if cogs_percentage < 20:  # Low COGS for services
                score += 5
                reasoning.append(f"Low COGS {cogs_percentage:.0f}% typical of services")
        
        return score, reasoning
    
    async def update_tenant_classification(
        self,
        tenant_id: str,
        classification: ClassificationResult,
        persistence_backend,
    ) -> bool:
        """Store classification result in tenant metadata"""
        try:
            await persistence_backend.update_tenant(
                tenant_id,
                {
                    "business_type": classification.business_type.value,
                    "business_type_confidence": classification.confidence.value,
                    "business_type_score": classification.confidence_score,
                    "classified_at": datetime.now().isoformat(),
                }
            )
            return True
        except Exception as e:
            print(f"Failed to update tenant classification: {e}")
            return False


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_business_classifier() -> BusinessTypeClassifier:
    """Factory function for creating business classifier"""
    return BusinessTypeClassifier()


async def classify_and_store(
    tenant_id: str,
    tenant_data: Dict[str, Any],
    transaction_data: Optional[Dict[str, Any]],
    persistence_backend,
) -> ClassificationResult:
    """
    Convenience function to classify and store in one call
    
    Usage:
        result = await classify_and_store(
            tenant_id="tenant-123",
            tenant_data={...},
            transaction_data={...},
            persistence_backend=db,
        )
    """
    classifier = create_business_classifier()
    result = await classifier.classify_tenant(
        tenant_id,
        tenant_data,
        transaction_data,
    )
    await classifier.update_tenant_classification(
        tenant_id,
        result,
        persistence_backend,
    )
    return result
