import { useState, useEffect } from 'react';
import type { Receipt } from '../types/receipt';
import { receiptsApi } from '../services/api';
import './ReceiptModal.css';

interface ReceiptModalProps {
  isOpen: boolean;
  onClose: () => void;
  receiptId?: number | null;
  onSave: () => void;
}

export default function ReceiptModal({ isOpen, onClose, receiptId, onSave }: ReceiptModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    vendor: '',
    total: '',
    description: '',
  });
  const [receipt, setReceipt] = useState<Receipt | null>(null);

  useEffect(() => {
    if (isOpen && receiptId) {
      loadReceipt();
    } else if (isOpen && !receiptId) {
      setIsEditing(true);
      setFormData({ vendor: '', total: '', description: '' });
      setReceipt(null);
    }
  }, [isOpen, receiptId]);

  const loadReceipt = async () => {
    if (!receiptId) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await receiptsApi.getById(receiptId);
      setReceipt(data);
      setFormData({
        vendor: data.vendor,
        total: data.total.toString(),
        description: data.description || '',
      });
      setIsEditing(false);
    } catch (err) {
      setError('Failed to load receipt');
      console.error('Error loading receipt:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.vendor || !formData.total) {
      setError('Vendor and total are required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const receiptData = {
        vendor: formData.vendor,
        total: parseFloat(formData.total),
        description: formData.description || null,
      };

      if (receiptId) {
        await receiptsApi.update(receiptId, receiptData);
      } else {
        await receiptsApi.create(receiptData);
      }

      onSave();
      handleClose();
    } catch (err) {
      setError('Failed to save receipt');
      console.error('Error saving receipt:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!receiptId || !confirm('Are you sure you want to delete this receipt?')) return;

    try {
      setLoading(true);
      setError(null);
      await receiptsApi.delete(receiptId);
      onSave();
      handleClose();
    } catch (err) {
      setError('Failed to delete receipt');
      console.error('Error deleting receipt:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({ vendor: '', total: '', description: '' });
    setReceipt(null);
    setIsEditing(false);
    setError(null);
    onClose();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{receiptId ? (isEditing ? 'Edit Receipt' : 'Receipt Details') : 'Add New Receipt'}</h2>
          <button className="close-btn" onClick={handleClose}>&times;</button>
        </div>

        {loading && <div className="modal-loading">Loading...</div>}
        {error && <div className="modal-error">{error}</div>}

        {!loading && (
          <>
            {!isEditing && receipt ? (
              <div className="receipt-details">
                <div className="detail-row">
                  <span className="detail-label">ID:</span>
                  <span className="detail-value">{receipt.id}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Date:</span>
                  <span className="detail-value">{formatDate(receipt.date)}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Vendor:</span>
                  <span className="detail-value">{receipt.vendor}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Total:</span>
                  <span className="detail-value amount">{formatCurrency(receipt.total)}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Description:</span>
                  <span className="detail-value">{receipt.description || '-'}</span>
                </div>

                <div className="modal-actions">
                  <button className="btn-edit" onClick={() => setIsEditing(true)}>
                    Edit
                  </button>
                  <button className="btn-delete" onClick={handleDelete}>
                    Delete
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="receipt-form">
                <div className="form-group">
                  <label htmlFor="vendor">Vendor *</label>
                  <input
                    type="text"
                    id="vendor"
                    value={formData.vendor}
                    onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                    required
                    placeholder="Enter vendor name"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="total">Total Amount *</label>
                  <input
                    type="number"
                    id="total"
                    step="0.01"
                    min="0"
                    value={formData.total}
                    onChange={(e) => setFormData({ ...formData, total: e.target.value })}
                    required
                    placeholder="0.00"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="description">Description</label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Enter description (optional)"
                    rows={4}
                  />
                </div>

                <div className="modal-actions">
                  <button type="submit" className="btn-save" disabled={loading}>
                    {loading ? 'Saving...' : 'Save'}
                  </button>
                  {receiptId && (
                    <button
                      type="button"
                      className="btn-cancel"
                      onClick={() => {
                        setIsEditing(false);
                        if (receipt) {
                          setFormData({
                            vendor: receipt.vendor,
                            total: receipt.total.toString(),
                            description: receipt.description || '',
                          });
                        }
                      }}
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </form>
            )}
          </>
        )}
      </div>
    </div>
  );
}
