from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import sqlite3
import os
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import io
import base64

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
bcrypt = Bcrypt(app)

# Database initialization
def init_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expense_tracker.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  phone TEXT NOT NULL,
                  password TEXT NOT NULL,
                  currency TEXT NOT NULL,
                  balance REAL NOT NULL DEFAULT 0,
                  theme TEXT DEFAULT 'light',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Expenses table
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  amount REAL NOT NULL,
                  category TEXT NOT NULL,
                  description TEXT,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Planned payments table
    c.execute('''CREATE TABLE IF NOT EXISTS planned_payments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  title TEXT NOT NULL,
                  amount REAL NOT NULL,
                  payment_date DATE NOT NULL,
                  category TEXT,
                  recurring INTEGER DEFAULT 0,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Budget table
    c.execute('''CREATE TABLE IF NOT EXISTS budget
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  month INTEGER NOT NULL,
                  year INTEGER NOT NULL,
                  amount REAL NOT NULL,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  UNIQUE(user_id, month, year))''')
    
    conn.commit()
    conn.close()

init_db()

# Helper functions
def get_db_connection():
    # Use absolute path to ensure database is in the correct location
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expense_tracker.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_expenses(user_id, days=30):
    conn = get_db_connection()
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    expenses = conn.execute(
        'SELECT * FROM expenses WHERE user_id = ? AND date >= ? ORDER BY date DESC',
        (user_id, start_date)
    ).fetchall()
    conn.close()
    return expenses

def get_user_balance(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT balance FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user['balance'] if user else 0

def update_user_balance(user_id, amount):
    conn = get_db_connection()
    conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        currency = data.get('currency')
        balance = float(data.get('balance', 0))
        
        conn = get_db_connection()
        
        # Check if username or email exists
        existing = conn.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Username or email already exists'})
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Insert user
        conn.execute(
            'INSERT INTO users (username, email, phone, password, currency, balance) VALUES (?, ?, ?, ?, ?, ?)',
            (username, email, phone, hashed_password, currency, balance)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Account created successfully'})
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()
        
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['theme'] = user['theme'] or 'light'
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Get last month expenses
    expenses = get_user_expenses(user_id, 30)
    if expenses is None:
        expenses = []
    
    # Get last 2-3 expenses
    recent_expenses = expenses[:3] if expenses else []
    
    # Get upcoming payments
    conn = get_db_connection()
    upcoming_payments = conn.execute(
        '''SELECT * FROM planned_payments 
           WHERE user_id = ? AND payment_date >= date('now')
           ORDER BY payment_date ASC LIMIT 5''',
        (user_id,)
    ).fetchall()
    conn.close()
    
    return render_template('home.html', user=user, expenses=expenses, 
                         recent_expenses=recent_expenses, upcoming_payments=upcoming_payments)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.get_json()
    user_id = session['user_id']
    amount = float(data.get('amount', 0))
    category = data.get('category')
    description = data.get('description', '')
    is_income = data.get('is_income', False)

    conn = get_db_connection()

    if is_income:
        conn.execute(
            'UPDATE users SET balance = balance + ? WHERE id = ?',
            (amount, user_id)
        )
    else:
        conn.execute(
            'INSERT INTO expenses (user_id, amount, category, description) VALUES (?, ?, ?, ?)',
            (user_id, amount, category, description)
        )
        conn.execute(
            'UPDATE users SET balance = balance - ? WHERE id = ?',
            (amount, user_id)
        )

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Transaction added successfully'})

#Added this edit method 
def edit_expense(expense_id):
    conn = get_db_connection()

    # Fetch expense
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session['user_id'])
    ).fetchone()

    if not expense:
        conn.close()
        return redirect('/all_records')

    categories = [
        "Foods & Drink", "Shopping", "Transportation",
        "Housing", "Vehicle", "Entertainment",
        "Investments", "Other"
    ]

    if request.method == 'POST':
        new_amount = float(request.form['amount'])
        new_category = request.form['category']
        new_description = request.form['description']

        old_amount = expense['amount']
        diff = new_amount - old_amount

        conn.execute(
            """UPDATE expenses
               SET amount = ?, category = ?, description = ?
               WHERE id = ?""",
            (new_amount, new_category, new_description, expense_id)
        )

        conn.execute(
            "UPDATE users SET balance = balance - ? WHERE id = ?",
            (diff, session['user_id'])
        )

        conn.commit()
        conn.close()
        return redirect('/all_records')

    conn.close()
    return render_template(
        'edit_expense.html',
        expense=expense,
        categories=categories
    )
    
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'POST':
        data = request.get_json()
        conn.execute(
            'UPDATE users SET username = ?, email = ?, phone = ?, currency = ? WHERE id = ?',
            (data.get('username'), data.get('email'), data.get('phone'), 
             data.get('currency'), user_id)
        )
        conn.commit()
        session['username'] = data.get('username')
    
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    return render_template('profile.html', user=user)

@app.route('/all_records')
def all_records():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    category_filter = request.args.get('category', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    conn = get_db_connection()
    query = 'SELECT * FROM expenses WHERE user_id = ?'
    params = [user_id]
    
    if category_filter:
        query += ' AND category = ?'
        params.append(category_filter)
    
    if date_from:
        query += ' AND date >= ?'
        params.append(date_from)
    
    if date_to:
        query += ' AND date <= ?'
        params.append(date_to + ' 23:59:59')
    
    query += ' ORDER BY date DESC'
    expenses = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('all_records.html', expenses=expenses)

@app.route('/statistics')
def statistics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('statistics.html')

@app.route('/api/expense_chart')
def expense_chart():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'})
    
    user_id = session['user_id']
    period = request.args.get('period', 'monthly')
    
    conn = get_db_connection()
    
    if period == 'monthly':
        expenses = conn.execute(
            '''SELECT category, SUM(amount) as total 
               FROM expenses 
               WHERE user_id = ? AND date >= datetime('now', '-30 days')
               GROUP BY category''',
            (user_id,)
        ).fetchall()
    elif period == 'yearly':
        expenses = conn.execute(
            '''SELECT category, SUM(amount) as total 
               FROM expenses 
               WHERE user_id = ? AND date >= datetime('now', '-365 days')
               GROUP BY category''',
            (user_id,)
        ).fetchall()
    else:  # daily
        expenses = conn.execute(
            '''SELECT category, SUM(amount) as total 
               FROM expenses 
               WHERE user_id = ? AND date >= datetime('now', '-7 days')
               GROUP BY category''',
            (user_id,)
        ).fetchall()
    
    conn.close()
    
    if not expenses:
        # Return empty chart
        plt.figure(figsize=(8, 8))
        plt.text(0.5, 0.5, 'No expenses yet', ha='center', va='center', fontsize=14)
        plt.axis('off')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return send_file(img, mimetype='image/png')
    
    categories = [e['category'] for e in expenses]
    amounts = [e['total'] for e in expenses]
    
    # Create pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
    plt.title(f'Expenses by Category ({period.capitalize()})')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return send_file(img, mimetype='image/png')

@app.route('/api/balance_chart')
def balance_chart():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'})
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Get balance history (last 30 days)
    expenses = conn.execute(
        '''SELECT date, amount FROM expenses 
           WHERE user_id = ? AND date >= datetime('now', '-30 days')
           ORDER BY date ASC''',
        (user_id,)
    ).fetchall()
    
    user = conn.execute('SELECT balance FROM users WHERE id = ?', (user_id,)).fetchone()
    current_balance = user['balance']
    conn.close()
    
    # Calculate running balance
    dates = []
    balances = []
    running_balance = current_balance
    
    for expense in reversed(expenses):
        running_balance += expense['amount']  # Add back since it was deducted
        try:
            # Try parsing the date - handle different formats
            date_str = expense['date']
            if isinstance(date_str, str):
                # Try different date formats
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date_obj = datetime.fromtimestamp(date_str)
            dates.append(date_obj)
            balances.append(running_balance)
        except Exception as e:
            # Skip invalid dates
            continue
    
    if dates:
        dates.append(datetime.now())
        balances.append(current_balance)
    
    # Create area chart
    plt.figure(figsize=(10, 6))
    if dates and len(dates) > 1:
        plt.fill_between(dates, balances, alpha=0.3)
        plt.plot(dates, balances, linewidth=2)
    elif dates and len(dates) == 1:
        # Only one point, show as horizontal line
        plt.axhline(y=current_balance, color='blue', linewidth=2, label='Balance')
        plt.text(0.5, 0.5, f'Current Balance: {current_balance:.2f}', 
                transform=plt.gca().transAxes, ha='center', va='center', fontsize=12)
    else:
        # No expenses, show current balance
        plt.text(0.5, 0.5, f'No transactions yet\nCurrent Balance: {current_balance:.2f}', 
                transform=plt.gca().transAxes, ha='center', va='center', fontsize=12)
    plt.title('Balance Trend (Last 30 Days)')
    plt.xlabel('Date')
    plt.ylabel('Balance')
    if dates and len(dates) > 1:
        plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return send_file(img, mimetype='image/png')

@app.route('/api/home_pie_chart')
def home_pie_chart():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'})
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    expenses = conn.execute(
        '''SELECT category, SUM(amount) as total 
           FROM expenses 
           WHERE user_id = ? AND date >= datetime('now', '-30 days')
           GROUP BY category''',
        (user_id,)
    ).fetchall()
    conn.close()
    
    if not expenses:
        # Return empty chart
        plt.figure(figsize=(6, 6))
        plt.text(0.5, 0.5, 'No expenses yet', ha='center', va='center')
        plt.axis('off')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return send_file(img, mimetype='image/png')
    
    categories = [e['category'] for e in expenses]
    amounts = [e['total'] for e in expenses]
    
    plt.figure(figsize=(6, 6))
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
    plt.title('Last Month Expenses')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return send_file(img, mimetype='image/png')

@app.route('/planned_payments', methods=['GET', 'POST'])
def planned_payments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'POST':
        data = request.get_json()
        conn.execute(
            '''INSERT INTO planned_payments (user_id, title, amount, payment_date, category, recurring)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, data.get('title'), float(data.get('amount')), 
             data.get('payment_date'), data.get('category'), 
             int(data.get('recurring', 0)))
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Planned payment added'})
    
    payments = conn.execute(
        '''SELECT * FROM planned_payments 
           WHERE user_id = ? 
           ORDER BY payment_date ASC''',
        (user_id,)
    ).fetchall()
    conn.close()
    
    return render_template('planned_payments.html', payments=payments, now=datetime.now())

@app.route('/budget', methods=['GET', 'POST'])
def budget():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'POST':
        data = request.get_json()
        month = int(data.get('month'))
        year = int(data.get('year'))
        amount = float(data.get('amount'))
        
        conn.execute(
            '''INSERT OR REPLACE INTO budget (user_id, month, year, amount)
               VALUES (?, ?, ?, ?)''',
            (user_id, month, year, amount)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Budget set successfully'})
    
    # Get current month budget
    now = datetime.now()
    budget = conn.execute(
        'SELECT * FROM budget WHERE user_id = ? AND month = ? AND year = ?',
        (user_id, now.month, now.year)
    ).fetchone()
    
    # Get current month expenses
    expenses = conn.execute(
        '''SELECT SUM(amount) as total FROM expenses 
           WHERE user_id = ? AND strftime("%m", date) = ? AND strftime("%Y", date) = ?''',
        (user_id, f'{now.month:02d}', str(now.year))
    ).fetchone()
    
    spent = expenses['total'] if expenses['total'] else 0
    conn.close()
    
    return render_template('budget.html', budget=budget, spent=spent, current_month=now.month, current_year=now.year)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        
        if action == 'toggle_theme':
            user = conn.execute('SELECT theme FROM users WHERE id = ?', (user_id,)).fetchone()
            new_theme = 'dark' if (user['theme'] or 'light') == 'light' else 'light'
            conn.execute('UPDATE users SET theme = ? WHERE id = ?', (new_theme, user_id))
            conn.commit()
            conn.close()
            session['theme'] = new_theme
            return jsonify({'success': True, 'theme': new_theme})
        
        elif action == 'delete_expenses':
            conn.execute('DELETE FROM expenses WHERE user_id = ?', (user_id,))
            conn.execute('UPDATE users SET balance = 0 WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'All expense data deleted'})
        
        elif action == 'delete_profile':
            conn.execute('DELETE FROM expenses WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM planned_payments WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM budget WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            session.clear()
            return jsonify({'success': True, 'message': 'Profile deleted'})
    
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    return render_template('settings.html', user=user)

@app.route('/export_statistics')
def export_statistics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    format_type = request.args.get('format', 'pdf')
    period = request.args.get('period', 'monthly')
    
    conn = get_db_connection()
    
    if period == 'monthly':
        expenses = conn.execute(
            '''SELECT category, SUM(amount) as total 
               FROM expenses 
               WHERE user_id = ? AND date >= datetime('now', '-30 days')
               GROUP BY category''',
            (user_id,)
        ).fetchall()
        title = 'Monthly Expenses'
    elif period == 'yearly':
        expenses = conn.execute(
            '''SELECT category, SUM(amount) as total 
               FROM expenses 
               WHERE user_id = ? AND date >= datetime('now', '-365 days')
               GROUP BY category''',
            (user_id,)
        ).fetchall()
        title = 'Yearly Expenses'
    else:
        expenses = conn.execute(
            '''SELECT category, SUM(amount) as total 
               FROM expenses 
               WHERE user_id = ? AND date >= datetime('now', '-7 days')
               GROUP BY category''',
            (user_id,)
        ).fetchall()
        title = 'Weekly Expenses'
    
    conn.close()
    
    categories = [e['category'] for e in expenses]
    amounts = [e['total'] for e in expenses]
    
    if format_type == 'pdf':
        # Create PDF with bar chart
        img = io.BytesIO()
        with PdfPages(img) as pdf:
            fig, ax = plt.subplots(figsize=(10, 6))
            if categories:
                ax.bar(categories, amounts)
                ax.set_title(title)
                ax.set_xlabel('Category')
                ax.set_ylabel('Amount')
                plt.xticks(rotation=45)
                plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)
        img.seek(0)
        return send_file(img, mimetype='application/pdf', as_attachment=True, 
                        download_name=f'expenses_{period}.pdf')
    else:
        # Create JPG
        plt.figure(figsize=(10, 6))
        if categories:
            plt.bar(categories, amounts)
            plt.title(title)
            plt.xlabel('Category')
            plt.ylabel('Amount')
            plt.xticks(rotation=45)
            plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='jpg', dpi=150)
        img.seek(0)
        plt.close()
        return send_file(img, mimetype='image/jpeg', as_attachment=True, 
                        download_name=f'expenses_{period}.jpg')

if __name__ == '__main__':
    app.run(debug=True)
