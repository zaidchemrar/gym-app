from flask import Flask, render_template, request, redirect, url_for
import pymysql

app = Flask(__name__)

# Database connection
def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='zaidzaid12',  # MySQL root password
        database='gym_db',
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
        SELECT m.first_name, m.last_name, p.payment_month, 
               p.amount, p.status, p.payment_date
        FROM payments p
        JOIN members m ON p.member_id = m.id
        ORDER BY p.status ASC
    """)
    payments = cursor.fetchall()
    db.close()
    return render_template('payments.html', payments=payments)

if __name__ == '__main__':
    app.run(debug=True)