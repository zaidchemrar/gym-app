from flask import Flask, render_template, request, redirect, url_for
import pymysql
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)

# Database connection
def get_db():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor
    )

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Members page
@app.route('/members')
def members():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    db.close()
    return render_template('members.html', members=members)

# Add member
@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        join_date = request.form['join_date']
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO members (first_name, last_name, email, phone, join_date) VALUES (%s, %s, %s, %s, %s)",
            (first_name, last_name, email, phone, join_date)
        )
        new_member_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO payments (member_id, payment_month, amount, status) VALUES (%s, CURDATE(), 29.00, 'unpaid')",
            (new_member_id,)
        )
        db.commit()
        db.close()
        return redirect(url_for('members'))
    return render_template('add_member.html')

# Sessions page
@app.route('/sessions')
def sessions():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id, m.first_name, m.last_name, s.session_date, 
               s.session_type, s.duration_minutes,
               CONCAT(t.first_name, ' ', t.last_name) AS trainer_name
        FROM sessions s
        JOIN members m ON s.member_id = m.id
        LEFT JOIN trainers t ON s.trainer_id = t.id
        ORDER BY s.session_date DESC
    """)
    sessions = cursor.fetchall()
    db.close()
    return render_template('sessions.html', sessions=sessions)

# Payments page
@app.route('/payments')
def payments():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT m.id AS member_id, m.first_name, m.last_name, p.payment_month, 
               p.amount, p.status, p.payment_date
        FROM payments p
        JOIN members m ON p.member_id = m.id
        ORDER BY p.status ASC
    """)
    payments = cursor.fetchall()
    db.close()
    return render_template('payments.html', payments=payments)
@app.route('/add_session', methods=['GET', 'POST'])
def add_session():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        member_id = request.form['member_id']
        session_date = request.form['session_date']
        session_type = request.form['session_type']
        duration_minutes = request.form['duration_minutes']
        trainer_id = request.form['trainer_id'] or None
        
        cursor.execute(
            "INSERT INTO sessions (member_id, session_date, session_type, duration_minutes, trainer_id) VALUES (%s, %s, %s, %s, %s)",
            (member_id, session_date, session_type, duration_minutes, trainer_id)
        )
        db.commit()
        db.close()
        return redirect(url_for('sessions'))
    
    cursor.execute("SELECT id, first_name, last_name FROM members")
    members = cursor.fetchall()
    cursor.execute("SELECT id, first_name, last_name FROM trainers")
    trainers = cursor.fetchall()
    db.close()
    return render_template('add_session.html', members=members, trainers=trainers)
@app.route('/mark_paid/<int:member_id>', methods=['POST'])
def mark_paid(member_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE payments 
        SET status = 'paid', payment_date = CURDATE()
        WHERE member_id = %s 
        AND MONTH(payment_month) = MONTH(CURDATE())
        AND YEAR(payment_month) = YEAR(CURDATE())
    """, (member_id,))
    db.commit()
    db.close()
    return redirect(url_for('payments'))
if __name__ == '__main__':
    app.run(debug=True)