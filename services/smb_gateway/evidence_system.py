"""
Evidence System for Coach Responses
Tracks data sources and provides citations for all facts
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class DataSource(BaseModel):
    """Represents a data source used in analysis"""
    id: str
    name: str  # e.g., "Shopify Orders", "QuickBooks Revenue", "Manual CSV"
    type: str  # "connector", "manual", "calculated"
    last_sync: Optional[datetime] = None
    record_count: int = 0


class Evidence(BaseModel):
    """Evidence citation for a specific fact or claim"""
    fact_id: str
    claim: str  # The actual claim being made
    data_source: str  # Which data source this comes from
    query: Optional[str] = None  # SQL-like query or calculation
    sample_data: Optional[List[Dict]] = None  # Sample records supporting the claim
    timestamp: datetime
    confidence: str = "high"  # high, medium, low


class EvidenceTracker:
    """Tracks evidence for coach responses"""
    
    def __init__(self):
        self.evidence_store: Dict[str, List[Evidence]] = {}
    
    def add_evidence(
        self,
        conversation_id: str,
        claim: str,
        data_source: str,
        query: Optional[str] = None,
        sample_data: Optional[List[Dict]] = None,
        confidence: str = "high"
    ) -> Evidence:
        """Add evidence for a claim"""
        evidence = Evidence(
            fact_id=f"ev_{len(self.evidence_store.get(conversation_id, []))}",
            claim=claim,
            data_source=data_source,
            query=query,
            sample_data=sample_data,
            timestamp=datetime.now(),
            confidence=confidence
        )
        
        if conversation_id not in self.evidence_store:
            self.evidence_store[conversation_id] = []
        
        self.evidence_store[conversation_id].append(evidence)
        return evidence
    
    def get_evidence(self, conversation_id: str) -> List[Evidence]:
        """Get all evidence for a conversation"""
        return self.evidence_store.get(conversation_id, [])
    
    def format_citation(self, evidence: Evidence, format: str = "inline") -> str:
        """Format evidence as a citation"""
        if format == "inline":
            return f"[Source: {evidence.data_source}, {evidence.confidence} confidence]"
        elif format == "footnote":
            return f"^{evidence.fact_id}^ {evidence.data_source}"
        else:
            return f"📊 {evidence.data_source}"


def create_evidence_enhanced_response(
    base_response: str,
    evidence_list: List[Evidence],
    include_sources_section: bool = True
) -> str:
    """
    Enhance a response with evidence citations
    
    Args:
        base_response: The original response text
        evidence_list: List of evidence supporting claims
        include_sources_section: Whether to append a sources section
    
    Returns:
        Response with inline citations and optional sources section
    """
    enhanced = base_response
    
    if include_sources_section and evidence_list:
        enhanced += "\n\n---\n**📚 Data Sources & Evidence:**\n"
        for i, evidence in enumerate(evidence_list, 1):
            enhanced += f"\n{i}. **{evidence.claim}**\n"
            enhanced += f"   • Source: {evidence.data_source}\n"
            enhanced += f"   • Confidence: {evidence.confidence}\n"
            
            if evidence.query:
                enhanced += f"   • Query: `{evidence.query}`\n"
            
            if evidence.sample_data:
                enhanced += f"   • Sample records: {len(evidence.sample_data)} available\n"
    
    return enhanced


def generate_data_lineage(
    metric_name: str,
    connector_data: Dict[str, Any],
    calculation_steps: List[str]
) -> Dict[str, Any]:
    """
    Generate data lineage for a metric showing how it was calculated
    
    Args:
        metric_name: Name of the metric (e.g., "Revenue Last 30 Days")
        connector_data: Raw data from connectors
        calculation_steps: Steps taken to calculate the metric
    
    Returns:
        Lineage information with sources and transformations
    """
    sources = []
    
    # Identify which connectors contributed
    if "orders" in connector_data:
        sources.append({
            "connector": "ecommerce",
            "table": "orders",
            "fields": ["total_amount", "created_at", "status"],
            "record_count": len(connector_data["orders"])
        })
    
    if "customers" in connector_data:
        sources.append({
            "connector": "crm",
            "table": "customers",
            "fields": ["id", "total_orders", "lifetime_value"],
            "record_count": len(connector_data["customers"])
        })
    
    if "inventory" in connector_data:
        sources.append({
            "connector": "inventory",
            "table": "inventory",
            "fields": ["quantity", "status", "unit_cost"],
            "record_count": len(connector_data["inventory"])
        })
    
    return {
        "metric": metric_name,
        "sources": sources,
        "transformations": calculation_steps,
        "generated_at": datetime.now().isoformat()
    }


# Global evidence tracker instance
_evidence_tracker = None

def get_evidence_tracker() -> EvidenceTracker:
    """Get global evidence tracker instance"""
    global _evidence_tracker
    if _evidence_tracker is None:
        _evidence_tracker = EvidenceTracker()
    return _evidence_tracker
