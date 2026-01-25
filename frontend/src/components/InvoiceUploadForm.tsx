import { useState, useCallback } from 'react';
import { invoiceApi } from '../services/invoiceApi';
import type { Invoice } from '../types/invoice';
import './InvoiceUploadForm.css';

interface InvoiceUploadFormProps {
  builderId?: string;
  onUploadSuccess?: (invoice: Invoice) => void;
}

export default function InvoiceUploadForm({ 
  builderId = '00000000-0000-0000-0000-000000000001',
  onUploadSuccess 
}: InvoiceUploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedInvoice, setUploadedInvoice] = useState<Invoice | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  }, []);

  const validateAndSetFile = (selectedFile: File) => {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    
    if (!allowedTypes.includes(selectedFile.type)) {
      setError('Invalid file type. Please upload PDF, JPG, or PNG files only.');
      setFile(null);
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) { // 10MB limit
      setError('File too large. Maximum size is 10MB.');
      setFile(null);
      return;
    }

    setError(null);
    setFile(selectedFile);
    setUploadedInvoice(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const invoice = await invoiceApi.uploadInvoice(file, builderId);
      setUploadedInvoice(invoice);
      setFile(null);
      
      if (onUploadSuccess) {
        onUploadSuccess(invoice);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadedInvoice(null);
    setError(null);
  };

  return (
    <div className="invoice-upload-form">
      <h2>📄 Upload Invoice</h2>
      
      {!uploadedInvoice ? (
        <>
          <div 
            className={`dropzone ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="dropzone-content">
              <svg className="upload-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              
              <p className="dropzone-text">
                {file ? file.name : 'Drag & drop invoice here'}
              </p>
              <p className="dropzone-subtext">
                or click to browse
              </p>
              <p className="dropzone-hint">
                PDF, JPG, PNG (max 10MB)
              </p>
              
              <input 
                type="file" 
                accept="application/pdf,image/jpeg,image/jpg,image/png"
                onChange={handleFileInput}
                className="file-input"
              />
            </div>
          </div>

          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}

          {file && !error && (
            <div className="file-info">
              <p><strong>Selected:</strong> {file.name}</p>
              <p><strong>Size:</strong> {(file.size / 1024).toFixed(2)} KB</p>
              <p><strong>Type:</strong> {file.type}</p>
            </div>
          )}

          <div className="button-group">
            <button 
              onClick={handleUpload}
              disabled={!file || isUploading}
              className="btn btn-primary"
            >
              {isUploading ? '⏳ Uploading...' : '📤 Upload Invoice'}
            </button>
            
            {file && (
              <button 
                onClick={handleReset}
                disabled={isUploading}
                className="btn btn-secondary"
              >
                ❌ Clear
              </button>
            )}
          </div>
        </>
      ) : (
        <div className="success-message">
          <div className="success-icon">✅</div>
          <h3>Upload Successful!</h3>
          <div className="invoice-details">
            <p><strong>Invoice ID:</strong> <code>{uploadedInvoice.id}</code></p>
            <p><strong>Filename:</strong> {uploadedInvoice.filename}</p>
            <p><strong>Status:</strong> <span className="status-badge">{uploadedInvoice.status}</span></p>
            <p><strong>Uploaded:</strong> {new Date(uploadedInvoice.uploaded_at).toLocaleString()}</p>
          </div>
          
          <button onClick={handleReset} className="btn btn-primary">
            📄 Upload Another Invoice
          </button>
        </div>
      )}
    </div>
  );
}

