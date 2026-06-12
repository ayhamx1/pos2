import sys
sys.path.append('.')

from PySide6.QtWidgets import QApplication
from gui.shift_manager import get_open_shift, OpenShiftDialog

app = QApplication(sys.argv)

# اختبار 1: البحث عن وردية مفتوحة
result = get_open_shift('كاشير 1')
print("وردية مفتوحة:", result)

# اختبار 2: فتح شاشة الوردية
session = {'full_name': 'كاشير 1', 'id': 2, 'pos_name': 'نقطة البيع 1'}
dialog = OpenShiftDialog(session)
dialog_result = dialog.exec()
print("نتيجة الشاشة:", dialog_result)

# اختبار 3: التحقق بعد الفتح
result2 = get_open_shift('كاشير 1')
print("وردية مفتوحة بعد الفتح:", result2)