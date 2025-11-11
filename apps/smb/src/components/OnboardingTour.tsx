import { Button, Group, Modal, Stack, Text, ThemeIcon } from '@mantine/core'
import { IconCheck, IconChevronLeft, IconChevronRight, IconSparkles } from '@tabler/icons-react'
import { useState } from 'react'

interface OnboardingStep {
    title: string
    description: string
    icon: React.ReactNode
}

const STEPS: OnboardingStep[] = [
    {
        title: 'Welcome to Your Business Coach',
        description: 'I\'m your AI business coach, here to help you improve your business health. I analyze your data and provide personalized insights every day.',
        icon: <IconSparkles size={24} />
    },
    {
        title: 'Check Your Health Score',
        description: 'Your health score (0-100) tracks Revenue, Operations, and Customer metrics. Green means good, yellow needs attention, red is critical.',
        icon: '💚'
    },
    {
        title: 'Track Your Goals',
        description: 'Set business goals and I\'ll track progress automatically. I\'ll alert you when goals are at risk or when you\'re crushing it!',
        icon: '🎯'
    },
    {
        title: 'Chat Naturally',
        description: 'Ask me anything about your business: "Why is revenue down?", "What should I focus on?", "Show me top customers". I understand context!',
        icon: '💬'
    },
    {
        title: 'Take Action Fast',
        description: 'I suggest quick actions based on your data. Click any suggestion to dive deeper. I\'ll show my evidence so you can trust my advice.',
        icon: '⚡'
    }
]

interface OnboardingTourProps {
    opened: boolean
    onClose: () => void
}

export default function OnboardingTour({ opened, onClose }: OnboardingTourProps) {
    const [currentStep, setCurrentStep] = useState(0)

    const handleNext = () => {
        if (currentStep < STEPS.length - 1) {
            setCurrentStep(currentStep + 1)
        } else {
            handleComplete()
        }
    }

    const handleBack = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1)
        }
    }

    const handleComplete = () => {
        localStorage.setItem('onboarding_completed', 'true')
        onClose()
    }

    const step = STEPS[currentStep]
    const isLastStep = currentStep === STEPS.length - 1

    return (
        <Modal
            opened={opened}
            onClose={handleComplete}
            size="md"
            centered
            withCloseButton={false}
        >
            <Stack gap="xl" p="md">
                <Group justify="center">
                    <ThemeIcon size={60} radius="xl" variant="light" color="blue">
                        {typeof step.icon === 'string' ? (
                            <Text size="xl">{step.icon}</Text>
                        ) : (
                            step.icon
                        )}
                    </ThemeIcon>
                </Group>

                <Stack gap="sm" align="center">
                    <Text size="xl" fw={700} ta="center">
                        {step.title}
                    </Text>
                    <Text size="sm" c="dimmed" ta="center">
                        {step.description}
                    </Text>
                </Stack>

                <Group justify="center" gap={6}>
                    {STEPS.map((_, i) => (
                        <div
                            key={i}
                            style={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                backgroundColor: i === currentStep
                                    ? 'var(--mantine-color-blue-6)'
                                    : 'var(--mantine-color-gray-3)',
                                transition: 'background-color 0.2s'
                            }}
                        />
                    ))}
                </Group>

                <Group justify="space-between">
                    <Button
                        variant="subtle"
                        onClick={handleBack}
                        disabled={currentStep === 0}
                        leftSection={<IconChevronLeft size={16} />}
                    >
                        Back
                    </Button>

                    <Text size="xs" c="dimmed">
                        {currentStep + 1} of {STEPS.length}
                    </Text>

                    <Button
                        onClick={handleNext}
                        rightSection={isLastStep ? <IconCheck size={16} /> : <IconChevronRight size={16} />}
                    >
                        {isLastStep ? 'Get Started' : 'Next'}
                    </Button>
                </Group>

                {currentStep === 0 && (
                    <Button
                        variant="subtle"
                        onClick={handleComplete}
                        size="xs"
                        c="dimmed"
                    >
                        Skip tour
                    </Button>
                )}
            </Stack>
        </Modal>
    )
}
