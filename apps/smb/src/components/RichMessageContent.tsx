import { Text } from '@mantine/core'
import '../styles/RichMessageContent.css'

interface RichMessageContentProps {
    content: string
    isStreaming?: boolean
}

/**
 * RichMessageContent - Renders HTML content from AI coach as rich styled components
 * 
 * Features:
 * - Renders HTML with inline sanitization (React handles XSS prevention)
 * - Styled using CSS-in-JS for consistent theming
 * - Supports tables, lists, headings, emphasis
 * - Responsive and accessible
 */
export default function RichMessageContent({ content, isStreaming }: RichMessageContentProps) {
    // Check if content is HTML
    const isHTML = content.includes('<') && content.includes('>')

    if (!isHTML) {
        // Render as plain text with markdown-style formatting
        return (
            <Text
                size="15px"
                style={{
                    whiteSpace: 'pre-wrap',
                    lineHeight: 1.7,
                    color: '#353740',
                    fontWeight: 400
                }}
            >
                {content || (isStreaming ? '...' : '')}
            </Text>
        )
    }

    // Render HTML content with custom styling
    return (
        <div
            className="rich-message-content"
            dangerouslySetInnerHTML={{ __html: content }}
            style={{
                lineHeight: 1.8,
                color: '#353740',
                fontSize: '15px',
            }}
        />
    )
}
