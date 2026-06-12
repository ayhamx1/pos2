import os
import subprocess
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
import arabic_reshaper
from bidi.algorithm import get_display


def arabic(text):
    """تحويل النص العربي ليظهر صح في PDF"""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)


def generate_receipt(sale_id, items, total, payment_details, cashier_name="", invoice_barcode="", invoice_type="sale"):

    # مسار حفظ الفاتورة
    receipts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "receipts")
    os.makedirs(receipts_dir, exist_ok=True)
    file_path = os.path.join(receipts_dir, f"receipt_{sale_id}.pdf")

    # حجم الورقة (عرض 80mm)
    page_width = 80 * mm
    page_height = (180 + (len(items) * 18)) * mm

    c = canvas.Canvas(file_path, pagesize=(page_width, page_height))

    # تسجيل خط عربي
    try:
        font_path = "C:/Windows/Fonts/arial.ttf"
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Arabic', font_path))
            font_name = 'Arabic'
        else:
            font_name = 'Helvetica'
    except:
        font_name = 'Helvetica'

    y = page_height - 15 * mm

    # === رأس الفاتورة ===
    c.setFont(font_name, 14)
    title_text = "فاتورة مرتجع" if invoice_type == "return" else "فاتورة مبيعات"
    c.drawCentredString(page_width / 2, y, arabic(title_text))
    y -= 8 * mm

    c.setFont(font_name, 8)
    c.drawCentredString(page_width / 2, y, "=" * 40)
    y -= 6 * mm

    c.setFont(font_name, 9)
    c.drawRightString(page_width - 5 * mm, y, arabic(f"رقم الفاتورة: {sale_id}"))
    y -= 5 * mm
    c.drawRightString(page_width - 5 * mm, y, arabic(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"))
    y -= 5 * mm
    if cashier_name:
        c.drawRightString(page_width - 5 * mm, y, arabic(f"الكاشير: {cashier_name}"))
        y -= 5 * mm

    c.drawCentredString(page_width / 2, y, "-" * 45)
    y -= 6 * mm

    # === رؤوس الأعمدة ===
    c.setFont(font_name, 8)
    c.drawString(5 * mm, y, arabic("الإجمالي"))
    c.drawCentredString(page_width / 2, y, arabic("الكمية × السعر"))
    c.drawRightString(page_width - 5 * mm, y, arabic("الصنف"))
    y -= 4 * mm

    c.drawCentredString(page_width / 2, y, "-" * 45)
    y -= 5 * mm

    # === الأصناف ===
    c.setFont(font_name, 8)
    for item in items:
        c.drawRightString(page_width - 5 * mm, y, arabic(str(item["name"])))
        c.drawCentredString(page_width / 2, y, f'{item["qty"]} x {item["price"]:.2f}')
        c.drawString(5 * mm, y, f'{item["total"]:.2f}')
        y -= 5 * mm

    y -= 2 * mm
    c.drawCentredString(page_width / 2, y, "=" * 40)
    y -= 6 * mm

    # === الإجمالي ===
    c.setFont(font_name, 11)
    c.drawRightString(page_width - 5 * mm, y, arabic(f"الإجمالي: {total:.2f} ج.م"))
    y -= 7 * mm

    c.setFont(font_name, 9)
    c.drawRightString(page_width - 5 * mm, y, arabic(f"طريقة الدفع: {payment_details['payment_method']}"))
    y -= 5 * mm
    c.drawRightString(page_width - 5 * mm, y, arabic(f"المدفوع: {payment_details['amount_paid']:.2f} ج.م"))
    y -= 5 * mm
    c.drawRightString(page_width - 5 * mm, y, arabic(f"الباقي: {payment_details['amount_change']:.2f} ج.م"))
    y -= 8 * mm

    y -= 4 * mm
    if invoice_barcode:
        barcode_obj = code128.Code128(invoice_barcode, barHeight=12 * mm, barWidth=0.35)
        barcode_width = barcode_obj.width
        x_pos = (page_width - barcode_width) / 2
        barcode_obj.drawOn(c, x_pos, y - 12 * mm)

        y -= 15 * mm
        c.setFont(font_name, 8)
        c.drawCentredString(page_width / 2, y, invoice_barcode)
        y -= 6 * mm

    # === الفوتر ===
    c.drawCentredString(page_width / 2, y, "-" * 45)
    y -= 6 * mm
    c.setFont(font_name, 8)
    c.drawCentredString(page_width / 2, y, arabic("شكراً لتعاملكم معنا"))
    y -= 5 * mm
    c.drawCentredString(page_width / 2, y, arabic("نتمنى لكم يوماً سعيداً"))

    c.save()
    return file_path


def open_pdf(file_path):
    try:
        if os.name == 'nt':
            os.startfile(file_path)
        elif os.name == 'posix':
            subprocess.run(['xdg-open', file_path])
    except Exception as e:
        print(f"خطأ في فتح الملف: {e}")


def print_receipt(sale_id, items, total, payment_details, cashier_name="", invoice_barcode="", invoice_type="sale"):
    file_path = generate_receipt(
        sale_id, items, total, payment_details,
        cashier_name, invoice_barcode, invoice_type
    )
    open_pdf(file_path)
    return file_path