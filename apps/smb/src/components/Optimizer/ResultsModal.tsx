import { Badge, Group, Modal, Stack, Table, Text, Title } from '@mantine/core'
import React from 'react'

export type OptimizationResults = {
    objective?: string
    total_cost?: number
    savings?: number
    eoq?: Array<{ sku: string; eoq: number; reorder_point?: number; safety_stock?: number }>
    schedule?: Array<{ period: string; staff: number }>
    details?: Record<string, any>
}

export type ResultsModalProps = {
    opened: boolean
    onClose: () => void
    title?: string
    results?: OptimizationResults | null
}

const Currency = ({ value }: { value: number | undefined }) => (
    <Text fw={600}>{typeof value === 'number' ? value.toLocaleString(undefined, { style: 'currency', currency: 'USD' }) : '-'}</Text>
)

export const ResultsModal: React.FC<ResultsModalProps> = ({ opened, onClose, title = 'Optimization Results', results }) => {
    return (
        <Modal opened={opened} onClose={onClose} title={title} centered size="lg">
            <Stack>
                {results ? (
                    <>
                        <Group>
                            {results.objective && <Badge color="blue">Objective: {results.objective}</Badge>}
                            {typeof results.total_cost === 'number' && <Badge color="grape">Total Cost: <Currency value={results.total_cost} /></Badge>}
                            {typeof results.savings === 'number' && <Badge color="teal">Savings: <Currency value={results.savings} /></Badge>}
                        </Group>

                        {Array.isArray(results.eoq) && results.eoq.length > 0 && (
                            <div>
                                <Title order={5}>EOQ Recommendations</Title>
                                <Table striped highlightOnHover withTableBorder>
                                    <Table.Thead>
                                        <Table.Tr>
                                            <Table.Th>SKU</Table.Th>
                                            <Table.Th>EOQ</Table.Th>
                                            <Table.Th>Reorder Point</Table.Th>
                                            <Table.Th>Safety Stock</Table.Th>
                                        </Table.Tr>
                                    </Table.Thead>
                                    <Table.Tbody>
                                        {results.eoq.map((row) => (
                                            <Table.Tr key={row.sku}>
                                                <Table.Td>{row.sku}</Table.Td>
                                                <Table.Td>{Math.round(row.eoq)}</Table.Td>
                                                <Table.Td>{row.reorder_point ?? '-'}</Table.Td>
                                                <Table.Td>{row.safety_stock ?? '-'}</Table.Td>
                                            </Table.Tr>
                                        ))}
                                    </Table.Tbody>
                                </Table>
                            </div>
                        )}

                        {Array.isArray(results.schedule) && results.schedule.length > 0 && (
                            <div>
                                <Title order={5}>Staffing Schedule</Title>
                                <Table withTableBorder>
                                    <Table.Thead>
                                        <Table.Tr>
                                            <Table.Th>Period</Table.Th>
                                            <Table.Th>Staff</Table.Th>
                                        </Table.Tr>
                                    </Table.Thead>
                                    <Table.Tbody>
                                        {results.schedule.map((row, idx) => (
                                            <Table.Tr key={`${row.period}-${idx}`}>
                                                <Table.Td>{row.period}</Table.Td>
                                                <Table.Td>{row.staff}</Table.Td>
                                            </Table.Tr>
                                        ))}
                                    </Table.Tbody>
                                </Table>
                            </div>
                        )}

                        {results.details && (
                            <div>
                                <Title order={5}>Details</Title>
                                <pre style={{ background: '#f8f9fa', padding: 12, borderRadius: 8, fontSize: 12 }}>
                                    {JSON.stringify(results.details, null, 2)}
                                </pre>
                            </div>
                        )}
                    </>
                ) : (
                    <Text c="dimmed">No results available yet.</Text>
                )}
            </Stack>
        </Modal>
    )
}

export default ResultsModal
