# ERP Sales Order Processing Pipeline

A production-grade Python backend application that processes ERP sales orders from a JSON input structure, validates totals, handles data discrepancies gracefully, applies business discount rules, and generates clean, professional invoice PDFs.

## Features
- [cite_start]**Data Validation:** Recalculates line item totals (`quantity` × `unit_price`) to flag inconsistencies[cite: 4, 5, 6].
- [cite_start]**Discrepancy Auditing:** Logs mismatched order totals automatically without crashing the execution loop[cite: 6, 10].
- [cite_start]**Tiered Discounts:** Applies a 10% corporate markdown for valid totals exceeding \$5,000[cite: 7].
- [cite_start]**Premium Document Layouts:** Generates structured, corporate-styled PDF invoices using `ReportLab`[cite: 8, 12].
- **Dual-Handler Logging:** Streams events to the console terminal and logs them securely to a local file.

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install reportlab