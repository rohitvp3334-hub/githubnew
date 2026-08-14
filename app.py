
from flask import Flask, request, redirect, url_for, session, flash, send_from_directory, render_template_string
import sqlite3, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "studenthub.db")
UPLOADS = os.path.join(BASE, "shared_notes")
os.makedirs(UPLOADS, exist_ok=True)

app = Flask(__name__)
app.secret_key = "studenthub-hackathon-change-this"
ALLOWED = {"pdf","doc","docx","ppt","pptx","txt"}

def con():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def today():
    return datetime.now().strftime("%d %b %Y")

def init_db():
    c = con()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, role TEXT NOT NULL, course TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, subject TEXT NOT NULL, semester TEXT NOT NULL,
        unit TEXT DEFAULT '', teacher TEXT NOT NULL, filename TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS projects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, description TEXT NOT NULL, skills TEXT NOT NULL,
        year TEXT NOT NULL, max_members INTEGER DEFAULT 4,
        creator TEXT NOT NULL, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL, student TEXT NOT NULL,
        status TEXT DEFAULT 'Pending', UNIQUE(project_id,student)
    );
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT, student TEXT NOT NULL,
        amount REAL NOT NULL, category TEXT NOT NULL,
        description TEXT DEFAULT '', date TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS announcements(
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        body TEXT NOT NULL, priority TEXT NOT NULL,
        author TEXT NOT NULL, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS progress(
        id INTEGER PRIMARY KEY AUTOINCREMENT, student TEXT NOT NULL,
        subject TEXT NOT NULL, unit TEXT NOT NULL, completed INTEGER DEFAULT 0,
        UNIQUE(student,subject,unit)
    );
    CREATE TABLE IF NOT EXISTS hostels(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, location TEXT,
        rent REAL, facilities TEXT
    );
    CREATE TABLE IF NOT EXISTS sports(
        id INTEGER PRIMARY KEY AUTOINCREMENT, sport TEXT, event TEXT,
        date TEXT, venue TEXT
    );
    """)

    demos = [
        ("Demo Student","student@demo.com","1234","Student","Computer Engineering"),
        ("Demo Teacher","teacher@demo.com","1234","Teacher","Computer Engineering")
    ]
    for row in demos:
        try:
            c.execute("INSERT INTO users(name,email,password,role,course) VALUES(?,?,?,?,?)",
                      (row[0],row[1],generate_password_hash(row[2]),row[3],row[4]))
        except sqlite3.IntegrityError:
            pass

    if c.execute("SELECT COUNT(*) FROM announcements").fetchone()[0] == 0:
        c.execute("INSERT INTO announcements(title,body,priority,author,created_at) VALUES(?,?,?,?,?)",
                  ("Hackathon Registration Open",
                   "Student registrations are now open. Check with your department.",
                   "High","Admin",today()))
    if c.execute("SELECT COUNT(*) FROM hostels").fetchone()[0] == 0:
        c.executemany("INSERT INTO hostels(name,location,rent,facilities) VALUES(?,?,?,?)",[
            ("Campus View PG","Near College",5500,"Wi-Fi, Food, Laundry"),
            ("Student Nest Hostel","1.5 km from College",4500,"Wi-Fi, Mess, Study Room"),
            ("Green Stay PG","2 km from College",6500,"Food, Parking, Wi-Fi")
        ])
    if c.execute("SELECT COUNT(*) FROM sports").fetchone()[0] == 0:
        c.executemany("INSERT INTO sports(sport,event,date,venue) VALUES(?,?,?,?)",[
            ("Volleyball","Inter College Volleyball","20 Aug 2026","College Ground"),
            ("Cricket","College Cricket Tournament","25 Aug 2026","Sports Ground"),
            ("Badminton","Badminton Selection","28 Aug 2026","Indoor Hall")
        ])
    c.commit()
    c.close()

def logged():
    return "user_id" in session

def is_teacher():
    return logged() and session.get("role") == "Teacher"

CSS = """
*{box-sizing:border-box}
body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:#07111f;color:#edf5ff}
a{text-decoration:none;color:inherit}
.nav{position:sticky;top:0;z-index:10;background:#0d1b2d;border-bottom:1px solid #203752;padding:12px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.logo{font-size:22px;font-weight:900;color:#60a5fa;white-space:nowrap}
.links{display:flex;gap:5px;overflow:auto;flex:1}.links a{padding:9px 10px;border-radius:9px;color:#b7c8dd;white-space:nowrap;font-size:14px}.links a:hover{background:#18304d;color:#fff}
.user{font-size:13px;color:#9db0c9;white-space:nowrap}
.container{width:min(1180px,94%);margin:auto;padding:28px 0}
.hero{padding:10px 0 20px}.hero h1{font-size:36px;margin:0 0 8px}.hero p,.muted{color:#91a5bf}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}.feature{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.card{background:#0d1b2d;border:1px solid #1d3551;border-radius:18px;padding:19px;margin-bottom:15px;box-shadow:0 8px 25px #0002}
.stat{min-height:125px}.num{font-size:29px;font-weight:900;margin-top:10px}
.btn,button{border:0;border-radius:10px;background:#2563eb;color:white;padding:11px 16px;font-weight:800;cursor:pointer;display:inline-block}.secondary{background:#172c46}.green{background:#059669}
.actions{display:flex;gap:9px;flex-wrap:wrap;align-items:center}
input,select,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #304965;background:#081524;color:#edf5ff;margin:6px 0 13px;font:inherit}textarea{min-height:110px}
label{font-size:14px;color:#b9c8db}.flash{padding:13px 15px;border-radius:10px;background:#173253;margin-bottom:14px}.flash.error{background:#5b2028}.flash.success{background:#124438}
.badge{display:inline-block;background:#203650;padding:4px 9px;border-radius:99px;font-size:12px}.high{background:#6b4511}.urgent{background:#7f1d1d}
.login-page{min-height:100vh;display:grid;place-items:center;padding:20px;background:radial-gradient(circle at top,#15385e,#07111f 60%)}
.login-card{width:min(450px,100%);background:#0d1b2d;border:1px solid #28415e;border-radius:25px;padding:32px;box-shadow:0 25px 80px #0007}.login-card h1{text-align:center;font-size:36px}.login-card p{text-align:center;color:#91a5bf}.login-card button,.login-card .btn{width:100%;text-align:center;margin-top:8px}
.check{display:flex;gap:10px;align-items:center;padding:9px}.check input{width:auto;margin:0}.empty{text-align:center;padding:25px;color:#8194ad}
footer{text-align:center;color:#71859e;padding:30px}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}.feature{grid-template-columns:1fr 1fr}.user{display:none}}
@media(max-width:600px){.container{width:94%;padding:18px 0}.grid,.two,.feature{grid-template-columns:1fr}.hero h1{font-size:28px}.nav{padding:10px}.links{order:3;flex-basis:100%}.links a{font-size:12px}.card{padding:15px}}
"""

def page(body, title="StudentHub"):
    nav = ""
    if logged():
        nav = f"""
        <nav class="nav">
        <a class="logo" href="/dashboard">🎓 StudentHub</a>
        <div class="links">
        <a href="/dashboard">🏠 Home</a><a href="/notes">📚 Notes</a>
        <a href="/projects">🚀 Projects</a><a href="/announcements">📢 Notices</a>
        <a href="/expenses">💰 Expenses</a><a href="/exams">📝 Exams</a>
        <a href="/fitness">💪 Fitness</a><a href="/hostels">🏠 PG</a>
        <a href="/laptop">💻 Laptop</a><a href="/sports">🏆 Sports</a>
        <a href="/logout">🚪 Logout</a>
        </div><div class="user">{session['name']} · {session['role']}</div>
        </nav>
        """
    msgs = ""
    for cat,msg in session.pop("_flashes",[]):
        msgs += f'<div class="flash {cat}">{msg}</div>'
    return f"""<!doctype html><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title><style>{CSS}</style></head><body>{nav}
    <main class="container">{msgs}{body}</main>
    <footer>🎓 StudentHub • Python + Flask + SQLite • Hackathon MVP</footer>
    </body></html>"""

@app.route("/")
def home():
    if logged(): return redirect("/dashboard")
    body = """
    <div class="login-page"><div class="login-card">
    <h1>🎓 StudentHub</h1><p>One platform for your complete student life.</p>
    <form method="post" action="/login">
    <label>Email</label><input name="email" type="email" placeholder="student@demo.com" required>
    <label>Password</label><input name="password" type="password" placeholder="1234" required>
    <label>Role</label><select name="role"><option>Student</option><option>Teacher</option></select>
    <button>LOGIN</button></form>
    <a class="btn secondary" href="/register">CREATE ACCOUNT</a>
    <p style="font-size:13px">Student: student@demo.com / 1234<br>Teacher: teacher@demo.com / 1234</p>
    </div></div>"""
    return page(body,"Login • StudentHub")

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form["name"].strip(); email=request.form["email"].strip().lower()
        password=request.form["password"]; role=request.form["role"]; course=request.form.get("course","")
        if not name or not email or not password:
            flash("Fill all required fields.","error"); return redirect("/register")
        c=con()
        try:
            c.execute("INSERT INTO users(name,email,password,role,course) VALUES(?,?,?,?,?)",
                      (name,email,generate_password_hash(password),role,course)); c.commit()
            flash("Account created. Please login.","success"); return redirect("/")
        except sqlite3.IntegrityError:
            flash("Email already registered.","error")
        finally: c.close()
    body="""<div class="card" style="max-width:650px;margin:25px auto"><h1>Create Account</h1>
    <form method="post"><div class="two"><div>
    <label>Name</label><input name="name" required><label>Email</label><input name="email" type="email" required>
    <label>Password</label><input name="password" type="password" required></div><div>
    <label>Course</label><input name="course" placeholder="Computer Engineering">
    <label>Role</label><select name="role"><option>Student</option><option>Teacher</option></select></div></div>
    <button>Create Account</button> <a class="btn secondary" href="/">Back</a></form></div>"""
    return page(body,"Register • StudentHub")

@app.post("/login")
def login():
    email=request.form["email"].strip().lower(); password=request.form["password"]; role=request.form["role"]
    c=con(); u=c.execute("SELECT * FROM users WHERE email=? AND role=?",(email,role)).fetchone(); c.close()
    if u and check_password_hash(u["password"],password):
        session["user_id"]=u["id"]; session["name"]=u["name"]; session["role"]=u["role"]
        return redirect("/dashboard")
    flash("Invalid email, password or role.","error"); return redirect("/")

@app.get("/logout")
def logout():
    session.clear(); return redirect("/")

@app.get("/dashboard")
def dashboard():
    if not logged(): return redirect("/")
    c=con()
    n=c.execute("SELECT COUNT(*) x FROM notes").fetchone()["x"]
    p=c.execute("SELECT COUNT(*) x FROM projects").fetchone()["x"]
    e=c.execute("SELECT COALESCE(SUM(amount),0) x FROM expenses WHERE student=?",(session["name"],)).fetchone()["x"]
    ann=c.execute("SELECT * FROM announcements ORDER BY id DESC LIMIT 4").fetchall(); c.close()
    body=f"""<div class="hero"><h1>Welcome, {session['name']}! 👋</h1><p>Your student life, organized in one place.</p></div>
    <div class="grid"><div class="card stat">📚 Notes<div class="num">{n}</div></div>
    <div class="card stat">🚀 Projects<div class="num">{p}</div></div>
    <div class="card stat">💰 My Expenses<div class="num">₹{e:.0f}</div></div>
    <div class="card stat">👤 Account<div class="num">{session['role']}</div></div></div>
    <div class="card"><h2>⚡ Quick Access</h2><div class="actions">
    <a class="btn" href="/notes">📚 Notes</a><a class="btn" href="/projects">🚀 Find Partners</a>
    <a class="btn" href="/expenses">💰 Add Expense</a><a class="btn" href="/announcements">📢 Notices</a>
    <a class="btn" href="/exams">📝 Exam Tracker</a></div></div><h2>📢 Latest Announcements</h2>"""
    for a in ann:
        body += f'<div class="card"><h3>{a["title"]}</h3><p>{a["body"]}</p><span class="badge">{a["priority"]}</span> <span class="muted">{a["author"]} · {a["created_at"]}</span></div>'
    return page(body,"Dashboard • StudentHub")

@app.get("/notes")
def notes():
    if not logged(): return redirect("/")
    q=request.args.get("q","").strip(); c=con()
    rows=c.execute("SELECT * FROM notes WHERE title LIKE ? OR subject LIKE ? OR unit LIKE ? ORDER BY id DESC",
                   (f"%{q}%",f"%{q}%",f"%{q}%")).fetchall(); c.close()
    body=f"""<div class="hero"><h1>📚 Student Notes Hub</h1><p>Search notes by subject, semester or unit.</p></div>
    <form class="actions" method="get"><input name="q" value="{q}" placeholder="Search notes..." style="flex:1"><button>Search</button></form>"""
    if is_teacher():
        body += """<div class="card"><h2>👨‍🏫 Upload & Share Notes</h2><form method="post" action="/notes/upload" enctype="multipart/form-data">
        <div class="two"><div><label>Title</label><input name="title" required><label>Subject</label><input name="subject" required>
        <label>Semester</label><input name="semester" required></div><div><label>Unit</label><input name="unit">
        <label>File</label><input name="file" type="file" required></div></div><button>📤 Share Note</button></form></div>"""
    for x in rows:
        body += f'<div class="card"><h2>📄 {x["title"]}</h2><p><b>{x["subject"]}</b> · Semester {x["semester"]} · {x["unit"]}</p><p class="muted">Shared by {x["teacher"]} · {x["created_at"]}</p><a class="btn" target="_blank" href="/notes/file/{x["filename"]}">Open Note</a></div>'
    if not rows: body += '<div class="empty">No notes found.</div>'
    return page(body,"Notes • StudentHub")

@app.post("/notes/upload")
def upload_note():
    if not is_teacher(): flash("Only teachers can upload notes.","error"); return redirect("/notes")
    f=request.files.get("file")
    if not f or not f.filename: flash("Select a file.","error"); return redirect("/notes")
    ext=f.filename.rsplit(".",1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED: flash("Allowed: PDF, DOC, DOCX, PPT, PPTX, TXT.","error"); return redirect("/notes")
    filename=secure_filename(f.filename); stem,ext2=os.path.splitext(filename); i=1
    while os.path.exists(os.path.join(UPLOADS,filename)):
        filename=f"{stem}_{i}{ext2}"; i+=1
    f.save(os.path.join(UPLOADS,filename))
    c=con(); c.execute("INSERT INTO notes(title,subject,semester,unit,teacher,filename,created_at) VALUES(?,?,?,?,?,?,?)",
                      (request.form["title"],request.form["subject"],request.form["semester"],request.form.get("unit",""),
                       session["name"],filename,datetime.now().strftime("%d %b %Y %H:%M"))); c.commit(); c.close()
    flash("Note shared successfully.","success"); return redirect("/notes")

@app.get("/notes/file/<path:name>")
def note_file(name):
    if not logged(): return redirect("/")
    return send_from_directory(UPLOADS,name)

@app.route("/projects",methods=["GET","POST"])
def projects():
    if not logged(): return redirect("/")
    c=con()
    if request.method=="POST":
        c.execute("INSERT INTO projects(title,description,skills,year,max_members,creator,created_at) VALUES(?,?,?,?,?,?,?)",
                  (request.form["title"],request.form["description"],request.form["skills"],request.form["year"],
                   int(request.form["max_members"]),session["name"],datetime.now().strftime("%d %b %Y %H:%M")))
        c.commit(); flash("Project posted! Other students can request to join.","success")
    rows=c.execute("SELECT * FROM projects ORDER BY id DESC").fetchall(); c.close()
    body="""<div class="hero"><h1>🚀 Project Team Finder</h1><p>Post a project and find interested partners from 1st to 4th year.</p></div>
    <div class="card"><h2>➕ Create Project</h2><form method="post"><div class="two"><div>
    <label>Project Title</label><input name="title" required><label>Description</label><textarea name="description" required></textarea>
    <label>Required Skills</label><input name="skills" placeholder="Python, ML, Web, UI..." required></div><div>
    <label>Preferred Year</label><select name="year"><option>Any Year</option><option>1st Year</option><option>2nd Year</option><option>3rd Year</option><option>4th Year</option></select>
    <label>Maximum Members</label><input name="max_members" type="number" value="4" min="2" max="20"></div></div><button>🚀 Post Project</button></form></div>"""
    for x in rows:
        body += f'<div class="card"><h2>🚀 {x["title"]}</h2><p>{x["description"]}</p><p><b>Skills:</b> {x["skills"]}</p><p class="muted">Year: {x["year"]} · Creator: {x["creator"]} · Max members: {x["max_members"]}</p>'
        if x["creator"] != session["name"]:
            body += f'<form method="post" action="/projects/{x["id"]}/request"><button class="green">👥 Request to Join</button></form>'
        else: body += '<span class="badge">Your Project</span>'
        body += '</div>'
    return page(body,"Projects • StudentHub")

@app.post("/projects/<int:pid>/request")
def project_request(pid):
    if not logged(): return redirect("/")
    c=con()
    try:
        c.execute("INSERT INTO requests(project_id,student) VALUES(?,?)",(pid,session["name"])); c.commit()
        flash("Join request sent!","success")
    except sqlite3.IntegrityError: flash("You already requested this project.","error")
    c.close(); return redirect("/projects")

@app.route("/announcements",methods=["GET","POST"])
def announcements():
    if not logged(): return redirect("/")
    c=con()
    if request.method=="POST" and is_teacher():
        c.execute("INSERT INTO announcements(title,body,priority,author,created_at) VALUES(?,?,?,?,?)",
                  (request.form["title"],request.form["body"],request.form["priority"],session["name"],today())); c.commit()
        flash("Announcement published.","success")
    rows=c.execute("SELECT * FROM announcements ORDER BY id DESC").fetchall(); c.close()
    body='<div class="hero"><h1>📢 College Announcement Dashboard</h1><p>Important notices in one place.</p></div>'
    if is_teacher():
        body += """<div class="card"><h2>Post Announcement</h2><form method="post"><label>Title</label><input name="title" required>
        <label>Message</label><textarea name="body" required></textarea><label>Priority</label><select name="priority"><option>Normal</option><option>High</option><option>Urgent</option></select><button>📢 Publish</button></form></div>"""
    for a in rows:
        cls="urgent" if a["priority"]=="Urgent" else ("high" if a["priority"]=="High" else "")
        body += f'<div class="card"><h2>📢 {a["title"]}</h2><p>{a["body"]}</p><span class="badge {cls}">{a["priority"]}</span> <span class="muted">{a["author"]} · {a["created_at"]}</span></div>'
    return page(body,"Announcements • StudentHub")

@app.route("/expenses",methods=["GET","POST"])
def expenses():
    if not logged(): return redirect("/")
    c=con()
    if request.method=="POST":
        try:
            amount=float(request.form["amount"])
            if amount<=0: raise ValueError
            c.execute("INSERT INTO expenses(student,amount,category,description,date) VALUES(?,?,?,?,?)",
                      (session["name"],amount,request.form["category"],request.form.get("description",""),today())); c.commit()
            flash("Expense added.","success")
        except ValueError: flash("Enter a valid amount.","error")
    rows=c.execute("SELECT * FROM expenses WHERE student=? ORDER BY id DESC",(session["name"],)).fetchall()
    total=c.execute("SELECT COALESCE(SUM(amount),0) x FROM expenses WHERE student=?",(session["name"],)).fetchone()["x"]; c.close()
    body=f"""<div class="hero"><h1>💰 Student Expense Tracker</h1><p>Track your daily student spending.</p></div>
    <div class="card"><h2>Total Spent: ₹{total:.2f}</h2><form method="post"><div class="two"><div>
    <label>Amount</label><input name="amount" type="number" step="0.01" required><label>Category</label>
    <select name="category"><option>Food</option><option>Travel</option><option>Study</option><option>Shopping</option><option>Bills</option><option>Other</option></select></div>
    <div><label>Description</label><input name="description" placeholder="Lunch, books, bus..."><button>+ Add Expense</button></div></div></form></div>"""
    for e in rows: body += f'<div class="card"><b>₹{e["amount"]:.2f}</b> · {e["category"]} <span class="muted">· {e["date"]}</span><p>{e["description"]}</p></div>'
    return page(body,"Expenses • StudentHub")

@app.route("/exams",methods=["GET","POST"])
def exams():
    if not logged(): return redirect("/")
    if request.method=="POST":
        c=con(); c.execute("""INSERT INTO progress(student,subject,unit,completed) VALUES(?,?,?,?)
        ON CONFLICT(student,subject,unit) DO UPDATE SET completed=excluded.completed""",
        (session["name"],request.form["subject"],request.form["unit"],int(request.form["completed"]))); c.commit(); c.close()
    subjects=["DBMS","Operating System","Computer Networks","Python","Machine Learning"]
    units=["Unit 1","Unit 2","Unit 3","Unit 4","Unit 5"]
    c=con(); done={(r["subject"],r["unit"]):r["completed"] for r in c.execute("SELECT * FROM progress WHERE student=?",(session["name"],)).fetchall()}; c.close()
    body='<div class="hero"><h1>📝 Exam Preparation Tracker</h1><p>Prepare in sequence, subject by subject.</p></div>'
    for s in subjects:
        body+=f'<div class="card"><h2>{s}</h2>'
        for u in units:
            d=done.get((s,u),0)
            body+=f'<form method="post" class="check"><input type="hidden" name="subject" value="{s}"><input type="hidden" name="unit" value="{u}"><input type="hidden" name="completed" value="{0 if d else 1}"><input type="checkbox" {"checked" if d else ""} onchange="this.form.submit()"> {u}</form>'
        body+='</div>'
    return page(body,"Exams • StudentHub")

@app.get("/fitness")
def fitness():
    if not logged(): return redirect("/")
    body="""<div class="hero"><h1>💪 Student Fitness</h1><p>Simple healthy habits for a balanced student routine.</p></div>
    <div class="feature"><div class="card"><h3>💧 Hydration</h3><p class="muted">Take regular water breaks.</p></div>
    <div class="card"><h3>🚶 Activity</h3><p class="muted">Take movement breaks between study sessions.</p></div>
    <div class="card"><h3>😴 Sleep</h3><p class="muted">Keep a consistent sleep routine.</p></div></div>
    <div class="card"><h2>Today's Checklist</h2>
    <label class="check"><input type="checkbox"> Took a study break</label>
    <label class="check"><input type="checkbox"> Did physical activity</label>
    <label class="check"><input type="checkbox"> Drank water</label>
    <label class="check"><input type="checkbox"> Planned tomorrow's study</label></div>"""
    return page(body,"Fitness • StudentHub")

@app.get("/hostels")
def hostels():
    if not logged(): return redirect("/")
    q=request.args.get("q","").strip(); c=con()
    rows=c.execute("SELECT * FROM hostels WHERE name LIKE ? OR location LIKE ? ORDER BY rent",(f"%{q}%",f"%{q}%")).fetchall(); c.close()
    body=f"""<div class="hero"><h1>🏠 PG / Hostel Finder</h1><p>Find student-friendly accommodation.</p></div>
    <form class="actions" method="get"><input name="q" value="{q}" placeholder="Search location..." style="flex:1"><button>Search</button></form>"""
    for h in rows: body+=f'<div class="card"><h2>🏠 {h["name"]}</h2><p>📍 {h["location"]}</p><p>💰 ₹{h["rent"]:.0f} / month</p><p>✓ {h["facilities"]}</p></div>'
    return page(body,"PG Finder • StudentHub")

@app.get("/laptop")
def laptop():
    if not logged(): return redirect("/")
    body="""<div class="hero"><h1>💻 Laptop & Software Advisor</h1><p>Get a basic recommendation for your course and workload.</p></div>
    <div class="card"><label>Course</label><select id="course"><option>Computer Engineering</option><option>Data Science</option><option>AI / ML</option><option>Web Development</option></select>
    <label>Budget</label><select id="budget"><option>Below ₹50K</option><option>₹50K–₹70K</option><option>₹70K–₹1L</option><option>Above ₹1L</option></select>
    <label>Main Use</label><select id="use"><option>Programming</option><option>Data Science / ML</option><option>Gaming</option><option>Video Editing</option><option>General Study</option></select>
    <button onclick="recommend()">Get Recommendation</button><div id="result" class="card" style="display:none;margin-top:18px"></div></div>
    <script>function recommend(){let u=document.getElementById('use').value;let gpu=['Data Science / ML','Gaming','Video Editing'].includes(u);let r='<h2>🎯 Suggested Specification</h2><p><b>RAM:</b> 16 GB preferred &nbsp; <b>SSD:</b> 512 GB+</p>';r+=gpu?'<p>Dedicated GPU is recommended.</p>':'<p>Integrated graphics is usually enough for coding/study.</p>';r+='<p><b>Software:</b> Python, VS Code, Git, Jupyter, MySQL</p>';document.getElementById('result').innerHTML=r;document.getElementById('result').style.display='block'}</script>"""
    return page(body,"Laptop Advisor • StudentHub")

@app.get("/sports")
def sports():
    if not logged(): return redirect("/")
    c=con(); rows=c.execute("SELECT * FROM sports ORDER BY id DESC").fetchall(); c.close()
    body='<div class="hero"><h1>🏆 Sports Hub</h1><p>College sports events and activities.</p></div>'
    for s in rows: body+=f'<div class="card"><h2>🏆 {s["sport"]}</h2><p>{s["event"]}</p><p>📅 {s["date"]} · 📍 {s["venue"]}</p></div>'
    return page(body,"Sports • StudentHub")

if __name__=="__main__":
    init_db()
    print("\n🎓 StudentHub is running")
    print("Laptop: http://127.0.0.1:5000")
    print("Student: student@demo.com / 1234")
    print("Teacher: teacher@demo.com / 1234\n")
    app.run(host="0.0.0.0",port=5000,debug=True)

    app = flask(studenthub)
