import axios from 'axios';
import type { Receipt } from '../types/receipt';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const receiptsApi = {
  getAll: async (): Promise<Receipt[]> => {
    const response = await api.get<Receipt[]>('/receipts/');
    return response.data;
  },

  getById: async (id: number): Promise<Receipt> => {
    const response = await api.get<Receipt>(`/receipts/${id}`);
    return response.data;
  },

  create: async (receipt: Omit<Receipt, 'id' | 'date'>): Promise<Receipt> => {
    const response = await api.post<Receipt>('/receipts/', receipt);
    return response.data;
  },

  update: async (id: number, receipt: Partial<Omit<Receipt, 'id' | 'date'>>): Promise<Receipt> => {
    const response = await api.put<Receipt>(`/receipts/${id}`, receipt);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/receipts/${id}`);
  },
};
