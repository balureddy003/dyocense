#!/bin/bash
# Compare Simple vs Advanced AI Models
# Shows the difference between basic and production-grade algorithms

set -e

BASE_URL="http://localhost:8001"
TENANT_ID="demo"

echo "=== AI Model Comparison Test ==="
echo ""

# Check capabilities
echo "Step 1: Checking available capabilities..."
curl -s "$BASE_URL/v1/capabilities" | python3 -m json.tool > /tmp/capabilities.json
PROPHET=$(jq -r '.capabilities.forecasting.prophet' /tmp/capabilities.json)
ORTOOLS=$(jq -r '.capabilities.optimization.ortools_lp' /tmp/capabilities.json)

echo "✅ Capabilities Retrieved"
echo "   - Prophet Available: $PROPHET"
echo "   - OR-Tools Available: $ORTOOLS"
echo ""

# Test 1: Forecasting Comparison
echo "=== Forecasting Comparison ==="
echo ""

echo "Simple Moving Average Model:"
curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/forecast" \
  -H "Content-Type: application/json" \
  -d '{"periods": 4, "model": "simple"}' | python3 -m json.tool > /tmp/forecast_simple.json

SIMPLE_MODEL=$(jq -r '.model' /tmp/forecast_simple.json)
SIMPLE_PRED=$(jq -r '.forecasts."WIDGET-001".predictions[0].predicted_quantity' /tmp/forecast_simple.json)
SIMPLE_TREND=$(jq -r '.forecasts."WIDGET-001".trend' /tmp/forecast_simple.json)

echo "  Model: $SIMPLE_MODEL"
echo "  Week 4 Prediction: $SIMPLE_PRED units"
echo "  Trend: $SIMPLE_TREND"
echo ""

if [ "$PROPHET" = "true" ]; then
    echo "Prophet (Advanced) Model:"
    curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/forecast" \
      -H "Content-Type: application/json" \
      -d '{"periods": 4, "model": "prophet"}' | python3 -m json.tool > /tmp/forecast_prophet.json
    
    PROPHET_MODEL=$(jq -r '.model' /tmp/forecast_prophet.json)
    PROPHET_PRED=$(jq -r '.forecasts."WIDGET-001".predictions[0].predicted_quantity' /tmp/forecast_prophet.json)
    PROPHET_TREND=$(jq -r '.forecasts."WIDGET-001".trend // 0' /tmp/forecast_prophet.json)
    
    echo "  Model: $PROPHET_MODEL"
    echo "  Week 4 Prediction: $PROPHET_PRED units"
    echo "  Trend: $PROPHET_TREND"
    echo ""
    
    echo "📊 Forecast Comparison:"
    echo "  Simple MA:  $SIMPLE_PRED units (trend: $SIMPLE_TREND)"
    echo "  Prophet:    $PROPHET_PRED units (trend: $PROPHET_TREND)"
else
    echo "⚠️  Prophet not available - install with: pip install prophet"
fi

echo ""
echo "=== Optimization Comparison ==="
echo ""

echo "Simple EOQ Model:"
curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/optimize/inventory" \
  -H "Content-Type: application/json" \
  -d '{"algorithm": "simple", "objective": "minimize_cost"}' | python3 -m json.tool > /tmp/optimize_simple.json

SIMPLE_SAVINGS=$(jq -r '.total_potential_savings' /tmp/optimize_simple.json)
SIMPLE_ACTIONS=$(jq -r '.actions_required' /tmp/optimize_simple.json)

echo "  Total Savings: \$$SIMPLE_SAVINGS"
echo "  Actions Required: $SIMPLE_ACTIONS"
echo ""

if [ "$ORTOOLS" = "true" ]; then
    echo "OR-Tools LP Model:"
    curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/optimize/inventory" \
      -H "Content-Type: application/json" \
      -d '{"algorithm": "lp", "objective": "minimize_cost"}' | python3 -m json.tool > /tmp/optimize_ortools.json
    
    ORTOOLS_SAVINGS=$(jq -r '.total_potential_savings' /tmp/optimize_ortools.json)
    ORTOOLS_ACTIONS=$(jq -r '.actions_required' /tmp/optimize_ortools.json)
    ORTOOLS_STATUS=$(jq -r '.solver_status' /tmp/optimize_ortools.json)
    ORTOOLS_OBJECTIVE=$(jq -r '.objective_value' /tmp/optimize_ortools.json)
    
    echo "  Solver Status: $ORTOOLS_STATUS"
    echo "  Objective Value: \$$ORTOOLS_OBJECTIVE"
    echo "  Total Savings: \$$ORTOOLS_SAVINGS"
    echo "  Actions Required: $ORTOOLS_ACTIONS"
    echo ""
    
    echo "📊 Optimization Comparison:"
    echo "  Simple EOQ:  \$$SIMPLE_SAVINGS savings, $SIMPLE_ACTIONS actions"
    echo "  OR-Tools LP: \$$ORTOOLS_SAVINGS savings, $ORTOOLS_ACTIONS actions"
    echo "  Improvement: $(python3 -c "print(f'{((${ORTOOLS_SAVINGS} - ${SIMPLE_SAVINGS}) / max(${SIMPLE_SAVINGS}, 0.01) * 100):.1f}%')")"
else
    echo "⚠️  OR-Tools not available - install with: pip install ortools"
fi

echo ""
echo "=== Narrative with Advanced Models ==="
echo ""

curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/coach/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What optimizations can reduce my costs?"}' | python3 -m json.tool > /tmp/narrative_advanced.json

NARRATIVE=$(jq -r '.narrative' /tmp/narrative_advanced.json)
INTENT=$(jq -r '.intent' /tmp/narrative_advanced.json)
REC_COUNT=$(jq -r '.recommendations | length' /tmp/narrative_advanced.json)

echo "Question: What optimizations can reduce my costs?"
echo "Intent Detected: $INTENT"
echo "Narrative: $NARRATIVE"
echo "Recommendations: $REC_COUNT"
echo ""

echo "=== Summary ==="
echo "✅ Simple Models: Always available (moving average, EOQ)"
if [ "$PROPHET" = "true" ]; then
    echo "✅ Prophet: Installed and working"
else
    echo "⏳ Prophet: Not installed"
fi

if [ "$ORTOOLS" = "true" ]; then
    echo "✅ OR-Tools: Installed and working"
else
    echo "⏳ OR-Tools: Not installed"
fi

echo ""
echo "Results saved to:"
echo "  - /tmp/capabilities.json"
echo "  - /tmp/forecast_simple.json"
if [ "$PROPHET" = "true" ]; then
    echo "  - /tmp/forecast_prophet.json"
fi
echo "  - /tmp/optimize_simple.json"
if [ "$ORTOOLS" = "true" ]; then
    echo "  - /tmp/optimize_ortools.json"
fi
echo "  - /tmp/narrative_advanced.json"
