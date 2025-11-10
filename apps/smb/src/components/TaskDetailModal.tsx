import { Button, Divider, List, Modal, Stack, Text, Textarea, Title } from '@mantine/core'
import { IconSparkles } from '@tabler/icons-react'
import { useState } from 'react'

interface TaskDetail {
    reasoning: string
    steps: string[]
    impact: string
    estimatedTime: string
}

interface TaskDetailModalProps {
    opened: boolean
    onClose: () => void
    task: {
        id: string
        title: string
        category: string
    }
}

/**
 * Generate AI-powered task details with reasoning, steps, and impact
 */
function generateTaskDetails(task: { title: string; category: string }): TaskDetail {
    const { title, category } = task

    // Mock AI-generated details based on task title and category
    if (title.toLowerCase().includes('email campaign') || title.toLowerCase().includes('black friday')) {
        return {
            reasoning:
                'Email marketing has 4× ROI for e-commerce. With Q4 revenue goal of $100K, a successful Black Friday campaign could drive $15-20K in sales.',
            steps: [
                'Segment your email list (past customers, abandoned carts, subscribers)',
                'Design 3 emails: teaser (Nov 20), main offer (Nov 24), last chance (Nov 26)',
                'Create 20-30% off offer for lawn care products',
                'Set up automation in your email tool (Mailchimp/Klaviyo)',
                'Test emails on mobile and desktop before sending',
            ],
            impact: 'Expected: 15-20% email open rate, 5-8% click rate, $15-20K revenue',
            estimatedTime: '3-4 hours',
        }
    }

    if (title.toLowerCase().includes('revenue streams') || title.toLowerCase().includes('analyze')) {
        return {
            reasoning: 'Understanding which products/services drive revenue helps you focus marketing and inventory decisions on winners.',
            steps: [
                'Export last 90 days of sales data from GrandNode',
                'Calculate revenue by product category',
                'Identify top 20% products generating 80% of revenue',
                'Check profit margin for each category',
                'Document findings in a simple spreadsheet',
            ],
            impact: 'Expected: Clear picture of best-sellers, informed inventory decisions, 10-15% revenue increase from focusing on winners',
            estimatedTime: '2 hours',
        }
    }

    if (title.toLowerCase().includes('inventory') || title.toLowerCase().includes('audit')) {
        return {
            reasoning:
                'Inventory audit prevents stockouts of best-sellers and reduces capital tied up in slow-moving items. Critical for cash flow.',
            steps: [
                'Pull current inventory levels from Salesforce Kennedy ERP',
                'Compare against sales velocity (units/week)',
                'Identify products with <2 weeks of stock (reorder urgently)',
                'Flag products with >12 weeks of stock (slow-moving)',
                'Create reorder list with recommended quantities',
            ],
            impact: 'Expected: Prevent 2-3 stockouts/month, free up $5-10K in working capital from slow inventory',
            estimatedTime: '3 hours',
        }
    }

    if (title.toLowerCase().includes('loyalty') || title.toLowerCase().includes('customer')) {
        return {
            reasoning: 'Repeat customers spend 3× more than new customers. A loyalty program increases lifetime value and word-of-mouth.',
            steps: [
                'Design simple points system: $1 spent = 1 point, 100 points = $5 discount',
                'Set up loyalty module in GrandNode',
                'Create welcome email explaining program benefits',
                'Add loyalty signup prompt at checkout',
                'Launch with special "founding member" bonus (50 points)',
            ],
            impact: 'Expected: 15-20% signup rate, 25% increase in repeat purchase rate within 6 months',
            estimatedTime: '4-5 hours',
        }
    }

    if (title.toLowerCase().includes('pricing') || title.toLowerCase().includes('optimize')) {
        return {
            reasoning:
                'Small pricing adjustments (5-10%) often have minimal impact on conversion but significantly boost margins. Test and measure.',
            steps: [
                'Identify products with <30% margin',
                'Research competitor pricing for same/similar products',
                'Test 5-10% price increase on low-margin items',
                'Monitor conversion rate for 2 weeks',
                'Roll back if conversion drops >15%, keep if stable',
            ],
            impact: 'Expected: 3-5% overall margin improvement without sacrificing volume',
            estimatedTime: '2-3 hours',
        }
    }

    // Default generic task details
    return {
        reasoning: `This ${category} task helps you make progress toward your goal by taking focused action.`,
        steps: [
            'Review the current state and gather relevant data',
            'Identify the specific action or decision needed',
            'Execute the task with attention to detail',
            'Document results and next steps',
            'Share outcome with your team if applicable',
        ],
        impact: 'Expected: Measurable progress toward your goal with clear next steps',
        estimatedTime: '1-2 hours',
    }
}

export default function TaskDetailModal({ opened, onClose, task }: TaskDetailModalProps) {
    const [refinementInput, setRefinementInput] = useState('')
    const [isRefining, setIsRefining] = useState(false)

    const details = generateTaskDetails(task)

    const handleRefineTask = async () => {
        if (!refinementInput.trim()) return

        setIsRefining(true)
        // Simulate AI refinement
        await new Promise((resolve) => setTimeout(resolve, 1000))
        setIsRefining(false)

        // In production, this would call AI to adjust the task
        // For now, just show feedback
        setRefinementInput('')
        onClose()
    }

    return (
        <Modal opened={opened} onClose={onClose} size="lg" title={<Title order={3}>{task.title}</Title>} centered>
            <Stack gap="lg">
                {/* Why this matters */}
                <div>
                    <Text fw={600} size="sm" mb="xs">
                        Why this matters:
                    </Text>
                    <Text size="sm" c="dimmed">
                        {details.reasoning}
                    </Text>
                </div>

                {/* How to do it */}
                <div>
                    <Text fw={600} size="sm" mb="xs">
                        How to do it:
                    </Text>
                    <List size="sm" spacing="xs" withPadding>
                        {details.steps.map((step, index) => (
                            <List.Item key={index}>
                                <Text size="sm">{step}</Text>
                            </List.Item>
                        ))}
                    </List>
                </div>

                {/* Expected impact */}
                <div>
                    <Text fw={600} size="sm" mb="xs">
                        Expected impact:
                    </Text>
                    <Text size="sm" c="teal.6">
                        {details.impact}
                    </Text>
                </div>

                {/* Estimated time */}
                <div>
                    <Text fw={600} size="sm" mb="xs">
                        Estimated time:
                    </Text>
                    <Text size="sm" c="dimmed">
                        ⏱️ {details.estimatedTime}
                    </Text>
                </div>

                <Divider />

                {/* Chat-based refinement */}
                <div>
                    <Text size="sm" c="dimmed" mb="sm">
                        Need this task adjusted?
                    </Text>
                    <Textarea
                        placeholder="E.g., 'Break this into smaller steps' or 'Focus on email marketing only'"
                        minRows={2}
                        value={refinementInput}
                        onChange={(e) => setRefinementInput(e.target.value)}
                        leftSection={<IconSparkles size={18} />}
                    />
                    <Button
                        mt="sm"
                        onClick={handleRefineTask}
                        disabled={!refinementInput.trim()}
                        loading={isRefining}
                        leftSection={<IconSparkles size={18} />}
                        fullWidth
                    >
                        {isRefining ? 'Refining with AI...' : 'Refine with AI Coach'}
                    </Button>
                </div>
            </Stack>
        </Modal>
    )
}
