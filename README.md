# ERP Sales Order Processing Pipeline

A production-grade Python backend application that processes ERP sales orders from a JSON input structure, validates totals, handles data discrepancies gracefully, applies business discount rules, and generates clean, professional invoice PDFs.

## Features
- **Data Validation:** Recalculates line item totals (`quantity` × `unit_price`) to flag inconsistencies.
- **Discrepancy Auditing:** Logs mismatched order totals automatically without crashing the execution loop.
- **Tiered Discounts:** Applies a 10% corporate markdown for valid totals exceeding \$5,000.
- **Premium Document Layouts:** Generates structured, corporate-styled PDF invoices using `ReportLab`.
- **Dual-Handler Logging:** Streams events to the console terminal and logs them securely to a local file.

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install reportlab
