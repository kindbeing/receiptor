import { useEffect, useState } from 'react';
import { receiptsApi } from '../services/api';
import type { Receipt } from '../types/receipt';
import ReceiptModal from './ReceiptModal';
import './ReceiptsTable.css';

export default function ReceiptsTable() {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedReceiptId, setSelectedReceiptId] = useState<number | null>(null);

  useEffect(() => {
    loadReceipts();
  }, []);

  const loadReceipts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await receiptsApi.getAll();
      setReceipts(data);
    } catch (err) {
      setError('Failed to load receipts. Make sure the backend is running.');
      console.error('Error loading receipts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReceiptClick = (id: number) => {
    setSelectedReceiptId(id);
    setIsModalOpen(true);
  };

  const handleAddReceipt = () => {
    setSelectedReceiptId(null);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedReceiptId(null);
  };

  const handleSave = () => {
    loadReceipts();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
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

  if (loading) {
    return <div className="loading">Loading receipts...</div>;
  }

  if (error) {
    return (
      <div className="error">
        <p>{error}</p>
        <button onClick={loadReceipts}>Retry</button>
      </div>
    );
  }

  return (
    <div className="receipts-container">
      <div className="receipts-header">
        <h1>Receipts</h1>
        <div className="header-actions">
          <button className="add-btn" onClick={handleAddReceipt}>
            + Add Receipt
          </button>
          <button className="refresh-btn" onClick={loadReceipts}>
            Refresh
          </button>
        </div>
      </div>

      {receipts.length === 0 ? (
        <div className="empty-state">
          <p>No receipts found</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="receipts-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Vendor</th>
                <th>Total</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {receipts.map((receipt) => (
                <tr key={receipt.id}>
                  <td>
                    <button 
                      className="receipt-id-link" 
                      onClick={() => handleReceiptClick(receipt.id)}
                    >
                      {receipt.id}
                    </button>
                  </td>
                  <td>{formatDate(receipt.date)}</td>
                  <td>{receipt.vendor}</td>
                  <td className="amount">{formatCurrency(receipt.total)}</td>
                  <td>{receipt.description || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="receipts-footer">
        <p>Total: {receipts.length} receipt{receipts.length !== 1 ? 's' : ''}</p>
      </div>

      <ReceiptModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        receiptId={selectedReceiptId}
        onSave={handleSave}
      />
    </div>
  );
}
