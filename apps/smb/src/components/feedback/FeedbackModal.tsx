/**
 * FeedbackModal - Collect user feedback on recommendations
 * 
 * Features:
 * - "Was this helpful?" thumbs up/down
 * - Dismissal reason selection
 * - Optional free-form comment
 * - Submit to API for ML training
 */

import {
    Button,
    Card,
    Group,
    Modal,
    Radio,
    Stack,
    Text,
    Textarea,
} from '@mantine/core';
import { IconCheck, IconThumbDown, IconThumbUp } from '@tabler/icons-react';
import { useState } from 'react';

interface FeedbackModalProps {
    opened: boolean;
    onClose: () => void;
    recommendationId: string;
    recommendationTitle: string;
    onSubmit: (feedback: RecommendationFeedback) => void;
}

export interface RecommendationFeedback {
    helpful: boolean;
    reason?: string;
    comment?: string;
}

const DISMISSAL_REASONS = [
    { value: 'not_relevant', label: 'Not relevant to my business' },
    { value: 'wrong_data', label: 'Based on incorrect data' },
    { value: 'already_done', label: 'Already addressed this' },
    { value: 'not_priority', label: 'Not a priority right now' },
    { value: 'unclear', label: 'Recommendation unclear' },
    { value: 'other', label: 'Other reason' },
];

export function FeedbackModal({
    opened,
    onClose,
    recommendationId,
    recommendationTitle,
    onSubmit,
}: FeedbackModalProps) {
    const [helpful, setHelpful] = useState<boolean | null>(null);
    const [reason, setReason] = useState<string>('');
    const [comment, setComment] = useState('');
    const [submitted, setSubmitted] = useState(false);

    const handleClose = () => {
        // Reset state
        setHelpful(null);
        setReason('');
        setComment('');
        setSubmitted(false);
        onClose();
    };

    const handleSubmit = () => {
        if (helpful === null) return;

        const feedback: RecommendationFeedback = {
            helpful,
            reason: !helpful ? reason : undefined,
            comment: comment.trim() || undefined,
        };

        onSubmit(feedback);
        setSubmitted(true);

        // Close after short delay to show success message
        setTimeout(() => {
            handleClose();
        }, 1500);
    };

    return (
        <Modal
            opened={opened}
            onClose={handleClose}
            title="Recommendation Feedback"
            size="md"
            padding="lg"
        >
            {!submitted ? (
                <Stack gap="lg">
                    {/* Recommendation Context */}
                    <Card withBorder padding="sm" style={{ backgroundColor: 'var(--mantine-color-gray-0)' }}>
                        <Text size="sm" fw={600} lineClamp={2}>
                            {recommendationTitle}
                        </Text>
                    </Card>

                    {/* Helpful Question */}
                    <div>
                        <Text size="md" fw={600} mb="md">
                            Was this recommendation helpful?
                        </Text>
                        <Group gap="md">
                            <Button
                                size="lg"
                                variant={helpful === true ? 'filled' : 'outline'}
                                color="green"
                                leftSection={<IconThumbUp size={20} />}
                                onClick={() => setHelpful(true)}
                                style={{ flex: 1 }}
                            >
                                Yes, it helped
                            </Button>
                            <Button
                                size="lg"
                                variant={helpful === false ? 'filled' : 'outline'}
                                color="red"
                                leftSection={<IconThumbDown size={20} />}
                                onClick={() => setHelpful(false)}
                                style={{ flex: 1 }}
                            >
                                No, not helpful
                            </Button>
                        </Group>
                    </div>

                    {/* Dismissal Reason (if not helpful) */}
                    {helpful === false && (
                        <Radio.Group
                            label="Why wasn't this helpful?"
                            value={reason}
                            onChange={setReason}
                        >
                            <Stack gap="xs" mt="xs">
                                {DISMISSAL_REASONS.map((r) => (
                                    <Radio
                                        key={r.value}
                                        value={r.value}
                                        label={r.label}
                                    />
                                ))}
                            </Stack>
                        </Radio.Group>
                    )}

                    {/* Optional Comment */}
                    {helpful !== null && (
                        <Textarea
                            label="Additional feedback (optional)"
                            placeholder={
                                helpful
                                    ? "What did you find most helpful?"
                                    : "How could we make this recommendation better?"
                            }
                            value={comment}
                            onChange={(e) => setComment(e.currentTarget.value)}
                            minRows={3}
                            maxRows={6}
                        />
                    )}

                    {/* Submit */}
                    <Group justify="space-between" mt="md">
                        <Button variant="subtle" onClick={handleClose}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSubmit}
                            disabled={helpful === null || (helpful === false && !reason)}
                        >
                            Submit Feedback
                        </Button>
                    </Group>
                </Stack>
            ) : (
                /* Success State */
                <Stack align="center" gap="md" py="xl">
                    <IconCheck size={48} color="green" />
                    <Text size="lg" fw={600}>
                        Thank you for your feedback!
                    </Text>
                    <Text size="sm" c="dimmed" ta="center">
                        Your input helps us improve recommendations for you and other users.
                    </Text>
                </Stack>
            )}
        </Modal>
    );
}
