import React, { useState } from 'react';
import type { Invoice, LineItemResponse } from '../types/invoice';
import { classifyCosts } from '../services/invoiceApi';
import './CostCodeClassifier.css';

interface CostCodeClassifierProps {
  invoice: Invoice | null;
  onClassificationComplete: () => void;
}

interface ClassifiedLineItem extends LineItemResponse {
  suggested_code?: string;
  confidence?: number;
}

interface ClassificationResult {
  invoice_id: string;
  line_items: ClassifiedLineItem[];
  status: string;
  needs_review: boolean;
  message: string;
}

export const CostCodeClassifier: React.FC<CostCodeClassifierProps> = ({
  invoice,
  onClassificationComplete
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ClassificationResult | null>(null);

  const handleClassify = async () => {
    if (!invoice) return;

    setLoading(true);
    setError(null);

    try {
      const data = await classifyCosts(invoice.id);
      setResult(data);
      onClassificationComplete();
    } catch (err: any) {
      setError(err.message || 'Classification failed');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceClass = (confidence?: number): string => {
    if (!confidence) return 'confidence-none';
    if (confidence >= 0.90) return 'confidence-high';
    if (confidence >= 0.80) return 'confidence-medium';
    return 'confidence-low';
  };

  const getConfidenceLabel = (confidence?: number): string => {
    if (!confidence) return 'N/A';
    if (confidence >= 0.90) return 'High';
    if (confidence >= 0.80) return 'Medium';
    return 'Low - Review Required';
  };

  if (!invoice) {
    return (
      <div className="cost-code-classifier">
        <div className="classifier-empty">
          <p>Select an invoice to classify cost codes</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cost-code-classifier">
      <div className="classifier-header">
        <h3>Cost Code Classification</h3>
        <button
          onClick={handleClassify}
          disabled={loading || invoice.status === 'uploaded'}
          className="classify-button"
        >
          {loading ? 'Classifying...' : result ? 'Re-classify' : 'Classify Line Items'}
        </button>
      </div>

      {invoice.status === 'uploaded' && (
        <div className="classifier-warning">
          <p>⚠️ Invoice must be extracted before classification</p>
        </div>
      )}

      {error && (
        <div className="classifier-error">
          <p>❌ {error}</p>
        </div>
      )}

      {result && (
        <div className="classification-results">
          <div className="results-summary">
            <div className="summary-item">
              <span className="summary-label">Status:</span>
              <span className={`summary-value status-${result.status}`}>
                {result.status}
              </span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Line Items:</span>
              <span className="summary-value">{result.line_items.length}</span>
            </div>
            {result.needs_review && (
              <div className="summary-item warning">
                <span className="summary-label">⚠️ Review Required:</span>
                <span className="summary-value">
                  {result.line_items.filter(item => (item.confidence || 0) < 0.80).length} items
                </span>
              </div>
            )}
          </div>

          <div className="line-items-table">
            <table>
              <thead>
                <tr>
                  <th>Description</th>
                  <th>Amount</th>
                  <th>Suggested Code</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {result.line_items.map((item, index) => (
                  <tr key={index} className={getConfidenceClass(item.confidence)}>
                    <td className="description-cell">{item.description}</td>
                    <td className="amount-cell">
                      ${typeof item.amount === 'number' ? item.amount.toFixed(2) : '0.00'}
                    </td>
                    <td className="code-cell">
                      {item.suggested_code || 'N/A'}
                    </td>
                    <td className="confidence-cell">
                      <div className="confidence-wrapper">
                        <span className="confidence-label">
                          {getConfidenceLabel(item.confidence)}
                        </span>
                        <div className="confidence-bar">
                          <div
                            className="confidence-fill"
                            style={{ width: `${(item.confidence || 0) * 100}%` }}
                          />
                        </div>
                        <span className="confidence-value">
                          {item.confidence ? `${(item.confidence * 100).toFixed(0)}%` : 'N/A'}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="classification-message">
            <p>{result.message}</p>
          </div>
        </div>
      )}
    </div>
  );
};
