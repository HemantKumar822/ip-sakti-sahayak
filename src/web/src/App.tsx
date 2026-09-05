import { useState, useEffect, useCallback } from 'react';

import { fetchSession } from './api/client';
import type { Message, QueryResponse, Citation } from './api/client';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import type { AppView } from './components/Topbar';
import { ChatInterface } from './components/ChatInterface';
import { TrustInspector } from './components/TrustInspector';
import { CitationModal } from './components/CitationModal';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastContainer } from './components/ToastContainer';
import { CorpusConsole } from './components/CorpusConsole';
import { LandingPage } from './components/LandingPage';
import { ApiKeyModal } from './components/ApiKeyModal';

const DISCLAIMER =
  'This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation.';

function getInitialSessionId(): string {
  if (typeof window !== 'undefined') {
    const fromUrl = new URLSearchParams(window.location.search).get('session');
    if (fromUrl && fromUrl.trim()) return fromUrl.trim();
    const fromStorage = localStorage.getItem('ip_sakti_session_id');
    if (fromStorage && fromStorage.trim()) return fromStorage.trim();
  }
  return crypto.randomUUID();
}

function App() {
  const [sessionId, setSessionId] = useState<string>(getInitialSessionId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [lastResponse, setLastResponse] = useState<QueryResponse | null>(null);
  const [authError, setAuthError] = useState<boolean>(false);
  const [activeView, setActiveView] = useState<AppView>('landing');
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [citationOpen, setCitationOpen] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  const [noticeDismissed, setNoticeDismissed] = useState(false);
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);

  useEffect(() => {
    try {
      localStorage.setItem('ip_sakti_session_id', sessionId);
      const url = new URL(window.location.href);
      if (url.searchParams.get('session') !== sessionId) {
        url.searchParams.set('session', sessionId);
        window.history.replaceState(null, '', url.toString());
      }
    } catch {
      /* sandboxed browser */
    }
  }, [sessionId]);

  useEffect(() => {
    let cancelled = false;
    async function hydrate() {
      try {
        const session = await fetchSession(sessionId);
        if (cancelled) return;
        if (session?.turns?.length) {
          const restored: Message[] = session.turns.map((t) => ({
            role: t.role,
            content: t.content,
            responseMetadata: t.response_metadata || undefined,
          }));
          setMessages(restored);
          const lastAssist = [...restored].reverse().find((m) => m.role === 'assistant');
          setLastResponse(lastAssist?.responseMetadata ?? null);
        } else {
          setMessages([]);
          setLastResponse(null);
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.message.includes('API Key Required')) {
          setAuthError(true);
          setNoticeDismissed(false);
        }
        if (!cancelled) {
          setMessages([]);
          setLastResponse(null);
        }
      }
    }
    hydrate();
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const handleReset = useCallback(() => {
    const id = crypto.randomUUID();
    setSessionId(id);
    setMessages([]);
    setLastResponse(null);
  }, []);

  const handleEnterWorkbench = useCallback((initialQuery?: string) => {
    setActiveView('workbench');
    if (initialQuery) setPendingQuery(initialQuery);
  }, []);

  const handleCitationClick = useCallback((citation: Citation) => {
    setSelectedCitation(citation);
    setCitationOpen(true);
  }, []);

  const handleSaveApiKey = useCallback((key: string) => {
    localStorage.setItem('ip_sakti_api_key', key.trim());
    setAuthError(false);
    window.location.reload();
  }, []);

  return (
    <ErrorBoundary onReset={handleReset}>
      <div className={`sk-shell${activeView === 'workbench' ? ' sk-shell-locked' : ''}`}>
        <ToastContainer />
        
        <ApiKeyModal 
          isOpen={authError && !noticeDismissed} 
          onClose={() => setNoticeDismissed(true)} 
          onSave={handleSaveApiKey} 
        />

        <Topbar 
          activeView={activeView} 
          onViewChange={setActiveView} 
          onHome={() => setActiveView('landing')} 
          leftSidebarOpen={leftSidebarOpen}
          onToggleLeftSidebar={() => setLeftSidebarOpen(!leftSidebarOpen)}
          rightSidebarOpen={rightSidebarOpen}
          onToggleRightSidebar={() => setRightSidebarOpen(!rightSidebarOpen)}
        />

        {activeView === 'landing' && (
          <main className="sk-main">
            <LandingPage onEnterWorkbench={handleEnterWorkbench} onEnterAdmin={() => setActiveView('admin')} />
          </main>
        )}

        {activeView === 'workbench' && (
          <main className="sk-main">
            <div className={`sk-wb ${!leftSidebarOpen ? 'sk-wb-no-left' : ''} ${!rightSidebarOpen ? 'sk-wb-no-right' : ''}`}>
              {leftSidebarOpen && (
                <div className="sk-history">
                  <Sidebar
                    onNewNote={handleReset}
                    activeSessionId={sessionId}
                    onSelectSession={setSessionId}
                    refreshTrigger={messages.length}
                    currentTurns={messages.length}
                  />
                </div>
              )}
              <div className="sk-dock">
                  <ChatInterface
                    messages={messages}
                    setMessages={setMessages}
                    lastResponse={lastResponse}
                    setLastResponse={setLastResponse}
                    sessionId={sessionId}
                    onReset={handleReset}
                    onAuthError={() => {
                      setAuthError(true);
                      setNoticeDismissed(false);
                    }}
                    onCitationClick={handleCitationClick}
                    onOpenEvidence={() => setEvidenceOpen(true)}
                    pendingQuery={pendingQuery}
                    onConsumePending={() => setPendingQuery(null)}
                  />
              </div>
              {rightSidebarOpen && (
                <div className="sk-evidence">
                  <TrustInspector response={lastResponse} />
                </div>
              )}
            </div>
          </main>
        )}

        {activeView === 'admin' && (
          <main className="sk-main">
            <CorpusConsole />
          </main>
        )}

        <footer className="sk-footer">{DISCLAIMER}</footer>

        {evidenceOpen && (
          <div className="sk-drawer-backdrop" onClick={() => setEvidenceOpen(false)} aria-hidden="true" />
        )}
        {evidenceOpen && (
          <div className="sk-drawer" role="dialog" aria-label="Evidence and verification">
            <TrustInspector response={lastResponse} onClose={() => setEvidenceOpen(false)} />
          </div>
        )}

        <CitationModal citation={selectedCitation} isOpen={citationOpen} onClose={() => setCitationOpen(false)} />
      </div>
    </ErrorBoundary>
  );
}

export default App;
