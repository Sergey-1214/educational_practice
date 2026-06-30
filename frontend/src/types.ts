export type DocumentStatus = 'uploaded' | 'processing' | 'processed' | 'failed'

export interface User { id: string; email: string; is_active: boolean; created_at: string }
export interface Tokens { access_token: string; refresh_token: string; token_type: string }
export interface DocumentItem {
  id: string; user_id: string | null; file_name: string; content_type: string;
  size_bytes: number; status: DocumentStatus; chunks_count: number;
  error_message: string | null; created_at: string; updated_at: string
}
export interface SearchResult {
  chunk_id: string; document_id: string; file_name: string; page: number; text: string; score: number
}
export interface HistoryItem {
  id: string; user_id: string; document_id: string | null; query: string;
  results_count: number; created_at: string
}
export interface UploadItem { id: string; name: string; progress: number; state: 'uploading' | 'indexing' | 'done' | 'error'; message?: string }
