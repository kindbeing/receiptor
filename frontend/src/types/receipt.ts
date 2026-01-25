export interface Receipt {
  id: number;
  date: string;
  total: number;
  vendor: string;
  description: string | null;
}
