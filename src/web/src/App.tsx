import { useState } from 'react';
import type { Message } from './api/client';
import { ChatInterface } from './components/ChatInterface';
import { Topbar } from './components/Topbar';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);

  const handleReset = () => {
    setMessages([]);
  };

  return (
    <div className="app-layout">
      <Topbar onReset={handleReset} hasMessages={messages.length > 0} />
      
      <main className="main-content">
        <ChatInterface messages={messages} setMessages={setMessages} />
      </main>

      <footer className="footer-disclaimer">
        This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation.
      </footer>
    </div>
  );
}

export default App;
