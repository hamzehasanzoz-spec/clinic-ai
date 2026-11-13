import sqlite3
import os

# تحديد مسار قاعدة البيانات (سيتم إنشاؤها داخل مجلد database)
DB_PATH = os.path.join(os.path.dirname(__file__), 'clinic.db')

def create_database():
    print("جاري الاتصال بقاعدة البيانات...")
    # الاتصال بقاعدة البيانات (إذا لم تكن موجودة، سيتم إنشاؤها)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. جدول المرضى (Patients)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        medical_history TEXT,
        allergies TEXT
    )
    ''')

    # 2. جدول المواعيد (Appointments)
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

    # 3. جدول الصور الشعاعية (Images)
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

    # 4. جدول المخزون (Inventory)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        min_threshold INTEGER DEFAULT 5
    )
    ''')

    # 5. جدول أعمال المخبر (Lab_Work)
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

    # حفظ التغييرات وإغلاق الاتصال
    conn.commit()
    conn.close()
    print("✅ تم إنشاء قاعدة البيانات والجداول بنجاح!")

if __name__ == "__main__":
    # إذا كان ملف قاعدة البيانات موجوداً مسبقاً، سنقوم بحذفه لإنشاء نسخة جديدة نظيفة (احتياط)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("تم حذف قاعدة البيانات القديمة لإنشاء نسخة جديدة.")
        
    create_database()
    