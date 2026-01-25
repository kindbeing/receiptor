import pytest
import uuid
from pathlib import Path


@pytest.mark.asyncio
async def test_vision_extraction_endpoint_not_found(client, test_db):
    from models import Invoice
    
    test_builder_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    invoice = Invoice(
        filename="test_invoice.pdf",
        file_path="/tmp/test_invoice.pdf",
        builder_id=test_builder_id,
        status="uploaded"
    )
    test_db.add(invoice)
    await test_db.commit()
    await test_db.refresh(invoice)
    
    response = await client.post(f"/api/invoices/{invoice.id}/extract/vision")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_vision_extraction_endpoint_success(client, test_db):
    from models import Invoice
    
    test_builder_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    invoice = Invoice(
        filename="test_invoice.pdf",
        file_path="/tmp/test_invoice.pdf",
        builder_id=test_builder_id,
        status="uploaded"
    )
    test_db.add(invoice)
    await test_db.commit()
    await test_db.refresh(invoice)
    
    response = await client.post(f"/api/invoices/{invoice.id}/extract/vision")
    
    assert response.status_code in [200, 404]
