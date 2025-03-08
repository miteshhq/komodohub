# Komodo Hub - Conservation Platform Setup Guide

## 1. Install Python Dependencies

Run the following commands to install the required Python packages:

```bash
pip install flask flask-login flask-sqlalchemy flask-wtf gunicorn sqlalchemy email-validator.post1 werkzeug wtforms python-dotenv
```

## 2. Database Setup (SQLite)

SQLite is a lightweight, file-based database that does not require additional setup.

- The database file will be stored locally in the project directory as `database.db`.

## 3. Environment Configuration

Create a `.env` file in the project root directory and add the following configuration:

```env
SESSION_SECRET=your-secret-key-here
DATABASE_URL=sqlite:///database.db
ADMIN_PASS=adminkomodo
```

## 4. Running the Application

### Local Access

- Start the Flask application:

  ```bash
  flask run
  ```
  
  or try running

  ```bash
  python -m flask run
  ```

- Open in your browser: [http://localhost:5000](http://localhost:5000)

### Network Access

- Access via your IP: `http://<your-ip>:5000`

## 5. Troubleshooting Guide

### 5.1 Missing Dependencies

If you encounter missing dependencies, follow these steps:

```bash
# Verify Python version
python --version

# Check installed packages
pip list

# Reinstall dependencies
pip install -r requirements.txt
```

## 6. Testing

### 6.1 Test Accounts

Use the following credentials to test different roles in the application:

#### Teacher Account

- **Email:** <teacher@komodohub.org>
- **Password:** password123
- **Role:** Teacher

#### Student Account

- **Email:** <student@komodohub.org>
- **Password:** password123
- **Role:** Student

#### Member Account

- **Email:** <member@komodohub.org>
- **Password:** password123
- **Role:** Member

#### Admin Account

- **Email:** <admin@komodohub.org>
- **Password:** Defined in `.env` file under `ADMIN_PASS`
- **Role:** Admin
