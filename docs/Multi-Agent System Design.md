Agent Architecture
Framework: LangGraph (state machine for agent workflows)

Agent Personas
Goal Planner Agent

Responsibility: Generate SMART goals from business context
Tools: query_metrics, get_benchmarks, calculate_feasibility
LLM: GPT-4o (requires reasoning)
Forecasting Agent

Responsibility: Predict future metrics
Tools: run_arima, run_prophet, run_xgboost, ensemble_forecast
Output: Time-series predictions with confidence intervals
Optimization Agent

Responsibility: Solve resource allocation problems
Tools: formulate_lp, solve_lp, sensitivity_analysis, pareto_frontier
Solver: OR-Tools, PuLP
Evidence Agent

Responsibility: Causal analysis and root cause diagnosis
Tools: discover_dag, estimate_causal_effect, granger_causality, counterfactual_analysis
Framework: DoWhy, pgmpy
Compliance Agent

Responsibility: Check regulatory requirements
Tools: check_soc2_controls, gdpr_assessment, generate_audit_report
Knowledge Base: Compliance standards in PostgreSQL
Coordination Pattern
Sequential: Goal Planner → Forecasting → Optimization → Evidence → Final Recommendation

Parallel: For complex queries, run multiple agents concurrently, aggregate results

Human-in-the-Loop: Critical decisions (e.g., "lay off 5 employees") require user approval
