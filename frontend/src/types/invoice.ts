// Invoice Automation Types - Matches backend schemas

export interface Invoice {
  id: string;
  filename: string;
  file_path: string;
  builder_id: string;
  uploaded_at: string;
  status: InvoiceStatus;
  processing_method?: ProcessingMethod;
  created_at: string;
}

export type InvoiceStatus = 
  | 'uploaded'
  | 'processing'
  | 'extracted'
  | 'matched'
  | 'classified'
  | 'needs_review'
  | 'approved'
  | 'rejected';

export type ProcessingMethod = 'traditional' | 'vision';

export interface LineItem {
  description: string;
  quantity?: number;
  unit_price?: number;
  total: number;
}

export interface LineItemResponse extends LineItem {
  id: string;
  invoice_id: string;
  amount: number;
  suggested_code?: string;
  confidence?: number;
  confirmed_code?: string;
  created_at: string;
}

export interface ExtractedFields {
  vendor_name?: string;
  invoice_number?: string;
  invoice_date?: string;
  total_amount?: number;
}

export interface ExtractedFieldResponse extends ExtractedFields {
  id: string;
  invoice_id: string;
  confidence?: number;
  raw_json?: any;
  created_at: string;
}

export interface ExtractionResult {
  invoice_id: string;
  processing_method: ProcessingMethod;
  extraction_status: 'success' | 'partial' | 'failed';
  fields: ExtractedFields;
  line_items: LineItem[];
  confidence: number;
  processing_time_ms: number;
  raw_output?: any;
  created_at: string;
}

export interface InvoiceDetail extends Invoice {
  extracted_fields?: ExtractedFieldResponse;
  line_items: LineItemResponse[];
  vendor_matches: VendorMatch[];
  processing_metrics: ProcessingMetric[];
}

export interface VendorMatch {
  id: string;
  invoice_id: string;
  subcontractor_id?: string;
  match_score?: number;
  confirmed_at?: string;
  created_at: string;
}

export interface Subcontractor {
  id: string;
  name: string;
  builder_id: string;
  contact_info?: any;
  created_at: string;
}

export interface CostCode {
  id: string;
  code: string;
  label: string;
  description?: string;
  builder_id: string;
  created_at: string;
}

export interface ProcessingMetric {
  id: string;
  invoice_id: string;
  method?: ProcessingMethod;
  processing_time_ms?: number;
  created_at: string;
}

export interface MatchCandidate {
  subcontractor_id: string;
  subcontractor_name: string;
  score: number;
  confidence_level: 'high' | 'auto_approve' | 'review' | 'low';
  contact_info?: any;
}

export interface VendorMatchResult {
  invoice_id: string;
  extracted_vendor: string;
  matches: MatchCandidate[];
  status: InvoiceStatus;
  message: string;
}

export interface CorrectionHistory {
  id: string;
  field_name: string;
  original_value: string | null;
  corrected_value: string | null;
  corrected_by?: string;
  correction_type: string;
  created_at: string;
}

export interface ReviewFormData {
  vendor_name?: string;
  invoice_number?: string;
  invoice_date?: string;
  total_amount?: number | string;
  line_items?: LineItemResponse[];
}

export interface CorrectionRequest {
  [field_name: string]: any;
}

export interface StatusUpdateResponse {
  invoice_id: string;
  status: InvoiceStatus;
  updated_at: string;
  message: string;
}

export interface CorrectionsResponse {
  invoice_id: string;
  corrections_saved: number;
  corrections: Array<{
    field_name: string;
    original_value: string | null;
    corrected_value: string | null;
    created_at: string;
  }>;
  message: string;
}

