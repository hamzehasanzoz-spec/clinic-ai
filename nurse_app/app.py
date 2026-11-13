from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# تحديد مسار قاعدة البيانات (نرجع خطوة للخلف لأننا داخل مجلد nurse_app)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'clinic.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # للوصول للبيانات كقاموس
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    # جلب المرضى والمواعيد
    patients = conn.execute('SELECT * FROM Patients').fetchall()
    appointments = conn.execute('''
        SELECT Appointments.*, Patients.name 
        FROM Appointments 
        JOIN Patients ON Appointments.patient_id = Patients.id
        ORDER BY date, time
    ''').fetchall()
    conn.close()
    return render_template('index.html', patients=patients, appointments=appointments)

@app.route('/add_patient', methods=['POST'])
def add_patient():
    name = request.form['name']
    phone = request.form['phone']
    
    if name:
        conn = get_db_connection()
        conn.execute('INSERT INTO Patients (name, phone) VALUES (?, ?)', (name, phone))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    patient_id = request.form['patient_id']
    date = request.form['date']
    time = request.form['time']
    
    if patient_id and date and time:
        conn = get_db_connection()
        conn.execute('INSERT INTO Appointments (patient_id, date, time) VALUES (?, ?, ?)', (patient_id, date, time))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # host='0.0.0.0' يسمح للممرضة بالدخول من هاتفها عبر شبكة الواي فاي
    app.run(host='0.0.0.0', port=5000, debug=True)