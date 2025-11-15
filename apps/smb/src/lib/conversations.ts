// Keep this file self-contained to avoid tight coupling with a specific Coach version.
// Define a minimal Message type compatible with CoachV4/V5 message shapes.
export interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
    metadata?: Record<string, any>
}

export interface Conversation {
    id: string
    title: string
    messages: Message[]
    createdAt: Date
    updatedAt: Date
    agent: string
    tenantId: string  // Ensure conversations are tenant-specific
    goalId?: string   // Optional link to a goal for context
}

const MAX_CONVERSATIONS = 50

/**
 * Get tenant-specific storage key
 */
function getStorageKey(tenantId: string): string {
    return `coach_conversations_${tenantId}`
}

/**
 * Load all conversations from localStorage for a specific tenant
 */
export function loadConversations(tenantId: string): Conversation[] {
    if (!tenantId) return []

    try {
        const stored = localStorage.getItem(getStorageKey(tenantId))
        if (!stored) return []
        const parsed = JSON.parse(stored)
        // Convert date strings back to Date objects
        return parsed.map((conv: any) => ({
            ...conv,
            createdAt: new Date(conv.createdAt),
            updatedAt: new Date(conv.updatedAt),
            messages: conv.messages.map((m: any) => ({
                ...m,
                timestamp: new Date(m.timestamp)
            }))
        }))
    } catch (error) {
        console.error('Failed to load conversations:', error)
        return []
    }
}

/**
 * Save a conversation to localStorage for a specific tenant
 */
export function saveConversation(conversation: Conversation, tenantId: string): void {
    if (!tenantId) return

    try {
        const conversations = loadConversations(tenantId)
        const existing = conversations.findIndex(c => c.id === conversation.id)

        if (existing >= 0) {
            conversations[existing] = conversation
        } else {
            conversations.unshift(conversation)
        }

        // Keep only last MAX_CONVERSATIONS
        const trimmed = conversations.slice(0, MAX_CONVERSATIONS)
        localStorage.setItem(getStorageKey(tenantId), JSON.stringify(trimmed))
    } catch (error) {
        console.error('Failed to save conversation:', error)
    }
}

/**
 * Delete a conversation for a specific tenant
 */
export function deleteConversation(id: string, tenantId: string): void {
    if (!tenantId) return

    try {
        const conversations = loadConversations(tenantId)
        const filtered = conversations.filter(c => c.id !== id)
        localStorage.setItem(getStorageKey(tenantId), JSON.stringify(filtered))
    } catch (error) {
        console.error('Failed to delete conversation:', error)
    }
}

/**
 * Generate a title from the first user message
 */
export function generateConversationTitle(messages: Message[]): string {
    const firstUserMessage = messages.find(m => m.role === 'user')
    if (!firstUserMessage) return 'New conversation'

    const content = firstUserMessage.content.trim()
    if (content.length <= 50) return content
    return content.slice(0, 47) + '...'
}

/**
 * Get a conversation by ID for a specific tenant
 */
export function getConversation(id: string, tenantId: string): Conversation | undefined {
    if (!tenantId) return undefined
    const conversations = loadConversations(tenantId)
    return conversations.find(c => c.id === id)
}
