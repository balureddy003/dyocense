import { Button, CopyButton, Group, Menu, Text, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
    IconCheck,
    IconCode,
    IconCopy,
    IconDownload,
    IconFileText,
    IconMarkdown,
    IconShare,
} from '@tabler/icons-react';
import { useState } from 'react';
import { API_BASE } from '../lib/api';

interface ReportDownloadButtonsProps {
    reportId: string;
    tenantId: string;
    reportTitle?: string;
}

export function ReportDownloadButtons({
    reportId,
    tenantId,
    reportTitle = 'Report',
}: ReportDownloadButtonsProps) {
    const [isSharing, setIsSharing] = useState(false);
    const [shareUrl, setShareUrl] = useState<string | null>(null);

    const handleDownload = async (format: 'html' | 'json' | 'markdown') => {
        try {
            const response = await fetch(`${API_BASE}/v1/tenants/${tenantId}/reports/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    report_id: reportId,
                    format,
                    include_thinking: true,
                    include_evidence: true,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to download report');
            }

            // Get filename from header or generate one
            const contentDisposition = response.headers.get('Content-Disposition');
            const filename = contentDisposition
                ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
                : `${reportTitle.replace(/\s+/g, '_')}.${format}`;

            // Download file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            notifications.show({
                title: 'Download Started',
                message: `Downloading ${format.toUpperCase()} report...`,
                color: 'green',
                icon: <IconCheck size={16} />,
            });
        } catch (error) {
            console.error('Download error:', error);
            notifications.show({
                title: 'Download Failed',
                message: 'Failed to download report. Please try again.',
                color: 'red',
            });
        }
    };

    const handleShare = async () => {
        setIsSharing(true);
        try {
            const response = await fetch(`${API_BASE}/v1/tenants/${tenantId}/reports/share`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    report_id: reportId,
                    expiry_days: 7,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to create share link');
            }

            const data = await response.json();
            const fullUrl = `${window.location.origin}/api${data.share_url}`;
            setShareUrl(fullUrl);

            notifications.show({
                title: 'Share Link Created',
                message: 'Link expires in 7 days. Click to copy.',
                color: 'blue',
                icon: <IconShare size={16} />,
            });
        } catch (error) {
            console.error('Share error:', error);
            notifications.show({
                title: 'Share Failed',
                message: 'Failed to create share link. Please try again.',
                color: 'red',
            });
        } finally {
            setIsSharing(false);
        }
    };

    return (
        <Group gap="xs">
            <Menu shadow="md" width={200}>
                <Menu.Target>
                    <Button
                        leftSection={<IconDownload size={16} />}
                        variant="light"
                        size="xs"
                    >
                        Download
                    </Button>
                </Menu.Target>

                <Menu.Dropdown>
                    <Menu.Label>Choose Format</Menu.Label>
                    <Menu.Item
                        leftSection={<IconFileText size={14} />}
                        onClick={() => handleDownload('html')}
                    >
                        HTML (Rich)
                    </Menu.Item>
                    <Menu.Item
                        leftSection={<IconMarkdown size={14} />}
                        onClick={() => handleDownload('markdown')}
                    >
                        Markdown
                    </Menu.Item>
                    <Menu.Item
                        leftSection={<IconCode size={14} />}
                        onClick={() => handleDownload('json')}
                    >
                        JSON (Data)
                    </Menu.Item>
                </Menu.Dropdown>
            </Menu>

            {shareUrl ? (
                <CopyButton value={shareUrl} timeout={2000}>
                    {({ copied, copy }) => (
                        <Tooltip label={copied ? 'Copied!' : 'Copy share link'} withArrow>
                            <Button
                                leftSection={copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                variant={copied ? 'filled' : 'light'}
                                color={copied ? 'green' : 'blue'}
                                size="xs"
                                onClick={copy}
                            >
                                {copied ? 'Copied!' : 'Copy Link'}
                            </Button>
                        </Tooltip>
                    )}
                </CopyButton>
            ) : (
                <Button
                    leftSection={<IconShare size={16} />}
                    variant="light"
                    size="xs"
                    onClick={handleShare}
                    loading={isSharing}
                >
                    Share
                </Button>
            )}

            {shareUrl && (
                <Text size="xs" c="dimmed" style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    Link expires in 7 days
                </Text>
            )}
        </Group>
    );
}
