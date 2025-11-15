import { Divider, Table, Text, useMantineTheme } from '@mantine/core'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownProps {
    content: string
    size?: 'xs' | 'sm' | 'md'
}

export function Markdown({ content, size = 'sm' }: MarkdownProps) {
    const theme = useMantineTheme()

    const fontSize = size === 'xs' ? '12px' : size === 'md' ? '14px' : '13px'

    return (
        <div style={{ fontSize, lineHeight: 1.6 }}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    h1: ({ children }) => (
                        <Text size="lg" fw={700} mt="md" mb="xs" c="dark.7">
                            {children}
                        </Text>
                    ),
                    h2: ({ children }) => (
                        <Text size="md" fw={700} mt="md" mb="xs" c="dark.7">
                            {children}
                        </Text>
                    ),
                    h3: ({ children }) => (
                        <Text size="sm" fw={600} mt="sm" mb="xs" c="dark.6">
                            {children}
                        </Text>
                    ),
                    p: ({ children }) => (
                        <Text size={size} mb="xs" style={{ lineHeight: 1.6 }}>
                            {children}
                        </Text>
                    ),
                    ul: ({ children }) => (
                        <ul style={{ marginLeft: '16px', marginBottom: '8px' }}>{children}</ul>
                    ),
                    ol: ({ children }) => (
                        <ol style={{ marginLeft: '16px', marginBottom: '8px' }}>{children}</ol>
                    ),
                    li: ({ children }) => (
                        <li style={{ marginBottom: '4px' }}>
                            <Text size={size}>{children}</Text>
                        </li>
                    ),
                    strong: ({ children }) => (
                        <strong style={{ fontWeight: 600, color: theme.colors.dark[8] as any }}>{children}</strong>
                    ),
                    hr: () => <Divider my="sm" />,
                    blockquote: ({ children }) => (
                        <blockquote
                            style={{
                                borderLeft: `3px solid ${theme.colors.gray[4]}`,
                                margin: '8px 0',
                                padding: '4px 8px',
                                color: theme.colors.dark[3],
                                background: theme.colors.gray[0],
                            }}
                        >
                            <Text size={size}>{children}</Text>
                        </blockquote>
                    ),
                    a: ({ href, children }) => (
                        <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: theme.colors.blue[6], textDecoration: 'underline' }}>
                            {children}
                        </a>
                    ),
                    table: ({ children }) => (
                        <div style={{ overflowX: 'auto', margin: '8px 0' }}>
                            <Table striped highlightOnHover withTableBorder withColumnBorders>
                                {children}
                            </Table>
                        </div>
                    ),
                    code: ({ children, className }) => {
                        const isInline = !className
                        return isInline ? (
                            <code
                                style={{
                                    background: theme.colors.gray[1],
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    fontFamily: 'monospace',
                                }}
                            >
                                {children}
                            </code>
                        ) : (
                            <pre
                                style={{
                                    background: theme.colors.gray[1],
                                    padding: '8px',
                                    borderRadius: '6px',
                                    overflow: 'auto',
                                    fontSize: '12px',
                                    fontFamily: 'monospace',
                                }}
                            >
                                <code>{children}</code>
                            </pre>
                        )
                    },
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    )
}
