import { useState, useEffect, useCallback } from 'react';
import { fetchSession } from './api/client';
import type { Message, QueryResponse } from './api/client';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { ChatInterface } from './components/ChatInterface';
import { TrustInspector } from './components/TrustInspector';
import './App.css';

function getInitialSessionId(): string {
  if (typeof window !== 'undefined') {
    const urlParams = new URLSearchParams(window.location.search);
    const fromUrl = urlParams.get('session');
    if (fromUrl && fromUrl.trim()) {
      return fromUrl.trim();
    }
    const fromStorage = localStorage.getItem('ip_sakti_session_id');
    if (fromStorage && fromStorage.trim()) {
      return fromStorage.trim();
    }
  }
  return crypto.randomUUID();
}

function App() {
  const [sessionId, setSessionId] = useState<string>(getInitialSessionId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [lastResponse, setLastResponse] = useState<QueryResponse | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(
    typeof window !== 'undefined' ? window.innerWidth > 768 : true
  );
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(
    typeof window !== 'undefined' ? window.innerWidth > 1100 : true
  );

  // Sync active session ID to URL and localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('ip_sakti_session_id', sessionId);
        const url = new URL(window.location.href);
        if (url.searchParams.get('session') !== sessionId) {
          url.searchParams.set('session', sessionId);
          window.history.replaceState(null, '', url.toString());
        }
      } catch {
        // Fallback for sandboxed browser environments
      }
    }
  }, [sessionId]);

  // Hydrate session turns from server upon initial mount or session change
  useEffect(() => {
    let isCancelled = false;
    async function hydrate() {
      try {
        const session = await fetchSession(sessionId);
        if (!isCancelled && session && session.turns && session.turns.length > 0) {
          const restored: Message[] = session.turns.map((t) => ({
            role: t.role,
            content: t.content,
            responseMetadata:
              t.response_metadata ||
              (t.citations
                ? {
                    status: 'answered',
                    answer: t.content,
                    citations: t.citations,
                    confidence_score: 1.0,
                    response_time_ms: 0,
                    abs_flag: false,
                    tkdl_flag: false,
                  }
                : undefined),
          }));
          setMessages(restored);

          const lastAssist = [...restored].reverse().find((m) => m.role === 'assistant');
          if (lastAssist?.responseMetadata) {
            setLastResponse(lastAssist.responseMetadata);
          }

          const lastUser = [...restored].reverse().find((m) => m.role === 'user');
          if (lastUser) {
            setCurrentQuery(lastUser.content);
          }
        }
      } catch {
        // Session not found or fresh session; leave empty
      }
    }

    hydrate();
    return () => {
      isCancelled = true;
    };
  }, [sessionId]);

  const handleReset = useCallback(() => {
    const newId = crypto.randomUUID();
    setSessionId(newId);
    setMessages([]);
    setLastResponse(null);
    setCurrentQuery('');
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('ip_sakti_session_id', newId);
        const url = new URL(window.location.href);
        url.searchParams.set('session', newId);
        window.history.replaceState(null, '', url.toString());
      } catch {
        // Fallback for sandboxed browser environments
      }
    }
  }, []);

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
            sessionId={sessionId}
            onReset={handleReset}
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
