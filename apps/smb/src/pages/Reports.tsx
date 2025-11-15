import {
    ActionIcon,
    Alert,
    Badge,
    Button,
    Card,
    Container,
    CopyButton,
    Grid,
    Group,
    Modal,
    MultiSelect,
    NumberInput,
    Select,
    Stack,
    Switch,
    Table,
    Tabs,
    Text,
    Textarea,
    TextInput,
    Title,
    Tooltip,
} from '@mantine/core';
import {
    IconCalendar,
    IconCheck,
    IconCopy,
    IconDownload,
    IconEye,
    IconFileText,
    IconLock,
    IconShare,
    IconTrash
} from '@tabler/icons-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

const apiUrl = (import.meta as any).env?.VITE_API_URL || '';

interface Report {
    id: string;
    title: string;
    template: string;
    format: string;
    file_size: number;
    generated_at: string;
    generated_by: string;
    metadata: Record<string, any>;
}

interface ReportSchedule {
    id: string;
    title: string;
    template: string;
    frequency: string;
    recipients: string[];
    enabled: boolean;
    next_run: string | null;
}

const metricOptions = [
    { value: 'revenue', label: 'Revenue' },
    { value: 'health_score', label: 'Health Score' },
    { value: 'task_completion', label: 'Task Completion' },
    { value: 'profit_margin', label: 'Profit Margin' },
];

const templateOptions = [
    { value: 'daily_summary', label: 'Daily Summary' },
    { value: 'weekly_performance', label: 'Weekly Performance' },
    { value: 'monthly_overview', label: 'Monthly Overview' },
    { value: 'custom', label: 'Custom Report' },
];

const formatOptions = [
    { value: 'html', label: 'HTML' },
    { value: 'pdf', label: 'PDF' },
    { value: 'markdown', label: 'Markdown' },
];

const frequencyOptions = [
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
];

export function Reports() {
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState<string | null>('reports');

    // Report generation state
    const [generateModalOpen, setGenerateModalOpen] = useState(false);
    const [template, setTemplate] = useState('weekly_performance');
    const [reportTitle, setReportTitle] = useState('Weekly Performance Report');
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['revenue', 'health_score']);
    const [format, setFormat] = useState('html');
    const [startDate, setStartDate] = useState(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000));
    const [endDate, setEndDate] = useState(new Date());

    // Share modal state
    const [shareModalOpen, setShareModalOpen] = useState(false);
    const [shareReportId, setShareReportId] = useState<string | null>(null);
    const [shareExpiryDays, setShareExpiryDays] = useState(7);
    const [sharePassword, setSharePassword] = useState('');
    const [shareUrl, setShareUrl] = useState('');

    // Schedule modal state
    const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
    const [scheduleTitle, setScheduleTitle] = useState('Weekly Report');
    const [scheduleTemplate, setScheduleTemplate] = useState('weekly_performance');
    const [scheduleMetrics, setScheduleMetrics] = useState<string[]>(['revenue', 'health_score']);
    const [scheduleFrequency, setScheduleFrequency] = useState('weekly');
    const [scheduleTime, setScheduleTime] = useState('09:00');
    const [scheduleRecipients, setScheduleRecipients] = useState('');
    const [scheduleDayOfWeek, setScheduleDayOfWeek] = useState(1);

    // View report modal
    const [viewModalOpen, setViewModalOpen] = useState(false);
    const [viewReportContent, setViewReportContent] = useState('');

    // Fetch reports
    const { data: reportsData, isLoading: reportsLoading } = useQuery({
        queryKey: ['reports'],
        queryFn: async () => {
            const response = await fetch(`${apiUrl}/v1/tenants/test-tenant/reports`);
            if (!response.ok) throw new Error('Failed to fetch reports');
            return response.json();
        },
        refetchInterval: 30000,
    });

    // Fetch schedules
    const { data: schedulesData, isLoading: schedulesLoading } = useQuery({
        queryKey: ['report-schedules'],
        queryFn: async () => {
            const response = await fetch(`${apiUrl}/v1/tenants/test-tenant/reports/schedules`);
            if (!response.ok) throw new Error('Failed to fetch schedules');
            return response.json();
        },
        refetchInterval: 30000,
    });

    // Generate report mutation
    const generateReportMutation = useMutation({
        mutationFn: async () => {
            const params = new URLSearchParams({
                template,
                title: reportTitle,
                metrics: selectedMetrics.join(','),
                start_date: startDate.toISOString(),
                end_date: endDate.toISOString(),
                format,
            });

            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/reports/generate?${params}`,
                { method: 'POST' }
            );

            if (!response.ok) throw new Error('Failed to generate report');
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reports'] });
            setGenerateModalOpen(false);
        },
    });

    // Share report mutation
    const shareReportMutation = useMutation({
        mutationFn: async (reportId: string) => {
            const params = new URLSearchParams({
                expires_in_days: shareExpiryDays.toString(),
            });

            if (sharePassword) {
                params.append('password', sharePassword);
            }

            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/reports/${reportId}/share?${params}`,
                { method: 'POST' }
            );

            if (!response.ok) throw new Error('Failed to share report');
            return response.json();
        },
        onSuccess: (data) => {
            setShareUrl(`${window.location.origin}${data.share_url}`);
        },
    });

    // Create schedule mutation
    const createScheduleMutation = useMutation({
        mutationFn: async () => {
            const params = new URLSearchParams({
                template: scheduleTemplate,
                title: scheduleTitle,
                metrics: scheduleMetrics.join(','),
                frequency: scheduleFrequency,
                time: scheduleTime,
                recipients: scheduleRecipients,
            });

            if (scheduleFrequency === 'weekly') {
                params.append('day_of_week', scheduleDayOfWeek.toString());
            }

            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/reports/schedules?${params}`,
                { method: 'POST' }
            );

            if (!response.ok) throw new Error('Failed to create schedule');
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['report-schedules'] });
            setScheduleModalOpen(false);
        },
    });

    // Delete schedule mutation
    const deleteScheduleMutation = useMutation({
        mutationFn: async (scheduleId: string) => {
            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/reports/schedules/${scheduleId}`,
                { method: 'DELETE' }
            );

            if (!response.ok) throw new Error('Failed to delete schedule');
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['report-schedules'] });
        },
    });

    // Toggle schedule mutation
    const toggleScheduleMutation = useMutation({
        mutationFn: async ({ scheduleId, enabled }: { scheduleId: string; enabled: boolean }) => {
            const params = new URLSearchParams({
                enabled: enabled.toString(),
            });

            const response = await fetch(
                `${apiUrl}/v1/tenants/test-tenant/reports/schedules/${scheduleId}?${params}`,
                { method: 'PUT' }
            );

            if (!response.ok) throw new Error('Failed to update schedule');
            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['report-schedules'] });
        },
    });

    const handleGenerateReport = () => {
        generateReportMutation.mutate();
    };

    const handleShareReport = (reportId: string) => {
        setShareReportId(reportId);
        setShareUrl('');
        setSharePassword('');
        setShareExpiryDays(7);
        setShareModalOpen(true);
    };

    const handleConfirmShare = () => {
        if (shareReportId) {
            shareReportMutation.mutate(shareReportId);
        }
    };

    const handleViewReport = async (reportId: string) => {
        try {
            const response = await fetch(`${apiUrl}/v1/tenants/test-tenant/reports/${reportId}`);
            if (!response.ok) throw new Error('Failed to fetch report');
            const data = await response.json();
            setViewReportContent(data.content);
            setViewModalOpen(true);
        } catch (error) {
            console.error('Error viewing report:', error);
        }
    };

    const handleDownloadReport = async (reportId: string, title: string) => {
        try {
            const response = await fetch(`${apiUrl}/v1/tenants/test-tenant/reports/${reportId}`);
            if (!response.ok) throw new Error('Failed to fetch report');
            const data = await response.json();

            const blob = new Blob([data.content], { type: 'text/html' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${title}.html`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading report:', error);
        }
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const formatDate = (dateString: string): string => {
        return new Date(dateString).toLocaleString();
    };

    const reports: Report[] = reportsData?.reports || [];
    const schedules: ReportSchedule[] = schedulesData?.schedules || [];

    return (
        <Container size="xl" py="xl">
            <Group justify="space-between" mb="xl">
                <Title order={1}>📊 Reports</Title>
                <Group>
                    <Button
                        leftSection={<IconFileText size={16} />}
                        onClick={() => setGenerateModalOpen(true)}
                    >
                        Generate Report
                    </Button>
                    <Button
                        leftSection={<IconCalendar size={16} />}
                        variant="light"
                        onClick={() => setScheduleModalOpen(true)}
                    >
                        Schedule Report
                    </Button>
                </Group>
            </Group>

            <Tabs value={activeTab} onChange={setActiveTab}>
                <Tabs.List>
                    <Tabs.Tab value="reports" leftSection={<IconFileText size={16} />}>
                        Generated Reports
                    </Tabs.Tab>
                    <Tabs.Tab value="schedules" leftSection={<IconCalendar size={16} />}>
                        Scheduled Reports
                    </Tabs.Tab>
                </Tabs.List>

                <Tabs.Panel value="reports" pt="md">
                    <Card shadow="sm" padding="lg" radius="md" withBorder>
                        {reportsLoading ? (
                            <Text>Loading reports...</Text>
                        ) : reports.length === 0 ? (
                            <Alert color="blue" title="No reports yet">
                                Generate your first report to get started!
                            </Alert>
                        ) : (
                            <Table highlightOnHover>
                                <Table.Thead>
                                    <Table.Tr>
                                        <Table.Th>Title</Table.Th>
                                        <Table.Th>Template</Table.Th>
                                        <Table.Th>Format</Table.Th>
                                        <Table.Th>Size</Table.Th>
                                        <Table.Th>Generated</Table.Th>
                                        <Table.Th>Actions</Table.Th>
                                    </Table.Tr>
                                </Table.Thead>
                                <Table.Tbody>
                                    {reports.map((report) => (
                                        <Table.Tr key={report.id}>
                                            <Table.Td>{report.title}</Table.Td>
                                            <Table.Td>
                                                <Badge variant="light">
                                                    {report.template.replace('_', ' ')}
                                                </Badge>
                                            </Table.Td>
                                            <Table.Td>
                                                <Badge color="blue">{report.format.toUpperCase()}</Badge>
                                            </Table.Td>
                                            <Table.Td>{formatFileSize(report.file_size)}</Table.Td>
                                            <Table.Td>{formatDate(report.generated_at)}</Table.Td>
                                            <Table.Td>
                                                <Group gap="xs">
                                                    <Tooltip label="View Report">
                                                        <ActionIcon
                                                            variant="light"
                                                            color="blue"
                                                            onClick={() => handleViewReport(report.id)}
                                                        >
                                                            <IconEye size={16} />
                                                        </ActionIcon>
                                                    </Tooltip>
                                                    <Tooltip label="Download">
                                                        <ActionIcon
                                                            variant="light"
                                                            color="green"
                                                            onClick={() => handleDownloadReport(report.id, report.title)}
                                                        >
                                                            <IconDownload size={16} />
                                                        </ActionIcon>
                                                    </Tooltip>
                                                    <Tooltip label="Share">
                                                        <ActionIcon
                                                            variant="light"
                                                            color="orange"
                                                            onClick={() => handleShareReport(report.id)}
                                                        >
                                                            <IconShare size={16} />
                                                        </ActionIcon>
                                                    </Tooltip>
                                                </Group>
                                            </Table.Td>
                                        </Table.Tr>
                                    ))}
                                </Table.Tbody>
                            </Table>
                        )}
                    </Card>
                </Tabs.Panel>

                <Tabs.Panel value="schedules" pt="md">
                    <Card shadow="sm" padding="lg" radius="md" withBorder>
                        {schedulesLoading ? (
                            <Text>Loading schedules...</Text>
                        ) : schedules.length === 0 ? (
                            <Alert color="blue" title="No scheduled reports">
                                Create a schedule to receive reports automatically!
                            </Alert>
                        ) : (
                            <Table highlightOnHover>
                                <Table.Thead>
                                    <Table.Tr>
                                        <Table.Th>Title</Table.Th>
                                        <Table.Th>Frequency</Table.Th>
                                        <Table.Th>Recipients</Table.Th>
                                        <Table.Th>Next Run</Table.Th>
                                        <Table.Th>Status</Table.Th>
                                        <Table.Th>Actions</Table.Th>
                                    </Table.Tr>
                                </Table.Thead>
                                <Table.Tbody>
                                    {schedules.map((schedule) => (
                                        <Table.Tr key={schedule.id}>
                                            <Table.Td>{schedule.title}</Table.Td>
                                            <Table.Td>
                                                <Badge variant="light">
                                                    {schedule.frequency}
                                                </Badge>
                                            </Table.Td>
                                            <Table.Td>
                                                <Text size="sm">{schedule.recipients.length} recipient(s)</Text>
                                            </Table.Td>
                                            <Table.Td>
                                                {schedule.next_run ? (
                                                    <Text size="sm">{formatDate(schedule.next_run)}</Text>
                                                ) : (
                                                    <Text size="sm" c="dimmed">Not scheduled</Text>
                                                )}
                                            </Table.Td>
                                            <Table.Td>
                                                <Switch
                                                    checked={schedule.enabled}
                                                    onChange={(e) =>
                                                        toggleScheduleMutation.mutate({
                                                            scheduleId: schedule.id,
                                                            enabled: e.currentTarget.checked,
                                                        })
                                                    }
                                                />
                                            </Table.Td>
                                            <Table.Td>
                                                <Tooltip label="Delete Schedule">
                                                    <ActionIcon
                                                        variant="light"
                                                        color="red"
                                                        onClick={() => deleteScheduleMutation.mutate(schedule.id)}
                                                    >
                                                        <IconTrash size={16} />
                                                    </ActionIcon>
                                                </Tooltip>
                                            </Table.Td>
                                        </Table.Tr>
                                    ))}
                                </Table.Tbody>
                            </Table>
                        )}
                    </Card>
                </Tabs.Panel>
            </Tabs>

            {/* Generate Report Modal */}
            <Modal
                opened={generateModalOpen}
                onClose={() => setGenerateModalOpen(false)}
                title="Generate Report"
                size="lg"
            >
                <Stack>
                    <TextInput
                        label="Report Title"
                        placeholder="Weekly Performance Report"
                        value={reportTitle}
                        onChange={(e) => setReportTitle(e.currentTarget.value)}
                        required
                    />

                    <Select
                        label="Template"
                        data={templateOptions}
                        value={template}
                        onChange={(value) => setTemplate(value || 'weekly_performance')}
                        required
                    />

                    <MultiSelect
                        label="Metrics"
                        data={metricOptions}
                        value={selectedMetrics}
                        onChange={setSelectedMetrics}
                        required
                    />

                    <Select
                        label="Format"
                        data={formatOptions}
                        value={format}
                        onChange={(value) => setFormat(value || 'html')}
                        required
                    />

                    <Grid>
                        <Grid.Col span={6}>
                            <Text size="sm" fw={500}>Start Date</Text>
                            <Text size="sm" c="dimmed">{startDate.toLocaleDateString()}</Text>
                        </Grid.Col>
                        <Grid.Col span={6}>
                            <Text size="sm" fw={500}>End Date</Text>
                            <Text size="sm" c="dimmed">{endDate.toLocaleDateString()}</Text>
                        </Grid.Col>
                    </Grid>

                    <Button
                        fullWidth
                        onClick={handleGenerateReport}
                        loading={generateReportMutation.isPending}
                        leftSection={<IconFileText size={16} />}
                    >
                        Generate Report
                    </Button>
                </Stack>
            </Modal>

            {/* Share Report Modal */}
            <Modal
                opened={shareModalOpen}
                onClose={() => setShareModalOpen(false)}
                title="Share Report"
                size="md"
            >
                <Stack>
                    {shareUrl ? (
                        <>
                            <Alert color="green" title="Share link created!" icon={<IconCheck size={16} />}>
                                Copy the link below to share this report.
                            </Alert>

                            <TextInput
                                label="Share URL"
                                value={shareUrl}
                                readOnly
                                rightSection={
                                    <CopyButton value={shareUrl}>
                                        {({ copied, copy }) => (
                                            <ActionIcon color={copied ? 'green' : 'blue'} onClick={copy}>
                                                {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                            </ActionIcon>
                                        )}
                                    </CopyButton>
                                }
                            />
                        </>
                    ) : (
                        <>
                            <NumberInput
                                label="Expires in (days)"
                                value={shareExpiryDays}
                                onChange={(value) => setShareExpiryDays(Number(value) || 7)}
                                min={1}
                                max={90}
                                required
                            />

                            <TextInput
                                label="Password (optional)"
                                placeholder="Leave empty for no password"
                                value={sharePassword}
                                onChange={(e) => setSharePassword(e.currentTarget.value)}
                                type="password"
                                leftSection={<IconLock size={16} />}
                            />

                            <Button
                                fullWidth
                                onClick={handleConfirmShare}
                                loading={shareReportMutation.isPending}
                                leftSection={<IconShare size={16} />}
                            >
                                Create Share Link
                            </Button>
                        </>
                    )}
                </Stack>
            </Modal>

            {/* Schedule Report Modal */}
            <Modal
                opened={scheduleModalOpen}
                onClose={() => setScheduleModalOpen(false)}
                title="Schedule Report"
                size="lg"
            >
                <Stack>
                    <TextInput
                        label="Schedule Title"
                        placeholder="Weekly Report"
                        value={scheduleTitle}
                        onChange={(e) => setScheduleTitle(e.currentTarget.value)}
                        required
                    />

                    <Select
                        label="Template"
                        data={templateOptions}
                        value={scheduleTemplate}
                        onChange={(value) => setScheduleTemplate(value || 'weekly_performance')}
                        required
                    />

                    <MultiSelect
                        label="Metrics"
                        data={metricOptions}
                        value={scheduleMetrics}
                        onChange={setScheduleMetrics}
                        required
                    />

                    <Select
                        label="Frequency"
                        data={frequencyOptions}
                        value={scheduleFrequency}
                        onChange={(value) => setScheduleFrequency(value || 'weekly')}
                        required
                    />

                    {scheduleFrequency === 'weekly' && (
                        <Select
                            label="Day of Week"
                            data={[
                                { value: '0', label: 'Monday' },
                                { value: '1', label: 'Tuesday' },
                                { value: '2', label: 'Wednesday' },
                                { value: '3', label: 'Thursday' },
                                { value: '4', label: 'Friday' },
                                { value: '5', label: 'Saturday' },
                                { value: '6', label: 'Sunday' },
                            ]}
                            value={scheduleDayOfWeek.toString()}
                            onChange={(value) => setScheduleDayOfWeek(Number(value) || 1)}
                        />
                    )}

                    <TextInput
                        label="Time (HH:MM)"
                        placeholder="09:00"
                        value={scheduleTime}
                        onChange={(e) => setScheduleTime(e.currentTarget.value)}
                        required
                    />

                    <Textarea
                        label="Recipients (comma-separated emails)"
                        placeholder="john@example.com, jane@example.com"
                        value={scheduleRecipients}
                        onChange={(e) => setScheduleRecipients(e.currentTarget.value)}
                        required
                    />

                    <Button
                        fullWidth
                        onClick={() => createScheduleMutation.mutate()}
                        loading={createScheduleMutation.isPending}
                        leftSection={<IconCalendar size={16} />}
                    >
                        Create Schedule
                    </Button>
                </Stack>
            </Modal>

            {/* View Report Modal */}
            <Modal
                opened={viewModalOpen}
                onClose={() => setViewModalOpen(false)}
                title="Report Preview"
                size="xl"
            >
                <div dangerouslySetInnerHTML={{ __html: viewReportContent }} />
            </Modal>
        </Container>
    );
}
