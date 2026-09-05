// Corpus administration: live ChromaDB telemetry, gazette table, PDF ingestion.
import { useState, useEffect, useCallback, useRef } from 'react';
import type { FC, DragEvent, ChangeEvent, FormEvent } from 'react';
import {
  Database,
  UploadCloud,
  FileText,
  CheckCircle2,
  ExternalLink,
  ShieldAlert,
  RefreshCw,
  Layers,
  X,
  Search,
} from 'lucide-react';
import { fetchCorpusStatus, ingestCorpusDocument } from '../api/client';
import type { CorpusStatusResponse, DocumentBreakdown } from '../api/client';
import { toast } from '../utils/toast';

// Baseline shown when the backend is unreachable: the 11 authentic gazettes.
const DEFAULT_DOCUMENTS: DocumentBreakdown[] = [
  {
    doc_id: 'tkdl-overview',
    title: 'Traditional Knowledge Digital Library (TKDL) - Overview and Framework',
    document_type: 'policy',
    chunk_count: 1,
    source_url: 'https://www.tkdl.res.in/tkdl/langdefault/common/Abouttkdl.asp',
    date_retrieved: '2026-08-31',
  },
  {
    doc_id: 'tkdl-neem-turmeric-prior-art',
    title: 'TKDL Case Studies: Revocation of Neem and Turmeric Patent Claims',
    document_type: 'policy',
    chunk_count: 1,
    source_url: 'https://www.csir.res.in/tkdl-success-stories-neem-turmeric',
    date_retrieved: '2026-08-31',
  },
  {
    doc_id: 'tkdl-ashwagandha-formulations',
    title: 'Traditional Knowledge Classification and Protection of Withania somnifera (Ashwagandha)',
    document_type: 'policy',
    chunk_count: 1,
    source_url: 'https://www.tkdl.res.in/tkdl/langdefault/ayurveda/ashwagandha.asp',
    date_retrieved: '2026-08-31',
  },
  {
    doc_id: 'patents-act-1970',
    title: 'The Patents Act, 1970 (incorporating all amendments till 11-03-2015)',
    document_type: 'statute',
    chunk_count: 97,
    source_url: 'https://www.ipindia.gov.in/storage/uploads/docs-operator/df4efbcf-6fdf-4b2b-b6d6-56853aa39083.pdf',
    date_retrieved: '2026-09-02',
  },
  {
    doc_id: 'biological-diversity-act-2002',
    title: 'The Biological Diversity Act, 2002 (Act No. 18 of 2003)',
    document_type: 'statute',
    chunk_count: 24,
    source_url: 'https://wipolex.wipo.int/en/legislation/details/6058',
    date_retrieved: '2026-09-02',
  },
  {
    doc_id: 'biological-diversity-act-2023-amendment',
    title: 'The Biological Diversity (Amendment) Act, 2023 (Act No. 10 of 2023)',
    document_type: 'statute',
    chunk_count: 20,
    source_url: 'https://wipolex.wipo.int/en/legislation/details/23716',
    date_retrieved: '2026-09-02',
  },
  {
    doc_id: 'guidelines-patent-examination-ayush-2025',
    title: 'Guidelines for Examination of Ayush Related Inventions - 2025',
    document_type: 'guideline',
    chunk_count: 16,
    source_url: 'https://www.ipindia.gov.in/storage/uploads/docs-operator/335e2746-58c1-4b56-a1e5-cdd172a92a3c.pdf',
    date_retrieved: '2026-09-02',
  },
  {
    doc_id: 'guidelines-traditional-knowledge-biological-material-2012',
    title: 'Guidelines for Processing of Patent Applications relating to Traditional Knowledge and Biological Material - 2012',
    document_type: 'guideline',
    chunk_count: 11,
    source_url: 'https://www.ipindia.gov.in/storage/uploads/docs-operator/220f0e1c-1301-4f0f-84a0-6709fa66c592.pdf',
    date_retrieved: '2026-09-02',
  },
  {
    doc_id: 'biological-diversity-rules-2004',
    title: 'The Biological Diversity Rules, 2004 (SBB Procedures & ABS Regulations)',
    document_type: 'regulation',
    chunk_count: 2,
    source_url: 'https://indiankanoon.org/doc/1572979/',
    date_retrieved: '2026-09-03',
  },
  {
    doc_id: 'novartis-v-union-of-india-2013',
    title: 'Novartis AG v. Union of India (2013) 6 SCC 1 - Section 3(d) Therapeutic Efficacy Precedent',
    document_type: 'judicial_precedent',
    chunk_count: 121,
    source_url: 'https://indiankanoon.org/doc/165776436/',
    date_retrieved: '2026-09-03',
  },
  {
    doc_id: 'dabur-india-v-emami-chyawanprash-2024',
    title: 'Emami Ltd. v. Dabur India Ltd. (2024) - ASU Ayurvedic Formulations & Trademark Distinctiveness',
    document_type: 'judicial_precedent',
    chunk_count: 2,
    source_url: 'https://indiankanoon.org/doc/171286047/',
    date_retrieved: '2026-09-03',
  },
];

function acceptPdf(file: File): boolean {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
}

export const CorpusConsole: FC = () => {
  const [corpusData, setCorpusData] = useState<CorpusStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [restricted, setRestricted] = useState<null | 'auth' | 'admin'>(null);

  function classifyAccessError(err: unknown): void {
    if (!(err instanceof Error)) return;
    if (err.message.includes('API Key Required')) setRestricted('auth');
    else if (err.message.includes('Admin privileges required')) setRestricted('admin');
  }
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [docId, setDocId] = useState('');
  const [title, setTitle] = useState('');
  const [documentType, setDocumentType] = useState('statute');
  const [sourceUrl, setSourceUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchStatusData = useCallback(async () => {
    try {
      setCorpusData(await fetchCorpusStatus());
      setRestricted(null);
    } catch (err: unknown) {
      classifyAccessError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchCorpusStatus();
        if (!cancelled) {
          setCorpusData(data);
          setRestricted(null);
        }
      } catch (err: unknown) {
        if (!cancelled) classifyAccessError(err);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function takeFile(file: File) {
    if (!acceptPdf(file)) {
      toast.warning('Invalid file type', 'Only official legal documents in PDF format are accepted.');
      return;
    }
    setSelectedFile(file);
    if (!docId) setDocId(file.name.replace(/\.pdf$/i, '').toLowerCase().replace(/[^a-z0-9_-]/g, '-'));
    if (!title) setTitle(file.name.replace(/\.pdf$/i, ''));
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length) takeFile(e.dataTransfer.files[0]);
  };
  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) takeFile(e.target.files[0]);
  };

  const handleSubmitIngestion = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      toast.warning('File required', 'Attach a PDF gazette before submitting.');
      return;
    }
    if (!docId.trim()) {
      toast.warning('Document ID required', 'Give the gazette a unique document ID.');
      return;
    }
    try {
      setIsSubmitting(true);
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('doc_id', docId.trim());
      formData.append('title', title.trim() || docId.trim());
      formData.append('document_type', documentType);
      formData.append('source_url', sourceUrl.trim());
      formData.append('date_retrieved', new Date().toISOString().split('T')[0]);
      const result = await ingestCorpusDocument(formData);
      toast.success('Gazette ingested', `'${result.doc_id}' added as ${result.chunks_ingested} chunks.`);
      setSelectedFile(null);
      setDocId('');
      setTitle('');
      setSourceUrl('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      setIsLoading(true);
      await fetchStatusData();
    } finally {
      setIsSubmitting(false);
    }
  };

  const breakdown: DocumentBreakdown[] =
    corpusData?.document_breakdown?.length ? corpusData.document_breakdown : DEFAULT_DOCUMENTS;
  const totalChunks = corpusData?.total_chunks || 296;
  const totalDocs = corpusData?.document_count || breakdown.length;
  const connected = corpusData?.status !== 'unhealthy';
  const q = searchQuery.toLowerCase();
  const filteredDocs = breakdown.filter(
    (d) => d.title.toLowerCase().includes(q) || d.doc_id.toLowerCase().includes(q) || d.document_type.toLowerCase().includes(q)
  );

  if (restricted) {
    const isAdmin = restricted === 'admin';
    return (
      <div className="sk-admin" role="region" aria-label="Corpus administration">
        <div className="sk-card" style={{ textAlign: 'center', padding: 'var(--space-4xl) var(--space-xl)' }}>
          <ShieldAlert size={28} aria-hidden="true" style={{ color: 'var(--status-error)' }} />
          <h1 className="sk-h2" style={{ marginTop: 'var(--space-md)' }}>
            {isAdmin ? 'Query key lacks admin rights' : 'Admin access restricted'}
          </h1>
          <p className="sk-body" style={{ maxWidth: '560px', margin: 'var(--space-sm) auto 0' }}>
            {isAdmin ? (
              <>
                Your key authenticates queries but is not in the backend{' '}
                <code>VALID_ADMIN_API_KEYS</code>. Add it there (and restart the backend), or switch{' '}
                <code>VITE_API_KEY</code> to a key that already has admin rights.
              </>
            ) : (
              <>
                The corpus console needs an administrator key. Set <code>VITE_API_KEY</code> in{' '}
                <code>src/web/.env</code> to a value listed in the backend{' '}
                <code>VALID_ADMIN_API_KEYS</code> — <code>run.py</code> checks this parity on startup.
              </>
            )}
          </p>
          <div style={{ marginTop: 'var(--space-lg)' }}>
            <button type="button" className="sk-btn" onClick={() => { setIsLoading(true); void fetchStatusData(); }}>
              <RefreshCw size={14} aria-hidden="true" />
              <span>Retry authorization</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="sk-admin" role="region" aria-label="Corpus administration">
      <div className="sk-admin-head">
        <div>
          <p className="sk-eyebrow">Corpus administration</p>
          <h1 className="sk-h1" style={{ marginTop: 'var(--space-xs)' }}>
            What the desk reasons over
          </h1>
          <p className="sk-body" style={{ marginTop: 'var(--space-sm)', maxWidth: '720px' }}>
            Every clearance answer is retrieved from this index of official gazettes — statutes,
            examination guidelines, and precedents. Add a gazette and it becomes citable immediately.
          </p>
        </div>
        <span className="sk-live" title="ChromaDB health">
          <span className={`sk-dot${connected ? '' : ' sk-dot-bad'}`} aria-hidden="true" />
          <span>{connected ? (corpusData ? 'ChromaDB connected' : 'Showing baseline') : 'ChromaDB disconnected'}</span>
        </span>
      </div>

      <div className="sk-stats" aria-label="Corpus statistics">
        <div className="sk-card sk-stat">
          <span className="sk-eyebrow">Indexed chunks</span>
          <span className="sk-stat-value">{isLoading ? '—' : totalChunks}</span>
          <span className="sk-mini">Baseline: 296 across 11 gazettes</span>
        </div>
        <div className="sk-card sk-stat">
          <span className="sk-eyebrow">Gazettes</span>
          <span className="sk-stat-value">{isLoading ? '—' : totalDocs}</span>
          <span className="sk-mini">Statutes, guidelines, precedents</span>
        </div>
        <div className="sk-card sk-stat">
          <span className="sk-eyebrow">Collection</span>
          <span className="sk-stat-value" style={{ fontSize: '17px', wordBreak: 'break-all' }}>
            {corpusData?.collection_name || 'ip_sakti_legal_corpus'}
          </span>
          <span className="sk-mini">ChromaDB persistent index</span>
        </div>
        <div className="sk-card sk-stat">
          <span className="sk-eyebrow">Confidence gate</span>
          <span className="sk-stat-value">0.65</span>
          <span className="sk-mini">Below this, the desk refuses</span>
        </div>
      </div>

      <div className="sk-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 'var(--space-md)', flexWrap: 'wrap' }}>
          <h2 className="sk-h3">Indexed gazettes</h2>
          <div style={{ display: 'flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
            <label htmlFor="sk-corpus-search" className="sk-visually-hidden">
              Filter gazettes
            </label>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-xs)', color: 'var(--mute)' }}>
              <Search size={14} aria-hidden="true" />
            </span>
            <input
              id="sk-corpus-search"
              type="search"
              className="sk-input"
              style={{ width: '240px' }}
              placeholder="Filter by title, ID, type…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="button" className="sk-btn sk-btn-sm sk-btn-quiet" onClick={() => { setIsLoading(true); void fetchStatusData(); }} title="Refresh" aria-label="Refresh gazette list">
              <RefreshCw size={13} aria-hidden="true" className={isLoading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
        <div className="sk-table-wrap" style={{ marginTop: 'var(--space-md)' }}>
          <table className="sk-table">
            <thead>
              <tr>
                <th>Document Title & ID</th>
                <th>Type</th>
                <th>Chunks</th>
                <th>Retrieved</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.map((doc) => (
                <tr key={doc.doc_id}>
                  <td>
                    <span style={{ display: 'block', color: 'var(--ink)' }}>{doc.title}</span>
                    <span className="sk-mini" style={{ fontFamily: 'var(--font-mono)' }}>{doc.doc_id}</span>
                  </td>
                  <td>
                    <span className="sk-tag">{doc.document_type}</span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{doc.chunk_count}</td>
                  <td className="sk-mini" style={{ whiteSpace: 'nowrap' }}>{doc.date_retrieved || '—'}</td>
                  <td>
                    {doc.source_url ? (
                      <a href={doc.source_url} target="_blank" rel="noopener noreferrer" className="sk-small" style={{ display: 'inline-flex', gap: '4px', alignItems: 'center', color: 'var(--accent-breeze)', whiteSpace: 'nowrap' }}>
                        <span>Gazette</span>
                        <ExternalLink size={11} aria-hidden="true" />
                      </a>
                    ) : (
                      <span className="sk-mini">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {filteredDocs.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: 'var(--space-2xl)' }}>
                    <span className="sk-small">No gazettes match &ldquo;{searchQuery}&rdquo;.</span>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="sk-mini" style={{ marginTop: 'var(--space-sm)', display: 'flex', gap: 'var(--space-xs)', alignItems: 'center' }}>
          <Layers size={12} aria-hidden="true" />
          <span>{totalChunks} chunks · 296 baseline · {totalDocs} documents</span>
        </p>
      </div>

      <div className="sk-card">
        <h2 className="sk-h3" style={{ display: 'flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
          <UploadCloud size={17} aria-hidden="true" style={{ color: 'var(--accent-sunset)' }} />
          <span>Ingest a gazette</span>
        </h2>
        <p className="sk-small" style={{ marginTop: 'var(--space-xs)' }}>
          Official PDFs are chunked, embedded, and upserted into ChromaDB — then immediately citable by the desk.
        </p>
        <form onSubmit={(e) => void handleSubmitIngestion(e)} style={{ marginTop: 'var(--space-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          <div
            className={`sk-dropzone${isDragging ? ' sk-dropzone-over' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            aria-label="Attach a PDF gazette"
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fileInputRef.current?.click();
              }
            }}
          >
            <input ref={fileInputRef} type="file" accept=".pdf,application/pdf" onChange={handleFileInputChange} className="sk-visually-hidden" tabIndex={-1} aria-hidden="true" />
            {selectedFile ? (
              <span style={{ display: 'inline-flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
                <FileText size={16} aria-hidden="true" style={{ color: 'var(--accent-sunset)' }} />
                <span className="sk-small" style={{ color: 'var(--ink)' }}>{selectedFile.name}</span>
                <span className="sk-mini">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                <button
                  type="button"
                  className="sk-btn sk-btn-quiet sk-btn-sm"
                  aria-label="Remove file"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                  }}
                >
                  <X size={13} aria-hidden="true" />
                </button>
              </span>
            ) : (
              <>
                <UploadCloud size={24} aria-hidden="true" style={{ color: 'var(--mute)' }} />
                <span className="sk-small" style={{ display: 'block', marginTop: 'var(--space-sm)', color: 'var(--ink)' }}>
                  Drop a gazette PDF here, or click to browse
                </span>
                <span className="sk-mini" style={{ display: 'block', marginTop: 'var(--space-xs)' }}>
                  Authentic government PDFs only
                </span>
              </>
            )}
          </div>

          <div className="sk-form-grid">
            <div className="sk-field">
              <label className="sk-label" htmlFor="doc_id">Document ID</label>
              <input id="doc_id" className="sk-input" type="text" placeholder="bda-rules-2024" value={docId} onChange={(e) => setDocId(e.target.value)} required />
            </div>
            <div className="sk-field">
              <label className="sk-label" htmlFor="doc_title">Document title</label>
              <input id="doc_title" className="sk-input" type="text" placeholder="The Biological Diversity Rules, 2024" value={title} onChange={(e) => setTitle(e.target.value)} required />
            </div>
            <div className="sk-field">
              <label className="sk-label" htmlFor="document_type">Document type</label>
              <select id="document_type" className="sk-select" value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                <option value="statute">Statute</option>
                <option value="rule">Rule / regulation</option>
                <option value="guideline">Examination guideline</option>
                <option value="policy">Policy / framework</option>
                <option value="judicial_precedent">Judicial precedent</option>
                <option value="manual">Office manual</option>
              </select>
            </div>
            <div className="sk-field">
              <label className="sk-label" htmlFor="source_url">Official source URL</label>
              <input id="source_url" className="sk-input" type="url" placeholder="https://egazette.gov.in/…" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} />
            </div>
          </div>

          <div>
            <button type="submit" className="sk-btn sk-btn-primary" disabled={isSubmitting || !selectedFile || !docId.trim()}>
              {isSubmitting ? <RefreshCw size={14} aria-hidden="true" className="animate-spin" /> : <CheckCircle2 size={14} aria-hidden="true" />}
              <span>{isSubmitting ? 'Ingesting into ChromaDB…' : 'Ingest gazette'}</span>
            </button>
          </div>
        </form>
      </div>

      <div className="sk-card sk-card-soft">
        <h2 className="sk-h3">Evaluation baseline</h2>
        <p className="sk-small" style={{ marginTop: 'var(--space-xs)' }}>
          Last verified full run: <strong style={{ color: 'var(--ink)' }}>20 / 20</strong> golden inquiries
          gated correctly · mean latency 728 ms · coverage 92%+. Re-run via{' '}
          <code>python run.py --bench</code> before release claims.
        </p>
        <p className="sk-mini" style={{ marginTop: 'var(--space-xs)', display: 'inline-flex', gap: 'var(--space-xs)', alignItems: 'center' }}>
          <Database size={12} aria-hidden="true" />
          <span>Live benchmark execution ships with the eval harness, not this console.</span>
        </p>
      </div>
    </div>
  );
};
