import requests
import unittest
import os
from PIL import Image
import io

# Use the public endpoint for testing
API_BASE_URL = "https://0e81ffeb-63ae-4dee-8b54-ab8b46006026.preview.emergentagent.com"

def test_upload_invoice():
    """Test uploading an invoice"""
    print("Creating test image...")
    # Create a simple test image
    image = Image.new('RGB', (400, 300), color='white')
    draw = Image.ImageDraw.Draw(image)
    draw.text((10, 10), "Test Invoice\nDate: 2025-02-15\nSupplier: Test Corp\nAmount: $123.45", fill='black')
    
    # Save image to a BytesIO object
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # Upload the image
    print("Uploading image...")
    files = {'file': ('test_invoice.png', img_byte_arr, 'image/png')}
    response = requests.post(f"{API_BASE_URL}/api/upload-invoice", files=files)
    
    # Check response
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response data: {data.get('message')}")
        if 'invoice' in data:
            invoice_id = data["invoice"]["id"]
            print(f"Invoice ID: {invoice_id}")
            return invoice_id
    else:
        print(f"Error response: {response.text[:200]}")
    return None

def test_add_impact_data(invoice_id):
    """Test adding impact data"""
    if not invoice_id:
        print("No invoice ID provided, skipping impact data test")
        return False
    
    print(f"Adding impact data for invoice {invoice_id}...")
    impact_data = {
        "invoice_id": invoice_id,
        "water_usage": 150.5,
        "co2_emissions": 2.3,
        "labor_score": 8,
        "recycling_rate": 75.0
    }
    response = requests.post(f"{API_BASE_URL}/api/impact-entry", json=impact_data)
    
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response data: {data.get('message')}")
        return True
    else:
        print(f"Error response: {response.text[:200]}")
    return False

def test_dashboard_summary():
    """Test the dashboard summary endpoint"""
    print("Testing dashboard summary...")
    response = requests.get(f"{API_BASE_URL}/api/dashboard-summary")
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if "summary" in data:
            summary = data["summary"]
            print(f"Total invoices: {summary.get('total_invoices')}")
            print(f"Total amount: {summary.get('total_amount')}")
            print(f"Verified transactions: {summary.get('verified_transactions')}")
            print(f"Impact entries: {summary.get('impact_entries')}")
            return True
    else:
        print(f"Error response: {response.text[:200]}")
    return False

if __name__ == "__main__":
    print("=== Testing QuadLedger API ===")
    
    # Test dashboard summary
    test_dashboard_summary()
    
    # Test upload invoice
    invoice_id = test_upload_invoice()
    
    # Test add impact data
    if invoice_id:
        test_add_impact_data(invoice_id)
        
        # Test dashboard summary again to see if it's updated
        print("\nTesting dashboard summary after adding data...")
        test_dashboard_summary()
    
    print("=== Testing completed ===")
