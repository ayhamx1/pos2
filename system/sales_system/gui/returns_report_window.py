import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QAbstractItemView, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor

from database.connection import get_connection


STYLE = """
    QWidget {
        background-color: #F5F5F5;
        font-family: 'Segoe UI';
    }
    QLabel {
        color: #2b2b2b;
        border: none;
        background-color: transparent;
    }
    QLineEdit, QDateEdit {
        border: 1px solid #cccccc;
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 13px;
        background-color: white;
    }
    QLineEdit:focus, QDateEdit:focus {
        border: 2px solid #1e5378;
    }
    QPushButton {
        background-color: #1e5378;
        color: white;
        font-size: 14px;
        font-weight: bold;
        border-radius: 18px;
        padding: 10px 20px;
        border: none;
    }
    QPushButton:hover {
        background-color: #163f5c;
    }
    QPushButton#clearBtn {
        background-color: #718096;
    }
    QPushButton#clearBtn:hover {
        background-color: #4a5568;
    }
    QTableWidget {
        background: white;
        border: 1px solid #dcdcdc;
        border-radius: 8px;
        font-size: 13px;
        gridline-color: #f0f0f0;
    }
    QHeaderView::section {
        background-color: #1e5378;
        color: white;
        font-weight: bold;
        padding: 8px;
        border: none;
    }
"""


class ReturnsReportWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تقرير المرتجعات")
        self.setGeometry(100, 60, 1300, 760)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(STYLE)

        self.init_ui()
        self.load_returns()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # ===== الهيدر =====
        header = QFrame()
        header.setStyleSheet("background-color: #d35400; border-radius: 10px; padding: 12px;")
        header_layout = QVBoxLayout(header)

        title = QLabel("تقرير المرتجعات")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")

        sub = QLabel("بحث وعرض جميع المرتجعات مع تفاصيل الأصناف")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #fdebd0;")

        header_layout.addWidget(title)
        header_layout.addWidget(sub)
        main_layout.addWidget(header)

        # ===== الفلاتر =====
        filters_frame = QFrame()
        filters_frame.setStyleSheet("""
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 10px;
        """)
        filters_layout = QVBoxLayout(filters_frame)
        filters_layout.setSpacing(10)

        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.txt_return_id = QLineEdit()
        self.txt_return_id.setPlaceholderText("رقم المرتجع")

        self.txt_original_invoice = QLineEdit()
        self.txt_original_invoice.setPlaceholderText("رقم الفاتورة الأصلية")

        self.txt_cashier = QLineEdit()
        self.txt_cashier.setPlaceholderText("اسم الكاشير")

        row1.addWidget(QLabel("رقم المرتجع:"))
        row1.addWidget(self.txt_return_id)
        row1.addWidget(QLabel("الفاتورة الأصلية:"))
        row1.addWidget(self.txt_original_invoice)
        row1.addWidget(QLabel("الكاشير:"))
        row1.addWidget(self.txt_cashier)

        filters_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setDisplayFormat("yyyy-MM-dd")

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("yyyy-MM-dd")

        btn_search = QPushButton("بحث")
        btn_search.clicked.connect(self.load_returns)

        btn_clear = QPushButton("مسح الفلاتر")
        btn_clear.setObjectName("clearBtn")
        btn_clear.clicked.connect(self.clear_filters)

        row2.addWidget(QLabel("من تاريخ:"))
        row2.addWidget(self.date_from)
        row2.addWidget(QLabel("إلى تاريخ:"))
        row2.addWidget(self.date_to)
        row2.addStretch()
        row2.addWidget(btn_search)
        row2.addWidget(btn_clear)

        filters_layout.addLayout(row2)
        main_layout.addWidget(filters_frame)

        # ===== ملخص سريع =====
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            background: #fdf2e9;
            border: 1px solid #f5cba7;
            border-radius: 10px;
            padding: 10px;
        """)
        summary_layout = QHBoxLayout(summary_frame)

        self.lbl_count = QLabel("عدد المرتجعات: 0")
        self.lbl_count.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.lbl_count.setStyleSheet("color: #a04000;")

        self.lbl_total = QLabel("إجمالي قيمة المرتجعات: 0.00 ج.م")
        self.lbl_total.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.lbl_total.setStyleSheet("color: #a04000;")

        summary_layout.addWidget(self.lbl_count)
        summary_layout.addStretch()
        summary_layout.addWidget(self.lbl_total)

        main_layout.addWidget(summary_frame)

        # ===== جدول المرتجعات =====
        lbl_main = QLabel("سجلات المرتجعات")
        lbl_main.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_main.setStyleSheet("color: #1e5378;")
        main_layout.addWidget(lbl_main)

        self.returns_table = QTableWidget()
        self.returns_table.setColumnCount(7)
        self.returns_table.setHorizontalHeaderLabels([
            "رقم المرتجع",
            "رقم الفاتورة الأصلية",
            "الكاشير",
            "الإجمالي",
            "طريقة الرد",
            "التاريخ",
            "ملاحظات"
        ])
        self.returns_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.returns_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.returns_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.returns_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.returns_table.itemSelectionChanged.connect(self.load_return_details)
        main_layout.addWidget(self.returns_table, stretch=3)

        # ===== تفاصيل المرتجع =====
        lbl_details = QLabel("تفاصيل أصناف المرتجع المحدد")
        lbl_details.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_details.setStyleSheet("color: #c0392b;")
        main_layout.addWidget(lbl_details)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "اسم الصنف",
            "الكمية",
            "السعر",
            "الإجمالي",
            "رقم بند البيع الأصلي"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.setSelectionMode(QAbstractItemView.NoSelection)
        main_layout.addWidget(self.items_table, stretch=2)

    def clear_filters(self):
        self.txt_return_id.clear()
        self.txt_original_invoice.clear()
        self.txt_cashier.clear()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.load_returns()

    def load_returns(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    id,
                    original_sale_id,
                    cashier_name,
                    total_amount,
                    refund_method,
                    created_at,
                    COALESCE(notes, '')
                FROM return_invoices
                WHERE 1=1
            """
            params = []

            if self.txt_return_id.text().strip():
                query += " AND id = %s"
                params.append(int(self.txt_return_id.text().strip()))

            if self.txt_original_invoice.text().strip():
                query += " AND original_sale_id = %s"
                params.append(int(self.txt_original_invoice.text().strip()))

            if self.txt_cashier.text().strip():
                query += " AND cashier_name ILIKE %s"
                params.append(f"%{self.txt_cashier.text().strip()}%")

            query += " AND DATE(created_at) BETWEEN %s AND %s"
            params.append(self.date_from.date().toString("yyyy-MM-dd"))
            params.append(self.date_to.date().toString("yyyy-MM-dd"))

            query += " ORDER BY id DESC"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            self.returns_table.setRowCount(len(rows))

            total_returns = 0.0

            for i, row in enumerate(rows):
                return_id, original_sale_id, cashier_name, total_amount, refund_method, created_at, notes = row
                total_returns += float(total_amount or 0)

                values = [
                    str(return_id),
                    str(original_sale_id),
                    str(cashier_name or ""),
                    f"{float(total_amount or 0):.2f} ج.م",
                    str(refund_method or ""),
                    created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "",
                    str(notes or "")
                ]

                for col, val in enumerate(values):
                    cell = QTableWidgetItem(val)
                    cell.setFont(QFont("Segoe UI", 11))
                    cell.setTextAlignment(Qt.AlignCenter)

                    if col == 3:
                        cell.setForeground(QColor("#c0392b"))
                        cell.setFont(QFont("Segoe UI", 11, QFont.Bold))

                    self.returns_table.setItem(i, col, cell)
                    self.returns_table.setRowHeight(i, 36)

            self.lbl_count.setText(f"عدد المرتجعات: {len(rows)}")
            self.lbl_total.setText(f"إجمالي قيمة المرتجعات: {total_returns:.2f} ج.م")

            cursor.close()
            conn.close()

            if rows:
                self.returns_table.selectRow(0)
            else:
                self.items_table.setRowCount(0)

        except Exception as e:
            print(f"خطأ تحميل المرتجعات: {e}")

    def load_return_details(self):
        row = self.returns_table.currentRow()
        if row < 0:
            self.items_table.setRowCount(0)
            return

        return_id_item = self.returns_table.item(row, 0)
        if not return_id_item:
            return

        return_id = int(return_id_item.text())

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    p.name,
                    ri.quantity,
                    ri.unit_price,
                    ri.total,
                    ri.original_sale_item_id
                FROM return_items ri
                JOIN products p ON p.id = ri.product_id
                WHERE ri.return_invoice_id = %s
                ORDER BY ri.id
            """, (return_id,))
            rows = cursor.fetchall()

            self.items_table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                name, qty, price, total, sale_item_id = row

                values = [
                    str(name or ""),
                    str(qty or 0),
                    f"{float(price or 0):.2f}",
                    f"{float(total or 0):.2f}",
                    str(sale_item_id or "")
                ]

                for col, val in enumerate(values):
                    cell = QTableWidgetItem(val)
                    cell.setFont(QFont("Segoe UI", 11))
                    cell.setTextAlignment(Qt.AlignCenter)

                    if col == 3:
                        cell.setForeground(QColor("#c0392b"))
                        cell.setFont(QFont("Segoe UI", 11, QFont.Bold))

                    self.items_table.setItem(i, col, cell)
                    self.items_table.setRowHeight(i, 34)

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"خطأ تحميل تفاصيل المرتجع: {e}")