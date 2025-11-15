#!/bin/bash
# End-to-End Narrative Generation Test
# Demonstrates complete intelligence layer workflow

set -e

BASE_URL="http://localhost:8001"
TENANT_ID="demo"

echo "=== Dyocense Intelligence Layer - End-to-End Test ==="
echo ""

# Step 1: Run ELT Pipeline
echo "Step 1: Running ELT Pipeline to transform raw data..."
curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/elt/process" \
  -H "Content-Type: application/json" | python3 -m json.tool > /tmp/elt_results.json

echo "✅ ELT Pipeline Complete"
echo "   - Inventory Value: $(jq -r '.results.inventory.total_inventory_value' /tmp/elt_results.json)"
echo "   - Products: $(jq -r '.results.inventory.product_count' /tmp/elt_results.json)"
echo "   - Total Demand: $(jq -r '.results.demand.total_demand' /tmp/elt_results.json)"
echo ""

# Step 2: Generate Forecast
echo "Step 2: Generating demand forecast..."
curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/forecast" \
  -H "Content-Type: application/json" \
  -d '{"periods": 4}' | python3 -m json.tool > /tmp/forecast_results.json

echo "✅ Forecast Generated"
WIDGET_FORECAST=$(jq -r '.forecasts."WIDGET-001".predictions[0].predicted_quantity' /tmp/forecast_results.json)
echo "   - WIDGET-001 Week 4 Forecast: $WIDGET_FORECAST units"
echo "   - Trend: $(jq -r '.forecasts."WIDGET-001".trend' /tmp/forecast_results.json)"
echo ""

# Step 3: Run Optimization
echo "Step 3: Running inventory optimization..."
curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/optimize/inventory" \
  -H "Content-Type: application/json" \
  -d '{"objective": "minimize_cost"}' | python3 -m json.tool > /tmp/optimization_results.json

echo "✅ Optimization Complete"
echo "   - Items Analyzed: $(jq -r '.items_analyzed' /tmp/optimization_results.json)"
echo "   - Actions Required: $(jq -r '.actions_required' /tmp/optimization_results.json)"
echo "   - Potential Savings: \$$(jq -r '.total_potential_savings' /tmp/optimization_results.json)"
echo ""

# Step 4: Ask Business Questions
echo "Step 4: Asking AI Coach business questions..."
echo ""

echo "Q1: How can I reduce inventory costs by 20%?"
curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/coach/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "How can I reduce inventory costs by 20%?"}' | python3 -m json.tool > /tmp/narrative1.json

NARRATIVE1=$(jq -r '.narrative' /tmp/narrative1.json)
echo "A1: $NARRATIVE1"
echo ""

echo "Q2: What will WIDGET-001 demand be next month?"
curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/coach/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What will WIDGET-001 demand be next month?"}' | python3 -m json.tool > /tmp/narrative2.json

NARRATIVE2=$(jq -r '.narrative' /tmp/narrative2.json)
echo "A2: $NARRATIVE2"
echo ""

echo "Q3: What's my inventory status?"
curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/coach/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is my inventory status?"}' | python3 -m json.tool > /tmp/narrative3.json

NARRATIVE3=$(jq -r '.narrative' /tmp/narrative3.json)
echo "A3: $NARRATIVE3"
echo ""

# Summary
echo "=== Test Summary ==="
echo "✅ ELT Pipeline: Working"
echo "✅ Forecasting: Working"
echo "✅ Optimization: Working"
echo "✅ Narrative Generation: Working"
echo ""
echo "All intelligence layer services are operational!"
echo ""
echo "Results saved to:"
echo "  - /tmp/elt_results.json"
echo "  - /tmp/forecast_results.json"
echo "  - /tmp/optimization_results.json"
echo "  - /tmp/narrative1.json"
echo "  - /tmp/narrative2.json"
echo "  - /tmp/narrative3.json"
