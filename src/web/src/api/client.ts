// src/api/client.ts
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
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
  answer: string;
  category?: string;
  jurisdiction?: string;
  citations: Citation[];
  confidence_score: number;
  response_time_ms: number;
  abs_flag: boolean;
  abs_detail?: string;
  tkdl_flag: boolean;
  tkdl_detail?: string;
}

export async function submitQuery(request: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Service temporarily unavailable');
  }

  return response.json();
}
