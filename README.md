# Expense Tracker Web Application

A comprehensive expense tracking web application built with Flask, HTML, CSS (Bootstrap), and JavaScript. This application helps users manage their expenses, track their balance, set budgets, and plan future payments.

## Features

### 1. User Authentication
- **Signup Page**: Create account with username, email, phone number, password, currency selection, and initial balance
- **Login Page**: Secure login with username and password
- Real-time form validation for all fields

### 2. Home Page
- Welcome message with user's name
- Current balance display
- Last month expenses pie chart (matplotlib)
- Recent expenses overview (last 2-3 records) with "Show More" option
- Balance trend area graph (last 30 days)
- Upcoming payments section (displays when user has planned payments)

### 3. Fixed Add Expense Button
- Floating '+' button in bottom right corner
- Visible on all pages except: Profile, Logout, Login, Signup
- Add expenses with categories:
  - Foods & Drink
  - Shopping
  - Transportation
  - Housing
  - Vehicle
  - Entertainment
  - Investments
  - Other
- Option to add income (increment balance)

### 4. Navigation Bar
- **Home**: Default page with dashboard
- **Profile**: View and edit user details
- **All Records**: View all expense records with filtering by date and category
- **Statistics**: View expense graphs (daily, monthly, yearly) with export to PDF/JPG
- **Planned Payments**: Manage future payments (SIP, loans, rent, subscriptions, EMI, etc.)
- **Budget**: Set monthly budget with exceed warnings
- **Settings**: Theme preferences, logout, delete data/profile

## Installation

1. **Navigate to the project directory:**
   ```bash
   cd expense_tracker
   ```

2. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the application:**
   Open your browser and go to: `http://localhost:5000`

## Project Structure

```
expense_tracker/
├── app.py                 # Main Flask application
├── requirements.txt        # Python dependencies
├── expense_tracker.db     # SQLite database (created automatically)
├── templates/             # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── signup.html
│   ├── home.html
│   ├── profile.html
│   ├── all_records.html
│   ├── statistics.html
│   ├── planned_payments.html
│   ├── budget.html
│   └── settings.html
└── static/
    ├── css/
    │   └── style.css      # Custom CSS styles
    └── js/
        ├── main.js        # Common JavaScript functions
        └── signup.js      # Signup form validation
```

## Database Schema

The application uses SQLite with the following tables:

- **users**: User accounts (username, email, phone, password, currency, balance, theme)
- **expenses**: Expense records (user_id, amount, category, description, date)
- **planned_payments**: Future payments (user_id, title, amount, payment_date, category, recurring)
- **budget**: Monthly budgets (user_id, month, year, amount)

## Usage

1. **Sign Up**: Create a new account with your details
2. **Login**: Access your account
3. **Add Expenses**: Use the floating '+' button to add expenses or income
4. **View Statistics**: Check your spending patterns with graphs
5. **Set Budget**: Set monthly spending limits
6. **Plan Payments**: Add upcoming payments like rent, loans, etc.
7. **Manage Profile**: Update your information and preferences

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **JavaScript**: Vanilla JavaScript
- **Database**: SQLite
- **Charts**: Matplotlib
- **Security**: Flask-Bcrypt for password hashing

## Notes

- The database file (`expense_tracker.db`) is created automatically on first run
- All passwords are hashed using bcrypt
- Charts are generated using matplotlib and served as images
- The application supports dark and light themes
- All pages are responsive and work on mobile devices

## Security Notes

- Change the `secret_key` in `app.py` before deploying to production
- Use environment variables for sensitive configuration
- Consider using a production WSGI server (like Gunicorn) for deployment
