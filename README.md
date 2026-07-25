# Library Management System

A Flask + MySQL web app for managing a library's books, members, and lending —
with search, due dates, and automatic late fines.

## Features

- **Dashboard** — books/members/loans at a glance, plus what's due soonest
- **Books** — add, edit, delete, search by title/author/ISBN, tracks copies available
- **Members** — add, edit, delete, search by name/email
- **Borrow / Return** — issue a book (14-day loan by default), return it and
  auto-calculate a late fine ($0.50/day by default)
- **Transactions** — full loan history with status and fines
- **Login** — single admin account gates the whole app

## Tech stack

Python (Flask) · MySQL (via PyMySQL) · HTML/CSS/JS (Jinja2 templates, no frontend framework)

## Setup

**1. Create the database**

Make sure MySQL is installed and running, then:

```bash
mysql -u root -p < schema.sql
```

This creates the `library_db` database, all four tables, a default admin
login, and a few sample books/members so the app isn't empty on first run.

**2. Configure your credentials**

Open `config.py` and set `DB_USER` / `DB_PASSWORD` to match your MySQL setup.

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

(Use a virtual environment if you'd like: `python -m venv venv && source venv/bin/activate` first.)

**4. Run it**

```bash
python app.py
```

Visit **http://localhost:5000** and log in with:

- Username: `admin`
- Password: `admin123`

Change this password (or add your own admin row) before using this anywhere
beyond your own machine — see "Next steps" below.

## Project structure

```
library_management_system/
├── app.py               # Routes and application logic
├── config.py             # DB credentials, secret key, loan/fine settings
├── schema.sql             # Database schema + seed data
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── js/script.js
└── templates/             # Jinja2 HTML templates
```

## How the data fits together

- **books** — catalog entries; `available_copies` decrements on borrow, increments on return
- **members** — registered patrons
- **transactions** — one row per loan: borrow date, due date, return date, fine, status
- **admins** — login accounts for staff

Deleting a book or member is blocked while they have an active (unreturned) loan.

## Next steps / ideas if you want to extend this

- Hash a new admin password with `werkzeug.security.generate_password_hash(...)`
  and insert it into the `admins` table to add more staff logins, or build a
  self-service "change password" page
- Add pagination once the catalog grows large
- Add a "renew" action that pushes a due date out without a full return/reissue
- Export transactions to CSV for reporting
- Add member-facing self-checkout instead of staff-only issuing

## Notes on the design

The visual style leans into the library's own materials — a warm ledger
green, brass, and manila palette, with due dates rendered as small stamped
badges (green = on loan, red = overdue). All of it is plain CSS in
`static/css/style.css` — no framework — so it's easy to reskin.
