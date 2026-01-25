import os
import uuid
from pathlib import Path
from typing import BinaryIO
from fastapi import UploadFile
import shutil

class InvoiceStorageService:
    """Handles file storage for uploaded invoices"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_invoice(self, file: UploadFile, invoice_id: uuid.UUID) -> str:
        """
        Save uploaded invoice file to disk.
        
        Args:
            file: The uploaded file from FastAPI
            invoice_id: UUID of the invoice record
        
        Returns:
            str: Relative file path where the file was saved
        """
        # Create directory for this invoice
        invoice_dir = self.upload_dir / str(invoice_id)
        invoice_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine file extension
        file_ext = self._get_file_extension(file.filename or "unknown.pdf")
        
        # Save file
        file_path = invoice_dir / f"original{file_ext}"
        
        # Write file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return relative path
        return str(file_path)
    
    def get_invoice_path(self, invoice_id: uuid.UUID) -> Path:
        """Get the directory path for an invoice"""
        return self.upload_dir / str(invoice_id)
    
    def get_original_file_path(self, invoice_id: uuid.UUID) -> Path:
        """Get the path to the original uploaded file"""
        invoice_dir = self.get_invoice_path(invoice_id)
        
        # Try common extensions
        for ext in ['.pdf', '.jpg', '.jpeg', '.png']:
            file_path = invoice_dir / f"original{ext}"
            if file_path.exists():
                return file_path
        
        raise FileNotFoundError(f"Original file not found for invoice {invoice_id}")
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        _, ext = os.path.splitext(filename)
        return ext.lower() if ext else '.pdf'
    
    def delete_invoice_files(self, invoice_id: uuid.UUID) -> None:
        """Delete all files associated with an invoice"""
        invoice_dir = self.get_invoice_path(invoice_id)
        if invoice_dir.exists():
            shutil.rmtree(invoice_dir)


# Singleton instance
storage_service = InvoiceStorageService()

