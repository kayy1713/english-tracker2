from flask import Flask, render_template_string, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
import random
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "english_tracker_secret"

UPLOAD_FOLDER = "uploads"
DB_NAME = "english_tracker.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS teacher (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS homeworks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        due_date TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        homework_id INTEGER,
        image TEXT,
        score INTEGER,
        feedback TEXT,
        submitted_at TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= BASE HTML =================

BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>English Tracker</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">

<style>

body{
    background:#f1f5f9;
    font-family:Arial;
}

.sidebar{
    position:fixed;
    left:0;
    top:0;
    width:260px;
    height:100vh;
    background:#111827;
    padding-top:90px;
}

.sidebar a{
    display:block;
    color:white;
    text-decoration:none;
    padding:16px 25px;
    margin:8px;
    border-radius:12px;
    transition:0.3s;
}

.sidebar a:hover{
    background:#374151;
}

.content{
    margin-left:270px;
    padding:30px;
}

.card{
    border:none;
    border-radius:20px;
    box-shadow:0 10px 25px rgba(0,0,0,0.08);
}

.navbar{
    height:70px;
}

.login-box{
    width:420px;
    margin:auto;
    margin-top:100px;
}

.gradient{
    background:linear-gradient(135deg,#667eea,#764ba2);
    min-height:100vh;
}

img.preview{
    max-height:220px;
    border-radius:15px;
}

</style>
</head>

<body>

{% if logged_in %}

<nav class="navbar navbar-dark bg-dark fixed-top">
<div class="container-fluid">
<span class="navbar-brand fs-4">English Tracker</span>

<a href="/logout" class="btn btn-outline-light">
Logout
</a>
</div>
</nav>

<div class="sidebar">

{% if role == 'teacher' %}

<a href="/create_homework">
<i class="fas fa-plus"></i>
Create Homework
</a>

<a href="/check_homeworks">
<i class="fas fa-check"></i>
Check Homeworks
</a>

{% endif %}

{% if role == 'student' %}

<a href="/pending_homeworks">
<i class="fas fa-clock"></i>
Pending Homeworks
</a>

<a href="/submit_homework">
<i class="fas fa-upload"></i>
Submit Homework
</a>

{% endif %}

</div>

{% endif %}

<div class="{{ 'content' if logged_in else '' }}">

{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}
{% for cat,msg in messages %}

<div class="alert alert-{{cat}}">
{{msg}}
</div>

{% endfor %}
{% endif %}
{% endwith %}

{{ content|safe }}

</div>

</body>
</html>
"""

# ================= HOME =================

@app.route("/")
def home():

    html = """

<div class="gradient d-flex justify-content-center align-items-center">

<div class="text-center">

<h1 class="text-white display-3 mb-5">
🇬🇧 English Tracker
</h1>

<a href="/teacher_login" class="btn btn-light btn-lg px-5 m-3">
Teacher
</a>

<a href="/student_login" class="btn btn-warning btn-lg px-5 m-3">
Student
</a>

</div>

</div>

"""

    return render_template_string(BASE_HTML,
                                  content=html,
                                  logged_in=False)

# ================= TEACHER LOGIN =================

@app.route("/teacher_login", methods=["GET", "POST"])
def teacher_login():

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == "POST":

        # SEND PASSWORD
        if "send_password" in request.form:

            phone = request.form["phone"]

            password = str(random.randint(100000, 999999))

            c.execute("DELETE FROM teacher")
            c.execute("INSERT INTO teacher(phone,password) VALUES(?,?)",
                      (phone, password))

            conn.commit()

            flash(f"Your password: {password}", "success")

        # LOGIN
        elif "login" in request.form:

            phone = request.form["phone"]
            password = request.form["password"]

            c.execute("SELECT * FROM teacher WHERE phone=? AND password=?",
                      (phone, password))

            teacher = c.fetchone()

            if teacher:

                session["logged_in"] = True
                session["role"] = "teacher"

                return redirect("/create_homework")

            else:
                flash("Wrong information!", "danger")

    conn.close()

    html = """

<div class="gradient">

<div class="login-box">

<div class="card p-5">

<h2 class="text-center mb-4">
Teacher Login
</h2>

<form method="POST">

<input type="hidden" name="send_password" value="1">

<input type="text"
name="phone"
class="form-control form-control-lg mb-3"
placeholder="Phone Number"
required>

<button class="btn btn-primary w-100">
Send Password
</button>

</form>

<hr>

<form method="POST">

<input type="hidden" name="login" value="1">

<input type="text"
name="phone"
class="form-control form-control-lg mb-3"
placeholder="Phone Number"
required>

<input type="password"
name="password"
class="form-control form-control-lg mb-3"
placeholder="Password"
required>

<button class="btn btn-success w-100">
Login
</button>

</form>

</div>

</div>

</div>

"""

    return render_template_string(BASE_HTML,
                                  content=html,
                                  logged_in=False)

# ================= STUDENT LOGIN =================

@app.route("/student_login", methods=["GET", "POST"])
def student_login():

    if request.method == "POST":

        if request.form["password"] == "5634":

            session["logged_in"] = True
            session["role"] = "student"

            return redirect("/pending_homeworks")

        else:
            flash("Wrong password!", "danger")

    html = """

<div class="gradient">

<div class="login-box">

<div class="card p-5">

<h2 class="text-center mb-4">
Student Login
</h2>

<form method="POST">

<input type="password"
name="password"
class="form-control form-control-lg mb-3"
placeholder="Student Password"
required>

<button class="btn btn-warning w-100">
Login
</button>

</form>

</div>

</div>

</div>

"""

    return render_template_string(BASE_HTML,
                                  content=html,
                                  logged_in=False)

# ================= CREATE HOMEWORK =================

@app.route("/create_homework", methods=["GET", "POST"])
def create_homework():

    if session.get("role") != "teacher":
        return redirect("/")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]

        c.execute("""
        INSERT INTO homeworks(title,description,due_date)
        VALUES(?,?,?)
        """, (title, description, due_date))

        conn.commit()

        flash("Homework sent to student!", "success")

    html = """

<h2 class="mb-4">
Create Homework
</h2>

<div class="card p-4">

<form method="POST">

<label class="mb-2">
Homework Title
</label>

<input type="text"
name="title"
class="form-control mb-3"
required>

<label class="mb-2">
Description
</label>

<textarea
name="description"
class="form-control mb-3"
rows="5"
required></textarea>

<label class="mb-2">
Due Date
</label>

<input type="date"
name="due_date"
class="form-control mb-4"
required>

<button class="btn btn-primary btn-lg">
Send To Student
</button>

</form>

</div>

"""

    conn.close()

    return render_template_string(BASE_HTML,
                                  content=html,
                                  logged_in=True,
                                  role="teacher")

# ================= PENDING HOMEWORKS =================

@app.route("/pending_homeworks")
def pending_homeworks():

    if session.get("role") != "student":
        return redirect("/")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM homeworks ORDER BY id DESC")
    homeworks = c.fetchall()

    html = "<h2 class='mb-4'>Pending Homeworks</h2>"

    for hw in homeworks:

        html += f"""

<div class="card p-4 mb-4">

<h4>{hw[1]}</h4>

<p>{hw[2]}</p>

<p>
<b>Due Date:</b> {hw[3]}
</p>

</div>

"""

    conn.close()

    return render_template_string(BASE_HTML,
                                  content=html,
                                  logged_in=True,
                                  role="student")

# ================= SUBMIT HOMEWORK =================

@app.route("/submit_homework", methods=["GET", "POST"])
def submit_homework():

    if session.get("role") != "student":
        return redirect("/")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == "POST":

        homework_id = request.form["homework_id"]

        file = request.files["image"]

        if file:

            filename = secure_filename(file.filename)

            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"

            file.save(os.path.join(UPLOAD_FOLDER, filename))

            c.execute("""
            INSERT INTO submissions(
            homework_id,
            image,
            score,
            feedback,
            submitted_at
            )
            VALUES(?,?,?,?,?)
            """, (
                homework_id,
                filename,
                0,
                "",
                datetime.now().strftime("%d/%m/%Y %H:%M")
            ))

            conn.commit()

            flash("Homework submitted!", "success")

    c.execute("SELECT * FROM homeworks")
    homeworks = c.fetchall()

    c.execute("""
    SELECT submissions.*, homeworks.title
    FROM submissions
    JOIN homeworks
    ON submissions.homework_id = homeworks.id
    ORDER BY submissions.id DESC
    """)

    submissions = c.fetchall()

    html = """

<h2 class="mb-4">
Submit Homework
</h2>

<div class="card p-4 mb-5">

<form method="POST" enctype="multipart/form-data">

<label class="mb-2">
Select Homework
</label>

<select name="homework_id" class="form-select mb-3">

"""

    for hw in homeworks:

        html += f"""
<option value="{hw[0]}">
{hw[1]}
</option>
"""

    html += """

</select>

<input type="file"
name="image"
class="form-control mb-4"
required>

<button class="btn btn-success btn-lg">
Send Homework
</button>

</form>

</div>

<h3 class="mb-4">
My Submitted Homeworks
</h3>

"""

    for s in submissions:

        html += f"""

<div class="card p-4 mb-4">

<h5>{s[6]}</h5>

<img src="/uploads/{s[2]}" class="preview mb-3">

<p>
<b>Submitted:</b> {s[5]}
</p>

<p>
<b>Score:</b> {s[3]}/100
</p>

<p>
<b>Teacher Feedback:</b> {s[4]}
</p>

</div>

"""

    conn.close()

    return render_template_string(BASE_HTML,
                                  content=html,
                                  logged_in=True,
                                  role="student")

# ================= CHECK HOMEWORKS =================

@app.route("/check_homeworks", methods=["GET", "POST"])
def check_homeworks():

    if session.get("role") != "teacher":
        return redirect("/")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == "POST":

        submission_id = request.form["submission_id"]
        score = request.form["score"]
        feedback = request.form["feedback"]

        c.execute("""
        UPDATE submissions
        SET score=?,
        feedback=?
        WHERE id=?
        """, (score, feedback, submission_id))

        conn.commit()

        flash("Homework scored!", "success")

    c.execute("""
    SELECT submissions.*, homeworks.title
    FROM submissions
    JOIN homeworks
    ON submissions.homework_id = homeworks.id
    ORDER BY submissions.id DESC
    """)

    submissions = c.fetchall()

    html = """

<h2 class="mb-4">
Check Homeworks
</h2>

"""

    for s in submissions:

        html += f"""

<div class="card p-4 mb-5">

<h4>{s[6]}</h4>

<img src="/uploads/{s[2]}" class="preview mb-4">

<p>
<b>Submitted:</b> {s[5]}
</p>

<form method="POST">

<input type="hidden"
name="submission_id"
value="{s[0]}">

<label class="mb-2">
Score
</label>

<input type="number"
name="score"
class="form-control mb-3"
min="0"
max="100"
value="{s[3]}">

<label class="mb-2">
Feedback
</label>

<textarea
name="feedback"
class="form-control mb-4"
rows="4">{s[4]}</textarea>

<button class="btn btn-primary">
Save Score
</button>

</form>

</div>

"""

    conn.close()

    return render_template_string(BASE_HTML,
                                  content=html,
                                  logged_in=True,
                                  role="teacher")

# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# ================= UPLOADS =================

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(UPLOAD_FOLDER, filename)

# ================= RUN =================

if __name__ == "__main__":

    print("\n✅ English Tracker Running!")
    print("http://127.0.0.1:5999\n")

    app.run(host="0.0.0.0", port=8225333333333333333333333333333333333333333333333333333333333333333333333333333333333333, debug=False)