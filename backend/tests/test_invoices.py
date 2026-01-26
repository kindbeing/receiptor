import pytest
from uuid import uuid4
from datetime import date

from models import Invoice, ExtractedField, LineItem, VendorMatch, ProcessingMetric


@pytest.mark.asyncio
async def test_get_invoice_with_relationships(client, test_db):
    """
    Test GET /api/invoices/{invoice_id} returns invoice with all relationships.
    This test proves the MissingGreenlet bug exists and validates the fix.
    """
    # Setup: Create test data
    builder_id = uuid4()
    invoice = Invoice(
        filename="test_invoice.pdf",
        file_path="/uploads/test/test_invoice.pdf",
        builder_id=builder_id,
        status="extracted",
        processing_method="vision"
    )
    test_db.add(invoice)
    await test_db.flush()
    
    # Add extracted fields
    extracted_field = ExtractedField(
        invoice_id=invoice.id,
        vendor_name="Test Vendor Inc.",
        invoice_number="INV-12345",
        invoice_date=date(2026, 1, 15),
        total_amount=1500.00,
        confidence=0.95,
        raw_json={"test": "data"}
    )
    test_db.add(extracted_field)
    
    # Add line items
    line_item_1 = LineItem(
        invoice_id=invoice.id,
        description="Labor for installation",
        quantity=10,
        unit_price=100.00,
        amount=1000.00,
        suggested_code="LABOR-001",
        confidence=0.88
    )
    line_item_2 = LineItem(
        invoice_id=invoice.id,
        description="Materials",
        quantity=5,
        unit_price=100.00,
        amount=500.00,
        suggested_code="MAT-001",
        confidence=0.92
    )
    test_db.add(line_item_1)
    test_db.add(line_item_2)
    
    # Add processing metric
    metric = ProcessingMetric(
        invoice_id=invoice.id,
        method="vision",
        processing_time_ms=1500
    )
    test_db.add(metric)
    
    await test_db.commit()
    
    # Test: Call the endpoint
    response = await client.get(f"/api/invoices/{invoice.id}")
    
    # Assert: Verify response
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    
    # Verify basic invoice fields
    assert data["id"] == str(invoice.id)
    assert data["filename"] == "test_invoice.pdf"
    assert data["builder_id"] == str(builder_id)
    assert data["status"] == "extracted"
    assert data["processing_method"] == "vision"
    
    # Verify extracted_fields relationship is loaded
    assert len(data["extracted_fields"]) == 1
    assert data["extracted_fields"][0]["vendor_name"] == "Test Vendor Inc."
    assert data["extracted_fields"][0]["invoice_number"] == "INV-12345"
    assert data["extracted_fields"][0]["total_amount"] == 1500.00
    assert data["extracted_fields"][0]["confidence"] == 0.95
    
    # Verify line_items relationship is loaded
    assert len(data["line_items"]) == 2
    descriptions = [item["description"] for item in data["line_items"]]
    assert "Labor for installation" in descriptions
    assert "Materials" in descriptions
    
    # Verify processing_metrics relationship is loaded
    assert len(data["processing_metrics"]) == 1
    assert data["processing_metrics"][0]["method"] == "vision"
    assert data["processing_metrics"][0]["processing_time_ms"] == 1500
    
    # Verify vendor_matches relationship is loaded (empty in this case)
    assert isinstance(data["vendor_matches"], list)


@pytest.mark.asyncio
async def test_get_invoice_not_found(client, test_db):
    """Test GET /api/invoices/{invoice_id} returns 404 for non-existent invoice."""
    non_existent_id = uuid4()
    response = await client.get(f"/api/invoices/{non_existent_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_invoice_invalid_uuid(client, test_db):
    """Test GET /api/invoices/{invoice_id} returns 400 for invalid UUID."""
    response = await client.get("/api/invoices/invalid-uuid")
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()

