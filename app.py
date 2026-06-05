import os
import json
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Logging
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

file_handler = logging.FileHandler("pipeline_execution.log", mode="w", encoding="utf-8")
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)


# Business Logic
def process_sales_pipeline(json_filepath: str, output_dir: str = "invoices"):
    logging.info(f"Initializing processing pipeline for data source: {json_filepath}")
    
    try:
        with open(json_filepath, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        logging.critical(f"Pipeline execution aborted: File '{json_filepath}' not found.")
        return
    except json.JSONDecodeError:
        logging.critical(f"Pipeline execution aborted: File '{json_filepath}' contains invalid JSON syntax.")
        return

    orders = data.get("orders", [])
    if not orders:
        logging.warning("Input file parsing yielded empty or missing orders payload.")
        return

    os.makedirs(output_dir, exist_ok=True)

    for order in orders:
        order_id = order.get("order_id", "UNKNOWN_ID")
        logging.info(f"Processing Order Target Context: {order_id}")
        
        try:
            customer = order.get("customer", {})
            customer_name = customer.get("name")
            customer_email = customer.get("email")
            
            if not customer_name or not customer_email:
                logging.error(f"Rejecting Order {order_id}: Core identity properties (name/email) are missing.")
                continue

            line_items = order.get("line_items", [])
            calculated_subtotal = 0.0
            sanitized_items = []

            for item in line_items:
                description = item.get("description", "Generic Line Item")
                qty = item.get("quantity")
                unit_price = item.get("unit_price")

                if qty is None or unit_price is None or qty < 0 or unit_price < 0:
                    logging.warning(f"Order {order_id}: Filtering out corrupted line item metrics for '{description}'.")
                    continue

                item_total = qty * unit_price
                calculated_subtotal += item_total
                
                sanitized_items.append({
                    "item_id": item.get("item_id", "N/A"),
                    "description": description,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total": item_total
                })

            provided_total = order.get("total")
            if provided_total is None or abs(calculated_subtotal - provided_total) > 0.01:
                logging.error(
                    f"Order Reference Discrepancy Detected! [Order ID: {order_id}] "
                    f"Payload Total: {provided_total}, Recalculated Summation: {calculated_subtotal:.2f}. "
                    f"Overriding payload value with programmatic computation for security compliance."
                )

            discount_amount = 0.0
            if calculated_subtotal > 5000.0:
                discount_amount = calculated_subtotal * 0.10
                logging.info(f"Applied 10% Discount Tier for Order {order_id}: Saved ${discount_amount:.2f}")

            final_payable = calculated_subtotal - discount_amount

            target_invoice_path = os.path.join(output_dir, f"Invoice_{order_id}.pdf")
            build_pdf_invoice(
                filepath=target_invoice_path,
                order_id=order_id,
                customer=customer,
                items=sanitized_items,
                subtotal=calculated_subtotal,
                discount=discount_amount,
                final_total=final_payable
            )
            logging.info(f"Dispatched document generation successfully: {target_invoice_path}")

        except Exception as err:
            logging.error(f"Pipeline isolated a structural runtime processing failure on order {order_id}: {str(err)}")

# UI Generation Logic
def build_pdf_invoice(filepath, order_id, customer, items, subtotal, discount, final_total):
    doc = SimpleDocTemplate(
        filepath, 
        pagesize=letter, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    story = []
    base_styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor('#0F172A')    
    secondary_color = colors.HexColor('#2563EB')  
    text_dark = colors.HexColor('#334155')        
    bg_light = colors.HexColor('#F8FAFC')         
    border_color = colors.HexColor('#E2E8F0')     
    
    title_style = ParagraphStyle(
        'HeaderTitle', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=28, leading=32, textColor=colors.white
    )
    meta_label_style = ParagraphStyle(
        'MetaLabel', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#94A3B8'), alignment=2 # Right Aligned
    )
    meta_value_style = ParagraphStyle(
        'MetaValue', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=colors.white, alignment=2 # Right Aligned
    )
    section_title = ParagraphStyle(
        'SectionTitle', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=secondary_color, spaceAfter=4
    )
    body_style = ParagraphStyle(
        'BodyText', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=15, textColor=text_dark
    )
    th_style = ParagraphStyle(
        'TableHeaderText', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.white
    )
    th_style_right = ParagraphStyle(
        'TableHeaderTextRight', parent=th_style, alignment=2
    )
    td_style = ParagraphStyle(
        'TableCellText', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=13, textColor=text_dark
    )
    td_style_right = ParagraphStyle(
        'TableCellTextRight', parent=td_style, alignment=2
    )
    summary_label = ParagraphStyle(
        'SummaryLabel', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=14, textColor=text_dark, alignment=2
    )
    summary_value = ParagraphStyle(
        'SummaryValue', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=primary_color, alignment=2
    )

    header_left = [
        Paragraph("INVOICE", title_style),
        Spacer(1, 4),
        Paragraph("<font color='#2563EB'><b>ERP Pipeline Automation</b></font>", td_style)
    ]
    
    header_right = [
        Paragraph(f"<b>INVOICE NO:</b> INV-{order_id.split('-')[-1]}", meta_value_style),
        Paragraph(f"<b>ORDER REF:</b> {order_id}", meta_label_style),
        Paragraph("<b>DATE:</b> June 05, 2026", meta_label_style)
    ]
    
    header_matrix = [[header_left, header_right]]
    header_table = Table(header_matrix, colWidths=[270, 270])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 18),
        ('BOTTOMPADDING', (0,0), (-1,-1), 18),
        ('LEFTPADDING', (0,0), (0,0), 16),
        ('RIGHTPADDING', (1,0), (1,0), 16),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 24))

    customer_info_html = (
        f"<b>{customer.get('name')}</b><br/>"
        f"Attn: {customer.get('contact', 'N/A')}<br/>"
        f"Email: {customer.get('email')}<br/>"
        f"Address: {customer.get('address', 'N/A')}"
    )
    
    bill_to_matrix = [
        ["", Paragraph("BILL TO", section_title)],
        ["", Paragraph(customer_info_html, body_style)]
    ]

    bill_to_table = Table(bill_to_matrix, colWidths=[4, 536])
    bill_to_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), secondary_color), # Paints the elegant vertical blue strip accent
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (1,0), (1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(bill_to_table)
    story.append(Spacer(1, 24))


    grid_matrix = [[
        Paragraph("Item ID", th_style),
        Paragraph("Product Description", th_style),
        Paragraph("Qty", th_style_right),
        Paragraph("Unit Price", th_style_right),
        Paragraph("Amount", th_style_right)
    ]]
    
    # Loop and inject data records 
    for product in items:
        grid_matrix.append([
            Paragraph(product['item_id'], td_style),
            Paragraph(product['description'], td_style),
            Paragraph(str(product['quantity']), td_style_right),
            Paragraph(f"${product['unit_price']:.2f}", td_style_right),
            Paragraph(f"${product['total']:.2f}", td_style_right)
        ])
        
  
    grid_table = Table(grid_matrix, colWidths=[70, 230, 40, 100, 100])
    
    grid_styles = [
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]
    
    for i in range(1, len(grid_matrix)):
        if i % 2 == 0:
            grid_styles.append(('BACKGROUND', (0, i), (-1, i), bg_light))
        grid_styles.append(('LINEBELOW', (0, i), (-1, i), 0.5, border_color))
        
    grid_table.setStyle(TableStyle(grid_styles))
    story.append(grid_table)
    story.append(Spacer(1, 16))

    # Financial calculation
    summary_matrix = [
        [Paragraph("Gross Subtotal:", summary_label), Paragraph(f"${subtotal:.2f}", summary_value)]
    ]
    
    if discount > 0:
        summary_matrix.append([
            Paragraph("Contract Discount (10%):", summary_label), 
            Paragraph(f"-${discount:.2f}", ParagraphStyle('DiscVal', parent=summary_value, textColor=colors.HexColor('#DC2626')))
        ])
        
    summary_matrix.append([
        Paragraph("Net Total Payable:", ParagraphStyle('FinalLbl', parent=summary_label, fontName='Helvetica-Bold', fontSize=11)), 
        Paragraph(f"${final_total:.2f}", ParagraphStyle('FinalVal', parent=summary_value, fontSize=11, textColor=secondary_color))
    ])
    
    summary_table = Table(summary_matrix, colWidths=[140, 100])
    summary_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (1,0), (1,-1), 10),
        ('LINEABOVE', (0, -1), (1, -1), 1, primary_color), 
    ]))
    
    # Wrap in an outer wrapper block to align the summary flush right
    outer_wrapper = Table([["", summary_table]], colWidths=[300, 240])
    outer_wrapper.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(outer_wrapper)

    # Compile the final document output
    doc.build(story)


if __name__ == "__main__":
    TARGET_DATASET = "SalesOrders_data 1.json"
    process_sales_pipeline(json_filepath=TARGET_DATASET)