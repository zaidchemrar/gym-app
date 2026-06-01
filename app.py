from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import bcrypt
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
app.secret_key = 'gymapp2026'
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

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
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM members")
    total_members = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total FROM sessions
        WHERE MONTH(session_date) = MONTH(CURDATE())
        AND YEAR(session_date) = YEAR(CURDATE())
    """)
    sessions_this_month = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total FROM payments
        WHERE status = 'paid'
        AND MONTH(payment_month) = MONTH(CURDATE())
        AND YEAR(payment_month) = YEAR(CURDATE())
    """)
    revenue = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total FROM payments
        WHERE status = 'unpaid'
        AND MONTH(payment_month) = MONTH(CURDATE())
        AND YEAR(payment_month) = YEAR(CURDATE())
    """)
    unpaid = cursor.fetchone()['total']

    cursor.execute("""
        SELECT m.first_name, m.last_name,
               COUNT(s.id) AS total_sessions,
               SUM(s.duration_minutes) AS total_minutes
        FROM members m
        JOIN sessions s ON m.id = s.member_id
        WHERE MONTH(s.session_date) = MONTH(CURDATE())
        AND YEAR(s.session_date) = YEAR(CURDATE())
        GROUP BY m.id
        ORDER BY total_sessions DESC
        LIMIT 5
    """)
    top_members = cursor.fetchall()
    db.close()

    stats = {
        'total_members': total_members,
        'sessions_this_month': sessions_this_month,
        'revenue': revenue,
        'unpaid': unpaid,
        'top_members': top_members
    }
    return render_template('index.html', stats=stats)

# Members page
@app.route('/members')
@login_required
def members():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM members")
    members = cursor.fetchall()
    db.close()
    return render_template('members.html', members=members)

# Add member
@app.route('/add_member', methods=['GET', 'POST'])
@login_required
def add_member():
    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        join_date = request.form['join_date']

        if not first_name or not last_name or not email or not phone or not join_date:
            flash('All fields are required.', 'error')
            return render_template('add_member.html')

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT id FROM members WHERE email = %s", (email,))
        existing = cursor.fetchone()
        if existing:
            flash('A member with this email already exists.', 'error')
            db.close()
            return render_template('add_member.html')

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
        flash('Member added successfully!', 'success')
        return redirect(url_for('members'))
    return render_template('add_member.html')

# Sessions page
@app.route('/sessions')
@login_required
def sessions():
    db = get_db()
    cursor = db.cursor()
    search = request.args.get('search', '')
    session_type = request.args.get('type', '')
    
    query = """
        SELECT s.id, m.first_name, m.last_name, s.session_date, 
               s.session_type, s.duration_minutes,
               CONCAT(t.first_name, ' ', t.last_name) AS trainer_name
        FROM sessions s
        JOIN members m ON s.member_id = m.id
        LEFT JOIN trainers t ON s.trainer_id = t.id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (m.first_name LIKE %s OR m.last_name LIKE %s)"
        params.extend(['%' + search + '%', '%' + search + '%'])
    
    if session_type:
        query += " AND s.session_type = %s"
        params.append(session_type)
    
    query += " ORDER BY s.session_date DESC"
    cursor.execute(query, params)
    sessions = cursor.fetchall()
    db.close()
    return render_template('sessions.html', sessions=sessions, search=search, session_type=session_type)

# Payments page
@app.route('/payments')
@login_required
def payments():
    db = get_db()
    cursor = db.cursor()
    status_filter = request.args.get('status', '')
    
    query = """
        SELECT m.id AS member_id, m.first_name, m.last_name, p.payment_month, 
               p.amount, p.status, p.payment_date
        FROM payments p
        JOIN members m ON p.member_id = m.id
        WHERE 1=1
    """
    params = []
    if status_filter:
        query += " AND p.status = %s"
        params.append(status_filter)
    
    query += " ORDER BY p.status ASC"
    cursor.execute(query, params)
    payments = cursor.fetchall()
    db.close()
    return render_template('payments.html', payments=payments, status_filter=status_filter)

@app.route('/add_session', methods=['GET', 'POST'])
@login_required
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
        flash('Session added successfully!', 'success')
        return redirect(url_for('sessions'))
    
    cursor.execute("SELECT id, first_name, last_name FROM members")
    members = cursor.fetchall()
    cursor.execute("SELECT id, first_name, last_name FROM trainers")
    trainers = cursor.fetchall()
    db.close()
    return render_template('add_session.html', members=members, trainers=trainers)
@app.route('/mark_paid/<int:member_id>', methods=['POST'])
@login_required
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
    flash('Payment marked as paid!', 'success')
    return redirect(url_for('payments'))
@app.route('/delete_member/<int:member_id>', methods=['POST'])
@login_required
def delete_member(member_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM payments WHERE member_id = %s", (member_id,))
    cursor.execute("DELETE FROM sessions WHERE member_id = %s", (member_id,))
    cursor.execute("DELETE FROM members WHERE id = %s", (member_id,))
    db.commit()
    db.close()
    flash('Member deleted.', 'success')
    return redirect(url_for('members'))
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
      return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        db.close()
        if user:
            stored = user['password']
            if isinstance(stored, str):
                stored = stored.encode('utf-8')
            if bcrypt.checkpw(password, stored):
                session['user'] = username
                flash('Welcome back, ' + username + '!', 'success')
                return redirect(url_for('index'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))
@app.route('/edit_member/<int:member_id>', methods=['GET', 'POST'])
@login_required
def edit_member(member_id):
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        if not first_name or not last_name or not email or not phone:
            flash('All fields are required.', 'error')
            return redirect(url_for('edit_member', member_id=member_id))
        cursor.execute("""
            UPDATE members 
            SET first_name=%s, last_name=%s, email=%s, phone=%s 
            WHERE id=%s
        """, (first_name, last_name, email, phone, member_id))
        db.commit()
        db.close()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('members'))
    cursor.execute("SELECT * FROM members WHERE id = %s", (member_id,))
    member = cursor.fetchone()
    db.close()
    return render_template('edit_member.html', member=member)

@app.route('/delete_session/<int:session_id>', methods=['POST'])
@login_required
def delete_session(session_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
    db.commit()
    db.close()
    flash('Session deleted.', 'success')
    return redirect(url_for('sessions'))
@app.route('/trainers')
@login_required
def trainers():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM trainers")
    trainers = cursor.fetchall()
    db.close()
    return render_template('trainers.html', trainers=trainers)

@app.route('/add_trainer', methods=['GET', 'POST'])
@login_required
def add_trainer():
    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        specialty = request.form['specialty'].strip()
        if not first_name or not last_name or not specialty:
            flash('All fields are required.', 'error')
            return render_template('add_trainer.html')
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO trainers (first_name, last_name, specialty) VALUES (%s, %s, %s)",
            (first_name, last_name, specialty)
        )
        db.commit()
        db.close()
        flash('Trainer added successfully!', 'success')
        return redirect(url_for('trainers'))
    return render_template('add_trainer.html')

@app.route('/delete_trainer/<int:trainer_id>', methods=['POST'])
@login_required
def delete_trainer(trainer_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE sessions SET trainer_id = NULL WHERE trainer_id = %s", (trainer_id,))
    cursor.execute("DELETE FROM trainers WHERE id = %s", (trainer_id,))
    db.commit()
    db.close()
    flash('Trainer deleted.', 'success')
    return redirect(url_for('trainers'))
@app.route('/member/<int:member_id>')
@login_required
def member_profile(member_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM members WHERE id = %s", (member_id,))
    member = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM payments 
        WHERE member_id = %s 
        AND MONTH(payment_month) = MONTH(CURDATE())
        AND YEAR(payment_month) = YEAR(CURDATE())
    """, (member_id,))
    payment = cursor.fetchone()

    cursor.execute("""
        SELECT s.*, CONCAT(t.first_name, ' ', t.last_name) AS trainer_name
        FROM sessions s
        LEFT JOIN trainers t ON s.trainer_id = t.id
        WHERE s.member_id = %s
        ORDER BY s.session_date DESC
    """, (member_id,))
    sessions = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) AS total_sessions,
               COALESCE(SUM(duration_minutes), 0) AS total_minutes
        FROM sessions
        WHERE member_id = %s
        AND MONTH(session_date) = MONTH(CURDATE())
        AND YEAR(session_date) = YEAR(CURDATE())
    """, (member_id,))
    monthly = cursor.fetchone()

    cursor.execute("""
        SELECT session_type, COUNT(*) AS count
        FROM sessions
        WHERE member_id = %s
        GROUP BY session_type
        ORDER BY count DESC
        LIMIT 1
    """, (member_id,))
    favorite = cursor.fetchone()

    db.close()
    return render_template('member_profile.html',
        member=member,
        payment=payment,
        sessions=sessions,
        monthly=monthly,
        favorite=favorite
    )
if __name__ == '__main__':
    app.run(debug=True)