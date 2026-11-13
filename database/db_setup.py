import sqlite3
import os

# تحديد مسار قاعدة البيانات
DB_PATH = os.path.join(os.path.dirname(__file__), 'clinic.db')

def create_database():
    print("جاري الاتصال بقاعدة البيانات...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. جدول المرضى
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        medical_history TEXT,
        allergies TEXT
    )
    ''')

    # 2. جدول المواعيد
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT DEFAULT 'مجدول',
        notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES Patients(id)
    )
    ''')

    # 3. جدول الصور
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        file_path TEXT NOT NULL,
        date TEXT,
        image_type TEXT,
        FOREIGN KEY (patient_id) REFERENCES Patients(id)
    )
    ''')

    # 4. جدول المخزون
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        min_threshold INTEGER DEFAULT 5
    )
    ''')

    # 5. جدول أعمال المخبر
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Lab_Work (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        description TEXT NOT NULL,
        expected_date TEXT,
        status TEXT DEFAULT 'قيد التنفيذ',
        FOREIGN KEY (patient_id) REFERENCES Patients(id)
    )
    ''')
    
    # --- إدخال بيانات تجريبية (Dummy Data) ---
    
    # إضافة مرضى وهميين
    patients_data = [
        ('أحمد محمد', '0933333333', 'لا يوجد', 'حساسية من البنسلين'),
        ('سارة علي', '0944444444', 'ضغط دم مرتفع', 'لا يوجد'),
        ('محمود حسن', '0955555555', 'سكري', 'لا يوجد'),
        ('ليلى خالد', '0966666666', 'لا يوجد', 'حساسية من الأسبرين')
    ]
    
    # التحقق من أن الجدول فارغ قبل إضافة البيانات (لتجنب التكرار)
    cursor.execute('SELECT COUNT(*) FROM Patients')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO Patients (name, phone, medical_history, allergies) VALUES (?, ?, ?, ?)', patients_data)
        
        # إضافة مواعيد وهمية
        appointments_data = [
            (1, '2026-11-14', '10:00', 'مجدول', 'فحص دوري'),
            (2, '2026-11-14', '11:30', 'مجدول', 'تنظيف'),
            (3, '2026-11-15', '09:00', 'مؤكد', 'حشوة ضرس العقل'),
            (4, '2026-11-15', '14:00', 'مجدول', 'متابعة')
        ]
        cursor.executemany('INSERT INTO Appointments (patient_id, date, time, status, notes) VALUES (?, ?, ?, ?, ?)', appointments_data)
        
        # إضافة مخزون وهمي
        inventory_data = [
            ('قفازات طبية', 150, 50),
            ('كمامات', 200, 100),
            ('مادة تخدير (Lidocaine)', 15, 20), # أقل من الحد الأدنى (لاختبار التنبيهات)
            ('قطن طبي', 50, 20)
        ]
        cursor.executemany('INSERT INTO Inventory (item_name, quantity, min_threshold) VALUES (?, ?, ?)', inventory_data)
        
        print("تمت إضافة بيانات تجريبية بنجاح!")

    conn.commit()
    conn.close()
    print("✅ تم إنشاء قاعدة البيانات والجداول وتجهيز البيانات بنجاح!")

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("تم حذف قاعدة البيانات القديمة لإنشاء نسخة جديدة.")
    create_database()