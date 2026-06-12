import sys
import os
import platform
import socket

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSpinBox, QLineEdit,
    QComboBox, QWidget, QFormLayout, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont, QGuiApplication

from database.connection import get_connection


MODERN_STYLE = """
    QDialog { background-color: transparent; }
    QFrame#mainFrame {
        background-color: #F5F5F5;
        border: 2px solid #1e5378;
        border-radius: 16px;
    }
    QLabel {
        font-family: 'Segoe UI';
        color: #2b2b2b;
        border: none;
        background-color: transparent;
    }
    QLineEdit, QSpinBox, QComboBox, QTextEdit {
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 6px;
        font-size: 14px;
        background: white;
    }
    QLineEdit:focus, QSpinBox:focus, QTextEdit:focus, QComboBox:focus {
        border: 2px solid #1e5378;
    }
    QPushButton {
        background-color: #1e5378;
        color: white;
        font-size: 14px;
        font-weight: bold;
        border-radius: 20px;
        padding: 10px 25px;
        border: none;
    }
    QPushButton:hover {
        background-color: #163f5c;
    }
    QHeaderView::section {
        background-color: #1e5378;
        color: white;
        font-weight: bold;
        padding: 8px;
        border: none;
    }
    QTableWidget {
        background: white;
        border: 2px solid #ddd;
        border-radius: 8px;
        font-size: 13px;
    }
    QTableWidget::item {
        padding: 5px;
    }
"""

DENOMINATIONS = [
    ("200 جنيه", 200.0),
    ("100 جنيه", 100.0),
    ("50 جنيه", 50.0),
    ("20 جنيه", 20.0),
    ("10 جنيه", 10.0),
    ("5 جنيه", 5.0),
    ("1 جنيه", 1.0),
    ("50 قرش", 0.50),
    ("25 قرش", 0.25),
]


def get_machine_info():
    try:
        return f"{platform.node()} | {socket.gethostbyname(socket.gethostname())} | {platform.system()}"
    except Exception:
        return "غير معروف"


def get_open_shift(cashier_name):
    """إرجاع رقم الوردية المفتوحة للكاشير إن وجدت"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id
            FROM shifts
            WHERE cashier_name = %s AND status = 'مفتوحة'
            ORDER BY id DESC
            LIMIT 1
        """, (cashier_name,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else None
    except Exception:
        return None


def log_audit(action, details, user_name):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO audit_log (action, details, user_name) VALUES (%s, %s, %s)",
            (action, details, user_name)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


# ==============================
# شاشة فتح الوردية
# ==============================
class OpenShiftDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.shift_id = None

        self.setFixedSize(550, 700)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        self.init_ui()

    def init_ui(self):
        container = QVBoxLayout(self)
        container.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(10)

        header = QFrame()
        header.setStyleSheet("background-color: #27ae60; border-radius: 10px; padding: 12px;")
        h_layout = QVBoxLayout(header)

        title = QLabel("فتح وردية جديدة")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")

        sub = QLabel("أدخل بيانات الوردية والرصيد الافتتاحي")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #d5f5e3;")

        h_layout.addWidget(title)
        h_layout.addWidget(sub)
        layout.addWidget(header)

        info_frame = QFrame()
        info_frame.setStyleSheet("""
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px;
        """)
        info_layout = QFormLayout(info_frame)
        info_layout.setSpacing(8)

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM shifts;")
            next_id = cur.fetchone()[0]
            cur.close()
            conn.close()
        except Exception:
            next_id = 1

        lbl_id = QLabel(str(next_id))
        lbl_id.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lbl_id.setStyleSheet("color: #1e5378;")
        info_layout.addRow("رقم الوردية:", lbl_id)

        lbl_cashier = QLabel(self.session.get('full_name', ''))
        lbl_cashier.setFont(QFont("Segoe UI", 12))
        info_layout.addRow("الكاشير:", lbl_cashier)

        self.cmb_branch = QComboBox()
        self.cmb_branch.addItems(["الفرع الرئيسي"])
        self.cmb_branch.setFixedHeight(35)
        info_layout.addRow("الفرع:", self.cmb_branch)

        lbl_pos = QLabel(self.session.get('pos_name', 'نقطة البيع 1'))
        lbl_pos.setFont(QFont("Segoe UI", 12))
        info_layout.addRow("نقطة البيع:", lbl_pos)

        lbl_time = QLabel(QDateTime.currentDateTime().toString("dd-MM-yyyy hh:mm:ss"))
        lbl_time.setFont(QFont("Segoe UI", 12))
        info_layout.addRow("وقت الفتح:", lbl_time)

        layout.addWidget(info_frame)

        sec = QLabel("الرصيد الافتتاحي (عد الفئات)")
        sec.setFont(QFont("Segoe UI", 13, QFont.Bold))
        sec.setStyleSheet("color: #1e5378;")
        layout.addWidget(sec)

        self.denom_table = QTableWidget()
        self.denom_table.setColumnCount(3)
        self.denom_table.setHorizontalHeaderLabels(["الفئة", "العدد", "الإجمالي"])
        self.denom_table.setColumnWidth(0, 120)
        self.denom_table.setColumnWidth(1, 120)
        self.denom_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.denom_table.verticalHeader().setVisible(False)
        self.denom_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.denom_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.denom_table.setStyleSheet("""
            QHeaderView::section {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        self.denom_table.setRowCount(len(DENOMINATIONS))

        self.denom_spins = []

        for i, (label, val) in enumerate(DENOMINATIONS):
            lbl = QTableWidgetItem(label)
            lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
            lbl.setTextAlignment(Qt.AlignCenter)
            self.denom_table.setItem(i, 0, lbl)

            spin = QSpinBox()
            spin.setRange(0, 9999)
            spin.setFont(QFont("Segoe UI", 13, QFont.Bold))
            spin.setAlignment(Qt.AlignCenter)
            spin.setFixedHeight(35)
            spin.setStyleSheet("""
                QSpinBox {
                    border: 2px solid #e2e8f0;
                    border-radius: 6px;
                    background: #f8f9fa;
                }
                QSpinBox:focus {
                    border: 2px solid #27ae60;
                }
            """)
            spin.valueChanged.connect(self.update_totals)
            self.denom_spins.append(spin)
            self.denom_table.setCellWidget(i, 1, spin)

            sub = QTableWidgetItem("0.00")
            sub.setFont(QFont("Segoe UI", 12))
            sub.setTextAlignment(Qt.AlignCenter)
            self.denom_table.setItem(i, 2, sub)
            self.denom_table.setRowHeight(i, 40)

        self.denom_table.setFixedHeight(len(DENOMINATIONS) * 40 + 30)
        layout.addWidget(self.denom_table)

        total_frame = QFrame()
        total_frame.setStyleSheet("""
            background: #f0fff4;
            border: 2px solid #27ae60;
            border-radius: 10px;
            padding: 12px;
        """)
        total_inner = QHBoxLayout(total_frame)

        lbl_t = QLabel("الرصيد الافتتاحي:")
        lbl_t.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lbl_t.setStyleSheet("color: #155724;")

        self.lbl_total = QLabel("0.00 ج.م")
        self.lbl_total.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.lbl_total.setStyleSheet("color: #27ae60;")

        total_inner.addWidget(lbl_t)
        total_inner.addStretch()
        total_inner.addWidget(self.lbl_total)
        layout.addWidget(total_frame)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_open = QPushButton("فتح الوردية")
        btn_open.setFixedSize(170, 48)
        btn_open.setStyleSheet("""
            QPushButton { background: #27ae60; font-size: 16px; }
            QPushButton:hover { background: #219a52; }
        """)
        btn_open.clicked.connect(self.open_shift)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setFixedSize(100, 48)
        btn_cancel.setStyleSheet("""
            QPushButton { background: #718096; }
            QPushButton:hover { background: #4a5568; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_open)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        scroll.setWidget(content)

        f_layout = QVBoxLayout(main_frame)
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.addWidget(scroll)

        container.addWidget(main_frame)

        if self.denom_spins:
            self.denom_spins[0].setFocus()

    def update_totals(self):
        total = 0.0
        for i, (_, val) in enumerate(DENOMINATIONS):
            sub = self.denom_spins[i].value() * val
            total += sub

            item = QTableWidgetItem(f"{sub:.2f}")
            item.setFont(QFont("Segoe UI", 12, QFont.Bold))
            item.setTextAlignment(Qt.AlignCenter)
            self.denom_table.setItem(i, 2, item)

        self.lbl_total.setText(f"{total:.2f} ج.م")

    def get_opening_cash(self):
        total = 0.0
        for spin, (_, val) in zip(self.denom_spins, DENOMINATIONS):
            total += spin.value() * val
        return total

    def get_denom_details(self):
        details = ""
        for spin, (label, val) in zip(self.denom_spins, DENOMINATIONS):
            if spin.value() > 0:
                details += f"{label}: {spin.value()} = {spin.value() * val:.2f} | "
        return details

    def open_shift(self):
        from gui.pos_window import SystemMessageBox

        cashier = self.session.get('full_name', '')

        existing = get_open_shift(cashier)
        if existing:
            SystemMessageBox.show_warning(
                self,
                f"يوجد وردية مفتوحة بالفعل (رقم {existing})!\nلا يمكن فتح وردية جديدة."
            )
            return

        opening_cash = self.get_opening_cash()
        details = self.get_denom_details()
        machine = get_machine_info()

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO shifts (
                    cashier_name, cashier_id, branch, pos_name,
                    opening_cash, opening_details, status, machine_info
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'مفتوحة', %s)
                RETURNING id
            """, (
                cashier,
                self.session.get('id', 1),
                self.cmb_branch.currentText(),
                self.session.get('pos_name', 'نقطة البيع 1'),
                opening_cash,
                details,
                machine
            ))
            self.shift_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            log_audit(
                "فتح وردية",
                f"وردية رقم {self.shift_id} - رصيد افتتاحي: {opening_cash:.2f}",
                cashier
            )

            SystemMessageBox.show_success(
                self,
                f"تم فتح الوردية رقم {self.shift_id}\nالرصيد الافتتاحي: {opening_cash:.2f} ج.م"
            )
            self.accept()

        except Exception as e:
            SystemMessageBox.show_critical(self, f"خطأ: {e}")


# ==============================
# شاشة إضافة/سحب نقدية
# ==============================
class CashTransactionDialog(QDialog):
    def __init__(self, shift_id, trans_type, session, parent=None):
        super().__init__(parent)
        self.shift_id = shift_id
        self.trans_type = trans_type
        self.session = session

        self.setFixedSize(420, 350)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        self.init_ui()

    def init_ui(self):
        container = QVBoxLayout(self)
        container.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(25, 20, 25, 15)
        layout.setSpacing(12)

        is_in = self.trans_type == "cash_in"
        color = "#27ae60" if is_in else "#e53e3e"
        title_text = "إضافة نقدية للخزنة" if is_in else "سحب نقدية من الخزنة"

        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {color};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("0.00")
        self.txt_amount.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.txt_amount.setFixedHeight(42)
        self.txt_amount.setAlignment(Qt.AlignCenter)
        form.addRow("المبلغ:", self.txt_amount)

        self.cmb_reason = QComboBox()
        self.cmb_reason.setFixedHeight(38)
        if is_in:
            self.cmb_reason.addItems(["تغيير فكة", "سلفة من الإدارة", "تحويل من كاشير آخر", "أخرى"])
        else:
            self.cmb_reason.addItems(["مصروفات", "إيداع خزنة", "تحويل لكاشير آخر", "أخرى"])
        form.addRow("السبب:", self.cmb_reason)

        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("ملاحظات اختيارية...")
        self.txt_notes.setFixedHeight(60)
        form.addRow("ملاحظات:", self.txt_notes)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_save = QPushButton("تأكيد")
        btn_save.setFixedSize(120, 42)
        btn_save.setStyleSheet(f"QPushButton {{ background: {color}; }}")
        btn_save.clicked.connect(self.save_transaction)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setFixedSize(100, 42)
        btn_cancel.setStyleSheet("""
            QPushButton { background: #718096; }
            QPushButton:hover { background: #4a5568; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        container.addWidget(main_frame)
        self.txt_amount.setFocus()

    def save_transaction(self):
        from gui.pos_window import SystemMessageBox

        try:
            amount = float(self.txt_amount.text())
            if amount <= 0:
                raise ValueError()
        except ValueError:
            SystemMessageBox.show_warning(self, "ادخل مبلغ صحيح!")
            return

        reason = self.cmb_reason.currentText()
        notes = self.txt_notes.toPlainText().strip()
        cashier = self.session.get('full_name', '')

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO shift_transactions (
                    shift_id, transaction_type, amount, reason, notes, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (self.shift_id, self.trans_type, amount, reason, notes, cashier))

            if self.trans_type == "cash_in":
                cur.execute(
                    "UPDATE shifts SET cash_in_total = cash_in_total + %s WHERE id = %s",
                    (amount, self.shift_id)
                )
            else:
                cur.execute(
                    "UPDATE shifts SET cash_out_total = cash_out_total + %s WHERE id = %s",
                    (amount, self.shift_id)
                )

            conn.commit()
            cur.close()
            conn.close()

            log_audit(
                "إضافة نقدية" if self.trans_type == "cash_in" else "سحب نقدية",
                f"وردية {self.shift_id} - {amount:.2f} - {reason}",
                cashier
            )

            action = "إضافة" if self.trans_type == "cash_in" else "سحب"
            SystemMessageBox.show_success(
                self,
                f"تم {action} مبلغ {amount:.2f} ج.م\nالسبب: {reason}"
            )
            self.accept()

        except Exception as e:
            SystemMessageBox.show_critical(self, f"خطأ: {e}")


# ==============================
# شاشة جرد وتقفيل الوردية
# ==============================
class CloseShiftDialog(QDialog):
    def __init__(self, shift_id, session, parent=None):
        super().__init__(parent)
        self.shift_id = shift_id
        self.session = session
        self.shift_data = {}

        # حجم مرن حسب الشاشة
        screen = QGuiApplication.primaryScreen().availableGeometry()
        width = min(760, screen.width() - 80)
        height = min(900, screen.height() - 60)

        self.resize(width, height)
        self.setMinimumSize(620, 720)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

        self.load_shift_data()
        self.init_ui()

    def load_shift_data(self):
        try:
            conn = get_connection()
            cur = conn.cursor()

            # بيانات الوردية
            cur.execute("SELECT * FROM shifts WHERE id = %s", (self.shift_id,))
            cols = [desc[0] for desc in cur.description]
            row = cur.fetchone()
            self.shift_data = dict(zip(cols, row))

            # مبيعات الوردية فقط
            cur.execute("""
                SELECT COUNT(*), COALESCE(SUM(total_amount), 0)
                FROM sales
                WHERE shift_id = %s
            """, (self.shift_id,))
            self.shift_data['invoice_count'], self.shift_data['total_sales'] = cur.fetchone()
            self.shift_data['total_sales'] = float(self.shift_data['total_sales'] or 0)

            # نقدي
            cur.execute("""
                SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
                FROM sales
                WHERE shift_id = %s
                  AND (payment_method LIKE '%%نقدي%%' OR payment_method LIKE '%%Cash%%' OR payment_method IS NULL)
            """, (self.shift_id,))
            cash_sales, cash_count = cur.fetchone()
            self.shift_data['total_cash_sales'] = float(cash_sales or 0)
            self.shift_data['cash_count'] = int(cash_count or 0)

            # فيزا
            cur.execute("""
                SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
                FROM sales
                WHERE shift_id = %s AND payment_method LIKE '%%فيزا%%'
            """, (self.shift_id,))
            visa_total, visa_count = cur.fetchone()
            self.shift_data['total_visa_sales'] = float(visa_total or 0)
            self.shift_data['visa_count'] = int(visa_count or 0)

            # آجل
            cur.execute("""
                SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
                FROM sales
                WHERE shift_id = %s AND payment_method LIKE '%%آجل%%'
            """, (self.shift_id,))
            credit_total, credit_count = cur.fetchone()
            self.shift_data['total_credit_sales'] = float(credit_total or 0)
            self.shift_data['credit_count'] = int(credit_count or 0)

            # مرتجعات
            cur.execute("""
                SELECT COUNT(*), COALESCE(SUM(ABS(total_amount)), 0)
                FROM sales
                WHERE shift_id = %s
                  AND invoice_type = 'return'
            """, (self.shift_id,))
            return_count, return_total = cur.fetchone()
            self.shift_data['return_count'] = int(return_count or 0)
            self.shift_data['total_returns'] = float(return_total or 0)

            # خصومات - لو لسه مش مطبقة فعلياً
            self.shift_data['total_discounts'] = 0.0

            # حركات الخزنة
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM shift_transactions
                WHERE shift_id = %s AND transaction_type = 'cash_in'
            """, (self.shift_id,))
            self.shift_data['cash_in_total'] = float(cur.fetchone()[0] or 0)

            cur.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM shift_transactions
                WHERE shift_id = %s AND transaction_type = 'cash_out'
            """, (self.shift_id,))
            self.shift_data['cash_out_total'] = float(cur.fetchone()[0] or 0)

            opening = float(self.shift_data.get('opening_cash', 0) or 0)
            self.shift_data['expected_cash'] = (
                opening
                + self.shift_data['total_cash_sales']
                + self.shift_data['cash_in_total']
                - self.shift_data['cash_out_total']
            )

            cur.close()
            conn.close()

        except Exception as e:
            print(f"خطأ تحميل بيانات الوردية: {e}")

    def init_ui(self):
        container = QVBoxLayout(self)
        container.setContentsMargins(0, 0, 0, 0)

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet(MODERN_STYLE)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(12)

        # الهيدر
        header = QFrame()
        header.setStyleSheet("background: #e53e3e; border-radius: 10px; padding: 12px;")
        h_layout = QVBoxLayout(header)

        title = QLabel("جرد وتقفيل الوردية")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")

        sub = QLabel("قم بعد النقدية الموجودة في درج الكاشير ثم سجل الإغلاق")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #ffd6d6;")

        h_layout.addWidget(title)
        h_layout.addWidget(sub)
        layout.addWidget(header)

        # بيانات أساسية فقط
        opened_at = self.shift_data.get("opened_at")
        open_time_str = opened_at.strftime("%d-%m-%Y %I:%M %p") if opened_at else "---"

        info_frame = QFrame()
        info_frame.setStyleSheet("""
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px;
        """)
        info_layout = QFormLayout(info_frame)
        info_layout.setSpacing(8)

        info_layout.addRow("رقم الوردية:", QLabel(str(self.shift_id)))
        info_layout.addRow("الكاشير:", QLabel(self.session.get("full_name", "")))
        info_layout.addRow("نقطة البيع:", QLabel(self.session.get("pos_name", "نقطة البيع 1")))
        info_layout.addRow("وقت الفتح:", QLabel(open_time_str))

        layout.addWidget(info_frame)

        # تنبيه
        note_frame = QFrame()
        note_frame.setStyleSheet("""
            background: #fffbea;
            border: 1px solid #f6c343;
            border-radius: 8px;
            padding: 10px;
        """)
        note_layout = QVBoxLayout(note_frame)

        lbl_note = QLabel("يرجى عد جميع الفئات النقدية بدقة قبل تأكيد الإغلاق.")
        lbl_note.setWordWrap(True)
        lbl_note.setFont(QFont("Segoe UI", 11))
        lbl_note.setStyleSheet("color: #8a6d3b;")

        note_layout.addWidget(lbl_note)
        layout.addWidget(note_frame)

        # جرد النقدية
        sec = QLabel("جرد درج النقدية")
        sec.setFont(QFont("Segoe UI", 13, QFont.Bold))
        sec.setStyleSheet("color: #e53e3e;")
        layout.addWidget(sec)

        self.denom_table = QTableWidget()
        self.denom_table.setColumnCount(3)
        self.denom_table.setHorizontalHeaderLabels(["الفئة", "العدد", "الإجمالي"])
        self.denom_table.setColumnWidth(0, 160)
        self.denom_table.setColumnWidth(1, 120)
        self.denom_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.denom_table.verticalHeader().setVisible(False)
        self.denom_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.denom_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.denom_table.setStyleSheet("""
            QHeaderView::section {
                background: #e53e3e;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
            QTableWidget {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        self.denom_table.setRowCount(len(DENOMINATIONS))

        self.denom_spins = []

        for i, (label, val) in enumerate(DENOMINATIONS):
            lbl = QTableWidgetItem(label)
            lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            lbl.setTextAlignment(Qt.AlignCenter)
            self.denom_table.setItem(i, 0, lbl)

            spin = QSpinBox()
            spin.setRange(0, 9999)
            spin.setFont(QFont("Segoe UI", 12, QFont.Bold))
            spin.setAlignment(Qt.AlignCenter)
            spin.setFixedHeight(34)
            spin.setStyleSheet("""
                QSpinBox {
                    border: 2px solid #e2e8f0;
                    border-radius: 6px;
                }
                QSpinBox:focus {
                    border: 2px solid #e53e3e;
                }
            """)
            spin.valueChanged.connect(self.update_actual_total)
            self.denom_spins.append(spin)
            self.denom_table.setCellWidget(i, 1, spin)

            sub = QTableWidgetItem("0.00")
            sub.setFont(QFont("Segoe UI", 11))
            sub.setTextAlignment(Qt.AlignCenter)
            self.denom_table.setItem(i, 2, sub)
            self.denom_table.setRowHeight(i, 36)

        self.denom_table.setMinimumHeight(len(DENOMINATIONS) * 36 + 40)
        self.denom_table.setMaximumHeight(len(DENOMINATIONS) * 36 + 40)
        layout.addWidget(self.denom_table)

        # النقدية الفعلية فقط
        actual_frame = QFrame()
        actual_frame.setStyleSheet("""
            background: #f7fafc;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            padding: 12px;
        """)
        actual_inner = QHBoxLayout(actual_frame)

        lbl_a = QLabel("النقدية الفعلية:")
        lbl_a.setFont(QFont("Segoe UI", 13, QFont.Bold))

        self.lbl_actual = QLabel("0.00 ج.م")
        self.lbl_actual.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.lbl_actual.setStyleSheet("color: #1e5378;")

        actual_inner.addWidget(lbl_a)
        actual_inner.addStretch()
        actual_inner.addWidget(self.lbl_actual)
        layout.addWidget(actual_frame)

        # ملاحظات
        notes_frame = QFrame()
        notes_frame.setStyleSheet("""
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 8px;
        """)
        notes_layout = QVBoxLayout(notes_frame)

        lbl_notes = QLabel("ملاحظات:")
        lbl_notes.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.txt_reason = QLineEdit()
        self.txt_reason.setPlaceholderText("أي ملاحظات تخص الإغلاق...")
        self.txt_reason.setFixedHeight(38)

        notes_layout.addWidget(lbl_notes)
        notes_layout.addWidget(self.txt_reason)
        layout.addWidget(notes_frame)

        # أزرار
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_close_shift = QPushButton("تسجيل الجرد وتقفيل الوردية")
        btn_close_shift.setFixedSize(220, 48)
        btn_close_shift.setStyleSheet("""
            QPushButton { background: #e53e3e; font-size: 15px; }
            QPushButton:hover { background: #c53030; }
        """)
        btn_close_shift.clicked.connect(self.close_shift)

        btn_reset = QPushButton("تصفير")
        btn_reset.setFixedSize(100, 48)
        btn_reset.setStyleSheet("""
            QPushButton { background: #718096; }
            QPushButton:hover { background: #4a5568; }
        """)
        btn_reset.clicked.connect(self.reset_counts)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setFixedSize(100, 48)
        btn_cancel.setStyleSheet("""
            QPushButton { background: #718096; }
            QPushButton:hover { background: #4a5568; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_close_shift)
        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        scroll.setWidget(content)

        f_layout = QVBoxLayout(main_frame)
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.addWidget(scroll)

        container.addWidget(main_frame)

        if self.denom_spins:
            self.denom_spins[0].setFocus()

    def add_section(self, parent_layout, title, data):
        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl.setStyleSheet("color: #1e5378;")
        parent_layout.addWidget(lbl)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["البيان", "القيمة"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        table.setColumnWidth(1, 190)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background: #1e5378;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
        """)
        table.setRowCount(len(data))

        for i, (label, value) in enumerate(data):
            l = QTableWidgetItem(label)
            l.setFont(QFont("Segoe UI", 11))

            v = QTableWidgetItem(value)
            v.setFont(QFont("Segoe UI", 11, QFont.Bold))
            v.setTextAlignment(Qt.AlignCenter)

            table.setItem(i, 0, l)
            table.setItem(i, 1, v)
            table.setRowHeight(i, 34)

        table.setMinimumHeight(len(data) * 34 + 38)
        table.setMaximumHeight(len(data) * 34 + 38)
        parent_layout.addWidget(table)

    def update_actual_total(self):
        total = 0.0
        for i, (_, val) in enumerate(DENOMINATIONS):
            sub = self.denom_spins[i].value() * val
            total += sub

            item = QTableWidgetItem(f"{sub:.2f}")
            item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            item.setTextAlignment(Qt.AlignCenter)
            self.denom_table.setItem(i, 2, item)

        self.lbl_actual.setText(f"{total:.2f} ج.م")

    def reset_counts(self):
        for spin in self.denom_spins:
            spin.setValue(0)
        self.txt_reason.clear()
        self.reason_frame.setVisible(False)
        self.lbl_actual.setText("0.00 ج.م")
        if self.denom_spins:
            self.denom_spins[0].setFocus()

    def get_closing_cash(self):
        total = 0.0
        for spin, (_, val) in zip(self.denom_spins, DENOMINATIONS):
            total += spin.value() * val
        return total

    def get_closing_details(self):
        details = ""
        for spin, (label, val) in zip(self.denom_spins, DENOMINATIONS):
            if spin.value() > 0:
                details += f"{label}: {spin.value()} = {spin.value() * val:.2f} | "
        return details

    def close_shift(self):
        from gui.pos_window import SystemMessageBox

        actual = self.get_closing_cash()
        if actual == 0:
            SystemMessageBox.show_warning(self, "عد النقدية في الخزنة أولاً!")
            return

        expected = float(self.shift_data.get('expected_cash', 0) or 0)
        diff = actual - expected

        # لو الفرق كبير لازم سبب
        if abs(diff) > 20 and not self.txt_reason.text().strip():
            SystemMessageBox.show_warning(self, "يوجد فرق كبير، يجب كتابة السبب أولاً.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            close_reason = self.txt_reason.text().strip()
            closing_details = self.get_closing_details()

            full_reason = close_reason
            if closing_details:
                if full_reason:
                    full_reason += "\n"
                full_reason += f"تفاصيل الجرد: {closing_details}"

            cur.execute("""
                UPDATE shifts SET
                    closing_cash = %s,
                    expected_cash = %s,
                    difference = %s,
                    status = 'مغلقة',
                    close_reason = %s,
                    total_sales = %s,
                    total_cash_sales = %s,
                    total_visa_sales = %s,
                    total_credit_sales = %s,
                    total_returns = %s,
                    invoice_count = %s,
                    return_count = %s,
                    closed_at = NOW()
                WHERE id = %s
            """, (
                actual,
                expected,
                diff,
                full_reason,
                self.shift_data.get('total_sales', 0),
                self.shift_data.get('total_cash_sales', 0),
                self.shift_data.get('total_visa_sales', 0),
                self.shift_data.get('total_credit_sales', 0),
                self.shift_data.get('total_returns', 0),
                self.shift_data.get('invoice_count', 0),
                self.shift_data.get('return_count', 0),
                self.shift_id
            ))

            conn.commit()
            cur.close()
            conn.close()

            cashier = self.session.get('full_name', '')
            log_audit(
                "غلق وردية",
                f"وردية {self.shift_id} - المتوقع {expected:.2f} - الفعلي {actual:.2f} - الفرق {diff:+.2f}",
                cashier
            )

            # لا نعرض المتوقع للكاشير
            SystemMessageBox.show_success(
                self,
                f"تم تسجيل الجرد وتقفيل الوردية رقم {self.shift_id} بنجاح"
            )
            self.accept()

        except Exception as e:
            SystemMessageBox.show_critical(self, f"خطأ: {e}")