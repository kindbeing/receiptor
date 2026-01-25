import { useState } from 'react'
import ReceiptsTable from './components/ReceiptsTable'
import InvoiceUploadForm from './components/InvoiceUploadForm'
import type { Invoice } from './types/invoice'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState<'receipts' | 'invoices'>('invoices')
  const [uploadedInvoices, setUploadedInvoices] = useState<Invoice[]>([])

  const handleUploadSuccess = (invoice: Invoice) => {
    setUploadedInvoices(prev => [invoice, ...prev])
  }

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
          <div>
            <InvoiceUploadForm onUploadSuccess={handleUploadSuccess} />
            
            {uploadedInvoices.length > 0 && (
              <div className="uploaded-invoices">
                <h3>Recently Uploaded ({uploadedInvoices.length})</h3>
                <ul className="invoice-list">
                  {uploadedInvoices.map(invoice => (
                    <li key={invoice.id} className="invoice-item">
                      <span className="invoice-filename">{invoice.filename}</span>
                      <span className="invoice-status">{invoice.status}</span>
                      <span className="invoice-time">
                        {new Date(invoice.uploaded_at).toLocaleTimeString()}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
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
