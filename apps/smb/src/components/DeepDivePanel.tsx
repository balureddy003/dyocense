import { Collapse, Group, Loader, Stack, Text, ThemeIcon, UnstyledButton } from '@mantine/core'
import { IconChevronDown, IconChevronUp, IconCircleCheck, IconDots } from '@tabler/icons-react'
import { useState } from 'react'

export type DeepDiveStep = {
    id: string
    label: string
    done: boolean
}

interface DeepDivePanelProps {
    steps: DeepDiveStep[]
    running: boolean
}

export function DeepDivePanel({ steps, running }: DeepDivePanelProps) {
    const [opened, setOpened] = useState(true)
    const allDone = steps.every(s => s.done)

    return (
        <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, background: '#ffffff' }}>
            <UnstyledButton
                onClick={() => setOpened(!opened)}
                style={{ width: '100%', padding: '10px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
            >
                <Group gap="sm">
                    <Text size="sm" fw={600} c="#0f172a">DeepDive Thinking {allDone ? 'Finished' : ''}</Text>
                    {!allDone && running && <Loader size="xs" />}
                </Group>
                {opened ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
            </UnstyledButton>
            <Collapse in={opened}>
                <Stack gap="xs" p="sm" style={{ background: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
                    {steps.map((s) => (
                        <Group key={s.id} gap="xs">
                            <ThemeIcon size="sm" radius="xl" variant={s.done ? 'light' : 'outline'} color={s.done ? 'teal' : 'gray'}>
                                {s.done ? <IconCircleCheck size={14} /> : <IconDots size={14} />}
                            </ThemeIcon>
                            <Text size="sm" c={s.done ? 'teal.9' : 'gray.7'}>{s.label}</Text>
                        </Group>
                    ))}
                </Stack>
            </Collapse>
        </div>
    )
}
