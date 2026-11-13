import os
import shutil
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'clinic.db')
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# تعريف المجلدات
INCOMING_DIR = os.path.join(BASE_DIR, 'data', 'incoming')
XRAYS_DIR = os.path.join(BASE_DIR, 'data', 'xrays')

# التأكد من وجود المجلدات عند تشغيل الكود
os.makedirs(INCOMING_DIR, exist_ok=True)
os.makedirs(XRAYS_DIR, exist_ok=True)

def get_incoming_files():
    """جلب قائمة الصور الجديدة التي لم يتم فرزها بعد"""
    files = []
    for f in os.listdir(INCOMING_DIR):
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.dcm')):
            files.append(os.path.join(INCOMING_DIR, f))
    return files

def process_image(file_path, patient_id, patient_name):
    """نقل الصورة لمجلد المريض وتسجيلها في قاعدة البيانات"""
    try:
        # 1. إنشاء مجلد خاص بالمريض (مثلاً: patient_1_أحمد_محمد)
        # نستخدم الـ ID لضمان عدم تكرار الأسماء
        patient_folder_name = f"patient_{patient_id}_{patient_name.replace(' ', '_')}"
        patient_folder = os.path.join(XRAYS_DIR, patient_folder_name)
        os.makedirs(patient_folder, exist_ok=True)
        
        # 2. إنشاء اسم جديد للصورة (التاريخ_الوقت_الاسم_الأصلي)
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}_{filename}"
        new_file_path = os.path.join(patient_folder, new_filename)
        
        # 3. نقل الملف
        shutil.move(file_path, new_file_path)
        
        # 4. حفظ المسار في قاعدة البيانات (نحفظ المسار النسبي ليكون أنظف)
        relative_path = os.path.relpath(new_file_path, BASE_DIR)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        today_date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('''
            INSERT INTO Images (patient_id, file_path, date, image_type)
            VALUES (?, ?, ?, ?)
        ''', (patient_id, relative_path, today_date, 'X-Ray'))
        conn.commit()
        conn.close()
        
        return True, new_file_path
    except Exception as e:
        print(f"Error processing image: {e}")
        return False, str(e)