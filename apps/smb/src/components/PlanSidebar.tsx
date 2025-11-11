import { Badge, Button, Card, Divider, Group, Menu, ScrollArea, Stack, Text } from '@mantine/core';
import { IconClock, IconDeviceFloppy, IconHistory, IconListCheck } from '@tabler/icons-react';

// Extract structured data from the assistant's markdown report
function extractPlan(content?: string): {
    overview: string;
    actions: string[];
    cost: number;
    evidence: string[];
    kpis: { name: string; value: string; description: string }[];
} {
    if (!content) {
        return { overview: '', actions: [], cost: 0, evidence: [], kpis: [] };
    }
    const lines = content.split('\n');

    // Overview: first non-empty paragraph (skip headings and list bullets)
    const overview = (
        lines.find(
            (l) => l.trim().length > 0 && !/^\s*#/.test(l) && !/^\s*(?:[-*•]|\d+\.)\s+/.test(l)
        ) || ''
    ).trim();

    // Evidence sources: unique [Source: ...] tags
    const evidence = Array.from(
        new Set((content.match(/\[Source:[^\]]+\]/g) || []).map((s) => s.slice(1, -1)))
    );

    // Actions: lines under headings "Recommended Actions", "Action Plan", "Next Steps"
    const actions: string[] = [];
    let inActions = false;
    for (const raw of lines) {
        const line = raw.trim();
        if (/^#+\s*(recommended actions|action plan|next steps)/i.test(line)) {
            inActions = true;
            continue;
        }
        if (/^#/.test(line)) {
            // New heading closes actions section
            inActions = false;
        }
        if (inActions) {
            const m = line.match(/^(?:[-*•]|\d+\.)\s+(.*)$/);
            if (m && m[1]) actions.push(m[1].trim());
        }
    }
    if (actions.length === 0) {
        // Fallback: collect up to 10 bullets anywhere
        for (const raw of lines) {
            const m = raw.trim().match(/^(?:[-*•]|\d+\.)\s+(.*)$/);
            if (m && m[1]) actions.push(m[1].trim());
            if (actions.length >= 10) break;
        }
    }

    // KPI table extraction: look for a table containing a KPI header cell
    const kpis: { name: string; value: string; description: string }[] = [];
    const tableHeaderIdx = lines.findIndex((l) => /\|\s*KPI\s*\|/i.test(l));
    if (tableHeaderIdx >= 0) {
        // Collect contiguous table lines (stop on blank or non-table)
        for (let i = tableHeaderIdx + 1; i < lines.length; i++) {
            const tl = lines[i];
            if (!tl.trim() || !tl.includes('|')) break;
            // Skip separator lines like | --- | --- |
            if (/^\s*\|?\s*-{3,}\s*\|/.test(tl)) continue;
            const cells = tl
                .split('|')
                .map((c) => c.trim())
                .filter((c) => c.length > 0);
            if (cells.length >= 2) {
                const [name, value, description = ''] = cells;
                if (name && value) {
                    kpis.push({ name, value, description });
                }
            }
            if (kpis.length >= 25) break;
        }
    }

    // Rough cost extraction: sum of literal $ amounts
    const moneyMatches = content.match(/\$\s?([0-9][0-9,]*(?:\.[0-9]{2})?)/g) || [];
    const cost = moneyMatches
        .map((m) => Number(m.replace(/[^0-9.]/g, '')))
        .filter((n) => !Number.isNaN(n))
        .reduce((a, b) => a + b, 0);

    return { overview, actions, cost, evidence, kpis };
}

interface PlanSidebarProps {
    tenantId?: string | null;
    personaId: string;
    content?: string;
}

export function PlanSidebar({ tenantId, personaId, content }: PlanSidebarProps) {
    const storageKey = `plan-versions-${tenantId || 'anon'}-${personaId}`;
    const { overview, actions, cost, evidence, kpis } = extractPlan(content);

    const saveVersion = () => {
        const versions = JSON.parse(localStorage.getItem(storageKey) || '[]') as any[];
        versions.unshift({ id: Date.now().toString(), name: new Date().toLocaleString(), content });
        localStorage.setItem(storageKey, JSON.stringify(versions.slice(0, 20)));
    };

    const restoreVersion = (v: any) => {
        if (navigator?.clipboard && v?.content) navigator.clipboard.writeText(v.content);
    };

    const versions = JSON.parse(localStorage.getItem(storageKey) || '[]') as any[];

    return (
        <Stack gap="md">
            <Card withBorder radius="md" p="md">
                <Group justify="space-between" mb="xs">
                    <Group gap="xs">
                        <IconListCheck size={18} />
                        <Text fw={600} size="sm">
                            Plan Inspector
                        </Text>
                    </Group>
                    <Group gap="xs">
                        <Button
                            size="xs"
                            variant="light"
                            leftSection={<IconDeviceFloppy size={14} />}
                            onClick={saveVersion}
                        >
                            Save version
                        </Button>
                        <Menu shadow="md" width={260}>
                            <Menu.Target>
                                <Button size="xs" variant="subtle" leftSection={<IconHistory size={14} />}>Versions</Button>
                            </Menu.Target>
                            <Menu.Dropdown>
                                {versions.length === 0 && <Menu.Item disabled>No versions yet</Menu.Item>}
                                {versions.map((v) => (
                                    <Menu.Item
                                        key={v.id}
                                        leftSection={<IconClock size={14} />}
                                        onClick={() => restoreVersion(v)}
                                    >
                                        {v.name}
                                    </Menu.Item>
                                ))}
                            </Menu.Dropdown>
                        </Menu>
                    </Group>
                </Group>
                <Text size="xs" c="dimmed">
                    Overview
                </Text>
                <Text size="sm" mb="sm">
                    {overview || 'No overview detected yet. Ask for an action plan to populate this panel.'}
                </Text>
                <Group gap="xs">
                    <Badge size="sm" color="blue">
                        Actions {actions.length}
                    </Badge>
                    <Badge size="sm" color="grape">
                        KPIs {kpis.length}
                    </Badge>
                    <Badge size="sm" color="green">Evidence {evidence.length}</Badge>
                    {cost > 0 && (
                        <Badge size="sm" color="teal">
                            Costs ~$ {cost.toLocaleString()}
                        </Badge>
                    )}
                </Group>
            </Card>

            <Card withBorder radius="md" p={0} style={{ overflow: 'hidden' }}>
                <ScrollArea h={360} p="md">
                    <Stack gap="xs">
                        {actions.length === 0 && (
                            <Text size="sm" c="dimmed">
                                No actions parsed yet. The assistant's next report with a "Recommended Actions" section will
                                appear here.
                            </Text>
                        )}
                        {actions.map((a, i) => (
                            <Group key={i} align="flex-start">
                                <Badge size="xs" variant="light" color="gray">
                                    {i + 1}
                                </Badge>
                                <Text size="sm" style={{ flex: 1 }}>
                                    {a}
                                </Text>
                            </Group>
                        ))}
                        {(kpis.length > 0 || evidence.length > 0) && <Divider my="sm" />}
                        {kpis.length > 0 && (
                            <>
                                <Text size="xs" c="dimmed">
                                    KPI Snapshot
                                </Text>
                                {kpis.slice(0, 6).map((k, i) => (
                                    <Group key={`kpi-${i}`} gap="xs">
                                        <Badge size="xs" color="indigo" variant="light">
                                            {k.name}
                                        </Badge>
                                        <Text size="xs" fw={600}>
                                            {k.value}
                                        </Text>
                                        <Text size="xs" c="dimmed" style={{ flex: 1 }}>
                                            {k.description}
                                        </Text>
                                    </Group>
                                ))}
                            </>
                        )}
                        {evidence.length > 0 && (
                            <>
                                <Divider my="xs" />
                                <Text size="xs" c="dimmed">
                                    Evidence Sources
                                </Text>
                                {evidence.map((e, i) => (
                                    <Group key={`ev-${i}`} gap="xs">
                                        <Badge size="xs" color="green" variant="light">
                                            {i + 1}
                                        </Badge>
                                        <Text size="xs" style={{ flex: 1 }}>
                                            {e.replace(/^Source:\s*/, '')}
                                        </Text>
                                    </Group>
                                ))}
                            </>
                        )}
                    </Stack>
                </ScrollArea>
            </Card>
        </Stack>
    );
}
