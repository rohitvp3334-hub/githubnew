from flask import Flask, request, redirect, url_for, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "campusconnect_secret_key"

DB = "campusconnect.db"

ADMIN_EMAIL = "rohitvp3334@gmail.com"
ADMIN_PASSWORD = "Rohit0506@@"

# ============================================================
# DATABASE
# ============================================================

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'Student',
            department TEXT,
            approved INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            skills TEXT,
            owner TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT,
            semester TEXT,
            owner TEXT NOT NULL,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            owner TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            amount REAL,
            category TEXT,
            owner TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            owner TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            sender TEXT,
            message TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS role_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            requested_role TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reset_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    # Permanent Admin
    admin = conn.execute(
        "SELECT * FROM users WHERE email=?",
        (ADMIN_EMAIL,)
    ).fetchone()

    if not admin:
        conn.execute("""
            INSERT INTO users
            (name,email,password,role,department,approved)
            VALUES (?,?,?,?,?,?)
        """, (
            "Rohit Patil",
            ADMIN_EMAIL,
            generate_password_hash(ADMIN_PASSWORD),
            "Admin",
            "Computer",
            1
        ))

    conn.commit()
    conn.close()


init_db()


# ============================================================
# COMMON HTML
# ============================================================

STYLE = """
<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background:
        radial-gradient(circle at top left,#1e3a8a,transparent 35%),
        radial-gradient(circle at bottom right,#581c87,transparent 35%),
        #020617;
    color: white;
    min-height: 100vh;
}

nav {
    background: rgba(2,6,23,.92);
    border-bottom: 1px solid #334155;
    padding: 15px 5%;
    display: flex;
    align-items: center;
    gap: 10px;
    position: sticky;
    top: 0;
    z-index: 10;
}

.logo {
    font-size: 24px;
    font-weight: bold;
    color: #60a5fa;
    margin-right: auto;
}

nav a {
    color: white;
    text-decoration: none;
    padding: 9px 12px;
    border-radius: 8px;
}

nav a:hover {
    background: #1e293b;
}

.container {
    width: 92%;
    max-width: 1200px;
    margin: 35px auto;
}

.hero {
    text-align: center;
    padding: 70px 20px;
}

.hero h1 {
    font-size: 65px;
    margin: 10px;
    color: #60a5fa;
}

.hero p {
    font-size: 20px;
    color: #cbd5e1;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit,minmax(250px,1fr));
    gap: 18px;
}

.card {
    background: rgba(15,23,42,.90);
    border: 1px solid #334155;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 18px;
}

.card:hover {
    border-color: #6366f1;
    transform: translateY(-2px);
}

.feature {
    min-height: 170px;
}

.btn {
    display: inline-block;
    border: none;
    background: linear-gradient(135deg,#4f46e5,#7c3aed);
    color: white;
    padding: 11px 17px;
    border-radius: 9px;
    text-decoration: none;
    cursor: pointer;
    font-weight: bold;
}

.btn:hover {
    opacity: .85;
}

.danger {
    background: #dc2626;
}

.green {
    background: #059669;
}

input, textarea, select {
    width: 100%;
    padding: 12px;
    margin: 7px 0 14px;
    border-radius: 9px;
    border: 1px solid #475569;
    background: #0f172a;
    color: white;
}

textarea {
    min-height: 110px;
}

.form {
    max-width: 600px;
    margin: auto;
}

.flash {
    background: #075985;
    padding: 13px;
    border-radius: 9px;
    margin-bottom: 15px;
}

.stat {
    background: #111827;
    border: 1px solid #334155;
    padding: 20px;
    border-radius: 15px;
}

.number {
    font-size: 35px;
    color: #a78bfa;
    font-weight: bold;
}

.tag {
    display: inline-block;
    background: #1e293b;
    padding: 5px 8px;
    border-radius: 7px;
    margin: 3px;
}

.chat {
    height: 400px;
    overflow-y: auto;
    background: #020617;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 15px;
}

.message {
    background: #1e293b;
    padding: 10px;
    border-radius: 10px;
    margin: 8px 0;
}

@media(max-width:700px) {
    .hero h1 {
        font-size: 43px;
    }

    nav {
        flex-wrap: wrap;
    }

    .logo {
        width: 100%;
    }
}

</style>
"""


def page(title, content):

    user = None

    if "user_id" in session:
        conn = db()
        user = conn.execute(
            "SELECT * FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()
        conn.close()

    nav = ""

    if user:

        nav = f"""
        <nav>
            <div class="logo">🎓 CampusConnect</div>

            <a href="/">🏠</a>
            <a href="/projects">🚀 Projects</a>
            <a href="/notes">📚 Notes</a>
            <a href="/sports">🏆 Sports</a>
            <a href="/expenses">💰 Expenses</a>
            <a href="/groups">💬 Groups</a>
        """

        if user["role"] == "Admin":
            nav += '<a href="/admin">🛡️ Admin</a>'

        nav += '<a href="/logout">Logout</a></nav>'

    else:

        nav = """
        <nav>
            <div class="logo">🎓 CampusConnect</div>
            <a href="/login">Login</a>
            <a class="btn" href="/register">Join</a>
        </nav>
        """

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width,initial-scale=1">

        <title>{title}</title>

        {STYLE}

    </head>

    <body>

        {nav}

        <div class="container">

            {content}

        </div>

    </body>

    </html>
    """


def current_user():

    if "user_id" not in session:
        return None

    conn = db()

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return user


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    if current_user():
        return redirect("/dashboard")

    content = """
    <div class="hero">

        <div style="font-size:80px">🎓</div>

        <h1>CampusConnect</h1>

        <p>
        One platform connecting students and teachers.
        </p>

        <p>
        Projects • Notes • Sports • Expenses • Groups
        </p>

        <br>

        <a class="btn" href="/register">
            🚀 Get Started
        </a>

        <a class="btn" href="/login">
            🔐 Login
        </a>

    </div>

    <div class="grid">

        <div class="card feature">
            <h2>🚀 Project Finder</h2>
            <p>Find students for your project.</p>
        </div>

        <div class="card feature">
            <h2>📚 Notes Hub</h2>
            <p>Share and access study material.</p>
        </div>

        <div class="card feature">
            <h2>🏆 Sports</h2>
            <p>College sports announcements.</p>
        </div>

        <div class="card feature">
            <h2>💰 Expense Tracker</h2>
            <p>Track your student expenses.</p>
        </div>

        <div class="card feature">
            <h2>💬 Groups</h2>
            <p>Create student and teacher groups.</p>
        </div>

        <div class="card feature">
            <h2>🛡️ Admin Control</h2>
            <p>Manage your campus community.</p>
        </div>

    </div>
    """

    return page("CampusConnect", content)


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"].lower().strip()
        password = request.form["password"]
        department = request.form["department"]
        requested_role = request.form["role"]

        if email == ADMIN_EMAIL:
            return page(
                "Error",
                """
                <div class="card">
                    <h2>❌ This email belongs to the Permanent Admin.</h2>
                    <a class="btn" href="/login">Login as Admin</a>
                </div>
                """
            )

        conn = db()

        existing = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if existing:

            conn.close()

            return page(
                "Account Exists",
                """
                <div class="card">
                    <h2>Account already exists.</h2>
                    <a class="btn" href="/login">Login</a>
                </div>
                """
            )

        conn.execute("""
            INSERT INTO users
            (name,email,password,role,department)
            VALUES (?,?,?,?,?)
        """, (
            name,
            email,
            generate_password_hash(password),
            "Student",
            department
        ))

        if requested_role in ["Teacher", "Admin"]:

            conn.execute("""
                INSERT INTO role_requests
                (name,email,requested_role)
                VALUES (?,?,?)
            """, (
                name,
                email,
                requested_role
            ))

        conn.commit()
        conn.close()

        return redirect("/login")

    content = """
    <div class="card form">

        <h1>🎓 Create CampusConnect Account</h1>

        <form method="POST">

            <input
                name="name"
                placeholder="Full Name"
                required
            >

            <input
                name="email"
                type="email"
                placeholder="Email"
                required
            >

            <input
                name="password"
                type="password"
                placeholder="Password"
                required
            >

            <input
                name="department"
                placeholder="Department"
            >

            <label>Requested Role</label>

            <select name="role">

                <option>Student</option>

                <option>Teacher</option>

                <option>Admin</option>

            </select>

            <button class="btn">
                Create Account
            </button>

        </form>

    </div>
    """

    return page("Register", content)


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].lower().strip()
        password = request.form["password"]

        conn = db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            return redirect("/dashboard")

        return page(
            "Login Error",
            """
            <div class="card form">

                <h2>❌ Invalid Login</h2>

                <p>
                Check your email and password.
                </p>

                <a class="btn" href="/login">
                    Try Again
                </a>

            </div>
            """
        )

    content = """
    <div class="card form">

        <h1>👋 Welcome Back</h1>

        <form method="POST">

            <input
                type="email"
                name="email"
                placeholder="Email"
                required
            >

            <input
                type="password"
                name="password"
                placeholder="Password"
                required
            >

            <button class="btn">
                🔐 Login
            </button>

        </form>

        <br>

        <a href="/forgot">
            Forgot Password?
        </a>

        <p>
        Don't have an account?
        <a href="/register">Create one</a>
        </p>

    </div>
    """

    return page("Login", content)


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    user = current_user()

    if not user:
        return redirect("/login")

    conn = db()

    project_count = conn.execute(
        "SELECT COUNT(*) FROM projects"
    ).fetchone()[0]

    notes_count = conn.execute(
        "SELECT COUNT(*) FROM notes"
    ).fetchone()[0]

    sports_count = conn.execute(
        "SELECT COUNT(*) FROM sports"
    ).fetchone()[0]

    expense_total = conn.execute(
        "SELECT SUM(amount) FROM expenses WHERE owner=?",
        (user["name"],)
    ).fetchone()[0] or 0

    conn.close()

    content = f"""

    <h1>Welcome, {user['name']} 👋</h1>

    <p>
    Role: <b>{user['role']}</b>
    |
    Department: <b>{user['department']}</b>
    </p>

    <div class="grid">

        <div class="stat">
            <div class="number">{project_count}</div>
            Projects
        </div>

        <div class="stat">
            <div class="number">{notes_count}</div>
            Notes
        </div>

        <div class="stat">
            <div class="number">{sports_count}</div>
            Sports Posts
        </div>

        <div class="stat">
            <div class="number">₹{expense_total}</div>
            My Expenses
        </div>

    </div>

    <br>

    <div class="grid">

        <div class="card feature">
            <h2>🚀 Project Finder</h2>
            <p>Find project partners.</p>
            <a class="btn" href="/projects">Open</a>
        </div>

        <div class="card feature">
            <h2>📚 Notes Hub</h2>
            <p>Access study notes.</p>
            <a class="btn" href="/notes">Open</a>
        </div>

        <div class="card feature">
            <h2>🏆 Sports</h2>
            <p>College sports updates.</p>
            <a class="btn" href="/sports">Open</a>
        </div>

        <div class="card feature">
            <h2>💰 Expenses</h2>
            <p>Track your spending.</p>
            <a class="btn" href="/expenses">Open</a>
        </div>

        <div class="card feature">
            <h2>💬 Groups</h2>
            <p>Chat with students and teachers.</p>
            <a class="btn" href="/groups">Open</a>
        </div>

    </div>
    """

    return page("Dashboard", content)


# ============================================================
# PROJECT FINDER
# ============================================================

@app.route("/projects", methods=["GET", "POST"])
def projects():

    user = current_user()

    if not user:
        return redirect("/login")

    conn = db()

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        skills = request.form["skills"]

        conn.execute("""
            INSERT INTO projects
            (title,description,skills,owner,created_at)
            VALUES (?,?,?,?,?)
        """, (
            title,
            description,
            skills,
            user["name"],
            datetime.now().strftime("%d-%m-%Y %H:%M")
        ))

        conn.commit()

    projects = conn.execute(
        "SELECT * FROM projects ORDER BY id DESC"
    ).fetchall()

    conn.close()

    create = """

    <div class="card">

        <h2>➕ Create Project</h2>

        <form method="POST">

            <input
                name="title"
                placeholder="Project Title"
                required
            >

            <input
                name="skills"
                placeholder="Required Skills e.g. Python, ML"
            >

            <textarea
                name="description"
                placeholder="Describe your project"
                required
            ></textarea>

            <button class="btn">
                🚀 Publish Project
            </button>

        </form>

    </div>
    """

    cards = ""

    for p in projects:

        delete = ""

        if p["owner"] == user["name"] or user["role"] == "Admin":

            delete = f"""
            <form method="POST"
                  action="/projects/delete/{p['id']}">

                <button class="btn danger">
                    Delete
                </button>

            </form>
            """

        cards += f"""

        <div class="card">

            <h2>🚀 {p['title']}</h2>

            <p>{p['description']}</p>

            <p>

            <b>Skills:</b>
            {p['skills']}

            </p>

            <p>
            👤 {p['owner']}
            |
            👁 {p['views']}
            </p>

            {delete}

        </div>

        """

    content = f"""

    <h1>🚀 Project Finder</h1>

    <p>
    Find students from 1st to 4th year for your project.
    </p>

    {create}

    <div class="grid">
        {cards}
    </div>

    """

    return page("Projects", content)


@app.route("/projects/delete/<int:pid>", methods=["POST"])
def delete_project(pid):

    user = current_user()

    if not user:
        return redirect("/login")

    conn = db()

    project = conn.execute(
        "SELECT * FROM projects WHERE id=?",
        (pid,)
    ).fetchone()

    if project:

        if (
            project["owner"] == user["name"]
            or user["role"] == "Admin"
        ):

            conn.execute(
                "DELETE FROM projects WHERE id=?",
                (pid,)
            )

            conn.commit()

    conn.close()

    return redirect("/projects")


# ============================================================
# NOTES
# ============================================================

@app.route("/notes", methods=["GET", "POST"])
def notes():

    user = current_user()

    if not user:
        return redirect("/login")

    conn = db()

    if request.method == "POST":

        if user["role"] not in ["Teacher", "Admin"]:

            return page(
                "Permission",
                """
                <div class="card">
                    <h2>❌ Only Teachers and Admin can upload notes.</h2>
                </div>
                """
            )

        conn.execute("""
            INSERT INTO notes
            (title,subject,semester,owner,created_at)
            VALUES (?,?,?,?,?)
        """, (
            request.form["title"],
            request.form["subject"],
            request.form["semester"],
            user["name"],
            datetime.now().strftime("%d-%m-%Y %H:%M")
        ))

        conn.commit()

    notes_list = conn.execute(
        "SELECT * FROM notes ORDER BY id DESC"
    ).fetchall()

    conn.close()

    upload = ""

    if user["role"] in ["Teacher", "Admin"]:

        upload = """

        <div class="card">

            <h2>➕ Share Notes</h2>

            <form method="POST">

                <input
                    name="title"
                    placeholder="Note Title"
                    required
                >

                <input
                    name="subject"
                    placeholder="Subject"
                >

                <input
                    name="semester"
                    placeholder="Semester"
                >

                <button class="btn">
                    📚 Share Note
                </button>

            </form>

        </div>

        """

    cards = ""

    for n in notes_list:

        delete = ""

        if (
            n["owner"] == user["name"]
            or user["role"] == "Admin"
        ):

            delete = f"""

            <form method="POST"
                  action="/notes/delete/{n['id']}">

                <button class="btn danger">
                    Delete
                </button>

            </form>

            """

        cards += f"""

        <div class="card">

            <h2>📄 {n['title']}</h2>

            <p>
            Subject: {n['subject']}
            </p>

            <p>
            Semester: {n['semester']}
            </p>

            <p>
            Shared by: {n['owner']}
            </p>

            {delete}

        </div>

        """

    return page(
        "Notes Hub",
        f"""
        <h1>📚 Student Notes Hub</h1>

        {upload}

        <div class="grid">
            {cards}
        </div>
        """
    )


@app.route("/notes/delete/<int:nid>", methods=["POST"])
def delete_note(nid):

    user = current_user()

    conn = db()

    note = conn.execute(
        "SELECT * FROM notes WHERE id=?",
        (nid,)
    ).fetchone()

    if note:

        if (
            note["owner"] == user["name"]
            or user["role"] == "Admin"
        ):

            conn.execute(
                "DELETE FROM notes WHERE id=?",
                (nid,)
            )

            conn.commit()

    conn.close()

    return redirect("/notes")


# ============================================================
# SPORTS
# ============================================================

@app.route("/sports", methods=["GET", "POST"])
def sports():

    user = current_user()

    if not user:
        return redirect("/login")

    conn = db()

    if request.method == "POST":

        if user["role"] not in ["Teacher", "Admin"]:

            return page(
                "Permission",
                """
                <div class="card">
                    <h2>❌ Only Teachers and Admin can post sports announcements.</h2>
                </div>
                """
            )

        conn.execute("""
            INSERT INTO sports
            (title,description,owner,created_at)
            VALUES (?,?,?,?)
        """, (
            request.form["title"],
            request.form["description"],
            user["name"],
            datetime.now().strftime("%d-%m-%Y %H:%M")
        ))

        conn.commit()

    posts = conn.execute(
        "SELECT * FROM sports ORDER BY id DESC"
    ).fetchall()

    conn.close()

    form = ""

    if user["role"] in ["Teacher", "Admin"]:

        form = """

        <div class="card">

            <h2>➕ Sports Announcement</h2>

            <form method="POST">

                <input
                    name="title"
                    placeholder="Event Title"
                    required
                >

                <textarea
                    name="description"
                    placeholder="Event details"
                ></textarea>

                <button class="btn">
                    🏆 Publish
                </button>

            </form>

        </div>

        """

    cards = ""

    for p in posts:

        delete = ""

        if (
            p["owner"] == user["name"]
            or user["role"] == "Admin"
        ):

            delete = f"""

            <form method="POST"
                  action="/sports/delete/{p['id']}">

                <button class="btn danger">
                    Delete
                </button>

            </form>

            """

        cards += f"""

        <div class="card">

            <h2>🏆 {p['title']}</h2>

            <p>{p['description']}</p>

            <p>
            👤 {p['owner']}
            |
            👁 {p['views']}
            </p>

            {delete}

        </div>

        """

    return page(
        "Sports",
        f"""
        <h1>🏆 Campus Sports</h1>

        {form}

        <div class="grid">
            {cards}
        </div>
        """
    )


@app.route("/sports/delete/<int:sid>", methods=["POST"])
def delete_sport(sid):

    user = current_user()

    conn = db()

    post = conn.execute(
        "SELECT * FROM sports WHERE id=?",
        (sid,)
    ).fetchone()

    if post:

        if (
            post["owner"] == user["name"]
            or user["role"] == "Admin"
        ):

            conn.execute(
                "DELETE FROM sports WHERE id=?",
                (sid,)
            )

            conn.commit()

    conn.close()

    return redirect("/sports")


# ============================================================
# EXPENSE TRACKER
# ============================================================

@app.route("/expenses", methods=["GET", "POST"])
def expenses():

    user = current_user()

    if not user:
        return redirect("/login")

    conn = db()

    if request.method == "POST":

        conn.execute("""
            INSERT INTO expenses
            (title,amount,category,owner,created_at)
            VALUES (?,?,?,?,?)
        """, (
            request.form["title"],
            float(request.form["amount"]),
            request.form["category"],
            user["name"],
            datetime.now().strftime("%d-%m-%Y")
        ))

        conn.commit()

    expenses_list = conn.execute(
        """
        SELECT * FROM expenses
        WHERE owner=?
        ORDER BY id DESC
        """,
        (user["name"],)
    ).fetchall()

    total = sum(
        x["amount"]
        for x in expenses_list
    )

    conn.close()

    cards = ""

    for e in expenses_list:

        cards += f"""

        <div class="card">

            <h3>💰 {e['title']}</h3>

            <h2>₹{e['amount']}</h2>

            <p>
            Category: {e['category']}
            </p>

            <p>{e['created_at']}</p>

        </div>

        """

    return page(
        "Expenses",
        f"""

        <h1>💰 Student Expense Tracker</h1>

        <div class="stat">

            <h2>Total Expense</h2>

            <div class="number">
                ₹{total}
            </div>

        </div>

        <br>

        <div class="card">

            <h2>➕ Add Expense</h2>

            <form method="POST">

                <input
                    name="title"
                    placeholder="Expense name"
                    required
                >

                <input
                    type="number"
                    step="0.01"
                    name="amount"
                    placeholder="Amount"
                    required
                >

                <select name="category">

                    <option>Food</option>
                    <option>Travel</option>
                    <option>Education</option>
                    <option>Entertainment</option>
                    <option>Other</option>

                </select>

                <button class="btn">
                    Add Expense
                </button>

            </form>

        </div>

        <div class="grid">
            {cards}
        </div>

        """
    )


# ============================================================
# GROUPS
# ============================================================

@app.route("/groups", methods=["GET", "POST"])
def groups():

    user = current_user()

    if not user:
        return redirect("/login")

    conn = db()

    if request.method == "POST":

        if user["role"] not in ["Teacher", "Admin"]:

            return page(
                "Permission",
                """
                <div class="card">
                    <h2>❌ Only Teachers and Admin can create groups.</h2>
                </div>
                """
            )

        conn.execute("""
            INSERT INTO groups
            (name,description,owner)
            VALUES (?,?,?)
        """, (
            request.form["name"],
            request.form["description"],
            user["name"]
        ))

        conn.commit()

    groups_list = conn.execute(
        "SELECT * FROM groups ORDER BY id DESC"
    ).fetchall()

    conn.close()

    create_group = ""

    if user["role"] in ["Teacher", "Admin"]:

        create_group = """

        <div class="card">

            <h2>➕ Create Group</h2>

            <form method="POST">

                <input
                    name="name"
                    placeholder="Group Name"
                    required
                >

                <textarea
                    name="description"
                    placeholder="Group description"
                ></textarea>

                <button class="btn">
                    Create Group
                </button>

            </form>

        </div>

        """

    cards = ""

    for g in groups_list:

        cards += f"""

        <div class="card">

            <h2>💬 {g['name']}</h2>

            <p>{g['description']}</p>

            <p>
            Created by {g['owner']}
            </p>

            <a class="btn"
               href="/groups/{g['id']}">

                Open Group

            </a>

        </div>

        """

    return page(
        "Groups",
        f"""

        <h1>💬 Campus Groups</h1>

        <p>
        Student + Teacher communication.
        </p>

        {create_group}

        <div class="grid">
            {cards}
        </div>

        """
    )


# ============================================================
# GROUP CHAT
# ============================================================

@app.route("/groups/<int:gid>", methods=["GET", "POST"])
def group_chat(gid):

    user = current_user()

    if not user:
        return redirect("/login")

    conn = db()

    group = conn.execute(
        "SELECT * FROM groups WHERE id=?",
        (gid,)
    ).fetchone()

    if not group:

        conn.close()

        return redirect("/groups")

    if request.method == "POST":

        message = request.form["message"]

        conn.execute("""
            INSERT INTO messages
            (group_id,sender,message,created_at)
            VALUES (?,?,?,?)
        """, (
            gid,
            user["name"],
            message,
            datetime.now().strftime("%H:%M")
        ))

        conn.commit()

    messages = conn.execute(
        """
        SELECT * FROM messages
        WHERE group_id=?
        ORDER BY id
        """,
        (gid,)
    ).fetchall()

    conn.close()

    message_html = ""

    for m in messages:

        message_html += f"""

        <div class="message">

            <b>{m['sender']}</b>

            <small>
            {m['created_at']}
            </small>

            <br>

            {m['message']}

        </div>

        """

    content = f"""

    <h1>💬 {group['name']}</h1>

    <div class="card">

        <div class="chat">

            {message_html}

        </div>

        <br>

        <form method="POST">

            <input
                name="message"
                placeholder="Type your message..."
                required
            >

            <button class="btn">
                Send Message
            </button>

        </form>

    </div>

    """

    return page("Group Chat", content)


# ============================================================
# FORGOT PASSWORD
# ============================================================

@app.route("/forgot", methods=["GET", "POST"])
def forgot():

    if request.method == "POST":

        email = request.form["email"].lower().strip()

        conn = db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user and email != ADMIN_EMAIL:

            conn.execute("""
                INSERT INTO reset_requests
                (email)
                VALUES (?)
            """, (email,))

            conn.commit()

        conn.close()

        return page(
            "Request Sent",
            """
            <div class="card">

                <h2>📩 Request Sent</h2>

                <p>
                If the account exists,
                the Admin can review your request.
                </p>

                <a class="btn" href="/login">
                    Back to Login
                </a>

            </div>
            """
        )

    return page(
        "Forgot Password",
        """

        <div class="card form">

            <h1>🔐 Forgot Password</h1>

            <form method="POST">

                <input
                    type="email"
                    name="email"
                    placeholder="Your registered email"
                    required
                >

                <button class="btn">
                    Send Request
                </button>

            </form>

        </div>

        """
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin():

    user = current_user()

    if not user:
        return redirect("/login")

    if (
        user["role"] != "Admin"
        or user["email"] != ADMIN_EMAIL
    ):

        return page(
            "Access Denied",
            """
            <div class="card">

                <h1>🚫 Access Denied</h1>

                <p>
                Only the permanent Admin can access
                this dashboard.
                </p>

            </div>
            """
        )

    conn = db()

    users = conn.execute(
        "SELECT * FROM users ORDER BY id DESC"
    ).fetchall()

    role_requests = conn.execute(
        "SELECT * FROM role_requests WHERE status='Pending'"
    ).fetchall()

    reset_requests = conn.execute(
        "SELECT * FROM reset_requests WHERE status='Pending'"
    ).fetchall()

    project_count = conn.execute(
        "SELECT COUNT(*) FROM projects"
    ).fetchone()[0]

    note_count = conn.execute(
        "SELECT COUNT(*) FROM notes"
    ).fetchone()[0]

    conn.close()

    role_html = ""

    for r in role_requests:

        role_html += f"""

        <div class="card">

            <h3>👤 {r['name']}</h3>

            <p>{r['email']}</p>

            <p>
            Requested:
            <b>{r['requested_role']}</b>
            </p>

            <form
                method="POST"
                action="/admin/approve-role/{r['id']}"
            >

                <button class="btn green">
                    Approve
                </button>

            </form>

        </div>

        """

    reset_html = ""

    for r in reset_requests:

        reset_html += f"""

        <div class="card">

            <h3>🔐 Password Reset</h3>

            <p>{r['email']}</p>

            <form
                method="POST"
                action="/admin/approve-reset/{r['id']}"
            >

                <button class="btn green">
                    Approve Reset
                </button>

            </form>

        </div>

        """

    user_html = ""

    for u in users:

        user_html += f"""

        <div class="card">

            <h3>{u['name']}</h3>

            <p>{u['email']}</p>

            <p>
            Role:
            <b>{u['role']}</b>
            </p>

            <p>
            Department:
            {u['department']}
            </p>

        </div>

        """

    content = f"""

    <h1>🛡️ Admin Dashboard</h1>

    <div class="card">

        <h2>Permanent Administrator</h2>

        <p>
        👤 Rohit Patil
        </p>

        <p>
        📧 {ADMIN_EMAIL}
        </p>

        <p>
        Department: Computer
        </p>

    </div>

    <div class="grid">

        <div class="stat">

            <div class="number">
                {len(users)}
            </div>

            Total Users

        </div>

        <div class="stat">

            <div class="number">
                {project_count}
            </div>

            Projects

        </div>

        <div class="stat">

            <div class="number">
                {note_count}
            </div>

            Notes

        </div>

        <div class="stat">

            <div class="number">
                {len(role_requests)}
            </div>

            Role Requests

        </div>

    </div>

    <h2>👨‍🏫 Teacher/Admin Requests</h2>

    {role_html if role_html else '<div class="card">No pending requests.</div>'}

    <h2>🔐 Password Reset Requests</h2>

    {reset_html if reset_html else '<div class="card">No pending requests.</div>'}

    <h2>👥 All Users</h2>

    <div class="grid">

        {user_html}

    </div>

    """

    return page("Admin Dashboard", content)


@app.route("/admin/approve-role/<int:rid>", methods=["POST"])
def approve_role(rid):

    user = current_user()

    if not user or user["email"] != ADMIN_EMAIL:
        return "Access Denied"

    conn = db()

    req = conn.execute(
        "SELECT * FROM role_requests WHERE id=?",
        (rid,)
    ).fetchone()

    if req:

        conn.execute("""
            UPDATE users
            SET role=?
            WHERE email=?
        """, (
            req["requested_role"],
            req["email"]
        ))

        conn.execute("""
            UPDATE role_requests
            SET status='Approved'
            WHERE id=?
        """, (rid,))

        conn.commit()

    conn.close()

    return redirect("/admin")


@app.route("/admin/approve-reset/<int:rid>", methods=["POST"])
def approve_reset(rid):

    user = current_user()

    if not user or user["email"] != ADMIN_EMAIL:
        return "Access Denied"

    conn = db()

    req = conn.execute(
        "SELECT * FROM reset_requests WHERE id=?",
        (rid,)
    ).fetchone()

    if req:

        # For this demo, generate a temporary password.
        temporary_password = "Campus@123"

        conn.execute("""
            UPDATE users
            SET password=?
            WHERE email=?
        """, (
            generate_password_hash(temporary_password),
            req["email"]
        ))

        conn.execute("""
            UPDATE reset_requests
            SET status='Approved'
            WHERE id=?
        """, (rid,))

        conn.commit()

    conn.close()

    return page(
        "Password Reset",
        """
        <div class="card">

            <h1>✅ Password Reset</h1>

            <p>
            Temporary password:
            </p>

            <h2>Campus@123</h2>

            <p>
            Tell the student to login and change it later.
            </p>

            <a class="btn" href="/admin">
                Back to Admin
            </a>

        </div>
        """
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    print("")
    print("======================================")
    print("       CAMPUSCONNECT STARTED")
    print("======================================")
    print("")
    print("Open: http://127.0.0.1:5000")
    print("")
    print("Permanent Admin:")
    print("Email:", ADMIN_EMAIL)
    print("Password:", ADMIN_PASSWORD)
    print("")
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
