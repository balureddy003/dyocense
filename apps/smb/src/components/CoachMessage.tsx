import { Text } from '@mantine/core'

interface CoachMessageProps {
    content: string
    isUser: boolean
}

/**
 * Renders coach messages with enhanced formatting
 * Supports markdown-like syntax for better UX
 */
export function CoachMessage({ content, isUser }: CoachMessageProps) {
    if (isUser) {
        return (
            <Text
                size="sm"
                style={{
                    whiteSpace: 'pre-wrap',
                    color: 'white',
                }}
            >
                {content}
            </Text>
        )
    }

    // Parse and format assistant messages
    const lines = content.split('\n')
    const elements: JSX.Element[] = []
    let key = 0

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i]

        // Empty line - add spacing
        if (!line.trim()) {
            elements.push(<div key={`space-${key++}`} style={{ height: '8px' }} />)
            continue
        }

        // Headers (bold text with **)
        if (line.match(/^\*\*(.+)\*\*$/)) {
            const text = line.replace(/^\*\*|\*\*$/g, '')
            elements.push(
                <Text key={`header-${key++}`} size="sm" fw={700} mb={4} style={{ color: '#0f172a' }}>
                    {text}
                </Text>
            )
            continue
        }

        // Bullet points (•)
        if (line.match(/^[•·]\s/)) {
            const text = line.replace(/^[•·]\s/, '')
            elements.push(
                <div key={`bullet-${key++}`} style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                    <Text size="sm" style={{ color: '#64748b' }}>•</Text>
                    <Text size="sm" style={{ flex: 1, color: '#334155' }}>{formatInlineText(text)}</Text>
                </div>
            )
            continue
        }

        // Numbered lists
        if (line.match(/^\d+\.\s/)) {
            elements.push(
                <div key={`numbered-${key++}`} style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                    <Text size="sm" fw={600} style={{ color: '#64748b', minWidth: '20px' }}>
                        {line.match(/^(\d+)\./)?.[1]}.
                    </Text>
                    <Text size="sm" style={{ flex: 1, color: '#334155' }}>
                        {formatInlineText(line.replace(/^\d+\.\s/, ''))}
                    </Text>
                </div>
            )
            continue
        }

        // Section dividers (---)
        if (line.match(/^---+$/)) {
            elements.push(<div key={`divider-${key++}`} style={{ borderTop: '1px solid #e2e8f0', margin: '12px 0' }} />)
            continue
        }

        // Regular text
        elements.push(
            <Text key={`text-${key++}`} size="sm" mb={4} style={{ color: '#475569' }}>
                {formatInlineText(line)}
            </Text>
        )
    }

    return <div>{elements}</div>
}

/**
 * Format inline text with bold (**text**) and inline code
 */
function formatInlineText(text: string): JSX.Element {
    const parts: (string | JSX.Element)[] = []
    let remaining = text
    let key = 0

    // Match bold text **...**
    const boldRegex = /\*\*(.+?)\*\*/g
    let lastIndex = 0
    let match: RegExpExecArray | null

    while ((match = boldRegex.exec(text)) !== null) {
        // Add text before match
        if (match.index > lastIndex) {
            parts.push(text.substring(lastIndex, match.index))
        }
        // Add bold text
        parts.push(
            <strong key={`bold-${key++}`} style={{ fontWeight: 600, color: '#1e293b' }}>
                {match[1]}
            </strong>
        )
        lastIndex = match.index + match[0].length
    }

    // Add remaining text
    if (lastIndex < text.length) {
        parts.push(text.substring(lastIndex))
    }

    // If no formatting found, return original text
    if (parts.length === 0) {
        return <>{text}</>
    }

    return <>{parts}</>
}
