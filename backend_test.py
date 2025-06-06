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
        self.assertEqual(response.status_code, 200, "Dashboard summary endpoint should return 200 OK")
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
    
    def test_07_end_to_end_workflow(self):
        """Test the complete end-to-end workflow"""
        print("\n🔄 Testing complete end-to-end workflow...")
        
        # Step 1: Create a test invoice image
        print("Step 1: Creating test invoice image...")
        image = Image.new('RGB', (800, 600), color='white')
        draw = Image.ImageDraw.Draw(image)
        draw.text((50, 50), "INVOICE", fill='black')
        draw.text((50, 100), "Date: 2025-02-15", fill='black')
        draw.text((50, 150), "Supplier: Eco Friendly Supplies Inc.", fill='black')
        draw.text((50, 200), "Amount: $456.78", fill='black')
        draw.text((50, 250), "Description: Office supplies and recycled paper", fill='black')
        draw.text((50, 300), "Currency: USD", fill='black')
        
        # Save image to a BytesIO object
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Step 2: Upload the invoice
        print("Step 2: Uploading invoice...")
        files = {'file': ('e2e_test_invoice.png', img_byte_arr, 'image/png')}
        response = requests.post(f"{API_BASE_URL}/api/upload-invoice", files=files)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Invoice processed successfully")
        self.assertIn("invoice", data)
        
        # Store invoice ID for later steps
        invoice_id = data["invoice"]["id"]
        print(f"✅ Invoice uploaded successfully. Invoice ID: {invoice_id}")
        
        # Step 3: Verify it appears in Financial Ledger
        print("Step 3: Verifying invoice appears in Financial Ledger...")
        response = requests.get(f"{API_BASE_URL}/api/ledger-entries")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find entries related to our invoice
        invoice_entries = [entry for entry in data["ledger_entries"] if entry.get("invoice_id") == invoice_id]
        self.assertTrue(len(invoice_entries) > 0, "Invoice should have ledger entries")
        print(f"✅ Found {len(invoice_entries)} ledger entries for the invoice")
        
        # Step 4: Verify it appears in Verified Transactions with proper hash
        print("Step 4: Verifying invoice appears in Verified Transactions...")
        response = requests.get(f"{API_BASE_URL}/api/verified-transactions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find transaction related to our invoice
        invoice_transaction = next((tx for tx in data["verified_transactions"] if tx.get("invoice_id") == invoice_id), None)
        self.assertIsNotNone(invoice_transaction, "Invoice should have a verified transaction")
        self.assertIn("hash", invoice_transaction)
        self.assertTrue(len(invoice_transaction["hash"]) > 0, "Transaction should have a valid hash")
        print(f"✅ Found verified transaction with hash: {invoice_transaction['hash'][:10]}...")
        
        # Step 5: Add impact data for the invoice
        print("Step 5: Adding impact data for the invoice...")
        impact_data = {
            "invoice_id": invoice_id,
            "water_usage": 250.5,
            "co2_emissions": 3.7,
            "labor_score": 9,
            "recycling_rate": 85.0
        }
        response = requests.post(f"{API_BASE_URL}/api/impact-entry", json=impact_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Impact entry created successfully")
        print(f"✅ Impact data added successfully")
        
        # Step 6: Verify it appears in Impact Ledger
        print("Step 6: Verifying invoice appears in Impact Ledger...")
        response = requests.get(f"{API_BASE_URL}/api/impact-entries")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find impact entry related to our invoice
        invoice_impact = next((impact for impact in data["impact_entries"] if impact.get("invoice_id") == invoice_id), None)
        self.assertIsNotNone(invoice_impact, "Invoice should have an impact entry")
        self.assertEqual(invoice_impact["water_usage"], impact_data["water_usage"])
        self.assertEqual(invoice_impact["co2_emissions"], impact_data["co2_emissions"])
        self.assertEqual(invoice_impact["labor_score"], impact_data["labor_score"])
        self.assertEqual(invoice_impact["recycling_rate"], impact_data["recycling_rate"])
        print(f"✅ Found impact entry for the invoice")
        
        # Step 7: Verify dashboard summary is updated
        print("Step 7: Verifying dashboard summary is updated...")
        response = requests.get(f"{API_BASE_URL}/api/dashboard-summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check if our invoice is in recent invoices
        recent_invoice_ids = [inv.get("id") for inv in data["recent_invoices"]]
        self.assertIn(invoice_id, recent_invoice_ids, "Uploaded invoice should appear in recent invoices")
        
        # Verify summary statistics
        summary = data["summary"]
        self.assertTrue(summary["total_invoices"] > 0, "Total invoices should be greater than 0")
        self.assertTrue(summary["total_amount"] > 0, "Total amount should be greater than 0")
        self.assertTrue(summary["verified_transactions"] > 0, "Verified transactions should be greater than 0")
        self.assertTrue(summary["impact_entries"] > 0, "Impact entries should be greater than 0")
        
        print("✅ Dashboard summary is updated with the new invoice data")
        print("\n🎉 End-to-end workflow test completed successfully!")

if __name__ == "__main__":
    # Run the tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
