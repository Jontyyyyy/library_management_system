"""
Library Management System
A Flask + MySQL app for managing books, members, and borrowing.

Setup:
    1. mysql -u root -p < schema.sql
    2. edit config.py with your MySQL credentials
    3. pip install -r requirements.txt
    4. python app.py
    5. open http://localhost:5000  (login: admin / admin123)
"""

from datetime import date, timedelta
from functools import wraps

import certifi
import pymysql
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


# ---------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------
def get_db():
    """Open a fresh connection for this request. Rows come back as dicts."""
    kwargs = dict(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    if config.DB_SSL:
        # Cloud MySQL-compatible hosts (TiDB Cloud, PlanetScale, etc.) require
        # TLS. certifi ships a trusted CA bundle so this works cross-platform
        # without hunting for your OS's certificate path.
        kwargs["ssl_ca"] = certifi.where()
        kwargs["ssl_verify_cert"] = True
        kwargs["ssl_verify_identity"] = True
    return pymysql.connect(**kwargs)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def student_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "student_member_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("student_login"))
        return view(*args, **kwargs)

    return wrapped


# ---------------------------------------------------------------
# Auth
# ---------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
                admin = cur.fetchone()
        finally:
            conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["admin_id"] = admin["admin_id"]
            session["username"] = admin["username"]
            return redirect(url_for("index"))

        flash("Incorrect username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------
# Student login (separate from staff — read-only, scoped to their own loans)
# ---------------------------------------------------------------
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM members WHERE email = %s", (email,))
                member = cur.fetchone()
        finally:
            conn.close()

        if member and member.get("password") and check_password_hash(member["password"], password):
            session["student_member_id"] = member["member_id"]
            session["student_name"] = member["name"]
            return redirect(url_for("student_dashboard"))

        flash("Incorrect email or password.", "error")

    return render_template("student_login.html")


@app.route("/student/logout")
def student_logout():
    session.pop("student_member_id", None)
    session.pop("student_name", None)
    flash("You've been logged out.", "success")
    return redirect(url_for("student_login"))


@app.route("/student")
@student_login_required
def student_dashboard():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT t.*, b.title, b.author
                   FROM transactions t
                   JOIN books b ON b.book_id = t.book_id
                   WHERE t.member_id = %s
                   ORDER BY (t.status = 'borrowed') DESC, t.due_date ASC""",
                (session["student_member_id"],),
            )
            loans = cur.fetchall()
    finally:
        conn.close()

    return render_template(
        "student_dashboard.html",
        loans=loans,
        today=date.today(),
        student_name=session.get("student_name"),
    )


# ---------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------
@app.route("/")
@login_required
def index():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM books")
            total_books = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM members")
            total_members = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM transactions WHERE status = 'borrowed'")
            borrowed_count = cur.fetchone()["c"]

            cur.execute(
                "SELECT COUNT(*) AS c FROM transactions "
                "WHERE status = 'borrowed' AND due_date < %s",
                (date.today(),),
            )
            overdue_count = cur.fetchone()["c"]

            cur.execute(
                """SELECT t.transaction_id, t.due_date, b.title, m.name
                   FROM transactions t
                   JOIN books b ON b.book_id = t.book_id
                   JOIN members m ON m.member_id = t.member_id
                   WHERE t.status = 'borrowed'
                   ORDER BY t.due_date ASC
                   LIMIT 6"""
            )
            upcoming = cur.fetchall()
    finally:
        conn.close()

    return render_template(
        "index.html",
        total_books=total_books,
        total_members=total_members,
        borrowed_count=borrowed_count,
        overdue_count=overdue_count,
        upcoming=upcoming,
        today=date.today(),
    )


# ---------------------------------------------------------------
# Books
# ---------------------------------------------------------------
@app.route("/books")
@login_required
def books():
    q = request.args.get("q", "").strip()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if q:
                like = f"%{q}%"
                cur.execute(
                    """SELECT * FROM books
                       WHERE title LIKE %s OR author LIKE %s OR isbn LIKE %s
                       ORDER BY title""",
                    (like, like, like),
                )
            else:
                cur.execute("SELECT * FROM books ORDER BY title")
            book_rows = cur.fetchall()
    finally:
        conn.close()

    return render_template("books.html", books=book_rows, q=q)


@app.route("/books/add", methods=["GET", "POST"])
@login_required
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        isbn = request.form.get("isbn", "").strip() or None
        genre = request.form.get("genre", "").strip()
        copies = max(1, int(request.form.get("copies", 1)))

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO books
                       (title, author, isbn, genre, total_copies, available_copies)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (title, author, isbn, genre, copies, copies),
                )
            conn.commit()
        finally:
            conn.close()

        flash(f'"{title}" was added to the catalog.', "success")
        return redirect(url_for("books"))

    return render_template("book_form.html", book=None)


@app.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    conn = get_db()
    try:
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            author = request.form.get("author", "").strip()
            isbn = request.form.get("isbn", "").strip() or None
            genre = request.form.get("genre", "").strip()
            new_total = max(1, int(request.form.get("copies", 1)))

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT total_copies, available_copies FROM books WHERE book_id = %s",
                    (book_id,),
                )
                row = cur.fetchone()
                if row is None:
                    flash("That book no longer exists.", "error")
                    return redirect(url_for("books"))

                # Keep available_copies in step with any change to total_copies
                diff = new_total - row["total_copies"]
                new_available = max(0, min(new_total, row["available_copies"] + diff))

                cur.execute(
                    """UPDATE books
                       SET title = %s, author = %s, isbn = %s, genre = %s,
                           total_copies = %s, available_copies = %s
                       WHERE book_id = %s""",
                    (title, author, isbn, genre, new_total, new_available, book_id),
                )
            conn.commit()
            flash(f'"{title}" was updated.', "success")
            return redirect(url_for("books"))

        with conn.cursor() as cur:
            cur.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
            book = cur.fetchone()
    finally:
        conn.close()

    if book is None:
        flash("That book no longer exists.", "error")
        return redirect(url_for("books"))

    return render_template("book_form.html", book=book)


@app.route("/books/delete/<int:book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS c FROM transactions WHERE book_id = %s AND status = 'borrowed'",
                (book_id,),
            )
            if cur.fetchone()["c"] > 0:
                flash("Can't delete a book that's currently on loan.", "error")
            else:
                cur.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
                conn.commit()
                flash("Book removed from the catalog.", "success")
    finally:
        conn.close()

    return redirect(url_for("books"))


# ---------------------------------------------------------------
# Members
# ---------------------------------------------------------------
@app.route("/members")
@login_required
def members():
    q = request.args.get("q", "").strip()
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if q:
                like = f"%{q}%"
                cur.execute(
                    """SELECT * FROM members
                       WHERE name LIKE %s OR email LIKE %s
                       ORDER BY name""",
                    (like, like),
                )
            else:
                cur.execute("SELECT * FROM members ORDER BY name")
            member_rows = cur.fetchall()
    finally:
        conn.close()

    return render_template("members.html", members=member_rows, q=q)


@app.route("/members/add", methods=["GET", "POST"])
@login_required
def add_member():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
        password_hash = generate_password_hash(password) if password else None

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO members (name, email, phone, password) VALUES (%s, %s, %s, %s)",
                    (name, email, phone, password_hash),
                )
            conn.commit()
        except pymysql.err.IntegrityError:
            flash("A member with that email already exists.", "error")
            return render_template("member_form.html", member=None)
        finally:
            conn.close()

        flash(f"{name} was added as a member.", "success")
        return redirect(url_for("members"))

    return render_template("member_form.html", member=None)


@app.route("/members/edit/<int:member_id>", methods=["GET", "POST"])
@login_required
def edit_member(member_id):
    conn = get_db()
    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            password = request.form.get("password", "").strip()

            try:
                with conn.cursor() as cur:
                    if password:
                        cur.execute(
                            "UPDATE members SET name = %s, email = %s, phone = %s, password = %s WHERE member_id = %s",
                            (name, email, phone, generate_password_hash(password), member_id),
                        )
                    else:
                        cur.execute(
                            "UPDATE members SET name = %s, email = %s, phone = %s WHERE member_id = %s",
                            (name, email, phone, member_id),
                        )
                conn.commit()
            except pymysql.err.IntegrityError:
                flash("A member with that email already exists.", "error")
                return render_template("member_form.html", member={"member_id": member_id, "name": name, "email": email, "phone": phone})

            flash(f"{name}'s details were updated.", "success")
            return redirect(url_for("members"))

        with conn.cursor() as cur:
            cur.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
            member = cur.fetchone()
    finally:
        conn.close()

    if member is None:
        flash("That member no longer exists.", "error")
        return redirect(url_for("members"))

    return render_template("member_form.html", member=member)


@app.route("/members/delete/<int:member_id>", methods=["POST"])
@login_required
def delete_member(member_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS c FROM transactions WHERE member_id = %s AND status = 'borrowed'",
                (member_id,),
            )
            if cur.fetchone()["c"] > 0:
                flash("Can't remove a member who currently has a book out.", "error")
            else:
                cur.execute("DELETE FROM members WHERE member_id = %s", (member_id,))
                conn.commit()
                flash("Member removed.", "success")
    finally:
        conn.close()

    return redirect(url_for("members"))


# ---------------------------------------------------------------
# Borrow / return
# ---------------------------------------------------------------
@app.route("/borrow", methods=["GET", "POST"])
@login_required
def borrow():
    conn = get_db()
    try:
        if request.method == "POST":
            book_id = int(request.form["book_id"])
            member_id = int(request.form["member_id"])
            borrow_date = date.today()
            due_date = borrow_date + timedelta(days=config.LOAN_PERIOD_DAYS)

            with conn.cursor() as cur:
                cur.execute("SELECT available_copies, title FROM books WHERE book_id = %s", (book_id,))
                book = cur.fetchone()

                if not book or book["available_copies"] < 1:
                    flash("That book isn't available right now.", "error")
                else:
                    cur.execute(
                        """INSERT INTO transactions
                           (book_id, member_id, borrow_date, due_date, status)
                           VALUES (%s, %s, %s, %s, 'borrowed')""",
                        (book_id, member_id, borrow_date, due_date),
                    )
                    cur.execute(
                        "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = %s",
                        (book_id,),
                    )
                    conn.commit()
                    flash(f'"{book["title"]}" issued — due back {due_date.strftime("%b %d, %Y")}.', "success")
            return redirect(url_for("borrow"))

        with conn.cursor() as cur:
            cur.execute("SELECT * FROM books WHERE available_copies > 0 ORDER BY title")
            available_books = cur.fetchall()
            cur.execute("SELECT * FROM members ORDER BY name")
            member_rows = cur.fetchall()
    finally:
        conn.close()

    return render_template("borrow.html", available_books=available_books, members=member_rows)


@app.route("/return/<int:transaction_id>", methods=["POST"])
@login_required
def return_book(transaction_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM transactions WHERE transaction_id = %s", (transaction_id,))
            txn = cur.fetchone()

            if not txn or txn["status"] != "borrowed":
                flash("That loan was already closed out.", "error")
                return redirect(url_for("transactions"))

            today = date.today()
            days_late = (today - txn["due_date"]).days
            fine = round(days_late * config.FINE_PER_DAY, 2) if days_late > 0 else 0.00

            cur.execute(
                "UPDATE transactions SET return_date = %s, status = 'returned', fine = %s WHERE transaction_id = %s",
                (today, fine, transaction_id),
            )
            cur.execute(
                "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = %s",
                (txn["book_id"],),
            )
            conn.commit()

            if fine > 0:
                flash(f"Book returned — ${fine:.2f} late fine applied.", "success")
            else:
                flash("Book returned on time. No fine.", "success")
    finally:
        conn.close()

    return redirect(url_for("transactions"))


@app.route("/transactions")
@login_required
def transactions():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT t.*, b.title, m.name
                   FROM transactions t
                   JOIN books b ON b.book_id = t.book_id
                   JOIN members m ON m.member_id = t.member_id
                   ORDER BY t.borrow_date DESC"""
            )
            txn_rows = cur.fetchall()
    finally:
        conn.close()

    return render_template("transactions.html", transactions=txn_rows, today=date.today())


if __name__ == "__main__":
    import os

    debug_mode = (os.environ.get("FLASK_DEBUG") or "true").lower() == "true"
    app.run(debug=debug_mode)
