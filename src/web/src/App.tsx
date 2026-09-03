import { useState } from 'react';
import type { Message, QueryResponse } from './api/client';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { ChatInterface } from './components/ChatInterface';
import { TrustInspector } from './components/TrustInspector';
import './App.css';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [lastResponse, setLastResponse] = useState<QueryResponse | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(
    typeof window !== 'undefined' ? window.innerWidth > 768 : true
  );
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(
    typeof window !== 'undefined' ? window.innerWidth > 1100 : true
  );

  const handleReset = () => {
    setMessages([]);
    setLastResponse(null);
    setCurrentQuery('');
  };

  return (
    <div className="workbench-root">
      {/* Notion Topbar with Breadcrumbs and Inspector Toggle */}
      <Topbar 
        onReset={handleReset} 
        hasMessages={messages.length > 0} 
        onToggleSidebar={() => setIsSidebarOpen(prev => !prev)}
        onToggleInspector={() => setIsInspectorOpen(prev => !prev)}
        isInspectorOpen={isInspectorOpen}
        activeCategory={lastResponse?.category}
      />

      <div className="workbench-layout">
        {/* Left Column: Navigation */}
        <div className={`workbench-sidebar ${isSidebarOpen ? '' : 'collapsed'}`}>
          <Sidebar
            onNewNote={handleReset}
          />
        </div>

        {/* Center Column: Notion Legal Research Canvas */}
        <main className="workbench-center">
          <ChatInterface 
            messages={messages} 
            setMessages={setMessages}
            lastResponse={lastResponse}
            setLastResponse={setLastResponse}
            currentQuery={currentQuery}
            setCurrentQuery={setCurrentQuery}
          />
        </main>

        {/* Right Column: Trust & Telemetry Inspector ("Why This Answer?") */}
        <div className={`workbench-inspector ${isInspectorOpen ? '' : 'hidden'}`}>
          <TrustInspector
            query={currentQuery}
            response={lastResponse}
            onClose={() => setIsInspectorOpen(false)}
          />
        </div>
      </div>

      {/* Statutory Legal Disclaimer */}
      <footer className="workbench-footer-disclaimer">
        This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation.
      </footer>
    </div>
  );
}

export default App;
