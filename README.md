# GymPro — Gym Management Web App

A full-stack gym management system built with Python, Flask, and MySQL.

## Live Demo
🔗 Coming soon
## Screenshots

### Login
![Login](screenshots/login.png)

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Members
![Members](screenshots/members.png)

### Member Profile
![Profile](screenshots/profile.png)

### Payments
![Payments](screenshots/payments.png)

## Features

### Admin Portal
- 🔐 Secure login with hashed passwords
- 📊 Dashboard with live stats (members, sessions, revenue, unpaid)
- 👥 Full member management (add, edit, delete, profile)
- 🏃 Session tracking with filters by member and type
- 💶 Payment tracking with CSV export
- 💪 Trainer management
- 📧 Automatic welcome email on member registration
- 🌙 Dark mode toggle

### Member Portal
- 🔐 Members can log in with their own account
- 📊 Personal dashboard with session history
- 📈 Sessions chart for last 6 months
- 💶 Payment status view
- ➕ Log their own sessions

### Technical
- Input validation and duplicate email detection
- Flash messages for all actions
- Auto-creates monthly payment records
- Responsive design (works on mobile)
- Passwords stored securely
- Sensitive config in `.env` file

## Tech Stack
- **Backend:** Python, Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript, Chart.js
- **Email:** Flask-Mail (Gmail SMTP)

## How to Run Locally

1. Clone the repo
2. Install dependencies: pip3 install flask pymysql python-dotenv flask-mail bcrypt
3. Create a `.env` file: DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=gym_db
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
4. Import `gym_db.sql` into MySQL
5. Run:python3 app.py
6. Open `http://127.0.0.1:5000`

## Pages
| Page | Description |
|------|-------------|
| `/login` | Admin login |
| `/` | Dashboard with stats |
| `/members` | Member list |
| `/sessions` | Session log |
| `/payments` | Payment tracker |
| `/trainers` | Trainer list |
| `/member-login` | Member portal login |
