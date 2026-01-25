import { useState } from 'react';
import { invoiceApi } from '../services/invoiceApi';
import type { ExtractionResult } from '../types/invoice';
import './TraditionalOCRProcessor.css';

interface TraditionalOCRProcessorProps {
  invoiceId: string;
  onExtractionComplete?: (result: ExtractionResult) => void;
}

export function TraditionalOCRProcessor({ invoiceId, onExtractionComplete }: TraditionalOCRProcessorProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExtract = async () => {
    setIsProcessing(true);
    setError(null);
    
    try {
      const extractionResult = await invoiceApi.extractTraditional(invoiceId);
      setResult(extractionResult);
      onExtractionComplete?.(extractionResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Extraction failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.85) return 'confidence-high';
    if (confidence >= 0.70) return 'confidence-medium';
    return 'confidence-low';
  };

  const getStatusBadge = (status: string) => {
    const statusMap = {
      success: { label: 'Success', className: 'status-success' },
      partial: { label: 'Partial', className: 'status-partial' },
      failed: { label: 'Failed', className: 'status-failed' },
    };
    const statusInfo = statusMap[status as keyof typeof statusMap] || statusMap.failed;
    return <span className={`status-badge ${statusInfo.className}`}>{statusInfo.label}</span>;
  };

  return (
    <div className="traditional-ocr-processor">
      <div className="processor-header">
        <h3>🔍 Traditional OCR Extraction</h3>
        <p className="processor-description">
          Uses Tesseract OCR + regex pattern matching to extract invoice data
        </p>
      </div>

      {!result && (
        <button
          className="extract-button"
          onClick={handleExtract}
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <span className="spinner"></span>
              Processing with OCR...
            </>
          ) : (
            <>
              <span className="icon">📄</span>
              Extract with Traditional OCR
            </>
          )}
        </button>
      )}

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className="extraction-results">
          <div className="results-header">
            <div className="results-status">
              {getStatusBadge(result.extraction_status)}
              <span className={`confidence-badge ${getConfidenceColor(result.confidence)}`}>
                Confidence: {(result.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="processing-time">
              ⏱️ {result.processing_time_ms}ms
            </div>
          </div>

          <div className="extracted-fields">
            <h4>Extracted Fields</h4>
            <div className="fields-grid">
              <div className="field-item">
                <label>Vendor Name</label>
                <div className={`field-value ${!result.fields.vendor_name ? 'empty' : ''}`}>
                  {result.fields.vendor_name || '—'}
                </div>
              </div>

              <div className="field-item">
                <label>Invoice Number</label>
                <div className={`field-value ${!result.fields.invoice_number ? 'empty' : ''}`}>
                  {result.fields.invoice_number || '—'}
                </div>
              </div>

              <div className="field-item">
                <label>Invoice Date</label>
                <div className={`field-value ${!result.fields.invoice_date ? 'empty' : ''}`}>
                  {result.fields.invoice_date || '—'}
                </div>
              </div>

              <div className="field-item">
                <label>Total Amount</label>
                <div className={`field-value ${!result.fields.total_amount ? 'empty' : ''}`}>
                  {result.fields.total_amount ? `$${result.fields.total_amount.toFixed(2)}` : '—'}
                </div>
              </div>
            </div>
          </div>

          {result.line_items.length > 0 && (
            <div className="line-items-section">
              <h4>Line Items ({result.line_items.length})</h4>
              <table className="line-items-table">
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Qty</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {result.line_items.map((item, index) => (
                    <tr key={index}>
                      <td>{item.description}</td>
                      <td>{item.quantity?.toFixed(2) || '—'}</td>
                      <td>{item.unit_price ? `$${item.unit_price.toFixed(2)}` : '—'}</td>
                      <td className="amount">${item.total.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {result.raw_output?.ocr_text && (
            <details className="raw-output">
              <summary>Raw OCR Text (first 500 chars)</summary>
              <pre>{result.raw_output.ocr_text}</pre>
            </details>
          )}

          <button
            className="extract-button secondary"
            onClick={handleExtract}
            disabled={isProcessing}
          >
            Re-extract
          </button>
        </div>
      )}
    </div>
  );
}

