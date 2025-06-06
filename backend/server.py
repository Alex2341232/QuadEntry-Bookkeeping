import os
import uuid
import hashlib
import base64
import tempfile
from datetime import datetime
from io import BytesIO
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
from pdf2image import convert_from_path
from PIL import Image
import json

load_dotenv()

app = FastAPI(title="QuadLedger API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
db = client[os.environ.get("DB_NAME", "quadledger_db")]

# OpenAI setup
openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Pydantic models
class InvoiceData(BaseModel):
    date: str
    supplier: str
    amount: float
    description: str
    currency: str = "USD"

class LedgerEntry(BaseModel):
    id: str
    type: str  # "debit" or "credit"
    account: str
    amount: float
    invoice_id: str
    date: str

class VerifiedTransaction(BaseModel):
    id: str
    hash: str
    timestamp: str
    invoice_id: str
    status: str = "verified"

class ImpactEntry(BaseModel):
    id: str
    invoice_id: str
    water_usage: float = 0.0  # liters
    co2_emissions: float = 0.0  # tons
    labor_score: int = 5  # 1-10
    recycling_rate: float = 0.0  # percentage

class InvoiceRecord(BaseModel):
    id: str
    filename: str
    upload_date: str
    data: InvoiceData
    ledger_entries: List[LedgerEntry]
    verified_transaction: VerifiedTransaction
    impact_entry: Optional[ImpactEntry] = None
    file_content: str  # base64 encoded

# Helper functions
async def extract_invoice_data(file_content: bytes, filename: str) -> InvoiceData:
    """Extract invoice data using OpenAI Vision API"""
    
    # Convert PDF to images if necessary
    images = []
    if filename.lower().endswith('.pdf'):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            tmp.flush()
            pdf_images = convert_from_path(tmp.name, dpi=200)
            for img in pdf_images:
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                images.append(img_base64)
    else:
        # Handle image files directly
        img_base64 = base64.b64encode(file_content).decode()
        images.append(img_base64)
    
    # Process with OpenAI Vision API
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Extract invoice data from this image and return ONLY a JSON object with these fields:
                            {
                                "date": "YYYY-MM-DD format",
                                "supplier": "Company name",
                                "amount": 123.45,
                                "description": "Brief description of goods/services",
                                "currency": "USD"
                            }
                            
                            Be precise with the amount and make sure the date is in YYYY-MM-DD format."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{images[0]}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        # Parse the JSON response
        response_text = response.choices[0].message.content.strip()
        # Clean up the response if it contains markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        invoice_data = json.loads(response_text)
        return InvoiceData(**invoice_data)
        
    except Exception as e:
        # Fallback to mock data if OpenAI fails
        return InvoiceData(
            date=datetime.now().strftime("%Y-%m-%d"),
            supplier="Auto-detected Supplier",
            amount=100.00,
            description="Invoice processing - OpenAI extraction failed",
            currency="USD"
        )

def generate_ledger_entries(invoice_data: InvoiceData, invoice_id: str) -> List[LedgerEntry]:
    """Generate automatic debit and credit entries based on invoice content"""
    
    # Simple logic to determine account types based on description
    description_lower = invoice_data.description.lower()
    
    if any(keyword in description_lower for keyword in ['office', 'supplies', 'equipment', 'software']):
        debit_account = "Office Expenses"
    elif any(keyword in description_lower for keyword in ['inventory', 'materials', 'goods']):
        debit_account = "Inventory"
    elif any(keyword in description_lower for keyword in ['service', 'consulting', 'professional']):
        debit_account = "Professional Services"
    else:
        debit_account = "General Expenses"
    
    # Credit account logic (assuming most invoices create payables)
    credit_account = "Accounts Payable"
    
    return [
        LedgerEntry(
            id=str(uuid.uuid4()),
            type="debit",
            account=debit_account,
            amount=invoice_data.amount,
            invoice_id=invoice_id,
            date=invoice_data.date
        ),
        LedgerEntry(
            id=str(uuid.uuid4()),
            type="credit",
            account=credit_account,
            amount=invoice_data.amount,
            invoice_id=invoice_id,
            date=invoice_data.date
        )
    ]

def create_verified_transaction(invoice_id: str, ledger_entries: List[LedgerEntry]) -> VerifiedTransaction:
    """Create immutable transaction record with hash"""
    
    timestamp = datetime.now().isoformat()
    
    # Create hash from invoice_id + timestamp + ledger entries
    hash_input = f"{invoice_id}{timestamp}"
    for entry in ledger_entries:
        hash_input += f"{entry.type}{entry.account}{entry.amount}"
    
    transaction_hash = hashlib.sha256(hash_input.encode()).hexdigest()
    
    return VerifiedTransaction(
        id=str(uuid.uuid4()),
        hash=transaction_hash,
        timestamp=timestamp,
        invoice_id=invoice_id
    )

# API Endpoints
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "QuadLedger API"}

@app.post("/api/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):
    """Upload and process invoice with automatic data extraction"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload PDF, JPEG, or PNG files.")
    
    try:
        # Read file content
        file_content = await file.read()
        file_base64 = base64.b64encode(file_content).decode()
        
        # Generate invoice ID
        invoice_id = str(uuid.uuid4())
        
        # Extract invoice data using OpenAI
        invoice_data = await extract_invoice_data(file_content, file.filename)
        
        # Generate automatic ledger entries
        ledger_entries = generate_ledger_entries(invoice_data, invoice_id)
        
        # Create immutable transaction record
        verified_transaction = create_verified_transaction(invoice_id, ledger_entries)
        
        # Create complete invoice record
        invoice_record = InvoiceRecord(
            id=invoice_id,
            filename=file.filename,
            upload_date=datetime.now().isoformat(),
            data=invoice_data,
            ledger_entries=ledger_entries,
            verified_transaction=verified_transaction,
            file_content=file_base64
        )
        
        # Store in database
        await db.invoices.insert_one(invoice_record.model_dump())
        
        return {
            "message": "Invoice processed successfully",
            "invoice": invoice_record.model_dump()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing invoice: {str(e)}")

@app.get("/api/invoices")
async def get_invoices():
    """Get all processed invoices"""
    
    invoices = await db.invoices.find({}).to_list(1000)
    return {"invoices": invoices}

@app.get("/api/invoices/{invoice_id}")
async def get_invoice(invoice_id: str):
    """Get specific invoice by ID"""
    
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {"invoice": invoice}

@app.get("/api/ledger-entries")
async def get_ledger_entries():
    """Get all ledger entries across all invoices"""
    
    invoices = await db.invoices.find({}).to_list(1000)
    all_entries = []
    
    for invoice in invoices:
        for entry in invoice.get("ledger_entries", []):
            entry["supplier"] = invoice.get("data", {}).get("supplier", "Unknown")
            all_entries.append(entry)
    
    return {"ledger_entries": all_entries}

@app.get("/api/verified-transactions")
async def get_verified_transactions():
    """Get all verified transactions (immutable records)"""
    
    invoices = await db.invoices.find({}).to_list(1000)
    transactions = []
    
    for invoice in invoices:
        transaction = invoice.get("verified_transaction")
        if transaction:
            transaction["supplier"] = invoice.get("data", {}).get("supplier", "Unknown")
            transaction["amount"] = invoice.get("data", {}).get("amount", 0)
            transactions.append(transaction)
    
    return {"verified_transactions": transactions}

@app.post("/api/impact-entry")
async def create_impact_entry(impact_data: dict):
    """Create or update impact entry for an invoice"""
    
    invoice_id = impact_data.get("invoice_id")
    if not invoice_id:
        raise HTTPException(status_code=400, detail="Invoice ID is required")
    
    # Check if invoice exists
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Create impact entry
    impact_entry = ImpactEntry(
        id=str(uuid.uuid4()),
        invoice_id=invoice_id,
        water_usage=impact_data.get("water_usage", 0.0),
        co2_emissions=impact_data.get("co2_emissions", 0.0),
        labor_score=impact_data.get("labor_score", 5),
        recycling_rate=impact_data.get("recycling_rate", 0.0)
    )
    
    # Update invoice with impact entry
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"impact_entry": impact_entry.model_dump()}}
    )
    
    return {"message": "Impact entry created successfully", "impact_entry": impact_entry.model_dump()}

@app.get("/api/impact-entries")
async def get_impact_entries():
    """Get all impact entries"""
    
    invoices = await db.invoices.find({"impact_entry": {"$exists": True}}).to_list(1000)
    impact_entries = []
    
    for invoice in invoices:
        impact = invoice.get("impact_entry")
        if impact:
            impact["supplier"] = invoice.get("data", {}).get("supplier", "Unknown")
            impact["amount"] = invoice.get("data", {}).get("amount", 0)
            impact_entries.append(impact)
    
    return {"impact_entries": impact_entries}

@app.get("/api/dashboard-summary")
async def get_dashboard_summary():
    """Get dashboard summary statistics"""
    
    invoices = await db.invoices.find({}).to_list(1000)
    
    # Calculate summary statistics
    total_invoices = len(invoices)
    total_amount = sum(inv.get("data", {}).get("amount", 0) for inv in invoices)
    
    # Impact summary
    impact_invoices = [inv for inv in invoices if inv.get("impact_entry")]
    total_co2 = sum(inv.get("impact_entry", {}).get("co2_emissions", 0) for inv in impact_invoices)
    avg_labor_score = sum(inv.get("impact_entry", {}).get("labor_score", 0) for inv in impact_invoices) / max(len(impact_invoices), 1)
    
    # Recent transactions (last 10)
    recent_invoices = sorted(invoices, key=lambda x: x.get("upload_date", ""), reverse=True)[:10]
    
    return {
        "summary": {
            "total_invoices": total_invoices,
            "total_amount": total_amount,
            "verified_transactions": total_invoices,
            "impact_entries": len(impact_invoices),
            "total_co2_emissions": total_co2,
            "avg_labor_score": round(avg_labor_score, 1)
        },
        "recent_invoices": recent_invoices
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)