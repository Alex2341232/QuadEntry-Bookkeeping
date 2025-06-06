# QuadLedger – Sustainability-Integrated Accounting App

**QuadLedger** is a prototype web application developed as part of a master's dissertation on the future of accounting. The app brings to life a new conceptual model called **Quad-Entry Bookkeeping**, which introduces a fourth ledger entry to account for the **environmental and social impact** of financial transactions.

## Academic Context

This application is part of the practical contribution to the dissertation:

> **Title:** Rethinking Accounting: The Emergence of Quad-Entry Bookkeeping  
> **Author:** Alexandru Gradinaru
> **Institution:** Bucharest University of Economic Studies (ASE)  
> **Year:** 2025

---

## What It Does

- **Invoice Upload**  
  Upload a PDF or image of a financial invoice.

- **AI-Powered Parsing**  
  The system extracts key data using OpenAI (e.g., supplier, date, amount).

 - **Auto-Generated Ledger Entries**  
  Based on the invoice, the app deduces the Debit and Credit entries.

-  **Immutable Transaction Record**  
  Each invoice is time-stamped and stored in a tamper-proof (simulated blockchain) ledger.

-  **Impact Ledger (Fourth Entry)**  
  Users input ESG data:
  - CO₂ emissions  
  - Water usage  
  - Labor compliance  
  - Waste recycling

-  **Dashboard**  
  See recent entries, download reports, and analyze sustainability impact.

---

##  Why It Matters

QuadLedger demonstrates that accounting can go beyond profit by embedding **transparency, ethics, and sustainability** into core financial systems. It blends AI, blockchain principles, and ESG reporting into a cohesive workflow.

---

## 🔧 Tech Stack

- `Frontend`: React (via Emergent.sh)  
- `Backend`: Python (AI-powered invoice parsing)  
- `AI Integration`: OpenAI API  
- `Data Storage`: Simulated write-once (immutable) database

---

## 🚀 Getting Started

> 📌 This is a prototype. For academic review or demonstration only.
