// src/api/client.ts
import { toast } from '../utils/toast';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8000/api/v1' : '/api/v1');
const API_KEY = import.meta.env.VITE_API_KEY || '';

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

async function handleResponseError(response: Response, defaultMessage: string): Promise<never> {
  const err = await response.json().catch(() => ({}));
  const detail = err.message || err.detail;

  if (response.status === 429) {
    toast.warning(
      'Rate Limit Reached (429)',
      detail || 'Gemini API quota exceeded. Please pause a moment before submitting another inquiry.'
    );
    throw new Error(detail || 'Gemini API Rate Limit reached (429). Please pause before retrying.');
  }

  if (response.status === 503) {
    toast.error(
      'Service Unavailable (503)',
      detail || 'Backend reasoning service is currently experiencing downtime or high load.'
    );
    throw new Error(detail || 'Service temporarily unavailable (503).');
  }

  if (response.status === 401) {
    toast.error(
      'Authentication Required (401)',
      'API Key Required / Unauthorized: Please check your configuration in .env.'
    );
    throw new Error('API Key Required / Unauthorized: Please check your configuration.');
  }

  const message = detail || defaultMessage;
  throw new Error(message);
}

function handleNetworkError(error: unknown): never {
  const isNetworkFailure =
    (typeof navigator !== 'undefined' && !navigator.onLine) ||
    (error instanceof TypeError && (error.message.includes('fetch') || error.message.includes('Network') || error.message.includes('failed')));

  if (isNetworkFailure) {
    toast.error(
      'Network Disconnection',
      'Unable to connect to the backend server. Please check your network connection.'
    );
  }
  throw error;
}

export async function submitQuery(request: QueryRequest): Promise<QueryResponse> {
  const safeRequest = {
    ...request,
    query_text: scrubPII(request.query_text),
  };

  try {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
      },
      body: JSON.stringify(safeRequest),
    });

    if (!response.ok) {
      return await handleResponseError(response, 'Service temporarily unavailable');
    }

    return response.json();
  } catch (err) {
    return handleNetworkError(err);
  }
}

export interface SessionTurn {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[] | null;
  response_metadata?: QueryResponse | null;
  created_at?: string;
}

export interface SessionDetail {
  session_id: string;
  turns: SessionTurn[];
  total_turns: number;
  created_at?: string;
  updated_at?: string;
}

export async function fetchSession(sessionId: string): Promise<SessionDetail> {
  try {
    const response = await fetch(`${API_BASE_URL}/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
      },
    });

    if (!response.ok) {
      return await handleResponseError(response, 'Failed to retrieve session');
    }

    return response.json();
  } catch (err) {
    return handleNetworkError(err);
  }
}

export interface SessionSummary {
  session_id: string;
  preview: string | null;
  total_turns: number;
  created_at?: string;
  updated_at?: string;
}

export async function fetchSessions(limit: number = 50): Promise<SessionSummary[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/sessions?limit=${limit}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
      },
    });

    if (!response.ok) {
      return await handleResponseError(response, 'Failed to retrieve sessions');
    }

    return response.json();
  } catch (err) {
    return handleNetworkError(err);
  }
}


