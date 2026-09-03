import { ChatInterface } from './components/ChatInterface'

function App() {
  return (
    <div className="app-layout">
      <header className="topbar">
        <div className="brand">
          <span className="brand-icon">🏛️</span>
          <span className="brand-text">IP-SAKTI Sahayak</span>
        </div>
        <div className="jurisdiction-pill">
          [India 🇮🇳]
        </div>
      </header>
      <main className="main-content">
        <ChatInterface />
      </main>
      <footer className="footer-disclaimer">
        This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation.
      </footer>
    </div>
  )
}

export default App
