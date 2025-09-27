import { createContext, ReactNode, useContext, useMemo, useReducer } from 'react';

export type MessageRole = 'assistant' | 'user' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  text: string;
  createdAt: Date;
}

interface ChatState {
  messages: ChatMessage[];
  providerId: string;
  loading: boolean;
}

interface ChatActionBase<T extends string> {
  type: T;
}

interface AddMessageAction extends ChatActionBase<'add-message'> {
  payload: ChatMessage;
}

interface SetProviderAction extends ChatActionBase<'set-provider'> {
  payload: string;
}

interface SetLoadingAction extends ChatActionBase<'set-loading'> {
  payload: boolean;
}

type ChatAction = AddMessageAction | SetProviderAction | SetLoadingAction;

const initialState: ChatState = {
  messages: [
    {
      id: 'welcome',
      role: 'assistant',
      text: 'Hi! Describe a planning goal and I will use the Dyocense kernel + LLM router to orchestrate a run.',
      createdAt: new Date()
    }
  ],
  providerId: 'openai',
  loading: false
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'add-message':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'set-provider':
      return { ...state, providerId: action.payload };
    case 'set-loading':
      return { ...state, loading: action.payload };
    default:
      return state;
  }
}

interface ChatStoreContextValue extends ChatState {
  addMessage: (message: ChatMessage) => void;
  setProvider: (providerId: string) => void;
  setLoading: (loading: boolean) => void;
}

const ChatStoreContext = createContext<ChatStoreContextValue | undefined>(undefined);

export function ChatStoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const value = useMemo<ChatStoreContextValue>(() => ({
    ...state,
    addMessage: (message: ChatMessage) => dispatch({ type: 'add-message', payload: message }),
    setProvider: (providerId: string) => dispatch({ type: 'set-provider', payload: providerId }),
    setLoading: (loading: boolean) => dispatch({ type: 'set-loading', payload: loading })
  }), [state]);

  return <ChatStoreContext.Provider value={value}>{children}</ChatStoreContext.Provider>;
}

export function useChatStore(): ChatStoreContextValue {
  const ctx = useContext(ChatStoreContext);
  if (!ctx) {
    throw new Error('useChatStore must be used within ChatStoreProvider');
  }
  return ctx;
}

export function createUserMessage(text: string): ChatMessage {
  return { id: `user-${Date.now()}`, role: 'user', text, createdAt: new Date() };
}

export function createAssistantMessage(text: string): ChatMessage {
  return { id: `assistant-${Date.now()}`, role: 'assistant', text, createdAt: new Date() };
}
