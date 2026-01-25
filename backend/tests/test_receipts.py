import pytest
import pytest_asyncio

@pytest.mark.asyncio
async def test_read_receipts(client):
    response = await client.get("/receipts/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_receipt(client):
    response = await client.post("/receipts/", json={"total": 10.0, "vendor": "Test Vendor", "description": "Test receipt"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 10.0
    assert data["vendor"] == "Test Vendor"
    assert "id" in data
    receipt_id = data["id"]

    response = await client.get(f"/receipts/{receipt_id}")
    assert response.status_code == 200
    assert response.json()["id"] == receipt_id

    response = await client.put(f"/receipts/{receipt_id}", json={"total": 20.0})
    assert response.status_code == 200
    assert response.json()["total"] == 20.0

    response = await client.delete(f"/receipts/{receipt_id}")
    assert response.status_code == 200

    response = await client.get(f"/receipts/{receipt_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_read_receipt_not_found(client):
    response = await client.get("/receipts/999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_receipt_not_found(client):
    response = await client.put("/receipts/999", json={"total": 15.0})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_receipt_not_found(client):
    response = await client.delete("/receipts/999")
    assert response.status_code == 404
