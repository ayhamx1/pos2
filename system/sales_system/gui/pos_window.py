import sys
import os
import bcrypt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QHeaderView, QFrame,
    QDialog, QFormLayout, QSpinBox, QComboBox,
    QAbstractItemView, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, QDateTime, QTimer, QEvent
from PySide6.QtGui import QFont, QColor, QShortcut, QKeySequence

from database.connection import get_connection

try:
    from utils.receipt_printer import print_receipt
except ImportError:
    print_receipt = None


MODERN_STYLE = """
    QMainWindow { background-color: #F5F5F5; }
    QDialog { background-color: transparent; }
    QFrame#mainFrame {
        background-color: #F5F5F5;
        border: 2px solid #1e5378;
        border-radius: 16px;
    }
    QLabel {
        font-family: 'Segoe UI', 'Arial', 'Cairo';
        color: #2b2b2b;
        border: none;
        background-color: transparent;
    }
    QLineEdit, QSpinBox, QComboBox {
        border: 1px solid #cccccc;
        border-radius: 8px;
        padding: 6px 10px;
        font-family: 'Segoe UI';
        font-size: 14px;
        background-color: #ffffff;
        color: #333333;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 2px solid #1e5378;
    }
    QTableWidget {
        background-color: #ffffff;
        border: 2px solid #d3d3d3;
        border-radius: 8px;
        gridline-color: #f0f0f0;
        font-family: 'Segoe UI';
        color: #333333;
    }
    QHeaderView::section {
        background-color: #1e5378;
        color: white;
        font-weight: bold;
        padding: 8px;
        border: none;
    }
    QPushButton {
        background-color: #1e5378;
        color: #ffffff;
        font-family: 'Segoe UI', 'Cairo';
        font-size: 14px;
        font-weight: bold;
        border-radius: 20px;
        padding: 10px 25px;
        border: none;
        min-height: 20px;
    }
    QPushButton:hover { background-color: #163f5c; }
    QPushButton:pressed { background-color: #0f2d42; }

    QPushButton#cancelBtn {
        background-color: #718096;
        color: white;
    }
    QPushButton#cancelBtn:hover {
        background-color: #4a5568;
    }

    QPushButton#fastCashBtn {
        background-color: #e2e8f0;
        color: #2d3748;
        font-family: 'Segoe UI';
        font-size: 13px;
        font-weight: bold;
        border-radius: 6px;
        padding: 6px;
        border: 1px solid #cbd5e0;
    }
    QPushButton#fastCashBtn:hover {
        background-color: #cbd5e0;
    }
"""


class SystemMessageBox(QDialog):
    def __init__(self, text, icon_type="info", parent=None):
        super().__init__(parent)
        self.setFixedSize(420, 160)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(20, 20, 20, 15)
        frame_layout.setSpacing(15)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        self.lbl_icon = QLabel()
        self.lbl_icon.setFont(QFont("Segoe UI", 26))
        self.lbl_icon.setAlignment(Qt.AlignCenter)

        if icon_type == "success":
            self.lbl_icon.setText("[OK]")
            self.lbl_icon.setStyleSheet("color: #2ed573; font-weight: bold;")
        elif icon_type == "warning":
            self.lbl_icon.setText("[!]")
            self.lbl_icon.setStyleSheet("color: #ffa502; font-weight: bold;")
        elif icon_type == "error":
            self.lbl_icon.setText("[X]")
            self.lbl_icon.setStyleSheet("color: #e53e3e; font-weight: bold;")
        elif icon_type == "question":
            self.lbl_icon.setText("[?]")
            self.lbl_icon.setStyleSheet("color: #1e90ff; font-weight: bold;")
        else:
            self.lbl_icon.setText("[i]")
            self.lbl_icon.setStyleSheet("color: #636e72; font-weight: bold;")

        self.lbl_text = QLabel(text)
        self.lbl_text.setFont(QFont("Segoe UI", 12, QFont.Medium))
        self.lbl_text.setWordWrap(True)

        content_layout.addWidget(self.lbl_icon, stretch=1)
        content_layout.addWidget(self.lbl_text, stretch=5)
        frame_layout.addLayout(content_layout, stretch=3)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        if icon_type == "question":
            self.btn_yes = QPushButton("نعم")
            self.btn_yes.clicked.connect(self.accept)

            self.btn_no = QPushButton("لا")
            self.btn_no.clicked.connect(self.reject)

            btn_layout.addWidget(self.btn_yes)
            btn_layout.addWidget(self.btn_no)
        else:
            self.btn_ok = QPushButton("موافق")
            self.btn_ok.clicked.connect(self.accept)
            btn_layout.addWidget(self.btn_ok)

        btn_layout.addStretch()
        frame_layout.addLayout(btn_layout, stretch=1)

        container_layout.addWidget(main_frame)

    @staticmethod
    def show_info(parent, text):
        return SystemMessageBox(text, "info", parent).exec()

    @staticmethod
    def show_success(parent, text):
        return SystemMessageBox(text, "success", parent).exec()

    @staticmethod
    def show_warning(parent, text):
        return SystemMessageBox(text, "warning", parent).exec()

    @staticmethod
    def show_critical(parent, text):
        return SystemMessageBox(text, "error", parent).exec()

    @staticmethod
    def show_question(parent, text):
        return SystemMessageBox(text, "question", parent).exec()


class PaymentDialog(QDialog):
    def __init__(self, total_amount, parent=None):
        super().__init__(parent)
        self.total_amount = total_amount
        self.setFixedSize(460, 480)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(25, 20, 25, 20)
        frame_layout.setSpacing(15)

        title = QLabel("شاشة إنهاء الدفع وتحصيل الفاتورة")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        frame_layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        self.lbl_required = QLabel(f"{self.total_amount:.2f} ج.م")
        self.lbl_required.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.lbl_required.setStyleSheet("color: #e53e3e;")
        form_layout.addRow(QLabel("المبلغ المطلوب:"), self.lbl_required)

        self.cmb_method = QComboBox()
        self.cmb_method.addItems(["نقدي (Cash)", "فيزا / ماستر كارد", "آجل (On Account)"])
        self.cmb_method.setFont(QFont("Segoe UI", 11))
        self.cmb_method.setFixedHeight(35)
        form_layout.addRow(QLabel("طريقة الدفع:"), self.cmb_method)

        self.txt_paid = QLineEdit()
        self.txt_paid.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.txt_paid.setFixedHeight(40)
        self.txt_paid.setStyleSheet("color: #1E90FF; font-weight: bold;")
        self.txt_paid.setText(f"{self.total_amount:.2f}")
        self.txt_paid.textChanged.connect(self.calculate_change)
        form_layout.addRow(QLabel("المبلغ المدفوع:"), self.txt_paid)

        fast_cash_layout = QHBoxLayout()
        fast_cash_layout.setSpacing(8)
        for val in [50, 100, 200, 500]:
            btn_fast = QPushButton(f"+{val}")
            btn_fast.setObjectName("fastCashBtn")
            btn_fast.clicked.connect(lambda checked=False, v=val: self.add_fast_cash(v))
            fast_cash_layout.addWidget(btn_fast)
        form_layout.addRow(QLabel("كاش سريع:"), fast_cash_layout)

        self.lbl_change = QLabel("0.00 ج.م")
        self.lbl_change.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.lbl_change.setStyleSheet("color: #2ed573;")
        form_layout.addRow(QLabel("الباقي للعميل:"), self.lbl_change)

        frame_layout.addLayout(form_layout)
        frame_layout.addSpacing(10)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_confirm = QPushButton("تأكيد وطباعة")
        self.btn_confirm.setFixedHeight(40)
        self.btn_confirm.clicked.connect(self.validate_and_accept)

        self.btn_cancel = QPushButton("إلغاء")
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_confirm, stretch=2)
        btn_layout.addWidget(self.btn_cancel, stretch=1)

        frame_layout.addLayout(btn_layout)
        container_layout.addWidget(main_frame)

        self.txt_paid.setFocus()
        self.txt_paid.selectAll()

    def add_fast_cash(self, value):
        try:
            current = float(self.txt_paid.text()) if self.txt_paid.text() else 0.0
            self.txt_paid.setText(f"{current + value:.2f}")
        except ValueError:
            self.txt_paid.setText(f"{value:.2f}")

    def calculate_change(self):
        try:
            paid = float(self.txt_paid.text()) if self.txt_paid.text() else 0.0
            change = paid - self.total_amount
            if change >= 0:
                self.lbl_change.setText(f"{change:.2f} ج.م")
                self.lbl_change.setStyleSheet("color: #2ed573;")
            else:
                self.lbl_change.setText(f"متبقي: {abs(change):.2f} ج.م")
                self.lbl_change.setStyleSheet("color: #e53e3e;")
        except ValueError:
            self.lbl_change.setText("0.00 ج.م")

    def validate_and_accept(self):
        try:
            paid = float(self.txt_paid.text()) if self.txt_paid.text() else 0.0
            if paid < self.total_amount and self.cmb_method.currentText() != "آجل (On Account)":
                SystemMessageBox.show_warning(self, "المبلغ المدفوع أقل من المطلوب!")
                return
            self.accept()
        except ValueError:
            SystemMessageBox.show_warning(self, "يرجى إدخال مبلغ صحيح!")

    def get_payment_details(self):
        paid = float(self.txt_paid.text()) if self.txt_paid.text() else 0.0
        return {
            "payment_method": self.cmb_method.currentText(),
            "amount_paid": paid,
            "amount_change": max(0.0, paid - self.total_amount)
        }


class CustomQtyInputDialog(QDialog):
    def __init__(self, item_name, current_qty, parent=None):
        super().__init__(parent)
        self.setFixedSize(420, 200)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(20, 20, 20, 15)
        frame_layout.setSpacing(15)

        lbl_title = QLabel(f"تعديل الكمية لـ ({item_name})")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        frame_layout.addWidget(lbl_title)

        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 100000)
        self.spin_qty.setValue(current_qty)
        self.spin_qty.setFont(QFont("Segoe UI", 12))
        self.spin_qty.setFixedHeight(40)
        frame_layout.addWidget(self.spin_qty)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("موافق")
        btn_ok.clicked.connect(self.accept)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()

        frame_layout.addLayout(btn_layout)
        container_layout.addWidget(main_frame)

        self.spin_qty.setFocus()
        self.spin_qty.selectAll()

    def get_value(self):
        return self.spin_qty.value()


class ItemSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_item_data = None

        self.setFixedSize(700, 500)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(20, 20, 20, 15)
        frame_layout.setSpacing(12)

        title = QLabel("بحث عن صنف")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title)

        search_layout = QHBoxLayout()
        lbl_search = QLabel("ابحث:")
        lbl_search.setFont(QFont("Segoe UI", 12, QFont.Bold))

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("اكتب اسم الصنف أو الباركود...")
        self.txt_search.setFont(QFont("Segoe UI", 13))
        self.txt_search.setFixedHeight(40)
        self.txt_search.textChanged.connect(self.load_data)

        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.txt_search)
        frame_layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["الباركود", "اسم الصنف", "الوحدة", "السعر", "المخزون"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.accept_selection)
        self.table.setStyleSheet("""
            QTableWidget { font-size: 14px; alternate-background-color: #f8f9fa; }
            QTableWidget::item:selected {
                background-color: #1e5378;
                color: white;
            }
        """)
        frame_layout.addWidget(self.table)

        self.lbl_count = QLabel("عدد النتائج: 0")
        self.lbl_count.setFont(QFont("Segoe UI", 10))
        self.lbl_count.setStyleSheet("color: #718096;")
        frame_layout.addWidget(self.lbl_count)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_select = QPushButton("إضافة للفاتورة")
        self.btn_select.setFixedHeight(40)
        self.btn_select.clicked.connect(self.accept_selection)

        self.btn_close = QPushButton("إغلاق")
        self.btn_close.setObjectName("cancelBtn")
        self.btn_close.setFixedHeight(40)
        self.btn_close.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_select)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(self.btn_close)
        btn_layout.addStretch()
        frame_layout.addLayout(btn_layout)

        container_layout.addWidget(main_frame)
        self.load_data()
        self.txt_search.setFocus()

    def load_data(self):
        search_text = self.txt_search.text().strip()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            if search_text:
                cursor.execute("""
                    SELECT id, barcode, name, unit, price, qty
                    FROM products
                    WHERE name ILIKE %s OR barcode ILIKE %s
                    ORDER BY name
                """, (f"%{search_text}%", f"%{search_text}%"))
            else:
                cursor.execute("""
                    SELECT id, barcode, name, unit, price, qty
                    FROM products
                    ORDER BY name
                """)

            rows = cursor.fetchall()
            self.table.setRowCount(0)

            for row_idx, row_data in enumerate(rows):
                self.table.insertRow(row_idx)

                display_data = [
                    str(row_data[1] or ""),
                    str(row_data[2] or ""),
                    str(row_data[3] or "قطعة"),
                    f"{float(row_data[4]):.2f}",
                    str(row_data[5] or 0)
                ]

                for col_idx, value in enumerate(display_data):
                    item = QTableWidgetItem(value)
                    item.setFont(QFont("Segoe UI", 12))
                    item.setTextAlignment(Qt.AlignCenter)

                    if col_idx == 4:
                        stock = int(row_data[5]) if row_data[5] else 0
                        if stock <= 0:
                            item.setForeground(QColor("#e53e3e"))
                            item.setText(f"{stock} (نفذ)")
                        elif stock <= 5:
                            item.setForeground(QColor("#e53e3e"))
                        elif stock <= 15:
                            item.setForeground(QColor("#dd6b20"))

                    if col_idx == 0:
                        item.setData(Qt.UserRole, row_data[0])

                    self.table.setItem(row_idx, col_idx, item)

            self.lbl_count.setText(f"عدد النتائج: {len(rows)}")

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"خطأ في البحث: {e}")

    def accept_selection(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            product_id = self.table.item(selected_row, 0).data(Qt.UserRole)
            barcode = self.table.item(selected_row, 0).text()
            name = self.table.item(selected_row, 1).text()
            unit = self.table.item(selected_row, 2).text() or "قطعة"
            price = float(self.table.item(selected_row, 3).text())
            stock_text = self.table.item(selected_row, 4).text().replace(" (نفذ)", "")
            stock = int(stock_text) if stock_text.isdigit() else 0

            if stock <= 0:
                SystemMessageBox.show_warning(self, f"المنتج ({name}) نفذ من المخزن!")
                return

            self.selected_item_data = (product_id, barcode, name, unit, price)
            self.accept()
        else:
            SystemMessageBox.show_warning(self, "اختر صنف من الجدول أولاً!")


class ItemInquiryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(520, 420)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(20, 20, 20, 15)
        frame_layout.setSpacing(15)

        top_layout = QHBoxLayout()
        lbl_scan = QLabel("امسح الباركود:")
        lbl_scan.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.txt_barcode = QLineEdit()
        self.txt_barcode.setPlaceholderText("اضرب الباركود هنا واضغط Enter...")
        self.txt_barcode.setFixedHeight(38)
        self.txt_barcode.returnPressed.connect(self.search_item)

        btn_search = QPushButton("استعلام")
        btn_search.clicked.connect(self.search_item)

        top_layout.addWidget(lbl_scan)
        top_layout.addWidget(self.txt_barcode)
        top_layout.addWidget(btn_search)
        frame_layout.addLayout(top_layout)

        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")

        info_layout = QVBoxLayout(self.info_frame)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(15, 15, 15, 15)

        self.lbl_name = QLabel("اسم الصنف: ---")
        self.lbl_barcode = QLabel("الباركود: ---")
        self.lbl_unit = QLabel("الوحدة: ---")
        self.lbl_price = QLabel("السعر: ---")
        self.lbl_stock = QLabel("المخزون المتاح: ---")

        for lbl in [self.lbl_name, self.lbl_barcode, self.lbl_unit, self.lbl_price, self.lbl_stock]:
            lbl.setFont(QFont("Segoe UI", 13, QFont.Medium))
            lbl.setStyleSheet("color: #4a5568;")
            info_layout.addWidget(lbl)

        self.lbl_price.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.lbl_price.setStyleSheet("color: #2ed573;")

        frame_layout.addWidget(self.info_frame)

        btn_layout = QHBoxLayout()
        btn_close = QPushButton("إغلاق")
        btn_close.setObjectName("cancelBtn")
        btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        frame_layout.addLayout(btn_layout)

        container_layout.addWidget(main_frame)
        self.txt_barcode.setFocus()

    def search_item(self):
        barcode = self.txt_barcode.text().strip()
        if not barcode:
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, barcode, unit, price, qty FROM products WHERE barcode = %s", (barcode,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                name, bc, unit, price, qty = result
                self.lbl_name.setText(f"اسم الصنف: {name}")
                self.lbl_barcode.setText(f"الباركود: {bc}")
                self.lbl_unit.setText(f"الوحدة: {unit or 'قطعة'}")
                self.lbl_price.setText(f"السعر: {float(price):.2f} ج.م")
                self.lbl_stock.setText(f"المخزون المتاح: {qty} {unit or 'قطعة'}")
            else:
                SystemMessageBox.show_warning(self, "هذا الباركود غير مسجل في النظام!")

        except Exception as e:
            SystemMessageBox.show_critical(self, f"فشل الاتصال: {e}")

        self.txt_barcode.clear()
        self.txt_barcode.setFocus()


class ItemReturnDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.return_data = None
        self.setFixedSize(420, 280)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(25, 20, 25, 15)
        frame_layout.setSpacing(12)

        title = QLabel("عملية إرجاع صنف")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        frame_layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.txt_barcode = QLineEdit()
        self.txt_barcode.setPlaceholderText("امسح أو اكتب الباركود...")
        self.txt_barcode.setFixedHeight(38)

        self.txt_qty = QLineEdit()
        self.txt_qty.setText("1")
        self.txt_qty.setAlignment(Qt.AlignCenter)
        self.txt_qty.setFixedHeight(38)

        form_layout.addRow(QLabel("باركود الصنف:"), self.txt_barcode)
        form_layout.addRow(QLabel("الكمية المرتجعة:"), self.txt_qty)
        frame_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("تأكيد المرتجع")
        btn_ok.clicked.connect(self.validate_and_accept)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("cancelBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()

        frame_layout.addLayout(btn_layout)
        container_layout.addWidget(main_frame)

        self.txt_barcode.setFocus()

    def validate_and_accept(self):
        barcode = self.txt_barcode.text().strip()
        qty_str = self.txt_qty.text().strip()

        if not barcode:
            SystemMessageBox.show_warning(self, "برجاء إدخال الباركود!")
            return

        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError()
        except ValueError:
            SystemMessageBox.show_warning(self, "برجاء إدخال كمية صحيحة!")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, unit, price FROM products WHERE barcode = %s", (barcode,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                self.return_data = {
                    'product_id': result[0],
                    'barcode': barcode,
                    'name': result[1],
                    'unit': result[2] or 'قطعة',
                    'price': float(result[3]),
                    'qty': qty
                }
                self.accept()
            else:
                SystemMessageBox.show_warning(self, "هذا الباركود غير موجود!")

        except Exception as e:
            SystemMessageBox.show_critical(self, f"فشل الاتصال: {e}")


class CashierLockDialog(QDialog):
    def __init__(self, user_name="", reason="", parent=None):
        super().__init__(parent)
        self.logout_requested = False
        self.user_name = user_name
        self.reason = reason

        self.setFixedSize(420, 320)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        container = QVBoxLayout(self)
        container.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        title = QLabel("تأمين الخزنة")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1e5378;")
        layout.addWidget(title)

        lbl_user = QLabel(f"المستخدم: {self.user_name}")
        lbl_user.setFont(QFont("Segoe UI", 12))
        lbl_user.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_user)

        lbl_reason = QLabel(self.reason if self.reason else "تم تأمين الشاشة")
        lbl_reason.setFont(QFont("Segoe UI", 11))
        lbl_reason.setAlignment(Qt.AlignCenter)
        lbl_reason.setStyleSheet("color: #718096;")
        layout.addWidget(lbl_reason)

        self.lbl_error = QLabel("")
        self.lbl_error.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setStyleSheet("color: #e53e3e;")
        layout.addWidget(self.lbl_error)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("ادخل كلمة المرور لفك التأمين")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setFixedHeight(42)
        self.input_password.returnPressed.connect(self.accept)
        layout.addWidget(self.input_password)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_unlock = QPushButton("فتح")
        btn_unlock.setFixedSize(120, 42)
        btn_unlock.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; font-weight: bold; border-radius: 20px; }
            QPushButton:hover { background-color: #219a52; }
        """)
        btn_unlock.clicked.connect(self.accept)

        btn_logout = QPushButton("تسجيل خروج")
        btn_logout.setFixedSize(120, 42)
        btn_logout.setStyleSheet("""
            QPushButton { background-color: #e53e3e; color: white; font-weight: bold; border-radius: 20px; }
            QPushButton:hover { background-color: #c53030; }
        """)
        btn_logout.clicked.connect(self.request_logout)

        btn_layout.addWidget(btn_unlock)
        btn_layout.addWidget(btn_logout)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        container.addWidget(main_frame)

        self.input_password.setFocus()

    def request_logout(self):
        self.logout_requested = True
        self.reject()

    def get_password(self):
        return self.input_password.text().strip()

    def set_error(self, text):
        self.lbl_error.setText(text)
        self.input_password.clear()
        self.input_password.setFocus()

class ManagerApprovalDialog(QDialog):
    def __init__(self, action_name="", parent=None):
        super().__init__(parent)
        self.setFixedSize(420, 260)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        container = QVBoxLayout(self)
        container.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)

        title = QLabel("موافقة مدير مطلوبة")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #e53e3e;")
        layout.addWidget(title)

        lbl_action = QLabel(f"العملية المطلوبة: {action_name}")
        lbl_action.setAlignment(Qt.AlignCenter)
        lbl_action.setFont(QFont("Segoe UI", 11))
        layout.addWidget(lbl_action)

        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setStyleSheet("color: #e53e3e; font-weight: bold;")
        layout.addWidget(self.lbl_error)

        form = QFormLayout()
        form.setSpacing(10)

        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("اسم مستخدم المدير")
        self.input_username.setFixedHeight(38)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("كلمة المرور")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setFixedHeight(38)
        self.input_password.returnPressed.connect(self.accept)

        form.addRow("اسم المستخدم:", self.input_username)
        form.addRow("كلمة المرور:", self.input_password)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_ok = QPushButton("اعتماد")
        btn_ok.setFixedSize(120, 42)
        btn_ok.clicked.connect(self.accept)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("cancelBtn")
        btn_cancel.setFixedSize(100, 42)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        container.addWidget(main_frame)
        self.input_username.setFocus()

    def get_credentials(self):
        return self.input_username.text().strip(), self.input_password.text().strip()

    def set_error(self, msg):
        self.lbl_error.setText(msg)
        self.input_password.clear()
        self.input_password.setFocus()

class POSWindow(QMainWindow):
    def __init__(self, user_data=None):
        super().__init__()

        self.session = user_data if user_data else {
            "id": 1,
            "full_name": "مدير النظام",
            "pos_id": 1,
            "pos_name": "نقطة البيع 1"
        }

        self.held_invoices = []
        self.return_mode = False
        self.return_original_sale_id = None
        self.return_invoice_barcode = None
        self.return_allowed_products = {}
        self.invoice_discount = 0.0
        self.is_locked = False
        self.auto_lock_minutes = 1

        self.setWindowTitle("شاشة الكاشير الذكية")
        self.setGeometry(50, 50, 1280, 720)
        self.showMaximized()
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(MODERN_STYLE)

        self.init_ui()
        self.connect_buttons()
        self.setup_keyboard_shortcuts()
        self.get_next_invoice_id()
        self.start_live_clock()
        self.setup_auto_lock()

        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

    # ==============================
    # Helpers
    # ==============================
    def get_open_shift_id(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id
                FROM shifts
                WHERE cashier_name = %s AND status = 'مفتوحة'
                ORDER BY id DESC
                LIMIT 1
            """, (self.session.get('full_name', ''),))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row[0] if row else None
        except Exception:
            return None

    def update_mode_label(self):
        if self.return_mode:
            self.lbl_mode.setText(f"الوضع: مرتجع | فاتورة: {self.return_invoice_barcode}")
            self.lbl_mode.setStyleSheet("color: #c0392b; font-weight: bold; border: none; padding-left: 5px;")
        else:
            self.lbl_mode.setText("الوضع: بيع عادي")
            self.lbl_mode.setStyleSheet("color: #333333; font-weight: bold; border: none; padding-left: 5px;")

    def clear_return_mode(self):
        self.return_mode = False
        self.return_original_sale_id = None
        self.return_invoice_barcode = None
        self.return_allowed_products = {}
        self.invoice_discount = 0.0
        self.update_mode_label()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        master_layout = QHBoxLayout(main_widget)
        master_layout.setContentsMargins(10, 10, 10, 10)
        master_layout.setSpacing(10)

        # الشريط الجانبي
        sidebar = QFrame()
        sidebar.setFixedWidth(205)
        sidebar.setStyleSheet("background-color: #ffffff; border: 1px solid #d3d3d3; border-radius: 4px;")

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(8)

        self.lbl_pos = QLabel(f"POS: {self.session.get('pos_name', 'الرئيسية')}")
        self.lbl_user = QLabel(f"User: {self.session.get('full_name', '')}")
        self.lbl_trans = QLabel("Trans: ...")
        self.lbl_date = QLabel()
        self.lbl_mode = QLabel("الوضع: بيع عادي")
    
        for lbl in [self.lbl_pos, self.lbl_user, self.lbl_trans, self.lbl_date, self.lbl_mode]:
            self.lbl_subtotal_info = QLabel("قبل الخصم: 0.00 ج.م")
            self.lbl_subtotal_info.setFont(QFont("Segoe UI", 10))
            self.lbl_subtotal_info.setStyleSheet("color: #555; border: none; padding-left: 5px;")
            sidebar_layout.addWidget(self.lbl_subtotal_info)

            self.lbl_invoice_discount_info = QLabel("خصم الفاتورة: 0.00 ج.م")
            self.lbl_invoice_discount_info.setFont(QFont("Segoe UI", 10))
            self.lbl_invoice_discount_info.setStyleSheet("color: #c0392b; border: none; padding-left: 5px;")
            sidebar_layout.addWidget(self.lbl_invoice_discount_info)
            lbl.setFont(QFont('Segoe UI', 10, QFont.Bold))
            lbl.setStyleSheet("color: #333333; border: none; padding-left: 5px;")
            sidebar_layout.addWidget(lbl)

        sidebar_layout.addSpacing(10)

        button_style = """
            QPushButton {
                background-color: #1e5378;
                color: white;
                font-family: 'Segoe UI';
                font-size: 15px;
                font-weight: bold;
                border-radius: 20px;
                padding: 16px;
                border: none;
            }
            QPushButton:hover { background-color: #163f5c; }
        """

        self.btn_save = QPushButton("حفظ الفاتورة")
        self.btn_search_item = QPushButton("بحث عن صنف")
        self.btn_cancel_invoice = QPushButton("إلغاء الفاتورة")

        for btn in [self.btn_save, self.btn_search_item, self.btn_cancel_invoice]:
            btn.setStyleSheet(button_style)
            btn.setCursor(Qt.PointingHandCursor)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addSpacing(5)

        self.btn_functions = QPushButton("وظائف أخرى ▼")
        self.btn_functions.setStyleSheet("""
            QPushButton {
                background-color: #1e5378;
                color: white;
                font-family: 'Segoe UI';
                font-size: 15px;
                font-weight: bold;
                border-radius: 20px;
                padding: 16px;
                border: none;
            }
            QPushButton:hover { background-color: #163f5c; }
            QPushButton::menu-indicator { image: none; }
        """)
        self.btn_functions.setCursor(Qt.PointingHandCursor)

        self.functions_menu = QMenu(self)
        self.functions_menu.setLayoutDirection(Qt.RightToLeft)
        self.functions_menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 2px solid #1e5378;
                border-radius: 10px;
                padding: 8px;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QMenu::item {
                padding: 12px 25px;
                border-radius: 6px;
                color: #333333;
                font-weight: bold;
            }
            QMenu::item:selected {
                background-color: #1e5378;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e0e0e0;
                margin: 5px 10px;
            }
        """)

        self.act_edit_qty = self.functions_menu.addAction("تعديل الكمية          *")
        self.act_delete_item = self.functions_menu.addAction("حذف صنف            Del")
        self.functions_menu.addSeparator()

        self.act_item_discount = self.functions_menu.addAction("خصم على صنف        F2")
        self.act_invoice_discount = self.functions_menu.addAction("خصم على الفاتورة   F9")

        self.act_return_item = self.functions_menu.addAction("مرتجع صنف           F4")
        self.act_inquire_item = self.functions_menu.addAction("استعلام عن صنف      F1")
        self.functions_menu.addSeparator()

        self.act_hold_invoice = self.functions_menu.addAction("تعليق فاتورة         F5")
        self.act_recall_invoice = self.functions_menu.addAction("استرجاع فاتورة       F6")
        self.functions_menu.addSeparator()

        self.act_reprint = self.functions_menu.addAction("إعادة طباعة فاتورة    F7")
        self.functions_menu.addSeparator()

        self.act_close_shift = self.functions_menu.addAction("جرد وتقفيل الوردية   F8")
        self.functions_menu.addSeparator()

        self.act_cash_in = self.functions_menu.addAction("إضافة نقدية          F10")
        self.act_cash_out = self.functions_menu.addAction("سحب نقدية            F11")
        self.functions_menu.addSeparator()

        self.act_lock_cashier = self.functions_menu.addAction("تأمين الخزنة        F12")

        self.btn_functions.setMenu(self.functions_menu)
        sidebar_layout.addWidget(self.btn_functions)

        sidebar_layout.addStretch()
        master_layout.addWidget(sidebar, stretch=1)

        # الجزء الأيمن
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setSpacing(10)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(8)
        self.sales_table.setHorizontalHeaderLabels([
            "الباركود", "اسم الصنف", "الوحدة", "السعر", "الكمية", "الخصم", "الإجمالي", "ID"
        ])
        self.sales_table.setColumnWidth(0, 180)
        self.sales_table.setColumnWidth(1, 300)
        self.sales_table.setColumnWidth(2, 100)
        self.sales_table.setColumnWidth(3, 100)
        self.sales_table.setColumnWidth(4, 100)
        self.sales_table.setColumnWidth(5, 100)
        self.sales_table.setColumnWidth(6, 120)
        self.sales_table.setColumnHidden(7, True)
        self.sales_table.horizontalHeader().setStretchLastSection(True)
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sales_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sales_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sales_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 3px solid #dcdcdc;
                gridline-color: #f0f0f0;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #4a5568;
                font-weight: 600;
                font-size: 13px;
                padding: 9px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #1e5378;
                color: white;
            }
        """)
        right_panel_layout.addWidget(self.sales_table, stretch=9)

        bottom_bar = QFrame()
        bottom_bar.setFixedHeight(65)
        bottom_bar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #d3d3d3;
                border-radius: 4px;
            }
            QLabel {
                font-size: 15px;
                font-weight: bold;
                border: none;
                color: #333333;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 15px;
                background-color: #ffffff;
            }
        """)

        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(15, 0, 15, 0)
        bottom_layout.setSpacing(15)

        bottom_layout.addWidget(QLabel("الباركود:"))
        self.txt_barcode = QLineEdit()
        self.txt_barcode.setPlaceholderText("اضرب الباركود هنا واضغط Enter...")
        self.txt_barcode.setMinimumWidth(300)
        bottom_layout.addWidget(self.txt_barcode)

        bottom_layout.addWidget(QLabel("العدد:"))
        self.txt_count = QLineEdit()
        self.txt_count.setText("0")
        self.txt_count.setAlignment(Qt.AlignCenter)
        self.txt_count.setFixedWidth(200)
        self.txt_count.setReadOnly(True)
        bottom_layout.addWidget(self.txt_count)

        bottom_layout.addStretch()
        bottom_layout.addWidget(QLabel("الإجمالي:"))

        self.lbl_total_box = QLabel("0.00")
        self.lbl_total_box.setFont(QFont('Segoe UI', 16, QFont.Bold))
        self.lbl_total_box.setAlignment(Qt.AlignCenter)
        self.lbl_total_box.setFixedWidth(200)
        self.lbl_total_box.setStyleSheet("""
            QLabel {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #bcbcbc;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        bottom_layout.addWidget(self.lbl_total_box)

        right_panel_layout.addWidget(bottom_bar, stretch=1)
        master_layout.addLayout(right_panel_layout, stretch=4)

        self.txt_barcode.setFocus()

    def connect_buttons(self):
        self.btn_save.clicked.connect(self.on_open_payment_screen)
        self.act_item_discount.triggered.connect(self.on_item_discount)
        self.act_invoice_discount.triggered.connect(self.on_invoice_discount)
        self.btn_search_item.clicked.connect(self.on_search_item)
        self.btn_cancel_invoice.clicked.connect(self.on_cancel_invoice)
        self.txt_barcode.returnPressed.connect(self.on_barcode_scanned)

        self.act_edit_qty.triggered.connect(self.on_edit_quantity)
        self.act_delete_item.triggered.connect(self.on_delete_item)
        self.act_return_item.triggered.connect(self.on_return_item)
        self.act_inquire_item.triggered.connect(self.on_inquire_item)
        self.act_hold_invoice.triggered.connect(self.on_hold_invoice)
        self.act_recall_invoice.triggered.connect(self.on_recall_invoice)
        self.act_reprint.triggered.connect(self.on_reprint_invoice)
        self.act_close_shift.triggered.connect(self.on_close_shift)
        self.act_cash_in.triggered.connect(self.on_cash_in)
        self.act_cash_out.triggered.connect(self.on_cash_out)
        self.act_lock_cashier.triggered.connect(self.on_lock_cashier)

    def setup_keyboard_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.on_open_payment_screen)
        QShortcut(QKeySequence("F2"), self).activated.connect(self.on_item_discount)
        QShortcut(QKeySequence("F9"), self).activated.connect(self.on_invoice_discount)
        QShortcut(QKeySequence("*"), self).activated.connect(self.on_edit_quantity)
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.on_delete_item)
        QShortcut(QKeySequence("Shift+Return"), self).activated.connect(self.on_cancel_invoice)
        QShortcut(QKeySequence("F3"), self).activated.connect(self.on_search_item)
        QShortcut(QKeySequence("F4"), self).activated.connect(self.on_return_item)
        QShortcut(QKeySequence("F1"), self).activated.connect(self.on_inquire_item)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.on_hold_invoice)
        QShortcut(QKeySequence("F6"), self).activated.connect(self.on_recall_invoice)
        QShortcut(QKeySequence("F7"), self).activated.connect(self.on_reprint_invoice)
        QShortcut(QKeySequence("F8"), self).activated.connect(self.on_close_shift)
        QShortcut(QKeySequence("F10"), self).activated.connect(self.on_cash_in)
        QShortcut(QKeySequence("F11"), self).activated.connect(self.on_cash_out)
        QShortcut(QKeySequence("F12"), self).activated.connect(self.on_lock_cashier)

    def start_live_clock(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_live_clock)
        self.timer.start(1000)
        self.update_live_clock()

    def update_live_clock(self):
        self.lbl_date.setText(QDateTime.currentDateTime().toString("dd-MM-yyyy hh:mm:ss"))

    def get_next_invoice_id(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM sales;")
            self.lbl_trans.setText(f"Trans: {cursor.fetchone()[0]}")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error: {e}")

    def update_invoice_totals(self):
        row_count = self.sales_table.rowCount()
        total_items = 0
        subtotal = 0.0

        for row in range(row_count):
            try:
                qty = int(self.sales_table.item(row, 4).text())
                total_items += abs(qty)
                subtotal += float(self.sales_table.item(row, 6).text())
            except Exception:
                pass

        # لو خصم الفاتورة أكبر من الإجمالي، نقصّه
        if self.invoice_discount > subtotal:
            self.invoice_discount = subtotal

        grand_total = max(subtotal - self.invoice_discount, 0.0)

        self.txt_count.setText(str(total_items))
        self.lbl_total_box.setText(f"{grand_total:.2f}")

        if hasattr(self, "lbl_subtotal_info"):
            self.lbl_subtotal_info.setText(f"قبل الخصم: {subtotal:.2f} ج.م")

        if hasattr(self, "lbl_invoice_discount_info"):
            self.lbl_invoice_discount_info.setText(f"خصم الفاتورة: {self.invoice_discount:.2f} ج.م")

    def add_item_to_table(self, product_id, barcode, item_name, unit, price, discount=0.0, qty=1, is_return=False):
        row_count = self.sales_table.rowCount()

        for row in range(row_count):
            if self.sales_table.item(row, 0).text() == barcode:
                existing_qty = int(self.sales_table.item(row, 4).text())
                existing_discount = float(self.sales_table.item(row, 5).text())

                if (is_return and existing_qty < 0) or (not is_return and existing_qty > 0):
                    new_qty = existing_qty + (-qty if is_return else qty)
                    self.sales_table.item(row, 4).setText(str(new_qty))

                    new_total = (price * new_qty) - existing_discount
                    self.sales_table.item(row, 6).setText(f"{new_total:.2f}")
                    self.update_invoice_totals()
                    return

        self.sales_table.insertRow(row_count)
        final_qty = -qty if is_return else qty
        total_price = (price * final_qty) - discount

        data = [
            barcode,
            item_name,
            unit,
            f"{price:.2f}",
            str(final_qty),
            f"{discount:.2f}",
            f"{total_price:.2f}",
            str(product_id)
        ]

        for i in range(8):
            item = QTableWidgetItem(data[i])
            item.setFont(QFont("Segoe UI", 14))
            item.setTextAlignment(Qt.AlignCenter)
            if is_return and i == 1:
                item.setForeground(QColor("#e53e3e"))
            self.sales_table.setItem(row_count, i, item)

        self.update_invoice_totals()

    def write_audit(self, action, details):
        try:
            from gui.shift_manager import log_audit
        except ImportError:
            from shift_manager import log_audit

        try:
            log_audit(action, details, self.session.get("full_name", ""))
        except Exception:
            pass

    def calculate_subtotal(self):
        subtotal = 0.0
        for row in range(self.sales_table.rowCount()):
            try:
                subtotal += float(self.sales_table.item(row, 6).text())
            except Exception:
                pass
        return subtotal

    def request_manager_approval(self, action_name):
        # المدير أو المشرف يمر مباشرة
        if self.session.get("role") in ("admin", "supervisor"):
            return True

        while True:
            dialog = ManagerApprovalDialog(action_name, self)
            result = dialog.exec()

            if result != QDialog.Accepted:
                return False

            username, password = dialog.get_credentials()
            if not username or not password:
                dialog.set_error("ادخل اسم المستخدم وكلمة المرور")
                continue

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT password, full_name, role
                    FROM users
                    WHERE username = %s
                """, (username,))
                row = cursor.fetchone()
                cursor.close()
                conn.close()

                if not row:
                    dialog.set_error("المستخدم غير موجود")
                    continue

                stored_password, manager_name, role = row

                if role not in ("admin", "supervisor"):
                    dialog.set_error("هذا المستخدم لا يملك صلاحية الاعتماد")
                    continue

                if bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
                    self.write_audit(
                        "اعتماد مدير",
                        f"اعتماد عملية: {action_name} بواسطة {manager_name}"
                    )
                    return True
                else:
                    dialog.set_error("كلمة المرور غير صحيحة")

            except Exception as e:
                SystemMessageBox.show_critical(self, f"خطأ أثناء التحقق: {e}")
                return False

    def handle_return_barcode(self, barcode):
        if barcode not in self.return_allowed_products:
            SystemMessageBox.show_warning(self, "هذا الصنف غير موجود في الفاتورة الأصلية أو غير متاح للمرتجع")
            return

        item = self.return_allowed_products[barcode]

        current_return_qty = 0
        for row in range(self.sales_table.rowCount()):
            if self.sales_table.item(row, 0).text() == barcode:
                current_return_qty = abs(int(self.sales_table.item(row, 4).text()))
                break

        if current_return_qty >= item["available_qty"]:
            SystemMessageBox.show_warning(
                self,
                f"تم الوصول لأقصى كمية مرتجعة مسموحة من هذا الصنف\nالمتاح: {item['available_qty']}"
            )
            return

        self.add_item_to_table(
            item["product_id"],
            item["barcode"],
            f"[مرتجع] {item['name']}",
            item["unit"],
            item["price"],
            discount=0.0,
            qty=1,
            is_return=True
        )

        self.reset_inactivity_timer()

    # ==============================
    # وظائف البيع
    # ==============================
    def on_barcode_scanned(self):
        barcode = self.txt_barcode.text().strip()
        if not barcode:
            return

        if self.return_mode:
            self.handle_return_barcode(barcode)
            self.txt_barcode.clear()
            self.txt_barcode.setFocus()
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, unit, price, qty FROM products WHERE barcode = %s",
                (barcode,)
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                if result[4] <= 0:
                    SystemMessageBox.show_warning(self, f"المنتج ({result[1]}) نفذ من المخزن!")
                else:
                    self.add_item_to_table(result[0], barcode, result[1], result[2] or 'قطعة', float(result[3]))
            else:
                SystemMessageBox.show_warning(self, "هذا الباركود غير مسجل في النظام!")

        except Exception as e:
            SystemMessageBox.show_critical(self, f"خطأ: {e}")

        self.txt_barcode.clear()
        self.txt_barcode.setFocus()

    def on_search_item(self):
        dialog = ItemSearchDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_item_data:
            product_id, barcode, name, unit, price = dialog.selected_item_data
            self.add_item_to_table(product_id, barcode, name, unit, price)
        self.reset_inactivity_timer()
        self.txt_barcode.setFocus()

    def on_inquire_item(self):
        ItemInquiryDialog(self).exec()
        self.reset_inactivity_timer()
        self.txt_barcode.setFocus()

    def on_return_item(self):
        if self.sales_table.rowCount() > 0:
            result = SystemMessageBox.show_question(
                self,
                "يوجد أصناف في الشاشة الحالية.\nهل تريد إلغاؤها والبدء في مرتجع جديد؟"
            )
            if result != QDialog.Accepted:
                return

            self.sales_table.setRowCount(0)
            self.invoice_discount = 0.0
            self.update_invoice_totals()

        invoice_barcode, ok = QInputDialog.getText(
            self,
            "مرتجع فاتورة",
            "امسح أو اكتب باركود الفاتورة الأصلية:"
        )

        if not ok or not invoice_barcode.strip():
            return

        self.start_return_mode(invoice_barcode.strip())
        self.reset_inactivity_timer()
        self.txt_barcode.setFocus()

    def start_return_mode(self, invoice_barcode):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, payment_method
                FROM sales
                WHERE invoice_barcode = %s
                  AND invoice_type = 'sale'
            """, (invoice_barcode,))
            sale_row = cursor.fetchone()

            if not sale_row:
                cursor.close()
                conn.close()
                SystemMessageBox.show_warning(self, "الفاتورة الأصلية غير موجودة")
                return

            sale_id = sale_row[0]

            cursor.execute("""
                SELECT
                    p.id,
                    p.barcode,
                    p.name,
                    p.unit,
                    si.unit_price,
                    SUM(si.quantity) AS sold_qty,
                    COALESCE((
                        SELECT ABS(SUM(rsi.quantity))
                        FROM sale_items rsi
                        JOIN sales rs ON rs.id = rsi.sale_id
                        WHERE rs.original_sale_id = %s
                          AND rs.invoice_type = 'return'
                          AND rsi.product_id = p.id
                    ), 0) AS returned_qty
                FROM sale_items si
                JOIN products p ON p.id = si.product_id
                WHERE si.sale_id = %s
                GROUP BY p.id, p.barcode, p.name, p.unit, si.unit_price
                ORDER BY p.name
            """, (sale_id, sale_id))

            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            allowed = {}
            for row in rows:
                product_id, barcode, name, unit, price, sold_qty, returned_qty = row
                available_qty = int(sold_qty or 0) - int(returned_qty or 0)
                if available_qty > 0:
                    allowed[barcode] = {
                        "product_id": product_id,
                        "barcode": barcode,
                        "name": name,
                        "unit": unit or "قطعة",
                        "price": float(price or 0),
                        "available_qty": available_qty
                    }

            if not allowed:
                SystemMessageBox.show_warning(self, "كل أصناف هذه الفاتورة تم إرجاعها بالفعل")
                return

            self.return_mode = True
            self.return_original_sale_id = sale_id
            self.return_invoice_barcode = invoice_barcode
            self.return_allowed_products = allowed
            self.sales_table.setRowCount(0)
            self.invoice_discount = 0.0
            self.update_mode_label()
            self.update_invoice_totals()

            SystemMessageBox.show_success(
                self,
                f"تم تفعيل وضع المرتجع\nالفاتورة: {invoice_barcode}\nابدأ بضرب أصناف الفاتورة المرتجعة"
            )

        except Exception as e:
            SystemMessageBox.show_critical(self, f"خطأ أثناء تحميل الفاتورة الأصلية: {e}")

    def on_edit_quantity(self):
        selected_row = self.sales_table.currentRow()
        if selected_row < 0:
            SystemMessageBox.show_warning(self, "حدد صنفاً أولاً!")
            return

        if not self.request_manager_approval("تعديل كمية صنف"):
            return

        current_qty = abs(int(self.sales_table.item(selected_row, 4).text()))
        item_name = self.sales_table.item(selected_row, 1).text()
        is_return = int(self.sales_table.item(selected_row, 4).text()) < 0
        old_qty = int(self.sales_table.item(selected_row, 4).text())

        dialog = CustomQtyInputDialog(item_name, current_qty, self)
        if dialog.exec() == QDialog.Accepted:
            new_qty = dialog.get_value()
            final_qty = -new_qty if is_return else new_qty

            self.sales_table.item(selected_row, 4).setText(str(final_qty))
            price = float(self.sales_table.item(selected_row, 3).text())
            discount = float(self.sales_table.item(selected_row, 5).text())
            self.sales_table.item(selected_row, 6).setText(f"{((price * final_qty) - discount):.2f}")

            self.update_invoice_totals()
            self.write_audit(
                "تعديل كمية",
                f"الصنف: {item_name} | من {old_qty} إلى {final_qty}"
            )
            self.reset_inactivity_timer()

    def on_delete_item(self):
        selected_row = self.sales_table.currentRow()
        if selected_row < 0:
            SystemMessageBox.show_warning(self, "حدد صنفاً لحذفه!")
            return

        if not self.request_manager_approval("حذف صنف من الفاتورة"):
            return

        item_name = self.sales_table.item(selected_row, 1).text()
        qty = self.sales_table.item(selected_row, 4).text()
        total = self.sales_table.item(selected_row, 6).text()

        self.sales_table.removeRow(selected_row)

        if self.sales_table.rowCount() == 0:
            self.invoice_discount = 0.0

        self.update_invoice_totals()
        self.write_audit(
            "حذف صنف",
            f"الصنف: {item_name} | الكمية: {qty} | الإجمالي: {total}"
        )
        self.reset_inactivity_timer()

    def on_cancel_invoice(self):
        if self.sales_table.rowCount() == 0 and not self.return_mode:
            return

        if SystemMessageBox.show_question(self, "هل أنت متأكد من إلغاء الفاتورة؟") == QDialog.Accepted:
            self.sales_table.setRowCount(0)
            self.invoice_discount = 0.0
            self.clear_return_mode()
            self.update_invoice_totals()
            self.reset_inactivity_timer()

    def save_return_invoice(self):
        if self.sales_table.rowCount() == 0:
            SystemMessageBox.show_warning(self, "لا توجد أصناف مرتجعة")
            return

        if not self.return_original_sale_id:
            SystemMessageBox.show_warning(self, "الفاتورة الأصلية غير محددة")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            shift_row = None
            cursor.execute("""
                SELECT id
                FROM shifts
                WHERE cashier_name = %s AND status = 'مفتوحة'
                ORDER BY id DESC LIMIT 1
            """, (self.session.get('full_name', ''),))
            shift_row = cursor.fetchone()

            if not shift_row:
                cursor.close()
                conn.close()
                SystemMessageBox.show_warning(self, "لا توجد وردية مفتوحة! لا يمكن تنفيذ المرتجع")
                return

            shift_id = shift_row[0]

            subtotal_amount = self.calculate_subtotal()  # هيكون بالسالب
            total_amount = subtotal_amount

            cursor.execute("""
                INSERT INTO sales (
                    subtotal, invoice_discount, total_amount, net_amount,
                    payment_method, amount_paid, amount_change,
                    shift_id, invoice_type, original_sale_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'return', %s)
                RETURNING id
            """, (
                subtotal_amount,
                0.0,
                total_amount,
                total_amount,
                "مرتجع",
                0.0,
                0.0,
                shift_id,
                self.return_original_sale_id
            ))
            sale_id = cursor.fetchone()[0]

            return_barcode = f"RTN{sale_id:08d}"
            cursor.execute("""
                UPDATE sales
                SET invoice_barcode = %s
                WHERE id = %s
            """, (return_barcode, sale_id))

            for row in range(self.sales_table.rowCount()):
                p_id = int(self.sales_table.item(row, 7).text())
                price = float(self.sales_table.item(row, 3).text())
                qty = int(self.sales_table.item(row, 4).text())  # بالسالب
                discount = float(self.sales_table.item(row, 5).text())

                cursor.execute("""
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, discount)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sale_id, p_id, qty, price, discount))

                # المرتجع يزيد المخزون
                cursor.execute(
                    "UPDATE products SET qty = qty + %s WHERE id = %s;",
                    (abs(qty), p_id)
                )

            conn.commit()
            cursor.close()
            conn.close()

            self.write_audit(
                "حفظ فاتورة مرتجع",
                f"مرتجع رقم {sale_id} | الفاتورة الأصلية: {self.return_original_sale_id} | الإجمالي: {abs(total_amount):.2f}"
            )

            SystemMessageBox.show_success(
                self,
                f"تم حفظ المرتجع بنجاح\nرقم المرتجع: {sale_id}\nباركود المرتجع: {return_barcode}"
            )

            self.sales_table.setRowCount(0)
            self.clear_return_mode()
            self.update_invoice_totals()
            self.get_next_invoice_id()
            self.reset_inactivity_timer()

        except Exception as e:
            SystemMessageBox.show_critical(self, f"فشل حفظ المرتجع: {e}")

    def on_open_payment_screen(self):
        if self.return_mode:
            self.save_return_invoice()
            return

        if self.sales_table.rowCount() == 0:
            SystemMessageBox.show_warning(self, "الفاتورة فارغة!")
            return

        subtotal_amount = self.calculate_subtotal()
        total_amount = max(subtotal_amount - self.invoice_discount, 0.0)

        pay_dialog = PaymentDialog(total_amount, self)

        if pay_dialog.exec() != QDialog.Accepted:
            return

        pay_details = pay_dialog.get_payment_details()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id
                FROM shifts
                WHERE cashier_name = %s AND status = 'مفتوحة'
                ORDER BY id DESC LIMIT 1
            """, (self.session.get('full_name', ''),))
            shift_row = cursor.fetchone()

            if not shift_row:
                cursor.close()
                conn.close()
                SystemMessageBox.show_warning(self, "لا توجد وردية مفتوحة! لا يمكن البيع قبل فتح الوردية.")
                return

            shift_id = shift_row[0]

            cursor.execute("""
                INSERT INTO sales (
                    subtotal, invoice_discount, total_amount, net_amount,
                    payment_method, amount_paid, amount_change, shift_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                subtotal_amount,
                self.invoice_discount,
                total_amount,
                total_amount,
                pay_details["payment_method"],
                pay_details["amount_paid"],
                pay_details["amount_change"],
                shift_id
            ))
            sale_id = cursor.fetchone()[0]
            invoice_barcode = f"INV{sale_id:08d}"
            cursor.execute("""
                UPDATE sales
                SET invoice_barcode = %s
                WHERE id = %s
            """, (invoice_barcode, sale_id))

            for row in range(self.sales_table.rowCount()):
                p_id = int(self.sales_table.item(row, 7).text())
                price = float(self.sales_table.item(row, 3).text())
                qty = int(self.sales_table.item(row, 4).text())
                discount = float(self.sales_table.item(row, 5).text())

                cursor.execute("""
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, discount)
                    VALUES (%s, %s, %s, %s, %s);
                """, (sale_id, p_id, qty, price, discount))

                cursor.execute(
                    "UPDATE products SET qty = qty - %s WHERE id = %s;",
                    (qty, p_id)
                )

            conn.commit()
            cursor.close()
            conn.close()

            if print_receipt:
                receipt_items = []
                for row in range(self.sales_table.rowCount()):
                    receipt_items.append({
                        "name": self.sales_table.item(row, 1).text(),
                        "qty": int(self.sales_table.item(row, 4).text()),
                        "price": float(self.sales_table.item(row, 3).text()),
                        "total": float(self.sales_table.item(row, 6).text())
                    })
                try:
                    print_receipt(
                        sale_id,
                        receipt_items,
                        total_amount,
                        pay_details,
                        self.session.get('full_name', ''),
                        invoice_barcode=invoice_barcode,
                        invoice_type="sale"
                    )
                except Exception as e:
                    print(f"خطأ في الطباعة: {e}")

            self.write_audit(
                "حفظ فاتورة",
                f"فاتورة رقم {sale_id} | قبل الخصم: {subtotal_amount:.2f} | خصم الفاتورة: {self.invoice_discount:.2f} | الصافي: {total_amount:.2f}"
            )

            SystemMessageBox.show_success(
                self,
                f"تم حفظ الفاتورة رقم ({sale_id})\n"
                f"طريقة الدفع: {pay_details['payment_method']}\n"
                f"الباقي للعميل: {pay_details['amount_change']:.2f} ج.م"
            )

            self.sales_table.setRowCount(0)
            self.invoice_discount = 0.0
            self.update_invoice_totals()
            self.get_next_invoice_id()
            self.reset_inactivity_timer()

        except Exception as e:
            SystemMessageBox.show_critical(self, f"فشل الحفظ: {e}")

    # ==============================
    # تعليق / استرجاع
    # ==============================
    def on_hold_invoice(self):
        if self.sales_table.rowCount() == 0:
            SystemMessageBox.show_warning(self, "الفاتورة فارغة! مفيش حاجة للتعليق.")
            return

        invoice_items = []
        for row in range(self.sales_table.rowCount()):
            invoice_items.append({
                "barcode": self.sales_table.item(row, 0).text(),
                "name": self.sales_table.item(row, 1).text(),
                "unit": self.sales_table.item(row, 2).text(),
                "price": self.sales_table.item(row, 3).text(),
                "qty": self.sales_table.item(row, 4).text(),
                "discount": self.sales_table.item(row, 5).text(),
                "total": self.sales_table.item(row, 6).text(),
                "product_id": self.sales_table.item(row, 7).text()
            })

        total = self.lbl_total_box.text()
        hold_time = QDateTime.currentDateTime().toString("hh:mm:ss")

        self.held_invoices.append({
            "items": invoice_items,
            "total": total,
            "time": hold_time,
            "invoice_discount": self.invoice_discount
        })

        self.sales_table.setRowCount(0)
        self.update_invoice_totals()

        SystemMessageBox.show_success(
            self,
            f"تم تعليق الفاتورة بنجاح\n"
            f"عدد الأصناف: {len(invoice_items)}\n"
            f"الإجمالي: {total} ج.م\n"
            f"عدد الفواتير المعلقة: {len(self.held_invoices)}"
        )
        self.reset_inactivity_timer()
        self.txt_barcode.setFocus()

    def on_recall_invoice(self):
        if not self.held_invoices:
            SystemMessageBox.show_warning(self, "لا توجد فواتير معلقة!")
            return

        if self.sales_table.rowCount() > 0:
            result = SystemMessageBox.show_question(
                self,
                "يوجد أصناف في الفاتورة الحالية.\nهل تريد تعليقها واسترجاع الفاتورة المعلقة؟"
            )
            if result != QDialog.Accepted:
                return
            self.on_hold_invoice()

        if len(self.held_invoices) == 1:
            self.restore_invoice(0)
            return

        dialog = QDialog(self)
        dialog.setFixedSize(450, 350)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setLayoutDirection(Qt.RightToLeft)

        container_layout = QVBoxLayout(dialog)
        container_layout.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(20, 20, 20, 15)
        frame_layout.setSpacing(12)

        title = QLabel(f"الفواتير المعلقة ({len(self.held_invoices)})")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["الوقت", "عدد الأصناف", "الإجمالي"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setRowCount(len(self.held_invoices))

        for i, inv in enumerate(self.held_invoices):
            table.setItem(i, 0, QTableWidgetItem(inv["time"]))
            table.setItem(i, 1, QTableWidgetItem(str(len(inv["items"]))))
            table.setItem(i, 2, QTableWidgetItem(f"{inv['total']} ج.م"))
            for col in range(3):
                table.item(i, col).setFont(QFont("Segoe UI", 12))
                table.item(i, col).setTextAlignment(Qt.AlignCenter)

        table.doubleClicked.connect(lambda: self.select_held_invoice(table, dialog))
        frame_layout.addWidget(table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_select = QPushButton("استرجاع")
        btn_select.clicked.connect(lambda: self.select_held_invoice(table, dialog))

        btn_delete = QPushButton("حذف")
        btn_delete.setObjectName("cancelBtn")
        btn_delete.clicked.connect(lambda: self.delete_held_invoice(table, dialog))

        btn_close = QPushButton("إغلاق")
        btn_close.setObjectName("cancelBtn")
        btn_close.clicked.connect(dialog.reject)

        btn_layout.addWidget(btn_select)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()

        frame_layout.addLayout(btn_layout)
        container_layout.addWidget(main_frame)

        dialog.exec()
        self.reset_inactivity_timer()
        self.txt_barcode.setFocus()

    def select_held_invoice(self, table, dialog):
        selected_row = table.currentRow()
        if selected_row >= 0:
            dialog.close()
            self.restore_invoice(selected_row)
        else:
            SystemMessageBox.show_warning(self, "اختر فاتورة أولاً!")

    def delete_held_invoice(self, table, dialog):
        selected_row = table.currentRow()
        if selected_row >= 0:
            result = SystemMessageBox.show_question(self, "هل تريد حذف هذه الفاتورة المعلقة؟")
            if result == QDialog.Accepted:
                del self.held_invoices[selected_row]
                table.removeRow(selected_row)
                if len(self.held_invoices) == 0:
                    dialog.close()
        else:
            SystemMessageBox.show_warning(self, "اختر فاتورة أولاً!")



    def restore_invoice(self, index):
        invoice = self.held_invoices[index]
        self.sales_table.setRowCount(0)

        for item in invoice["items"]:
            row = self.sales_table.rowCount()
            self.sales_table.insertRow(row)

            data = [
                item["barcode"], item["name"], item["unit"],
                item["price"], item["qty"], item["discount"],
                item["total"], item["product_id"]
            ]

            for col, value in enumerate(data):
                cell = QTableWidgetItem(str(value))
                cell.setFont(QFont("Segoe UI", 14))
                self.sales_table.setItem(row, col, cell)

        del self.held_invoices[index]
        self.invoice_discount = float(invoice.get("invoice_discount", 0.0))
        self.update_invoice_totals()
        self.reset_inactivity_timer()

        SystemMessageBox.show_success(
            self,
            f"تم استرجاع الفاتورة\nالفواتير المعلقة المتبقية: {len(self.held_invoices)}"
        )

    # ==============================
    # إعادة طباعة
    # ==============================
    def on_reprint_invoice(self):
        dialog = QDialog(self)
        dialog.setFixedSize(420, 250)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setLayoutDirection(Qt.RightToLeft)

        container_layout = QVBoxLayout(dialog)
        container_layout.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(20, 20, 20, 15)
        frame_layout.setSpacing(15)

        title = QLabel("إعادة طباعة فاتورة")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        txt_invoice_id = QLineEdit()
        txt_invoice_id.setPlaceholderText("ادخل رقم الفاتورة...")
        txt_invoice_id.setFont(QFont("Segoe UI", 14))
        txt_invoice_id.setFixedHeight(40)
        txt_invoice_id.setAlignment(Qt.AlignCenter)

        form_layout.addRow(QLabel("رقم الفاتورة:"), txt_invoice_id)

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM sales;")
            last_id = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            if last_id:
                lbl_hint = QLabel(f"آخر فاتورة: {last_id}")
                lbl_hint.setFont(QFont("Segoe UI", 10))
                lbl_hint.setStyleSheet("color: #718096;")
                lbl_hint.setAlignment(Qt.AlignCenter)
                frame_layout.addWidget(lbl_hint)
                txt_invoice_id.setText(str(last_id))
                txt_invoice_id.selectAll()
        except Exception:
            pass

        frame_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_print = QPushButton("طباعة")
        btn_print.setFixedHeight(40)

        btn_close = QPushButton("إغلاق")
        btn_close.setObjectName("cancelBtn")
        btn_close.setFixedHeight(40)
        btn_close.clicked.connect(dialog.reject)

        btn_layout.addWidget(btn_print)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        frame_layout.addLayout(btn_layout)

        container_layout.addWidget(main_frame)

        def do_reprint():
            invoice_id = txt_invoice_id.text().strip()
            if not invoice_id or not invoice_id.isdigit():
                SystemMessageBox.show_warning(self, "ادخل رقم فاتورة صحيح!")
                return

            try:
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, total_amount, payment_method, amount_paid, amount_change, sale_date
                    FROM sales
                    WHERE id = %s
                """, (int(invoice_id),))
                sale = cursor.fetchone()

                if not sale:
                    SystemMessageBox.show_warning(self, f"الفاتورة رقم {invoice_id} غير موجودة!")
                    cursor.close()
                    conn.close()
                    return

                cursor.execute("""
                    SELECT p.name, si.quantity, si.unit_price,
                           (si.quantity * si.unit_price) as total
                    FROM sale_items si
                    JOIN products p ON p.id = si.product_id
                    WHERE si.sale_id = %s
                """, (int(invoice_id),))
                items = cursor.fetchall()

                cursor.close()
                conn.close()

                if not items:
                    SystemMessageBox.show_warning(self, "لا توجد أصناف في هذه الفاتورة!")
                    return

                receipt_items = []
                for item in items:
                    receipt_items.append({
                        "name": item[0],
                        "qty": item[1],
                        "price": float(item[2]),
                        "total": float(item[3])
                    })

                payment_details = {
                    "payment_method": sale[2] or "نقدي",
                    "amount_paid": float(sale[3]) if sale[3] else float(sale[1]),
                    "amount_change": float(sale[4]) if sale[4] else 0.0
                }

                if print_receipt:
                    print_receipt(
                        sale[0],
                        receipt_items,
                        float(sale[1]),
                        payment_details,
                        self.session.get('full_name', '')
                    )
                    SystemMessageBox.show_success(self, f"تم إعادة طباعة الفاتورة رقم {invoice_id}")
                else:
                    SystemMessageBox.show_warning(self, "وظيفة الطباعة غير متاحة!")

            except Exception as e:
                SystemMessageBox.show_critical(self, f"خطأ: {e}")

        btn_print.clicked.connect(do_reprint)
        txt_invoice_id.returnPressed.connect(do_reprint)
        txt_invoice_id.setFocus()

        dialog.exec()
        self.reset_inactivity_timer()
        self.txt_barcode.setFocus()

    # ==============================
    # الوردية
    # ==============================
    def on_close_shift(self):
        if self.sales_table.rowCount() > 0:
            SystemMessageBox.show_warning(self, "يوجد فاتورة مفتوحة!\nاحفظها أو الغيها أولاً.")
            return

        try:
            from gui.shift_manager import get_open_shift, CloseShiftDialog
        except ImportError:
            from shift_manager import get_open_shift, CloseShiftDialog

        cashier_name = self.session.get('full_name', '')
        shift_id = get_open_shift(cashier_name)

        if not shift_id:
            SystemMessageBox.show_warning(self, "لا توجد وردية مفتوحة لهذا الكاشير!")
            return

        dialog = CloseShiftDialog(shift_id, self.session, self)
        result = dialog.exec()

        if result == QDialog.Accepted:
            self.force_logout()
            return

        self.txt_barcode.setFocus()

    def on_cash_in(self):
        try:
            from gui.shift_manager import get_open_shift, CashTransactionDialog
        except ImportError:
            from shift_manager import get_open_shift, CashTransactionDialog

        shift_id = get_open_shift(self.session.get('full_name', ''))
        if not shift_id:
            SystemMessageBox.show_warning(self, "لا توجد وردية مفتوحة!")
            return

        CashTransactionDialog(shift_id, "cash_in", self.session, self).exec()
        self.reset_inactivity_timer()
        self.txt_barcode.setFocus()

    def on_cash_out(self):
        try:
            from gui.shift_manager import get_open_shift, CashTransactionDialog
        except ImportError:
            from shift_manager import get_open_shift, CashTransactionDialog

        shift_id = get_open_shift(self.session.get('full_name', ''))
        if not shift_id:
            SystemMessageBox.show_warning(self, "لا توجد وردية مفتوحة!")
            return

        CashTransactionDialog(shift_id, "cash_out", self.session, self).exec()
        self.reset_inactivity_timer()
        self.txt_barcode.setFocus()

    # ==============================
    # تأمين الخزنة
    # ==============================
    def setup_auto_lock(self):
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.auto_lock_cashier)
        self.reset_inactivity_timer()

    def reset_inactivity_timer(self):
        if hasattr(self, "inactivity_timer") and not self.is_locked:
            self.inactivity_timer.start(self.auto_lock_minutes * 60 * 1000)

    def auto_lock_cashier(self):
        if QApplication.activeModalWidget() is not None:
            self.reset_inactivity_timer()
            return

        self.lock_cashier("تم التأمين التلقائي بسبب عدم وجود أي حركة")

    def on_lock_cashier(self):
        self.lock_cashier("تم تأمين الخزنة يدوياً")

    def verify_current_user_password(self, password):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE id = %s", (self.session.get("id"),))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if not row or not row[0]:
                return False

            stored_password = row[0].encode("utf-8")
            return bcrypt.checkpw(password.encode("utf-8"), stored_password)

        except Exception:
            return False

    def lock_cashier(self, reason=""):
        if self.is_locked:
            return

        self.is_locked = True
        if hasattr(self, "inactivity_timer"):
            self.inactivity_timer.stop()

        try:
            from gui.shift_manager import log_audit
            log_audit("تأمين الخزنة", reason, self.session.get("full_name", ""))
        except Exception:
            pass

        while self.is_locked:
            dialog = CashierLockDialog(
                user_name=self.session.get("full_name", ""),
                reason=reason,
                parent=self
            )
            result = dialog.exec()

            if dialog.logout_requested:
                self.is_locked = False
                self.force_logout()
                return

            if result == QDialog.Accepted:
                password = dialog.get_password()
                if self.verify_current_user_password(password):
                    self.is_locked = False
                    self.reset_inactivity_timer()
                    self.txt_barcode.setFocus()

                    try:
                        from gui.shift_manager import log_audit
                        log_audit("فك تأمين الخزنة", "تم فك التأمين بنجاح", self.session.get("full_name", ""))
                    except Exception:
                        pass
                    return
                else:
                    SystemMessageBox.show_warning(self, "كلمة المرور غير صحيحة")

    def eventFilter(self, obj, event):
        if not self.is_locked:
            if event.type() in (QEvent.MouseButtonPress, QEvent.KeyPress):
                self.reset_inactivity_timer()
        return super().eventFilter(obj, event)

            # ==============================
            # الخروج
            # ==============================
    def force_logout(self):
        """خروج مباشر بدون سؤال"""
        try:
            from gui.login_window import LoginWindow
        except ImportError:
            from login_window import LoginWindow

        if hasattr(self, "inactivity_timer"):
            self.inactivity_timer.stop()

        self.login_win = LoginWindow()
        self.login_win.show()
        self.close()

    def on_item_discount(self):
        row = self.sales_table.currentRow()
        if row < 0:
            SystemMessageBox.show_warning(self, "اختر صنف أولاً!")
            return

        if not self.request_manager_approval("خصم على صنف"):
            return

        item_name = self.sales_table.item(row, 1).text()
        price = float(self.sales_table.item(row, 3).text())
        qty = int(self.sales_table.item(row, 4).text())
        current_discount = float(self.sales_table.item(row, 5).text())

        max_discount = abs(price * qty)

        discount, ok = QInputDialog.getDouble(
            self,
            "خصم على صنف",
            f"ادخل مبلغ الخصم على الصنف:\n{item_name}",
            current_discount,
            0,
            max_discount,
            2
        )

        if ok:
            self.sales_table.item(row, 5).setText(f"{discount:.2f}")
            new_total = (price * qty) - discount
            self.sales_table.item(row, 6).setText(f"{new_total:.2f}")
            self.update_invoice_totals()
            self.write_audit(
                "خصم على صنف",
                f"الصنف: {item_name} | الكمية: {qty} | الخصم: {discount:.2f}"
            )
            self.reset_inactivity_timer()

    def on_invoice_discount(self):
        if self.sales_table.rowCount() == 0:
            SystemMessageBox.show_warning(self, "الفاتورة فارغة!")
            return

        if not self.request_manager_approval("خصم على الفاتورة"):
            return

        subtotal = self.calculate_subtotal()

        discount, ok = QInputDialog.getDouble(
            self,
            "خصم على الفاتورة",
            "ادخل مبلغ الخصم على إجمالي الفاتورة:",
            self.invoice_discount,
            0,
            subtotal,
            2
        )

        if ok:
            self.invoice_discount = discount
            self.update_invoice_totals()
            self.write_audit(
                "خصم على الفاتورة",
                f"إجمالي قبل الخصم: {subtotal:.2f} | خصم الفاتورة: {discount:.2f}"
            )
            self.reset_inactivity_timer()

    def on_logout(self):
        if SystemMessageBox.show_question(self, "هل تريد تسجيل الخروج؟") == QDialog.Accepted:
            self.force_logout()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POSWindow()
    window.show()
    sys.exit(app.exec())