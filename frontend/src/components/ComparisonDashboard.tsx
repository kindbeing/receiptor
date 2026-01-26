import React, { useState, useEffect } from 'react';
import type { Invoice } from '../types/invoice';
import { getComparison } from '../services/invoiceApi';
import './ComparisonDashboard.css';

interface ComparisonDashboardProps {
  invoice: Invoice | null;
}

interface MethodData {
  available: boolean;
  fields: {
    vendor_name?: string;
    invoice_number?: string;
    invoice_date?: string;
    total_amount?: number;
  } | null;
  line_items: Array<{
    description: string;
    quantity?: number;
    unit_price?: number;
    amount: number;
  }>;
  confidence?: number;
  processing_time_ms?: number;
}

interface ComparisonData {
  invoice_id: string;
  invoice_filename: string;
  traditional: MethodData;
  vision: MethodData;
  comparison: {
    field_match_rate?: number;
    time_difference_ms?: number;
    confidence_difference?: number;
    winner?: string;
  };
}

export const ComparisonDashboard: React.FC<ComparisonDashboardProps> = ({ invoice }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ComparisonData | null>(null);

  useEffect(() => {
    if (invoice && invoice.status !== 'uploaded') {
      loadComparison();
    }
  }, [invoice?.id]);

  const loadComparison = async () => {
    if (!invoice) return;

    setLoading(true);
    setError(null);

    try {
      const comparisonData = await getComparison(invoice.id);
      setData(comparisonData);
    } catch (err: any) {
      setError(err.message || 'Failed to load comparison');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (ms?: number): string => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatConfidence = (conf?: number): string => {
    if (!conf) return 'N/A';
    return `${(conf * 100).toFixed(0)}%`;
  };

  const getWinnerBadge = (winner?: string): React.ReactElement | null => {
    if (!winner) return null;
    if (winner === 'tie') return <span className="winner-badge tie">Tie</span>;
    if (winner === 'vision') return <span className="winner-badge vision">Vision AI Winner</span>;
    if (winner === 'traditional') return <span className="winner-badge traditional">Traditional Winner</span>;
    return null;
  };

  if (!invoice) {
    return (
      <div className="comparison-dashboard">
        <div className="comparison-empty">
          <p>Select an invoice to view comparison</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="comparison-dashboard">
        <div className="comparison-loading">
          <p>Loading comparison data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="comparison-dashboard">
        <div className="comparison-error">
          <p>❌ {error}</p>
          <button onClick={loadComparison} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="comparison-dashboard">
        <div className="comparison-empty">
          <p>No comparison data available</p>
          <button onClick={loadComparison} className="load-button">Load Comparison</button>
        </div>
      </div>
    );
  }

  const { traditional, vision, comparison } = data;

  return (
    <div className="comparison-dashboard">
      <div className="comparison-header">
        <h2>Extraction Method Comparison</h2>
        {getWinnerBadge(comparison.winner)}
      </div>

      <div className="comparison-metrics">
        <div className="metric-card">
          <div className="metric-label">Field Match Rate</div>
          <div className="metric-value">
            {comparison.field_match_rate !== null && comparison.field_match_rate !== undefined
              ? `${(comparison.field_match_rate * 100).toFixed(0)}%`
              : 'N/A'}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Time Difference</div>
          <div className="metric-value">
            {comparison.time_difference_ms !== null && comparison.time_difference_ms !== undefined
              ? formatTime(Math.abs(comparison.time_difference_ms))
              : 'N/A'}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Confidence Difference</div>
          <div className="metric-value">
            {comparison.confidence_difference !== null && comparison.confidence_difference !== undefined
              ? `${(Math.abs(comparison.confidence_difference) * 100).toFixed(0)}%`
              : 'N/A'}
          </div>
        </div>
      </div>

      <div className="comparison-grid">
        <div className="method-panel traditional-panel">
          <div className="panel-header">
            <h3>Traditional OCR</h3>
            <span className="method-badge traditional">Tesseract</span>
          </div>

          {!traditional.available ? (
            <div className="panel-empty">
              <p>Not processed with Traditional OCR</p>
            </div>
          ) : (
            <>
              <div className="panel-stats">
                <div className="stat-item">
                  <span className="stat-label">Confidence:</span>
                  <span className="stat-value">{formatConfidence(traditional.confidence)}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Time:</span>
                  <span className="stat-value">{formatTime(traditional.processing_time_ms)}</span>
                </div>
              </div>

              <div className="panel-fields">
                <h4>Extracted Fields</h4>
                <div className="field-list">
                  <div className="field-item">
                    <span className="field-label">Vendor:</span>
                    <span className="field-value">{traditional.fields?.vendor_name || 'N/A'}</span>
                  </div>
                  <div className="field-item">
                    <span className="field-label">Invoice #:</span>
                    <span className="field-value">{traditional.fields?.invoice_number || 'N/A'}</span>
                  </div>
                  <div className="field-item">
                    <span className="field-label">Date:</span>
                    <span className="field-value">{traditional.fields?.invoice_date || 'N/A'}</span>
                  </div>
                  <div className="field-item">
                    <span className="field-label">Total:</span>
                    <span className="field-value">
                      {traditional.fields?.total_amount
                        ? `$${traditional.fields.total_amount.toFixed(2)}`
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="panel-line-items">
                <h4>Line Items ({traditional.line_items.length})</h4>
                <div className="line-items-preview">
                  {traditional.line_items.slice(0, 3).map((item, idx) => (
                    <div key={idx} className="line-item-preview">
                      <span className="item-desc">{item.description}</span>
                      <span className="item-amount">${item.amount.toFixed(2)}</span>
                    </div>
                  ))}
                  {traditional.line_items.length > 3 && (
                    <div className="line-items-more">
                      +{traditional.line_items.length - 3} more items
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        <div className="method-panel vision-panel">
          <div className="panel-header">
            <h3>Vision AI</h3>
            <span className="method-badge vision">Qwen2.5vl:7b</span>
          </div>

          {!vision.available ? (
            <div className="panel-empty">
              <p>Not processed with Vision AI</p>
            </div>
          ) : (
            <>
              <div className="panel-stats">
                <div className="stat-item">
                  <span className="stat-label">Confidence:</span>
                  <span className="stat-value">{formatConfidence(vision.confidence)}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Time:</span>
                  <span className="stat-value">{formatTime(vision.processing_time_ms)}</span>
                </div>
              </div>

              <div className="panel-fields">
                <h4>Extracted Fields</h4>
                <div className="field-list">
                  <div className="field-item">
                    <span className="field-label">Vendor:</span>
                    <span className="field-value">{vision.fields?.vendor_name || 'N/A'}</span>
                  </div>
                  <div className="field-item">
                    <span className="field-label">Invoice #:</span>
                    <span className="field-value">{vision.fields?.invoice_number || 'N/A'}</span>
                  </div>
                  <div className="field-item">
                    <span className="field-label">Date:</span>
                    <span className="field-value">{vision.fields?.invoice_date || 'N/A'}</span>
                  </div>
                  <div className="field-item">
                    <span className="field-label">Total:</span>
                    <span className="field-value">
                      {vision.fields?.total_amount
                        ? `$${vision.fields.total_amount.toFixed(2)}`
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="panel-line-items">
                <h4>Line Items ({vision.line_items.length})</h4>
                <div className="line-items-preview">
                  {vision.line_items.slice(0, 3).map((item, idx) => (
                    <div key={idx} className="line-item-preview">
                      <span className="item-desc">{item.description}</span>
                      <span className="item-amount">${item.amount.toFixed(2)}</span>
                    </div>
                  ))}
                  {vision.line_items.length > 3 && (
                    <div className="line-items-more">
                      +{vision.line_items.length - 3} more items
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
