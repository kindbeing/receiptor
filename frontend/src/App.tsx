import { useState } from 'react'
import ReceiptsTable from './components/ReceiptsTable'
import InvoiceUploadForm from './components/InvoiceUploadForm'
import { TraditionalOCRProcessor } from './components/TraditionalOCRProcessor'
import { VisionAIProcessor } from './components/VisionAIProcessor'
import { VendorMatcher } from './components/VendorMatcher'
import { CostCodeClassifier } from './components/CostCodeClassifier'
import { ComparisonDashboard } from './components/ComparisonDashboard'
import type { Invoice, ExtractionResult } from './types/invoice'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState<'receipts' | 'invoices'>('invoices')
  const [uploadedInvoices, setUploadedInvoices] = useState<Invoice[]>([])
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null)

  const handleUploadSuccess = (invoice: Invoice) => {
    setUploadedInvoices(prev => [invoice, ...prev])
    // Auto-select the newly uploaded invoice for processing
    setSelectedInvoiceId(invoice.id)
  }

  const handleExtractionComplete = (result: ExtractionResult) => {
    console.log('Extraction complete:', result)
    // Update invoice status in the list
    setUploadedInvoices(prev => 
      prev.map(inv => 
        inv.id === result.invoice_id 
          ? { ...inv, status: 'extracted', processing_method: result.processing_method }
          : inv
      )
    )
  }

  const handleMatchComplete = () => {
    // Refresh invoice list to show updated status
    console.log('Vendor matching complete')
    // Update invoice status in the list
    if (selectedInvoiceId) {
      setUploadedInvoices(prev => 
        prev.map(inv => 
          inv.id === selectedInvoiceId 
            ? { ...inv, status: 'matched' }
            : inv
        )
      )
    }
  }

  const handleClassificationComplete = () => {
    // Refresh invoice list to show updated status
    console.log('Cost code classification complete')
    if (selectedInvoiceId) {
      setUploadedInvoices(prev => 
        prev.map(inv => 
          inv.id === selectedInvoiceId 
            ? { ...inv, status: 'classified' }
            : inv
        )
      )
    }
  }

  // Check if selected invoice has been extracted
  const selectedInvoice = uploadedInvoices.find(inv => inv.id === selectedInvoiceId)
  const showVendorMatcher = selectedInvoice && 
    ['extracted', 'matched', 'classified', 'needs_review'].includes(selectedInvoice.status)
  const showCostCodeClassifier = selectedInvoice && 
    ['extracted', 'matched', 'classified', 'needs_review'].includes(selectedInvoice.status)

  return (
    <div className="app">
      <header className="app-header">
        <h1>🧾 Invoice Automation System</h1>
        <nav className="tab-nav">
          <button 
            className={`tab-btn ${activeTab === 'invoices' ? 'active' : ''}`}
            onClick={() => setActiveTab('invoices')}
          >
            📄 Invoices
          </button>
          <button 
            className={`tab-btn ${activeTab === 'receipts' ? 'active' : ''}`}
            onClick={() => setActiveTab('receipts')}
          >
            🧾 Receipts (Legacy)
          </button>
        </nav>
      </header>

      <main className="app-main">
        {activeTab === 'invoices' && (
          <div className="invoices-container">
            <div className="invoices-left">
              <InvoiceUploadForm onUploadSuccess={handleUploadSuccess} />
              
              {uploadedInvoices.length > 0 && (
                <div className="uploaded-invoices">
                  <h3>Recently Uploaded ({uploadedInvoices.length})</h3>
                  <ul className="invoice-list">
                    {uploadedInvoices.map(invoice => (
                      <li 
                        key={invoice.id} 
                        className={`invoice-item ${selectedInvoiceId === invoice.id ? 'selected' : ''}`}
                        onClick={() => setSelectedInvoiceId(invoice.id)}
                      >
                        <span className="invoice-filename">{invoice.filename}</span>
                        <span className={`invoice-status status-${invoice.status}`}>
                          {invoice.status}
                        </span>
                        <span className="invoice-time">
                          {new Date(invoice.uploaded_at).toLocaleTimeString()}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="invoices-right">
              {selectedInvoiceId ? (
                <>
                  <div className="processors-grid">
                    <TraditionalOCRProcessor 
                      invoiceId={selectedInvoiceId}
                      onExtractionComplete={handleExtractionComplete}
                    />
                    <VisionAIProcessor 
                      invoiceId={selectedInvoiceId}
                      onExtractionComplete={handleExtractionComplete}
                    />
                  </div>
                  
                  {showVendorMatcher && (
                    <VendorMatcher 
                      invoiceId={selectedInvoiceId}
                      onMatchComplete={handleMatchComplete}
                    />
                  )}
                  
                  {showCostCodeClassifier && (
                    <CostCodeClassifier 
                      invoice={selectedInvoice}
                      onClassificationComplete={handleClassificationComplete}
                    />
                  )}
                  
                  <ComparisonDashboard invoice={selectedInvoice || null} />
                </>
              ) : (
                <div className="no-selection">
                  <p>👈 Upload an invoice or select one from the list to process</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'receipts' && (
          <ReceiptsTable />
        )}
      </main>
    </div>
  )
}

export default App
