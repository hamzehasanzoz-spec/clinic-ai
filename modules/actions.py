import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'clinic.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 1. أداة: تجهيز ملف المريض والصور (للبحث عن المريض)
def get_patient_info(patient_name):
    conn = get_db()
    patient = conn.execute("SELECT * FROM Patients WHERE name LIKE ?", (f"%{patient_name}%",)).fetchone()
    
    if not patient:
        conn.close()
        return {"status": "error", "message": f"لم أجد مريضاً باسم {patient_name}"}
    
    images = conn.execute("SELECT file_path FROM Images WHERE patient_id = ?", (patient['id'],)).fetchall()
    # المسارات النسبية للصور
    image_paths = [img['file_path'] for img in images]
    
    conn.close()
    return {
        "status": "success",
        "patient_id": patient['id'],
        "patient_name": patient['name'],
        "medical_history": patient['medical_history'],
        "allergies": patient['allergies'],
        "images_count": len(image_paths),
        "images": image_paths
    }

# 2. أداة: تغيير أو تأجيل موعد
def reschedule_appointment(patient_name, new_date, new_time):
    conn = get_db()
    patient = conn.execute("SELECT id, name FROM Patients WHERE name LIKE ?", (f"%{patient_name}%",)).fetchone()
    
    if not patient:
        conn.close()
        return {"status": "error", "message": "المريض غير موجود."}
    
    # تحديث الموعد (نبحث عن أقرب موعد غير مكتمل)
    appt = conn.execute("SELECT id FROM Appointments WHERE patient_id = ? AND status = 'مجدول' ORDER BY date LIMIT 1", (patient['id'],)).fetchone()
    
    if appt:
        conn.execute("UPDATE Appointments SET date=?, time=? WHERE id=?", (new_date, new_time, appt['id']))
        msg = f"تم تأجيل موعد المريض {patient['name']} إلى تاريخ {new_date} الساعة {new_time}."
    else:
        # إذا لم يوجد موعد، ننشئ واحداً جديداً
        conn.execute("INSERT INTO Appointments (patient_id, date, time) VALUES (?, ?, ?)", (patient['id'], new_date, new_time))
        msg = f"لم يكن هناك موعد سابق، تم حجز موعد جديد للمريض {patient['name']}."
        
    conn.commit()
    conn.close()
    return {"status": "success", "message": msg}

# 3. أداة: جلب قائمة مواعيد اليوم
def get_today_appointments():
    # نفترض أن التاريخ اليوم هو 2026-11-14 (للتجربة)
    # في الواقع سنستخدم datetime.now().strftime('%Y-%m-%d')
    today = "2026-11-14" 
    conn = get_db()
    appts = conn.execute('''
        SELECT p.name, a.time, a.notes 
        FROM Appointments a JOIN Patients p ON a.patient_id = p.id 
        WHERE a.date = ? ORDER BY a.time
    ''', (today,)).fetchall()
    conn.close()
    
    if not appts:
        return {"status": "success", "message": "لا توجد مواعيد اليوم."}
        
    result = [f"المريض {a['name']} الساعة {a['time']}" for a in appts]
    return {"status": "success", "message": f"مواعيد اليوم: {', '.join(result)}"}

# 4. أداة: معرفة النواقص في المخزون
def check_inventory_shortages():
    conn = get_db()
    items = conn.execute("SELECT item_name, quantity FROM Inventory WHERE quantity <= min_threshold").fetchall()
    conn.close()
    
    if not items:
        return {"status": "success", "message": "المخزون ممتاز، لا يوجد أي نقص حالياً."}
        
    result = [f"{item['item_name']} (المتبقي: {item['quantity']})" for item in items]
    return {"status": "success", "message": f"نواقص المخزون: {', '.join(result)}"}

# 5. أداة: تحديث حالة أعمال المخبر
def update_lab_status(patient_name, new_status):
    conn = get_db()
    patient = conn.execute("SELECT id, name FROM Patients WHERE name LIKE ?", (f"%{patient_name}%",)).fetchone()
    if not patient:
        conn.close()
        return {"status": "error", "message": "المريض غير موجود."}
        
    # تحديث حالة آخر طلب مخبر
    lab = conn.execute("SELECT id FROM Lab_Work WHERE patient_id = ? ORDER BY id DESC LIMIT 1", (patient['id'],)).fetchone()
    if lab:
        conn.execute("UPDATE Lab_Work SET status=? WHERE id=?", (new_status, lab['id']))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"تم تحديث حالة مخبر المريض {patient['name']} إلى: {new_status}."}
    else:
        conn.close()
        return {"status": "error", "message": "لا يوجد طلبات مخبر سابقة لهذا المريض."}