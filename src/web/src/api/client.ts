// src/api/client.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8000/api/v1' : '/api/v1');

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  responseMetadata?: QueryResponse;
}

export interface QueryRequest {
  query_text: string;
  session_id: string;
  conversation_history?: Message[];
}

export interface Citation {
  doc_id: string;
  snippet?: string;
  section?: string;
  source_url?: string;
  title?: string;
  doc_type?: string;
  date_retrieved?: string;
}

export interface QueryResponse {
  status: 'answered' | 'abstained';
  answer: string | null;
  category?: string;
  jurisdiction?: string;
  citations: Citation[];
  confidence_score: number;
  response_time_ms: number;
  abs_flag: boolean;
  abs_detail?: string;
  tkdl_flag: boolean;
  tkdl_detail?: string;
  abstention_message?: string;
  disclaimer?: string;
  grounding_score?: number;
  verification_status?: string;
}

function scrubPII(text: string): string {
  if (!text) return text;
  let scrubbed = text;
  // Aadhaar format (12 digits)
  scrubbed = scrubbed.replace(/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, '[REDACTED AADHAAR]');
  // Phone number format (10 digits)
  scrubbed = scrubbed.replace(/\b(\+91[\s-]?)?\d{10}\b/g, '[REDACTED PHONE]');
  // Email format
  scrubbed = scrubbed.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[REDACTED EMAIL]');
  return scrubbed;
}

export async function submitQuery(request: QueryRequest): Promise<QueryResponse> {
  const safeRequest = {
    ...request,
    query_text: scrubPII(request.query_text),
  };

  const response = await fetch(`${API_BASE_URL}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(safeRequest),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Service temporarily unavailable');
  }

  return response.json();
}
