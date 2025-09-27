import { ChatStoreProvider } from './store/chatStore';
import { ChatPage } from './pages/Chat';
import './styles.css';

export default function App() {
  return (
    <ChatStoreProvider>
      <ChatPage />
    </ChatStoreProvider>
  );
}
