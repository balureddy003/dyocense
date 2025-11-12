import { Button, Card, Group, Stack, Text, Textarea } from '@mantine/core'
import { useState } from 'react'
import { post } from '../lib/api'

export type HumanReview = {
    reviewId: string
    proposedResult: any
}

type Props = {
    tenantId: string
    apiToken?: string
    review: HumanReview
    onSubmitted?: (summary: any) => void
}

export function HumanReviewPanel({ tenantId, apiToken, review, onSubmitted }: Props) {
    const [feedback, setFeedback] = useState('')
    const [corrections, setCorrections] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const submit = async (approved: boolean) => {
        setSubmitting(true)
        setError(null)
        try {
            let correctionsJson: any | undefined = undefined
            if (corrections.trim()) {
                try { correctionsJson = JSON.parse(corrections) } catch (e: any) {
                    setError('Corrections must be valid JSON')
                    setSubmitting(false)
                    return
                }
            }

            const summary = await post(`/v1/tenants/${tenantId}/task-planner/reviews/${review.reviewId}`, {
                approved,
                feedback: feedback || undefined,
                corrections: correctionsJson,
            }, apiToken)
            onSubmitted?.(summary)
        } catch (e: any) {
            setError(e?.message || 'Failed to submit review')
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <Card withBorder radius="md" padding="md" style={{ background: '#fffaf0', borderColor: '#fbbf24' }}>
            <Stack gap={8}>
                <Text size="sm" fw={600}>⏸ Awaiting Human Approval</Text>
                <Text size="xs" c="dimmed">Review ID: {review.reviewId}</Text>
                <Text size="sm">Proposed result preview:</Text>
                <pre style={{ maxHeight: 160, overflow: 'auto', background: '#fff', padding: 8, borderRadius: 6, border: '1px solid #eee' }}>
                    {JSON.stringify(review.proposedResult, null, 2)}
                </pre>
                <Textarea
                    label="Feedback (optional)"
                    placeholder="Add reviewer comments"
                    autosize
                    minRows={2}
                    value={feedback}
                    onChange={(e) => setFeedback(e.currentTarget.value)}
                />
                <Textarea
                    label="Corrections JSON (optional)"
                    placeholder='e.g. {"title":"Updated Report Title"}'
                    autosize
                    minRows={2}
                    value={corrections}
                    onChange={(e) => setCorrections(e.currentTarget.value)}
                />
                {error && <Text size="xs" c="red">{error}</Text>}
                <Group justify="flex-end" gap={8}>
                    <Button size="xs" variant="default" onClick={() => submit(false)} loading={submitting}>Request changes</Button>
                    <Button size="xs" color="teal" onClick={() => submit(true)} loading={submitting}>Approve</Button>
                </Group>
            </Stack>
        </Card>
    )
}
