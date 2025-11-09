/**
 * Business Health Score Calculator
 * Calculates a 0-100 score based on 7 weighted metrics
 */

export interface BusinessMetrics {
    // Revenue Growth (25%)
    revenueGrowth?: number // YoY % growth (-100 to 500+)

    // Profit Margin (20%)
    profitMargin?: number // % (0 to 100)

    // Cash Flow (15%)
    cashFlowRatio?: number // Operating cash flow / Revenue (0 to 2+)

    // Inventory Health (15%)
    inventoryTurnover?: number // Times per year (0 to 20+)

    // Customer Satisfaction (10%)
    customerRating?: number // Average rating (0 to 5)

    // Operational Efficiency (10%)
    orderFulfillmentRate?: number // % of orders fulfilled on time (0 to 100)

    // Sales Velocity (5%)
    salesGrowthRate?: number // MoM % growth (-100 to 500+)
}

interface MetricScore {
    metric: string
    weight: number
    rawValue?: number
    normalizedScore: number
    weightedScore: number
}

interface HealthScoreResult {
    overallScore: number
    breakdown: MetricScore[]
    status: 'Excellent' | 'Strong' | 'Good' | 'Needs Attention' | 'Critical'
    recommendations: string[]
}

/**
 * Normalize revenue growth to 0-100 scale
 * -20% or worse = 0, 0% = 40, 10% = 60, 25% = 80, 50%+ = 100
 */
function normalizeRevenueGrowth(growth: number): number {
    if (growth <= -20) return 0
    if (growth < 0) return 40 + (growth / -20) * 40 // -20 to 0 → 0 to 40
    if (growth < 10) return 40 + (growth / 10) * 20 // 0 to 10 → 40 to 60
    if (growth < 25) return 60 + ((growth - 10) / 15) * 20 // 10 to 25 → 60 to 80
    if (growth < 50) return 80 + ((growth - 25) / 25) * 20 // 25 to 50 → 80 to 100
    return 100
}

/**
 * Normalize profit margin to 0-100 scale
 * <0% = 0, 5% = 40, 10% = 60, 20% = 80, 30%+ = 100
 */
function normalizeProfitMargin(margin: number): number {
    if (margin <= 0) return 0
    if (margin < 5) return (margin / 5) * 40 // 0 to 5 → 0 to 40
    if (margin < 10) return 40 + ((margin - 5) / 5) * 20 // 5 to 10 → 40 to 60
    if (margin < 20) return 60 + ((margin - 10) / 10) * 20 // 10 to 20 → 60 to 80
    if (margin < 30) return 80 + ((margin - 20) / 10) * 20 // 20 to 30 → 80 to 100
    return 100
}

/**
 * Normalize cash flow ratio to 0-100 scale
 * <0 = 0, 0.1 = 40, 0.2 = 60, 0.4 = 80, 0.6+ = 100
 */
function normalizeCashFlowRatio(ratio: number): number {
    if (ratio <= 0) return 0
    if (ratio < 0.1) return (ratio / 0.1) * 40 // 0 to 0.1 → 0 to 40
    if (ratio < 0.2) return 40 + ((ratio - 0.1) / 0.1) * 20 // 0.1 to 0.2 → 40 to 60
    if (ratio < 0.4) return 60 + ((ratio - 0.2) / 0.2) * 20 // 0.2 to 0.4 → 60 to 80
    if (ratio < 0.6) return 80 + ((ratio - 0.4) / 0.2) * 20 // 0.4 to 0.6 → 80 to 100
    return 100
}

/**
 * Normalize inventory turnover to 0-100 scale
 * <2 = 0-40, 4 = 60, 8 = 80, 12+ = 100
 */
function normalizeInventoryTurnover(turnover: number): number {
    if (turnover < 2) return (turnover / 2) * 40 // 0 to 2 → 0 to 40
    if (turnover < 4) return 40 + ((turnover - 2) / 2) * 20 // 2 to 4 → 40 to 60
    if (turnover < 8) return 60 + ((turnover - 4) / 4) * 20 // 4 to 8 → 60 to 80
    if (turnover < 12) return 80 + ((turnover - 8) / 4) * 20 // 8 to 12 → 80 to 100
    return 100
}

/**
 * Normalize customer rating to 0-100 scale
 * 1.0 = 0, 2.5 = 40, 3.5 = 60, 4.0 = 80, 4.5+ = 100
 */
function normalizeCustomerRating(rating: number): number {
    if (rating <= 1) return 0
    if (rating < 2.5) return ((rating - 1) / 1.5) * 40 // 1 to 2.5 → 0 to 40
    if (rating < 3.5) return 40 + ((rating - 2.5) / 1.0) * 20 // 2.5 to 3.5 → 40 to 60
    if (rating < 4.0) return 60 + ((rating - 3.5) / 0.5) * 20 // 3.5 to 4.0 → 60 to 80
    if (rating < 4.5) return 80 + ((rating - 4.0) / 0.5) * 20 // 4.0 to 4.5 → 80 to 100
    return 100
}

/**
 * Normalize order fulfillment rate to 0-100 scale
 * Direct mapping: 0% = 0, 100% = 100
 */
function normalizeOrderFulfillment(rate: number): number {
    return Math.max(0, Math.min(100, rate))
}

/**
 * Normalize sales growth rate (MoM) to 0-100 scale
 * Similar to revenue growth but monthly
 */
function normalizeSalesGrowth(growth: number): number {
    if (growth <= -10) return 0
    if (growth < 0) return 40 + (growth / -10) * 40 // -10 to 0 → 0 to 40
    if (growth < 5) return 40 + (growth / 5) * 20 // 0 to 5 → 40 to 60
    if (growth < 15) return 60 + ((growth - 5) / 10) * 20 // 5 to 15 → 60 to 80
    if (growth < 30) return 80 + ((growth - 15) / 15) * 20 // 15 to 30 → 80 to 100
    return 100
}

/**
 * Calculate business health score from metrics
 */
export function calculateHealthScore(metrics: BusinessMetrics): HealthScoreResult {
    const breakdown: MetricScore[] = []
    let totalScore = 0

    // Revenue Growth (25%)
    if (metrics.revenueGrowth !== undefined) {
        const normalized = normalizeRevenueGrowth(metrics.revenueGrowth)
        const weighted = (normalized * 25) / 100
        breakdown.push({
            metric: 'Revenue Growth',
            weight: 25,
            rawValue: metrics.revenueGrowth,
            normalizedScore: normalized,
            weightedScore: weighted,
        })
        totalScore += weighted
    }

    // Profit Margin (20%)
    if (metrics.profitMargin !== undefined) {
        const normalized = normalizeProfitMargin(metrics.profitMargin)
        const weighted = (normalized * 20) / 100
        breakdown.push({
            metric: 'Profit Margin',
            weight: 20,
            rawValue: metrics.profitMargin,
            normalizedScore: normalized,
            weightedScore: weighted,
        })
        totalScore += weighted
    }

    // Cash Flow (15%)
    if (metrics.cashFlowRatio !== undefined) {
        const normalized = normalizeCashFlowRatio(metrics.cashFlowRatio)
        const weighted = (normalized * 15) / 100
        breakdown.push({
            metric: 'Cash Flow',
            weight: 15,
            rawValue: metrics.cashFlowRatio,
            normalizedScore: normalized,
            weightedScore: weighted,
        })
        totalScore += weighted
    }

    // Inventory Health (15%)
    if (metrics.inventoryTurnover !== undefined) {
        const normalized = normalizeInventoryTurnover(metrics.inventoryTurnover)
        const weighted = (normalized * 15) / 100
        breakdown.push({
            metric: 'Inventory Health',
            weight: 15,
            rawValue: metrics.inventoryTurnover,
            normalizedScore: normalized,
            weightedScore: weighted,
        })
        totalScore += weighted
    }

    // Customer Satisfaction (10%)
    if (metrics.customerRating !== undefined) {
        const normalized = normalizeCustomerRating(metrics.customerRating)
        const weighted = (normalized * 10) / 100
        breakdown.push({
            metric: 'Customer Satisfaction',
            weight: 10,
            rawValue: metrics.customerRating,
            normalizedScore: normalized,
            weightedScore: weighted,
        })
        totalScore += weighted
    }

    // Operational Efficiency (10%)
    if (metrics.orderFulfillmentRate !== undefined) {
        const normalized = normalizeOrderFulfillment(metrics.orderFulfillmentRate)
        const weighted = (normalized * 10) / 100
        breakdown.push({
            metric: 'Operational Efficiency',
            weight: 10,
            rawValue: metrics.orderFulfillmentRate,
            normalizedScore: normalized,
            weightedScore: weighted,
        })
        totalScore += weighted
    }

    // Sales Velocity (5%)
    if (metrics.salesGrowthRate !== undefined) {
        const normalized = normalizeSalesGrowth(metrics.salesGrowthRate)
        const weighted = (normalized * 5) / 100
        breakdown.push({
            metric: 'Sales Velocity',
            weight: 5,
            rawValue: metrics.salesGrowthRate,
            normalizedScore: normalized,
            weightedScore: weighted,
        })
        totalScore += weighted
    }

    // Calculate overall score (scale up based on available metrics)
    const totalWeight = breakdown.reduce((sum, m) => sum + m.weight, 0)
    const overallScore = totalWeight > 0 ? (totalScore / totalWeight) * 100 : 0

    // Determine status
    let status: HealthScoreResult['status']
    if (overallScore >= 90) status = 'Excellent'
    else if (overallScore >= 75) status = 'Strong'
    else if (overallScore >= 60) status = 'Good'
    else if (overallScore >= 40) status = 'Needs Attention'
    else status = 'Critical'

    // Generate recommendations
    const recommendations = generateRecommendations(breakdown, overallScore)

    return {
        overallScore: Math.round(overallScore),
        breakdown,
        status,
        recommendations,
    }
}

/**
 * Generate AI-style recommendations based on scores
 */
function generateRecommendations(breakdown: MetricScore[], overallScore: number): string[] {
    const recommendations: string[] = []

    // Find weakest metrics
    const weakMetrics = breakdown.filter((m) => m.normalizedScore < 50).sort((a, b) => a.normalizedScore - b.normalizedScore)

    if (weakMetrics.length === 0 && overallScore >= 90) {
        recommendations.push('🎉 Excellent work! All metrics are performing well. Keep maintaining your current strategies.')
        return recommendations
    }

    weakMetrics.forEach((metric) => {
        switch (metric.metric) {
            case 'Revenue Growth':
                recommendations.push(
                    `📈 Revenue growth is ${metric.rawValue?.toFixed(1)}%. Consider launching new products or expanding to new markets.`
                )
                break
            case 'Profit Margin':
                recommendations.push(
                    `💰 Profit margin at ${metric.rawValue?.toFixed(1)}%. Review pricing strategy and reduce operational costs.`
                )
                break
            case 'Cash Flow':
                recommendations.push(
                    `💵 Cash flow ratio is ${metric.rawValue?.toFixed(2)}. Improve collection processes and manage payment terms.`
                )
                break
            case 'Inventory Health':
                recommendations.push(
                    `📦 Inventory turnover is ${metric.rawValue?.toFixed(1)}x/year. Optimize stock levels and reduce slow-moving items.`
                )
                break
            case 'Customer Satisfaction':
                recommendations.push(
                    `⭐ Customer rating is ${metric.rawValue?.toFixed(1)}/5. Focus on customer support and product quality improvements.`
                )
                break
            case 'Operational Efficiency':
                recommendations.push(
                    `⚡ Fulfillment rate is ${metric.rawValue?.toFixed(1)}%. Streamline operations and reduce delivery delays.`
                )
                break
            case 'Sales Velocity':
                recommendations.push(
                    `🚀 Sales growth is ${metric.rawValue?.toFixed(1)}% MoM. Increase marketing efforts and sales team productivity.`
                )
                break
        }
    })

    // Add general recommendation if overall score is low
    if (overallScore < 60) {
        recommendations.push(
            '💡 Consider setting specific goals for your weakest metrics. Break them into weekly action plans for steady improvement.'
        )
    }

    return recommendations.slice(0, 3) // Limit to top 3 recommendations
}

/**
 * Mock function to get business metrics from connectors
 * TODO: Replace with real connector data
 */
export async function getBusinessMetricsFromConnectors(): Promise<BusinessMetrics> {
    // Mock CycloneRake.com data
    return {
        revenueGrowth: 15, // 15% YoY growth
        profitMargin: 18, // 18% profit margin
        cashFlowRatio: 0.25, // 25% of revenue
        inventoryTurnover: 6.5, // 6.5 times per year
        customerRating: 4.6, // 4.6/5 stars
        orderFulfillmentRate: 92, // 92% on-time
        salesGrowthRate: 8, // 8% MoM
    }
}
