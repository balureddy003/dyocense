import { ActionIcon, Button, Divider, Group, NumberInput, Popover, Select, Slider, Stack, Text } from '@mantine/core'
import { IconAdjustments, IconX } from '@tabler/icons-react'
import { useState } from 'react'

interface ModelSettings {
    temperature: number
    maxTokens: number
    model: string
}

interface ModelSettingsPopoverProps {
    settings: ModelSettings
    onChange: (settings: ModelSettings) => void
    provider?: string
}

export function ModelSettingsPopover({ settings, onChange, provider = 'ollama' }: ModelSettingsPopoverProps) {
    const [opened, setOpened] = useState(false)

    const modelOptions = {
        ollama: [
            { value: 'llama3.1', label: 'Llama 3.1' },
            { value: 'llama3.2', label: 'Llama 3.2' },
            { value: 'mistral', label: 'Mistral' },
            { value: 'codellama', label: 'Code Llama' },
        ],
        openai: [
            { value: 'gpt-4o', label: 'GPT-4o' },
            { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
            { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
            { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
        ],
        azure: [
            { value: 'gpt-4o', label: 'GPT-4o (Azure)' },
            { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Azure)' },
        ],
    }

    const models = modelOptions[provider as keyof typeof modelOptions] || modelOptions.ollama

    return (
        <Popover opened={opened} onChange={setOpened} width={320} position="bottom-end" shadow="md">
            <Popover.Target>
                <ActionIcon
                    variant="subtle"
                    size="lg"
                    onClick={() => setOpened((o) => !o)}
                    title="Model Settings"
                >
                    <IconAdjustments size={18} />
                </ActionIcon>
            </Popover.Target>

            <Popover.Dropdown>
                <Group justify="space-between" mb="sm">
                    <Text size="sm" fw={600}>
                        Model Settings
                    </Text>
                    <ActionIcon variant="subtle" size="sm" onClick={() => setOpened(false)}>
                        <IconX size={14} />
                    </ActionIcon>
                </Group>

                <Stack gap="md">
                    <Select
                        label="Model"
                        description="Which LLM to use"
                        data={models}
                        value={settings.model}
                        onChange={(val) => onChange({ ...settings, model: val || models[0].value })}
                        size="xs"
                    />

                    <div>
                        <Text size="xs" fw={500} mb={4}>
                            Temperature: {settings.temperature.toFixed(2)}
                        </Text>
                        <Slider
                            min={0}
                            max={2}
                            step={0.1}
                            value={settings.temperature}
                            onChange={(val) => onChange({ ...settings, temperature: val })}
                            marks={[
                                { value: 0, label: 'Focused' },
                                { value: 1, label: 'Balanced' },
                                { value: 2, label: 'Creative' },
                            ]}
                            size="sm"
                        />
                        <Text size="xs" c="dimmed" mt={4}>
                            Lower = more deterministic, Higher = more creative
                        </Text>
                    </div>

                    <NumberInput
                        label="Max Tokens"
                        description="Maximum response length"
                        value={settings.maxTokens}
                        onChange={(val) => onChange({ ...settings, maxTokens: Number(val) || 2048 })}
                        min={128}
                        max={8192}
                        step={128}
                        size="xs"
                    />

                    <Divider />

                    <Button
                        size="xs"
                        variant="light"
                        fullWidth
                        onClick={() => {
                            onChange({ temperature: 0.7, maxTokens: 2048, model: models[0].value })
                            setOpened(false)
                        }}
                    >
                        Reset to Defaults
                    </Button>
                </Stack>
            </Popover.Dropdown>
        </Popover>
    )
}
