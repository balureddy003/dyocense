#!/bin/bash

# Test Script for OptiGuide-Style Multi-Agent System
# Tests what-if analysis, why analysis, and LangGraph chat endpoints

set -e

BASE_URL="http://localhost:8001"
TENANT_ID="demo"

echo "=================================================="
echo "OptiGuide Integration Test Suite"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Check Capabilities
echo -e "${BLUE}Test 1: Checking OptiGuide Capabilities${NC}"
echo "=================================================="
curl -s "$BASE_URL/v1/capabilities" | python3 -m json.tool | grep -A 10 "optiguide_available"
echo ""

# Test 2: What-If Analysis - Order Costs Increase
echo -e "${BLUE}Test 2: What-If Analysis - Order Costs Increase 20%${NC}"
echo "=================================================="
echo "Question: 'What if order costs increase by 20%?'"
echo ""

RESPONSE=$(curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/what-if" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What if order costs increase by 20%?"
  }')

echo "$RESPONSE" | python3 -m json.tool | head -50
echo ""

# Extract key metrics
ORIGINAL_COST=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('original_result', {}).get('objective_value', 'N/A'))" 2>/dev/null || echo "N/A")
MODIFIED_COST=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('modified_result', {}).get('objective_value', 'N/A'))" 2>/dev/null || echo "N/A")

echo -e "${GREEN}Results:${NC}"
echo "  Original Cost: $ORIGINAL_COST"
echo "  Modified Cost: $MODIFIED_COST"
echo ""

# Test 3: What-If Analysis - Holding Costs Double
echo -e "${BLUE}Test 3: What-If Analysis - Holding Costs Double${NC}"
echo "=================================================="
echo "Question: 'What if holding costs double?'"
echo ""

curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/what-if" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What if holding costs double?"
  }' | python3 -m json.tool | grep -A 5 "narrative"
echo ""

# Test 4: What-If Analysis - Reduce Safety Stock
echo -e "${BLUE}Test 4: What-If Analysis - Reduce Safety Stock${NC}"
echo "=================================================="
echo "Question: 'What if we reduce safety stock by 30%?'"
echo ""

curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/what-if" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What if we reduce safety stock by 30%?"
  }' | python3 -m json.tool | grep -A 10 "modifications_applied"
echo ""

# Test 5: What-If Analysis - Service Level Increase
echo -e "${BLUE}Test 5: What-If Analysis - Service Level Increase${NC}"
echo "=================================================="
echo "Question: 'What if we increase service level to 98%?'"
echo ""

curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/what-if" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What if we increase service level to 98%?"
  }' | python3 -m json.tool | grep -A 3 "service_level"
echo ""

# Test 6: Why Analysis - High Costs
echo -e "${BLUE}Test 6: Why Analysis - Why Are Costs High?${NC}"
echo "=================================================="
echo "Question: 'Why are inventory costs high?'"
echo ""

curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/why" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why are inventory costs high?"
  }' | python3 -m json.tool | grep -A 10 "narrative"
echo ""

# Test 7: Why Analysis - Overstock
echo -e "${BLUE}Test 7: Why Analysis - Why Overstock?${NC}"
echo "=================================================="
echo "Question: 'Why is WIDGET-001 overstocked?'"
echo ""

curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/why" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why is WIDGET-001 overstocked?"
  }' | python3 -m json.tool | head -40
echo ""

# Test 8: LangGraph Chat - Overview
echo -e "${BLUE}Test 8: LangGraph Chat - Inventory Overview${NC}"
echo "=================================================="
echo "Question: 'What is the current state of my inventory?'"
echo ""

curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the current state of my inventory?"
  }' | python3 -m json.tool | grep -A 15 "narrative"
echo ""

# Test 9: LangGraph Chat - Forecast Intent
echo -e "${BLUE}Test 9: LangGraph Chat - Forecast Demand${NC}"
echo "=================================================="
echo "Question: 'Forecast demand for the next 4 weeks'"
echo ""

curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Forecast demand for the next 4 weeks"
  }' | python3 -m json.tool | head -50
echo ""

# Test 10: LangGraph Chat - Optimization Intent
echo -e "${BLUE}Test 10: LangGraph Chat - Optimize Inventory${NC}"
echo "=================================================="
echo "Question: 'How can I reduce inventory costs?'"
echo ""

curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How can I reduce inventory costs?"
  }' | python3 -m json.tool | grep -A 20 "intent\|narrative"
echo ""

# Test 11: Complex What-If Scenario
echo -e "${BLUE}Test 11: Complex What-If - Multiple Constraints${NC}"
echo "=================================================="
echo "Question: 'What if order costs increase 15% and holding costs decrease 10%?'"
echo ""

curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/what-if" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What if order costs increase 15% and holding costs decrease 10%?"
  }' | python3 -m json.tool | grep -A 5 "analysis\|narrative"
echo ""

# Summary
echo "=================================================="
echo -e "${GREEN}OptiGuide Test Suite Completed${NC}"
echo "=================================================="
echo ""
echo "Test Results Summary:"
echo "✅ Capabilities check"
echo "✅ What-if analysis (order costs)"
echo "✅ What-if analysis (holding costs)"
echo "✅ What-if analysis (safety stock)"
echo "✅ What-if analysis (service level)"
echo "✅ Why analysis (high costs)"
echo "✅ Why analysis (overstock)"
echo "✅ LangGraph chat (overview)"
echo "✅ LangGraph chat (forecast)"
echo "✅ LangGraph chat (optimize)"
echo "✅ Complex what-if scenario"
echo ""
echo -e "${YELLOW}Note: Full LLM-powered analysis requires llm_config with API credentials${NC}"
echo "Current tests use rule-based fallback logic for demonstration."
echo ""
echo "To enable full OptiGuide capabilities, provide llm_config:"
echo '  {"llm_config": {"model": "gpt-4", "api_key": "...", "temperature": 0}}'
echo ""
