import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QLineEdit, QSpinBox, QComboBox,
    QWidget, QMessageBox, QGridLayout, QSplitter, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QGuiApplication

from database.connection import get_connection
from gui.shift_manager import get_open_shift, log_audit


STYLE = """
QDialog {
    background-color: transparent;
}

QFrame#mainFrame {
    background-color: #f4f6f8;
    border: 2px solid #d35400;
    border-radius: 16px;
}

QLabel {
    font-family: 'Segoe UI';
    color: #2c3e50;
    background: transparent;
    border: none;
}

QLineEdit, QSpinBox, QComboBox {
    border: 1px solid #d6dbe1;
    border-radius: 10px;
    padding: 7px 10px;
    font-size: 13px;
    background: white;
    color: #2c3e50;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 2px solid #d35400;
}

QPushButton {
    background-color: #d35400;
    color: white;
    font-size: 14px;
    font-weight: bold;
    border-radius: 16px;
    padding: 10px 16px;
    border: none;
}

QPushButton:hover {
    background-color: #b54700;
}

QPushButton#dangerBtn {
    background-color: #c0392b;
}
QPushButton#dangerBtn:hover {
    background-color: #a93226;
}

QPushButton#successBtn {
    background-color: #27ae60;
}
QPushButton#successBtn:hover {
    background-color: #1f8b4d;
}

QPushButton#cancelBtn {
    background-color: #718093;
}
QPushButton#cancelBtn:hover {
    background-color: #57606f;
}

QTableWidget {
    background: white;
    border: 1px solid #dcdfe4;
    border-radius: 10px;
    font-size: 13px;
    gridline-color: #ecf0f1;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background-color: #1e5378;
    color: white;
}

QHeaderView::section {
    background-color: #2c3e50;
    color: white;
    font-weight: bold;
    padding: 8px;
    border: none;
}

QSplitter::handle {
    background: #dfe6e9;
    width: 6px;
}
"""


class LinkedReturnDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.invoice_items = []
        self.return_items = []
        self.original_sale_id = None
        self.return_invoice_id = None

        screen = QGuiApplication.primaryScreen().availableGeometry()
        width = min(1380, screen.width() - 40)
        height = min(860, screen.height() - 40)

        self.resize(width, height)
        self.setMinimumSize(1180, 760)
        self.setWindowTitle("مرتجع مرتبط بفاتورة أصلية")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(STYLE)

        self.init_ui()

    # ==============================
    # Helpers
    # ==============================
    def show_message(self, text, level="info"):
        from gui.pos_window import SystemMessageBox
        if level == "success":
            SystemMessageBox.show_success(self, text)
        elif level == "warning":
            SystemMessageBox.show_warning(self, text)
        elif level == "error":
            SystemMessageBox.show_critical(self, text)
        else:
            SystemMessageBox.show_info(self, text)

    def money(self, value):
        return f"{float(value or 0):.2f} ج.م"

    def create_info_card(self, title, value="---", color="#2c3e50"):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e1e5ea;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_title.setStyleSheet("color: #7f8c8d;")

        lbl_value = QLabel(value)
        lbl_value.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_value.setStyleSheet(f"color: {color};")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        return frame, lbl_value

    # ==============================
    # UI
    # ==============================
    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")

        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(10)

        # ===== Header =====
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #d35400;
                border-radius: 12px;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(2)

        title = QLabel("مرتجع مرتبط بفاتورة أصلية")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")

        sub = QLabel("ابحث عن الفاتورة الأصلية ثم اختر الأصناف المطلوب إرجاعها")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #ffe7d1;")

        header_layout.addWidget(title)
        header_layout.addWidget(sub)
        main_layout.addWidget(header)

        # ===== Search Bar =====
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e1e5ea;
                border-radius: 12px;
            }
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 10, 12, 10)
        search_layout.setSpacing(10)

        lbl_invoice = QLabel("رقم الفاتورة الأصلية")
        lbl_invoice.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.txt_invoice_id = QLineEdit()
        self.txt_invoice_id.setPlaceholderText("ادخل رقم الفاتورة...")
        self.txt_invoice_id.setFixedHeight(40)
        self.txt_invoice_id.returnPressed.connect(self.load_invoice_items)

        btn_load = QPushButton("تحميل")
        btn_load.setObjectName("successBtn")
        btn_load.setFixedSize(120, 40)
        btn_load.clicked.connect(self.load_invoice_items)

        self.lbl_invoice_status = QLabel("لم يتم تحميل فاتورة بعد")
        self.lbl_invoice_status.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_invoice_status.setStyleSheet("color: #7f8c8d;")

        search_layout.addWidget(lbl_invoice)
        search_layout.addWidget(self.txt_invoice_id, 2)
        search_layout.addWidget(btn_load)
        search_layout.addWidget(self.lbl_invoice_status, 2)

        main_layout.addWidget(search_frame)

        # ===== Invoice cards =====
        cards_grid = QGridLayout()
        cards_grid.setSpacing(10)

        card1, self.lbl_sale_total = self.create_info_card("إجمالي الفاتورة", "---", "#27ae60")
        card2, self.lbl_sale_method = self.create_info_card("طريقة الدفع", "---", "#2980b9")
        card3, self.lbl_sale_shift = self.create_info_card("الوردية", "---", "#8e44ad")
        card4, self.lbl_sale_count = self.create_info_card("عدد الأصناف", "---", "#d35400")

        cards_grid.addWidget(card1, 0, 0)
        cards_grid.addWidget(card2, 0, 1)
        cards_grid.addWidget(card3, 0, 2)
        cards_grid.addWidget(card4, 0, 3)

        main_layout.addLayout(cards_grid)

        # ===== Main splitter =====
        splitter = QSplitter(Qt.Horizontal)

        # ----------------- Source invoice panel -----------------
        source_panel = QFrame()
        source_panel.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e1e5ea;
                border-radius: 12px;
            }
        """)
        source_layout = QVBoxLayout(source_panel)
        source_layout.setContentsMargins(12, 12, 12, 12)
        source_layout.setSpacing(8)

        lbl_source = QLabel("أصناف الفاتورة الأصلية")
        lbl_source.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_source.setStyleSheet("color: #2c3e50;")
        source_layout.addWidget(lbl_source)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "الباركود", "اسم الصنف", "المباع", "تم إرجاعه", "المتاح", "السعر", "sale_item_id"
        ])
        self.items_table.setColumnHidden(6, True)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.itemSelectionChanged.connect(self.on_item_selection_changed)
        source_layout.addWidget(self.items_table)

        qty_tools = QFrame()
        qty_tools.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #ebedf0;
                border-radius: 10px;
            }
        """)
        qty_tools_layout = QHBoxLayout(qty_tools)
        qty_tools_layout.setContentsMargins(10, 8, 10, 8)
        qty_tools_layout.setSpacing(10)

        lbl_qty = QLabel("كمية المرتجع:")
        lbl_qty.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 1)
        self.spin_qty.setValue(1)
        self.spin_qty.setFixedSize(100, 38)
        self.spin_qty.setAlignment(Qt.AlignCenter)

        btn_add = QPushButton("إضافة إلى المرتجع")
        btn_add.setFixedHeight(38)
        btn_add.clicked.connect(self.add_selected_item_to_return)

        qty_tools_layout.addWidget(lbl_qty)
        qty_tools_layout.addWidget(self.spin_qty)
        qty_tools_layout.addWidget(btn_add)
        qty_tools_layout.addStretch()

        source_layout.addWidget(qty_tools)

        # ----------------- Return cart panel -----------------
        return_panel = QFrame()
        return_panel.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e1e5ea;
                border-radius: 12px;
            }
        """)
        return_layout = QVBoxLayout(return_panel)
        return_layout.setContentsMargins(12, 12, 12, 12)
        return_layout.setSpacing(8)

        lbl_return = QLabel("أصناف المرتجع الحالي")
        lbl_return.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_return.setStyleSheet("color: #c0392b;")
        return_layout.addWidget(lbl_return)

        self.return_table = QTableWidget()
        self.return_table.setColumnCount(6)
        self.return_table.setHorizontalHeaderLabels([
            "اسم الصنف", "الكمية", "السعر", "الإجمالي", "sale_item_id", "product_id"
        ])
        self.return_table.setColumnHidden(4, True)
        self.return_table.setColumnHidden(5, True)
        self.return_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.return_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.return_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.return_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        return_layout.addWidget(self.return_table)

        btn_remove = QPushButton("حذف العنصر المحدد")
        btn_remove.setObjectName("dangerBtn")
        btn_remove.setFixedHeight(38)
        btn_remove.clicked.connect(self.remove_selected_return_item)
        return_layout.addWidget(btn_remove)

        splitter.addWidget(source_panel)
        splitter.addWidget(return_panel)
        splitter.setSizes([700, 420])

        main_layout.addWidget(splitter, 1)

        # ===== Bottom panel =====
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e1e5ea;
                border-radius: 12px;
            }
        """)
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(12, 12, 12, 12)
        bottom_layout.setSpacing(12)

        left_form = QFormLayout()
        left_form.setSpacing(8)

        self.cmb_refund_method = QComboBox()
        self.cmb_refund_method.addItems(["نقدي", "استبدال", "رصيد عميل"])
        self.cmb_refund_method.setFixedHeight(38)

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("ملاحظات على المرتجع...")
        self.txt_notes.setFixedHeight(38)

        left_form.addRow("طريقة رد القيمة:", self.cmb_refund_method)
        left_form.addRow("ملاحظات:", self.txt_notes)

        total_box = QFrame()
        total_box.setStyleSheet("""
            QFrame {
                background: #fff5f0;
                border: 2px solid #e67e22;
                border-radius: 12px;
            }
        """)
        total_layout = QVBoxLayout(total_box)
        total_layout.setContentsMargins(18, 14, 18, 14)

        lbl_total_title = QLabel("إجمالي المرتجع")
        lbl_total_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_total_title.setAlignment(Qt.AlignCenter)
        lbl_total_title.setStyleSheet("color: #a04000;")

        self.lbl_total_return = QLabel("0.00 ج.م")
        self.lbl_total_return.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.lbl_total_return.setAlignment(Qt.AlignCenter)
        self.lbl_total_return.setStyleSheet("color: #c0392b;")

        total_layout.addWidget(lbl_total_title)
        total_layout.addWidget(self.lbl_total_return)

        bottom_layout.addLayout(left_form, 3)
        bottom_layout.addWidget(total_box, 1)

        main_layout.addWidget(bottom_frame)

        # ===== Final buttons =====
        btns = QHBoxLayout()
        btns.addStretch()

        btn_save = QPushButton("اعتماد المرتجع")
        btn_save.setObjectName("dangerBtn")
        btn_save.setFixedSize(180, 45)
        btn_save.clicked.connect(self.save_return)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("cancelBtn")
        btn_cancel.setFixedSize(120, 45)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        btns.addStretch()

        main_layout.addLayout(btns)

        root.addWidget(main_frame)
        self.txt_invoice_id.setFocus()

    # ==============================
    # Data
    # ==============================
    def load_invoice_items(self):
        invoice_id_text = self.txt_invoice_id.text().strip()
        if not invoice_id_text.isdigit():
            self.show_message("ادخل رقم فاتورة صحيح", "warning")
            return

        invoice_id = int(invoice_id_text)

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, total_amount, payment_method, shift_id
                FROM sales
                WHERE id = %s
            """, (invoice_id,))
            sale_row = cursor.fetchone()

            if not sale_row:
                cursor.close()
                conn.close()
                self.show_message("الفاتورة غير موجودة", "warning")
                return

            self.original_sale_id = sale_row[0]
            self.lbl_sale_total.setText(self.money(sale_row[1]))
            self.lbl_sale_method.setText(str(sale_row[2] or "---"))
            self.lbl_sale_shift.setText(str(sale_row[3] if sale_row[3] else "---"))

            cursor.execute("""
                SELECT
                    si.id AS sale_item_id,
                    si.product_id,
                    p.barcode,
                    p.name,
                    si.quantity AS sold_qty,
                    COALESCE(SUM(ri.quantity), 0) AS returned_qty,
                    si.unit_price,
                    (si.quantity - COALESCE(SUM(ri.quantity), 0)) AS available_qty
                FROM sale_items si
                JOIN products p ON p.id = si.product_id
                LEFT JOIN return_items ri ON ri.original_sale_item_id = si.id
                WHERE si.sale_id = %s
                GROUP BY si.id, si.product_id, p.barcode, p.name, si.quantity, si.unit_price
                HAVING (si.quantity - COALESCE(SUM(ri.quantity), 0)) > 0
                ORDER BY si.id
            """, (invoice_id,))
            rows = cursor.fetchall()

            cursor.close()
            conn.close()

            self.invoice_items = []
            self.return_items = []
            self.items_table.setRowCount(0)
            self.refresh_return_table()

            if not rows:
                self.lbl_invoice_status.setText(f"الفاتورة {invoice_id} - لا يوجد أصناف متاحة")
                self.lbl_invoice_status.setStyleSheet("color: #c0392b; font-weight: bold;")
                self.lbl_sale_count.setText("---")
                self.show_message("كل أصناف هذه الفاتورة تم إرجاعها أو لا يوجد أصناف صالحة للمرتجع", "warning")
                return

            self.lbl_invoice_status.setText(f"تم تحميل الفاتورة رقم {invoice_id}")
            self.lbl_invoice_status.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.lbl_sale_count.setText(str(len(rows)))

            self.items_table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                item_data = {
                    "sale_item_id": row[0],
                    "product_id": row[1],
                    "barcode": row[2] or "",
                    "name": row[3] or "",
                    "sold_qty": int(row[4] or 0),
                    "returned_qty": int(row[5] or 0),
                    "price": float(row[6] or 0),
                    "available_qty": int(row[7] or 0)
                }
                self.invoice_items.append(item_data)

                values = [
                    item_data["barcode"],
                    item_data["name"],
                    str(item_data["sold_qty"]),
                    str(item_data["returned_qty"]),
                    str(item_data["available_qty"]),
                    f"{item_data['price']:.2f}",
                    str(item_data["sale_item_id"])
                ]

                for col, val in enumerate(values):
                    cell = QTableWidgetItem(val)
                    cell.setFont(QFont("Segoe UI", 10))
                    cell.setTextAlignment(Qt.AlignCenter)

                    if col == 4:
                        cell.setForeground(QColor("#d35400"))
                        cell.setFont(QFont("Segoe UI", 10, QFont.Bold))

                    self.items_table.setItem(i, col, cell)
                    self.items_table.setRowHeight(i, 34)

            self.items_table.selectRow(0)
            self.on_item_selection_changed()

        except Exception as e:
            self.show_message(f"خطأ أثناء تحميل الفاتورة: {e}", "error")

    def on_item_selection_changed(self):
        row = self.items_table.currentRow()
        if row < 0 or row >= len(self.invoice_items):
            return

        item = self.invoice_items[row]
        already_selected = 0

        for r in self.return_items:
            if r["sale_item_id"] == item["sale_item_id"]:
                already_selected = r["qty"]
                break

        remaining = max(item["available_qty"] - already_selected, 1)
        self.spin_qty.setMaximum(remaining)
        self.spin_qty.setValue(1)

    def add_selected_item_to_return(self):
        row = self.items_table.currentRow()
        if row < 0 or row >= len(self.invoice_items):
            self.show_message("اختر صنف من جدول الفاتورة أولاً", "warning")
            return

        item = self.invoice_items[row]
        qty = self.spin_qty.value()

        already_selected = 0
        existing_index = -1
        for idx, r in enumerate(self.return_items):
            if r["sale_item_id"] == item["sale_item_id"]:
                already_selected = r["qty"]
                existing_index = idx
                break

        remaining = item["available_qty"] - already_selected

        if qty <= 0 or qty > remaining:
            self.show_message("الكمية المطلوبة أكبر من المتاح للمرتجع", "warning")
            return

        if existing_index >= 0:
            self.return_items[existing_index]["qty"] += qty
            self.return_items[existing_index]["total"] = (
                self.return_items[existing_index]["qty"] * self.return_items[existing_index]["price"]
            )
        else:
            self.return_items.append({
                "sale_item_id": item["sale_item_id"],
                "product_id": item["product_id"],
                "name": item["name"],
                "qty": qty,
                "price": item["price"],
                "total": qty * item["price"]
            })

        self.refresh_return_table()
        self.on_item_selection_changed()

    def remove_selected_return_item(self):
        row = self.return_table.currentRow()
        if row < 0 or row >= len(self.return_items):
            self.show_message("اختر صنف من جدول المرتجع أولاً", "warning")
            return

        del self.return_items[row]
        self.refresh_return_table()
        self.on_item_selection_changed()

    def refresh_return_table(self):
        self.return_table.setRowCount(len(self.return_items))
        total = 0.0

        for i, item in enumerate(self.return_items):
            values = [
                item["name"],
                str(item["qty"]),
                f"{item['price']:.2f}",
                f"{item['total']:.2f}",
                str(item["sale_item_id"]),
                str(item["product_id"])
            ]
            total += item["total"]

            for col, val in enumerate(values):
                cell = QTableWidgetItem(val)
                cell.setFont(QFont("Segoe UI", 10))
                cell.setTextAlignment(Qt.AlignCenter)

                if col == 3:
                    cell.setForeground(QColor("#c0392b"))
                    cell.setFont(QFont("Segoe UI", 10, QFont.Bold))

                self.return_table.setItem(i, col, cell)
                self.return_table.setRowHeight(i, 34)

        self.lbl_total_return.setText(self.money(total))

    def save_return(self):
        if not self.original_sale_id:
            self.show_message("حمّل الفاتورة الأصلية أولاً", "warning")
            return

        if not self.return_items:
            self.show_message("لا توجد أصناف في المرتجع", "warning")
            return

        cashier_name = self.session.get("full_name", "")
        shift_id = get_open_shift(cashier_name)
        if not shift_id:
            self.show_message("لا توجد وردية مفتوحة! لا يمكن تنفيذ المرتجع بدون وردية", "warning")
            return

        refund_method = self.cmb_refund_method.currentText()
        notes = self.txt_notes.text().strip()
        total_return = sum(item["total"] for item in self.return_items)

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # تحقق نهائي
            for item in self.return_items:
                cursor.execute("""
                    SELECT
                        si.quantity - COALESCE(SUM(ri.quantity), 0) AS available_qty
                    FROM sale_items si
                    LEFT JOIN return_items ri ON ri.original_sale_item_id = si.id
                    WHERE si.id = %s
                    GROUP BY si.id, si.quantity
                """, (item["sale_item_id"],))
                row = cursor.fetchone()

                if not row:
                    raise Exception(f"بند البيع الأصلي غير موجود: {item['name']}")

                available_now = int(row[0] or 0)
                if item["qty"] > available_now:
                    raise Exception(f"الكمية المتاحة من ({item['name']}) هي {available_now} فقط")

            # إنشاء سند المرتجع
            cursor.execute("""
                INSERT INTO return_invoices (
                    original_sale_id, shift_id, cashier_name,
                    total_amount, refund_method, notes
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                self.original_sale_id,
                shift_id,
                cashier_name,
                total_return,
                refund_method,
                notes
            ))
            self.return_invoice_id = cursor.fetchone()[0]

            # البنود
            for item in self.return_items:
                cursor.execute("""
                    INSERT INTO return_items (
                        return_invoice_id, original_sale_item_id,
                        product_id, quantity, unit_price, total
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    self.return_invoice_id,
                    item["sale_item_id"],
                    item["product_id"],
                    item["qty"],
                    item["price"],
                    item["total"]
                ))

                cursor.execute("""
                    UPDATE products
                    SET qty = qty + %s
                    WHERE id = %s
                """, (item["qty"], item["product_id"]))

            if refund_method == "نقدي":
                cursor.execute("""
                    INSERT INTO shift_transactions (
                        shift_id, transaction_type, amount, reason, notes, created_by
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    shift_id,
                    "cash_out",
                    total_return,
                    f"مرتجع فاتورة أصلية رقم {self.original_sale_id}",
                    notes,
                    cashier_name
                ))

                cursor.execute("""
                    UPDATE shifts
                    SET cash_out_total = cash_out_total + %s
                    WHERE id = %s
                """, (total_return, shift_id))

            conn.commit()
            cursor.close()
            conn.close()

            log_audit(
                "مرتجع فاتورة أصلية",
                f"مرتجع رقم {self.return_invoice_id} مرتبط بالفاتورة {self.original_sale_id} بقيمة {total_return:.2f}",
                cashier_name
            )

            self.show_message(
                f"تم حفظ المرتجع بنجاح\nرقم المرتجع: {self.return_invoice_id}\nالإجمالي: {total_return:.2f} ج.م",
                "success"
            )
            self.accept()

        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            self.show_message(f"خطأ أثناء حفظ المرتجع: {e}", "error")