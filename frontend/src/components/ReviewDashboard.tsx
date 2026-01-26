import React, { useState, useEffect } from 'react';
import type { Invoice, InvoiceDetail } from '../types/invoice';
import { listInvoices, getInvoice, updateInvoiceStatus } from '../services/invoiceApi';
import { InvoiceReviewForm } from './InvoiceReviewForm';
import './ReviewDashboard.css';

const TEST_BUILDER_ID = '00000000-0000-0000-0000-000000000001';

export const ReviewDashboard: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceDetail | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadInvoices();
  }, [statusFilter]);

  const loadInvoices = async () => {
    setLoading(true);
    setError(null);

    try {
      const params: any = { builderId: TEST_BUILDER_ID };
      
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }

      const data = await listInvoices(params);
      setInvoices(data);

      // If an invoice is selected, reload it to get updated data
      if (selectedInvoice) {
        const updatedInvoice = await getInvoice(selectedInvoice.id);
        setSelectedInvoice(updatedInvoice);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectInvoice = async (invoice: Invoice) => {
    try {
      const detail = await getInvoice(invoice.id);
      setSelectedInvoice(detail);
    } catch (err: any) {
      setError(err.message || 'Failed to load invoice details');
    }
  };

  const handleApprove = async () => {
    if (!selectedInvoice) return;

    try {
      setActionMessage('Approving invoice...');
      await updateInvoiceStatus(selectedInvoice.id, 'approved');
      setActionMessage('✅ Invoice approved!');
      
      setTimeout(() => setActionMessage(null), 3000);
      
      // Reload data
      await loadInvoices();
    } catch (err: any) {
      setActionMessage(`❌ Failed to approve: ${err.message}`);
      setTimeout(() => setActionMessage(null), 5000);
    }
  };

  const handleReject = async () => {
    if (!selectedInvoice) return;

    const confirmed = window.confirm('Are you sure you want to reject this invoice?');
    if (!confirmed) return;

    try {
      setActionMessage('Rejecting invoice...');
      await updateInvoiceStatus(selectedInvoice.id, 'rejected');
      setActionMessage('✅ Invoice rejected');
      
      setTimeout(() => setActionMessage(null), 3000);
      
      // Reload data
      await loadInvoices();
    } catch (err: any) {
      setActionMessage(`❌ Failed to reject: ${err.message}`);
      setTimeout(() => setActionMessage(null), 5000);
    }
  };

  const handleSaveSuccess = () => {
    // Reload invoices to reflect any status changes
    loadInvoices();
  };

  const getStatusBadgeClass = (status: string): string => {
    const baseClass = 'status-badge';
    switch (status) {
      case 'uploaded': return `${baseClass} status-uploaded`;
      case 'processing': return `${baseClass} status-processing`;
      case 'extracted': return `${baseClass} status-extracted`;
      case 'matched': return `${baseClass} status-matched`;
      case 'classified': return `${baseClass} status-classified`;
      case 'needs_review': return `${baseClass} status-needs-review`;
      case 'approved': return `${baseClass} status-approved`;
      case 'rejected': return `${baseClass} status-rejected`;
      default: return baseClass;
    }
  };

  const getInvoiceImageUrl = (invoice: InvoiceDetail): string => {
    // Assuming images are served from backend uploads folder
    return `http://localhost:8000/uploads/${invoice.id}/${invoice.filename}`;
  };

  return (
    <div className="review-dashboard">
      <div className="dashboard-header">
        <h2>📋 Review Queue</h2>
        <div className="filter-controls">
          <label htmlFor="status-filter">Filter by Status:</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="status-filter"
          >
            <option value="all">All Invoices</option>
            <option value="needs_review">Needs Review</option>
            <option value="classified">Classified</option>
            <option value="matched">Matched</option>
            <option value="extracted">Extracted</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <button onClick={loadInvoices} className="refresh-button" disabled={loading}>
            {loading ? '⟳' : '↻'} Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          ❌ {error}
        </div>
      )}

      <div className="dashboard-content">
        {/* Invoice List */}
        <div className="invoice-list">
          <h3>Invoices ({invoices.length})</h3>
          {loading && <div className="loading-message">Loading invoices...</div>}
          {!loading && invoices.length === 0 && (
            <div className="empty-message">
              No invoices found for this filter.
            </div>
          )}
          {invoices.map((invoice) => (
            <div
              key={invoice.id}
              className={`invoice-card ${selectedInvoice?.id === invoice.id ? 'selected' : ''}`}
              onClick={() => handleSelectInvoice(invoice)}
            >
              <div className="invoice-card-header">
                <span className="invoice-filename">{invoice.filename}</span>
                <span className={getStatusBadgeClass(invoice.status)}>
                  {invoice.status.replace('_', ' ')}
                </span>
              </div>
              <div className="invoice-card-meta">
                <span>Uploaded: {new Date(invoice.uploaded_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Review Panel */}
        <div className="review-panel">
          {!selectedInvoice && (
            <div className="no-selection">
              <h3>👈 Select an invoice to review</h3>
              <p>Choose an invoice from the list to view details and make corrections.</p>
            </div>
          )}

          {selectedInvoice && (
            <>
              <div className="invoice-preview">
                <h3>Invoice Preview</h3>
                <div className="preview-container">
                  <img 
                    src={getInvoiceImageUrl(selectedInvoice)} 
                    alt={selectedInvoice.filename}
                    onError={(e) => {
                      // Fallback if image fails to load
                      (e.target as HTMLImageElement).style.display = 'none';
                      const parent = (e.target as HTMLElement).parentElement;
                      if (parent) {
                        parent.innerHTML = '<div class="preview-error">Preview not available</div>';
                      }
                    }}
                  />
                </div>
              </div>

              <div className="invoice-form">
                <InvoiceReviewForm 
                  invoice={selectedInvoice} 
                  onSaveSuccess={handleSaveSuccess}
                />
              </div>

              <div className="action-panel">
                <h3>Final Decision</h3>
                {actionMessage && (
                  <div className={`action-message ${actionMessage.startsWith('❌') ? 'error' : 'success'}`}>
                    {actionMessage}
                  </div>
                )}
                <div className="action-buttons">
                  <button 
                    onClick={handleApprove} 
                    className="approve-button"
                    disabled={selectedInvoice.status === 'approved'}
                  >
                    ✓ Approve Invoice
                  </button>
                  <button 
                    onClick={handleReject} 
                    className="reject-button"
                    disabled={selectedInvoice.status === 'rejected'}
                  >
                    ✗ Reject Invoice
                  </button>
                </div>
                {selectedInvoice.status === 'approved' && (
                  <div className="status-info approved-info">
                    ✅ This invoice has been approved
                  </div>
                )}
                {selectedInvoice.status === 'rejected' && (
                  <div className="status-info rejected-info">
                    ❌ This invoice has been rejected
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

