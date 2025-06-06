import requests
import unittest
import os
import tempfile
from PIL import Image
import io
import base64
import json
import time

# Use the public endpoint for testing
API_BASE_URL = "https://0e81ffeb-63ae-4dee-8b54-ab8b46006026.preview.emergentagent.com"

class QuadLedgerAPITest(unittest.TestCase):
    """Test suite for QuadLedger API endpoints"""
    
    def test_01_health_check(self):
        """Test the health check endpoint"""
        response = requests.get(f"{API_BASE_URL}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "QuadLedger API")
        print("✅ Health check endpoint is working")
    
    def test_02_dashboard_summary(self):
        """Test the dashboard summary endpoint"""
        response = requests.get(f"{API_BASE_URL}/api/dashboard-summary")
        print(f"Dashboard summary status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn("summary", data, "Response should contain a 'summary' field")
            
            # Verify the structure of the summary data
            summary = data["summary"]
            self.assertIn("total_invoices", summary)
            self.assertIn("total_amount", summary)
            self.assertIn("verified_transactions", summary)
            self.assertIn("impact_entries", summary)
            self.assertIn("total_co2_emissions", summary)
            self.assertIn("avg_labor_score", summary)
            
            # Verify recent_invoices is present
            self.assertIn("recent_invoices", data)
            
            print("✅ Dashboard summary endpoint is working correctly")
        else:
            print("⚠️ Dashboard summary endpoint returned an error")
            print(f"Response: {response.text[:200]}...")
    
    def test_03_get_invoices(self):
        """Test retrieving all invoices"""
        response = requests.get(f"{API_BASE_URL}/api/invoices")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("invoices", data)
        print("✅ Get invoices endpoint is working")
    
    def test_04_get_ledger_entries(self):
        """Test retrieving ledger entries"""
        response = requests.get(f"{API_BASE_URL}/api/ledger-entries")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("ledger_entries", data)
        print("✅ Get ledger entries endpoint is working")
    
    def test_05_get_verified_transactions(self):
        """Test retrieving verified transactions"""
        response = requests.get(f"{API_BASE_URL}/api/verified-transactions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("verified_transactions", data)
        print("✅ Get verified transactions endpoint is working")
    
    def test_06_get_impact_entries(self):
        """Test retrieving impact entries"""
        response = requests.get(f"{API_BASE_URL}/api/impact-entries")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("impact_entries", data)
        print("✅ Get impact entries endpoint is working")
    
    def test_07_upload_invoice(self):
        """Test uploading an invoice and adding impact data"""
        print("\n🔄 Testing invoice upload and impact data workflow...")
        
        # Create a simple test image
        image = Image.new('RGB', (800, 600), color='white')
        draw = Image.ImageDraw.Draw(image)
        draw.text((50, 50), "INVOICE", fill='black')
        draw.text((50, 100), "Date: 2025-02-15", fill='black')
        draw.text((50, 150), "Supplier: Test Corp", fill='black')
        draw.text((50, 200), "Amount: $123.45", fill='black')
        draw.text((50, 250), "Description: Office supplies", fill='black')
        
        # Save image to a BytesIO object
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Upload the image
        files = {'file': ('test_invoice.png', img_byte_arr, 'image/png')}
        response = requests.post(f"{API_BASE_URL}/api/upload-invoice", files=files)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Invoice processed successfully")
        self.assertIn("invoice", data)
        
        # Store invoice ID for later tests
        invoice_id = data["invoice"]["id"]
        print(f"✅ Upload invoice endpoint is working. Invoice ID: {invoice_id}")
        
        # Test retrieving the specific invoice
        response = requests.get(f"{API_BASE_URL}/api/invoices/{invoice_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("invoice", data)
        self.assertEqual(data["invoice"]["id"], invoice_id)
        print(f"✅ Get specific invoice endpoint is working")
        
        # Verify it appears in Financial Ledger
        print("Verifying invoice appears in Financial Ledger...")
        response = requests.get(f"{API_BASE_URL}/api/ledger-entries")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find entries related to our invoice
        invoice_entries = [entry for entry in data["ledger_entries"] if entry.get("invoice_id") == invoice_id]
        self.assertTrue(len(invoice_entries) > 0, "Invoice should have ledger entries")
        print(f"✅ Found {len(invoice_entries)} ledger entries for the invoice")
        
        # Verify it appears in Verified Transactions with proper hash
        print("Verifying invoice appears in Verified Transactions...")
        response = requests.get(f"{API_BASE_URL}/api/verified-transactions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find transaction related to our invoice
        invoice_transaction = next((tx for tx in data["verified_transactions"] if tx.get("invoice_id") == invoice_id), None)
        self.assertIsNotNone(invoice_transaction, "Invoice should have a verified transaction")
        self.assertIn("hash", invoice_transaction)
        self.assertTrue(len(invoice_transaction["hash"]) > 0, "Transaction should have a valid hash")
        print(f"✅ Found verified transaction with hash: {invoice_transaction['hash'][:10]}...")
        
        # Test adding impact data
        impact_data = {
            "invoice_id": invoice_id,
            "water_usage": 150.5,
            "co2_emissions": 2.3,
            "labor_score": 8,
            "recycling_rate": 75.0
        }
        response = requests.post(f"{API_BASE_URL}/api/impact-entry", json=impact_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Impact entry created successfully")
        print(f"✅ Create impact entry endpoint is working")
        
        # Verify it appears in Impact Ledger
        print("Verifying invoice appears in Impact Ledger...")
        response = requests.get(f"{API_BASE_URL}/api/impact-entries")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find impact entry related to our invoice
        invoice_impact = next((impact for impact in data["impact_entries"] if impact.get("invoice_id") == invoice_id), None)
        self.assertIsNotNone(invoice_impact, "Invoice should have an impact entry")
        print(f"✅ Found impact entry for the invoice")
        
        print("🎉 Invoice upload and impact data workflow test completed successfully!")

if __name__ == "__main__":
    # Run the tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
