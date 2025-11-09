type TelemetryPayload = Record<string, unknown>

export function trackEvent(event: string, payload: TelemetryPayload = {}) {
    try {
        if (typeof window === 'undefined') return
        ;(window as any).dataLayer = (window as any).dataLayer || []
        ;(window as any).dataLayer.push({
            event,
            timestamp: Date.now(),
            ...payload,
        })
    } catch {
        // swallow errors in dev
    }
}
