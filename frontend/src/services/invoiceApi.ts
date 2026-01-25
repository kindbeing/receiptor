// Invoice API Service
import type { Invoice, InvoiceDetail, ExtractionResult, VendorMatchResult } from '../types/invoice';

const API_BASE_URL = 'http://localhost:8000/api/invoices';

export const invoiceApi = {
  /**
   * Upload an invoice file
   */
  async uploadInvoice(file: File, builderId: string): Promise<Invoice> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('builder_id', builderId);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload invoice');
    }

    return response.json();
  },

  /**
   * Get invoice by ID
   */
  async getInvoice(invoiceId: string): Promise<InvoiceDetail> {
    const response = await fetch(`${API_BASE_URL}/${invoiceId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch invoice');
    }

    return response.json();
  },

  /**
   * List invoices with optional filters
   */
  async listInvoices(params?: {
    builderId?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<Invoice[]> {
    const queryParams = new URLSearchParams();
    
    if (params?.builderId) queryParams.append('builder_id', params.builderId);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());

    const url = queryParams.toString() 
      ? `${API_BASE_URL}?${queryParams.toString()}`
      : API_BASE_URL;

    const response = await fetch(url);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch invoices');
    }

    return response.json();
  },

  /**
   * Delete invoice
   */
  async deleteInvoice(invoiceId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/${invoiceId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete invoice');
    }
  },

  /**
   * Extract invoice data using Traditional OCR
   */
  async extractTraditional(invoiceId: string): Promise<ExtractionResult> {
    const response = await fetch(`${API_BASE_URL}/${invoiceId}/extract/traditional`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to extract invoice with Traditional OCR');
    }

    return response.json();
  },

  /**
   * Extract invoice data using Vision AI
   */
  async extractVision(invoiceId: string): Promise<ExtractionResult> {
    const response = await fetch(`${API_BASE_URL}/${invoiceId}/extract/vision`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to extract invoice with Vision AI');
    }

    return response.json();
  },

  /**
   * Match extracted vendor to known subcontractors
   */
  async matchVendor(invoiceId: string): Promise<VendorMatchResult> {
    const response = await fetch(`${API_BASE_URL}/${invoiceId}/match-vendor`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to match vendor');
    }

    return response.json();
  },

  /**
   * Classify line items to cost codes using semantic similarity
   */
  async classifyCosts(invoiceId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/${invoiceId}/classify-costs`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to classify costs');
    }

    return response.json();
  },

  /**
   * Get comparison of Traditional OCR vs Vision AI extraction results
   */
  async getComparison(invoiceId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/${invoiceId}/comparison`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get comparison');
    }

    return response.json();
  },
};

export const { uploadInvoice, getInvoice, listInvoices, deleteInvoice, extractTraditional, extractVision, matchVendor, classifyCosts, getComparison } = invoiceApi;

