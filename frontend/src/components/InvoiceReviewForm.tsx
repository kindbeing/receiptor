import React, { useState, useEffect } from 'react';
import type { InvoiceDetail, ReviewFormData, ExtractedFieldResponse } from '../types/invoice';
import { saveCorrections } from '../services/invoiceApi';
import './InvoiceReviewForm.css';

interface InvoiceReviewFormProps {
  invoice: InvoiceDetail;
  onSaveSuccess?: () => void;
}

export const InvoiceReviewForm: React.FC<InvoiceReviewFormProps> = ({ invoice, onSaveSuccess }) => {
  const [formData, setFormData] = useState<ReviewFormData>({});
  const [originalData, setOriginalData] = useState<ReviewFormData>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    // Load extracted fields from invoice
    // extracted_fields is an array - select the best one (highest confidence, or most recent)
    const extractedFields = invoice.extracted_fields || [];
    
    let bestExtraction = null;
    if (extractedFields.length > 0) {
      // Sort by confidence (descending), then by created_at (most recent first)
      const sorted = [...extractedFields].sort((a, b) => {
        const confA = a.confidence ?? 0;
        const confB = b.confidence ?? 0;
        if (confA !== confB) {
          return confB - confA; // Higher confidence first
        }
        // If confidence is equal, use most recent
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      bestExtraction = sorted[0];
    }
    
    if (bestExtraction) {
      const data: ReviewFormData = {
        vendor_name: bestExtraction.vendor_name || '',
        invoice_number: bestExtraction.invoice_number || '',
        invoice_date: bestExtraction.invoice_date || '',
        total_amount: bestExtraction.total_amount || 0,
        line_items: invoice.line_items || []
      };
      
      setFormData(data);
      setOriginalData(JSON.parse(JSON.stringify(data))); // Deep copy
    }
  }, [invoice]);

  const getConfidence = (fieldName: string): number | undefined => {
    // Get confidence from the best extraction (highest confidence)
    const extractedFields = invoice.extracted_fields || [];
    if (extractedFields.length === 0) return undefined;
    
    const sorted = [...extractedFields].sort((a, b) => {
      const confA = a.confidence ?? 0;
      const confB = b.confidence ?? 0;
      return confB - confA;
    });
    
    return sorted[0]?.confidence;
  };

  const isLowConfidence = (fieldName: string): boolean => {
    const confidence = getConfidence(fieldName);
    return confidence !== undefined && confidence < 0.85;
  };

  const hasChanges = (): boolean => {
    return JSON.stringify(formData) !== JSON.stringify(originalData);
  };

  const handleFieldChange = (fieldName: keyof ReviewFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleSaveCorrections = async () => {
    if (!hasChanges()) {
      setSaveMessage('No changes to save');
      setTimeout(() => setSaveMessage(null), 3000);
      return;
    }

    setIsSaving(true);
    setSaveMessage(null);

    try {
      // Build corrections object with only changed fields
      const corrections: Record<string, any> = {};
      
      (Object.keys(formData) as Array<keyof ReviewFormData>).forEach(key => {
        if (key !== 'line_items' && formData[key] !== originalData[key]) {
          corrections[key] = formData[key];
        }
      });

      if (Object.keys(corrections).length === 0) {
        setSaveMessage('No field-level changes to save');
        setIsSaving(false);
        setTimeout(() => setSaveMessage(null), 3000);
        return;
      }

      await saveCorrections(invoice.id, corrections);
      
      setSaveMessage(`✅ Saved ${Object.keys(corrections).length} correction(s)`);
      setOriginalData(JSON.parse(JSON.stringify(formData))); // Update original after save
      
      setTimeout(() => setSaveMessage(null), 5000);
      
      if (onSaveSuccess) {
        onSaveSuccess();
      }
    } catch (error: any) {
      setSaveMessage(`❌ Error: ${error.message}`);
      setTimeout(() => setSaveMessage(null), 5000);
    } finally {
      setIsSaving(false);
    }
  };

  const getFieldClassName = (fieldName: string, hasChanged: boolean): string => {
    const classes = ['form-field'];
    if (isLowConfidence(fieldName)) classes.push('low-confidence');
    if (hasChanged) classes.push('changed');
    return classes.join(' ');
  };

  return (
    <div className="invoice-review-form">
      <div className="form-header">
        <h3>Invoice Details</h3>
        {(() => {
          const confidence = getConfidence('');
          return confidence !== undefined && (
            <div className="overall-confidence">
              Overall Confidence: {(confidence * 100).toFixed(0)}%
            </div>
          );
        })()}
      </div>

      <div className="form-body">
        <div className={getFieldClassName('vendor_name', formData.vendor_name !== originalData.vendor_name)}>
          <label htmlFor="vendor_name">
            Vendor Name
            {isLowConfidence('vendor_name') && <span className="warning-badge">Low Confidence</span>}
          </label>
          <input
            type="text"
            id="vendor_name"
            value={formData.vendor_name || ''}
            onChange={(e) => handleFieldChange('vendor_name', e.target.value)}
            placeholder="Enter vendor name"
          />
        </div>

        <div className="form-row">
          <div className={getFieldClassName('invoice_number', formData.invoice_number !== originalData.invoice_number)}>
            <label htmlFor="invoice_number">
              Invoice Number
              {isLowConfidence('invoice_number') && <span className="warning-badge">Low Confidence</span>}
            </label>
            <input
              type="text"
              id="invoice_number"
              value={formData.invoice_number || ''}
              onChange={(e) => handleFieldChange('invoice_number', e.target.value)}
              placeholder="Enter invoice number"
            />
          </div>

          <div className={getFieldClassName('invoice_date', formData.invoice_date !== originalData.invoice_date)}>
            <label htmlFor="invoice_date">
              Invoice Date
              {isLowConfidence('invoice_date') && <span className="warning-badge">Low Confidence</span>}
            </label>
            <input
              type="date"
              id="invoice_date"
              value={formData.invoice_date || ''}
              onChange={(e) => handleFieldChange('invoice_date', e.target.value)}
            />
          </div>
        </div>

        <div className={getFieldClassName('total_amount', formData.total_amount !== originalData.total_amount)}>
          <label htmlFor="total_amount">
            Total Amount
            {isLowConfidence('total_amount') && <span className="warning-badge">Low Confidence</span>}
          </label>
          <input
            type="number"
            id="total_amount"
            step="0.01"
            value={formData.total_amount || 0}
            onChange={(e) => handleFieldChange('total_amount', parseFloat(e.target.value))}
            placeholder="0.00"
          />
        </div>

        {formData.line_items && formData.line_items.length > 0 && (
          <div className="line-items-section">
            <h4>Line Items ({formData.line_items.length})</h4>
            <div className="line-items-table">
              <table>
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Qty</th>
                    <th>Unit Price</th>
                    <th>Amount</th>
                    <th>Cost Code</th>
                  </tr>
                </thead>
                <tbody>
                  {formData.line_items.map((item, index) => (
                    <tr key={item.id || index}>
                      <td>{item.description}</td>
                      <td>{item.quantity || '-'}</td>
                      <td>{item.unit_price ? `$${item.unit_price.toFixed(2)}` : '-'}</td>
                      <td>${item.amount.toFixed(2)}</td>
                      <td>
                        {item.suggested_code && (
                          <span className={item.confidence && item.confidence < 0.8 ? 'code-low-conf' : 'code-high-conf'}>
                            {item.suggested_code}
                            {item.confidence && ` (${(item.confidence * 100).toFixed(0)}%)`}
                          </span>
                        )}
                        {!item.suggested_code && '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <div className="form-footer">
        {saveMessage && (
          <div className={`save-message ${saveMessage.startsWith('❌') ? 'error' : 'success'}`}>
            {saveMessage}
          </div>
        )}
        <button
          onClick={handleSaveCorrections}
          disabled={!hasChanges() || isSaving}
          className="save-button"
        >
          {isSaving ? 'Saving...' : hasChanges() ? 'Save Corrections' : 'No Changes'}
        </button>
      </div>
    </div>
  );
};

