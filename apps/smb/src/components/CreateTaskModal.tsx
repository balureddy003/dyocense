import { Button, Group, Modal, Select, Stack, TextInput } from '@mantine/core'
import { useEffect, useState } from 'react'

export type CreateTaskPayload = {
    title: string
    status?: 'todo' | 'in_progress' | 'completed'
    priority?: 'low' | 'medium' | 'high' | 'urgent'
    horizon?: 'daily' | 'weekly' | 'quarterly' | 'yearly'
}

interface CreateTaskModalProps {
    opened: boolean
    onClose: () => void
    onCreate: (task: CreateTaskPayload) => Promise<void> | void
    initialTitle?: string
}

export default function CreateTaskModal({ opened, onClose, onCreate, initialTitle }: CreateTaskModalProps) {
    const [title, setTitle] = useState(initialTitle || '')
    const [priority, setPriority] = useState<'low' | 'medium' | 'high' | 'urgent'>('medium')
    const [horizon, setHorizon] = useState<'daily' | 'weekly' | 'quarterly' | 'yearly'>('weekly')
    const [submitting, setSubmitting] = useState(false)

    useEffect(() => {
        setTitle(initialTitle || '')
    }, [initialTitle, opened])

    const handleCreate = async () => {
        if (!title.trim()) return
        setSubmitting(true)
        try {
            await onCreate({ title: title.trim(), status: 'todo', priority, horizon })
            onClose()
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <Modal opened={opened} onClose={onClose} title="Save as task" centered>
            <Stack gap="sm">
                <TextInput label="Title" placeholder="Describe the task" value={title} onChange={(e) => setTitle(e.currentTarget.value)} autoFocus />
                <Group grow>
                    <Select label="Priority" data={[{ label: 'Low', value: 'low' }, { label: 'Medium', value: 'medium' }, { label: 'High', value: 'high' }, { label: 'Urgent', value: 'urgent' }]} value={priority} onChange={(v) => setPriority((v as any) || 'medium')} />
                    <Select label="Horizon" data={[{ label: 'Daily', value: 'daily' }, { label: 'Weekly', value: 'weekly' }, { label: 'Quarterly', value: 'quarterly' }, { label: 'Yearly', value: 'yearly' }]} value={horizon} onChange={(v) => setHorizon((v as any) || 'weekly')} />
                </Group>
                <Group justify="flex-end" mt="sm">
                    <Button variant="subtle" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleCreate} loading={submitting}>Create task</Button>
                </Group>
            </Stack>
        </Modal>
    )
}
