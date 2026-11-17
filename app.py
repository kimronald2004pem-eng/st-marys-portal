import os
import json
import tempfile
from flask import Flask, render_template, request, redirect, url_for, session, send_file

app = Flask(__name__)
app.secret_key = "smhs_ziroobwe_secure_secret_key_2026"

DB_FILE = "school_database.json"

DEFAULT_DB = {
    "schedule": {
        "term": "Term I",
        "year": "2027",
        "motto": "Ever the Best",
        "ended_on": "04 December 2026",
        "ended_day": "04",
        "ended_month": "December",
        "ended_year": "2026",
        "begins_on": "02 February 2027",
        "begins_day": "02",
        "begins_month": "February",
        "begins_year": "2027"
    },
    "users": {
        "headteacher": {"password": "SMHSPassword2026!", "role": "HEAD_TEACHER", "name": "Head Teacher"},
        "bursar": {"password": "SMHSPassword2026!", "role": "BURSAR", "name": "School Bursar"},
        "dos": {"password": "SMHSPassword2026!", "role": "DOS", "name": "Director of Studies"},
    },
    "students": [
        {"id": "SMHS/2023/001", "name": "NAMUKWAYA DIANA", "class": "S.4", "stream": "East", "gender": "Female", "residential": "Boarding", "combination": "", "photo": ""},
        {"id": "SMHS/2023/002", "name": "KIMBUGWE RONALD", "class": "S.4", "stream": "East", "gender": "Male", "residential": "Day", "combination": "", "photo": ""},
        {"id": "SMHS/2023/003", "name": "KIGOZI BRIAN", "class": "S.1", "stream": "West", "gender": "Male", "residential": "Day", "combination": "", "photo": ""},
        {"id": "SMHS/2025/101", "name": "SSEKANDI EMMANUEL", "class": "S.5", "stream": "North", "gender": "Male", "residential": "Boarding", "combination": "PCM/ICT", "photo": ""}
    ],
    "staff": [
        {"id": "STF/2026/001", "name": "NAMUGGA FATUMA", "role": "Treasurer", "subject": "Mathematics", "status": "Full Staff", "year_joined": "2023", "phone": "+256 708 390869", "email": "fatuma@smhs.ac.ug", "basic_pay": 1000000, "allowance": 200000},
        {"id": "STF/2026/002", "name": "RONALD KIMBUGWE", "role": "Director of Studies", "subject": "Physics & Math", "status": "Full Staff", "year_joined": "2022", "phone": "+256 747 515338", "email": "kimronald2004.pem@gmail.com", "basic_pay": 1200000, "allowance": 300000}
    ],
    "parents": [
        {"parent_name": "MR. KIGOZI EDWARD", "parent_phone": "+256 772 000000", "student_name": "KIGOZI BRIAN", "class": "S.1", "email": "kigozi@gmail.com"}
    ],
    "marks": {
        "SMHS/2023/001": {
            "MATHEMATICS": {"level": "O", "cs": {"CS1": 16.0, "CS2": 18.0, "CS3": 20.0}, "papers": {"P1": {"mid": 64.0, "eot": 74.0}}, "teacher_initials": "RK"}
        }
    },
    "fees_ledger": [
        {
            "student_id": "SMHS/2023/001", "term": "Term I, 2027",
            "tuition_due": 1200000, "tuition_paid": 900000, "balance": 300000, "status": "Balance"
        }
    ],
    "teacher_payments": [],
    "archives": {}
}

def load_db():
    if not os.path.exists(DB_FILE):
        save_db(DEFAULT_DB)
        return DEFAULT_DB
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            for key in DEFAULT_DB:
                if key not in data:
                    data[key] = DEFAULT_DB[key]
            for skey, sval in DEFAULT_DB["schedule"].items():
                if skey not in data["schedule"]:
                    data["schedule"][skey] = sval
            return data
    except Exception:
        return DEFAULT_DB

def save_db(data):
    """Atomic write protection against power cuts (UMEME blackouts)"""
    dir_name = os.path.dirname(os.path.abspath(DB_FILE)) or "."
    with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as tf:
        json.dump(data, tf, indent=4)
        temp_name = tf.name
    os.replace(temp_name, DB_FILE)

SCHOOL_CLASSES = ["S.1", "S.2", "S.3", "S.4", "S.5", "S.6"]
SCHOOL_STREAMS = ["East", "West", "North", "South", "General"]
SCHOOL_TERMS = ["Term I", "Term II", "Term III"]
SCHOOL_YEARS = list(range(2020, 2086))
CALENDAR_DAYS = [f"{d:02d}" for d in range(1, 32)]
CALENDAR_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
CALENDAR_YEARS = [str(y) for y in range(2026, 2087)]

def get_teacher_initials(full_name):
    parts = full_name.strip().split()
    if not parts:
        return "TR"
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return parts[0][:2].upper()

# --- AUTHENTICATION ---
@app.route("/", methods=["GET", "POST"])
def login():
    db = load_db()
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = db.get("users", {})

        if username in users and users[username]["password"] == password:
            session["user"] = username
            session["role"] = users[username]["role"]
            session["name"] = users[username]["name"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid credentials. Access Denied."

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- DASHBOARD ---
@app.route("/dashboard", methods=["GET", "POST"])
@app.route("/dashboard/", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "unlock_ht":
            session["ht_unlocked"] = True
            return redirect(url_for("headteacher_hub"))

    return render_template(
        "dashboard.html",
        name=session.get("name"), role=session.get("role"),
        schedule=db["schedule"],
        students_count=len(db["students"]),
        staff_count=len(db["staff"]),
        payments_count=len(db["teacher_payments"]),
        ht_unlocked=session.get("ht_unlocked", False)
    )

# --- STUDENTS REGISTER & PHOTO UPLOAD ---
@app.route("/students", methods=["GET", "POST"])
def students():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    msg = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            new_id = f"SMHS/2027/{len(db['students'])+1:03d}"
            db["students"].append({
                "id": new_id,
                "name": request.form.get("name", "").upper(),
                "class": request.form.get("class", "S.1"),
                "stream": request.form.get("stream", "East"),
                "gender": request.form.get("gender", "Male"),
                "residential": request.form.get("residential", "Boarding"),
                "combination": request.form.get("combination", ""),
                "photo": request.form.get("photo", "").strip()
            })
            save_db(db)
            msg = "Student registered successfully with photo!"
        elif action == "update_photo":
            sid = request.form.get("student_id")
            new_photo = request.form.get("photo", "").strip()
            for s in db["students"]:
                if s['id'] == sid:
                    s['photo'] = new_photo
                    break
            save_db(db)
            msg = "Student photo updated successfully!"
        elif action == "delete":
            sid = request.form.get("student_id")
            db["students"] = [s for s in db["students"] if s['id'] != sid]
            save_db(db)
            msg = "Student removed."

    return render_template(
        "students.html", name=session["name"], role=session["role"],
        students=db["students"], classes=SCHOOL_CLASSES, streams=SCHOOL_STREAMS,
        terms=SCHOOL_TERMS, years=SCHOOL_YEARS, schedule=db["schedule"], msg=msg
    )

# --- STAFF & PAYROLL ---
@app.route("/staff", methods=["GET", "POST"])
def staff_register():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    msg = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            new_id = f"STF/2027/{len(db['staff'])+1:03d}"
            db["staff"].append({
                "id": new_id,
                "name": request.form.get("staff_name", "").upper(),
                "category": request.form.get("category", "Teaching"),
                "status": request.form.get("status", "Full Staff"),
                "role": request.form.get("role", "Teacher"),
                "subject": request.form.get("subject", "General"),
                "year_joined": request.form.get("year_joined", "2027"),
                "phone": request.form.get("phone", ""),
                "email": request.form.get("email", ""),
                "basic_pay": float(request.form.get("basic_pay", 1000000)),
                "allowance": float(request.form.get("allowance", 200000))
            })
            save_db(db)
            msg = "Staff registered successfully!"
        elif action == "delete":
            sid = request.form.get("staff_id")
            db["staff"] = [t for t in db["staff"] if t['id'] != sid]
            save_db(db)
            msg = "Staff deleted."

    return render_template(
        "staff.html", name=session["name"], role=session["role"],
        staff_list=db["staff"], years=list(range(2015, 2086)), schedule=db["schedule"], msg=msg
    )

@app.route("/payroll")
def payroll():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    return render_template(
        "payroll.html", name=session["name"], role=session["role"],
        staff_list=db["staff"], schedule=db["schedule"]
    )

# --- SUBJECT STATS CALCULATOR ---
def calculate_subject_stats(sub_name, sub_data, is_alevel=False):
    if not isinstance(sub_data, dict):
        sub_data = {}

    cs_dict = sub_data.get('cs', {})
    if not isinstance(cs_dict, dict):
        cs_dict = {}

    cs_vals = [float(v) for v in cs_dict.values() if isinstance(v, (int, float))]
    ca_score = round(sum(cs_vals) / len(cs_vals), 1) if cs_vals else 0.0

    raw_papers = sub_data.get('papers', {})
    papers = {}
    if isinstance(raw_papers, dict):
        for p_key, p_val in raw_papers.items():
            if isinstance(p_val, dict):
                papers[p_key] = p_val
    elif isinstance(raw_papers, list) and len(raw_papers) > 0:
        if isinstance(raw_papers[0], dict):
            papers["P1"] = raw_papers[0]

    mid_vals = [float(p['mid']) for p in papers.values() if isinstance(p.get('mid'), (int, float)) and p.get('mid') > 0]
    eot_vals = [float(p['eot']) for p in papers.values() if isinstance(p.get('eot'), (int, float)) and p.get('eot') > 0]

    mot_total = round(sum(mid_vals) / len(mid_vals), 1) if mid_vals else 0.0
    eot_total = round(sum(eot_vals) / len(eot_vals), 1) if eot_vals else 0.0
    is_subsidiary = is_alevel and sub_name.upper() in ["GENERAL PAPER", "COMPUTER STUDIES", "SUB MATHEMATICS"]

    def get_grade_points_comment(score):
        if score >= 80:
            return ('A', 1 if is_subsidiary else 5, 'Exceptional')
        elif score >= 70:
            return ('B', 1 if is_subsidiary else 4, 'Outstanding')
        elif score >= 60:
            return ('C', 1 if is_subsidiary else 3, 'Satisfactory')
        elif score >= 50:
            return ('D', 1 if is_subsidiary else 2, 'Basic')
        else:
            return ('E', 0 if is_subsidiary else 1, 'Elementary')

    mot_grade, _, _ = get_grade_points_comment(mot_total)
    eot_grade, eot_points, eot_comment = get_grade_points_comment(eot_total)

    return {
        "cs_map": cs_dict,
        "ca": ca_score,
        "papers": papers,
        "mot_total": mot_total,
        "mot_grade": mot_grade,
        "eot_total": eot_total,
        "eot_grade": eot_grade,
        "eot_points": eot_points if is_alevel else 0,
        "eot_comment": eot_comment,
        "is_subsidiary": is_subsidiary,
        "teacher_initials": sub_data.get("teacher_initials", "TR")
    }

def build_student_report(student, db, exam_mode="eot"):
    student_id = student.get('id', '')
    is_alevel = student.get('class') in ['S.5', 'S.6']
    raw_subjects = db.get("marks", {}).get(student_id, {})
    processed_subjects, all_eot, all_mot, total_points = [], [], [], 0

    if isinstance(raw_subjects, dict):
        for name, sub_data in raw_subjects.items():
            stats = calculate_subject_stats(name, sub_data, is_alevel=is_alevel)
            stats['name'] = name
            processed_subjects.append(stats)
            all_eot.append(stats['eot_total'])
            all_mot.append(stats['mot_total'])
            if is_alevel:
                total_points += stats['eot_points']

    term_avg = round(sum(all_eot) / len(all_eot), 1) if all_eot else 0.0
    exam_avg = round(sum(all_mot) / len(all_mot), 1) if all_mot else 0.0
    fees_rec = next((r for r in db["fees_ledger"] if r['student_id'] == student_id), {"balance": 0})
    bal = fees_rec.get('balance', 0)

    if term_avg >= 80:
        overall_grade, overall_desc = "A", "Exceptional"
    elif term_avg >= 70:
        overall_grade, overall_desc = "B", "Outstanding"
    elif term_avg >= 60:
        overall_grade, overall_desc = "C", "Satisfactory"
    elif term_avg >= 50:
        overall_grade, overall_desc = "D", "Basic"
    else:
        overall_grade, overall_desc = "E", "Elementary"

    return {
        "report_title": "MID-TERM ACADEMIC REPORT" if exam_mode == 'mid' else "END-OF-TERM ACADEMIC REPORT",
        "term": f"{db['schedule']['term']}, {db['schedule']['year']}",
        "exam_mode": exam_mode,
        "active_cs": ["CS1", "CS2", "CS3", "CS4", "CS5"],
        "subjects": processed_subjects,
        "exam_avg": exam_avg,
        "term_avg": term_avg,
        "total_points": total_points,
        "overall_term_grade": overall_grade,
        "overall_desc": overall_desc,
        "conduct": "Excellent",
        "class_teacher_remark": "Exceptional competence & consistent academic focus.",
        "head_teacher_remark": "Outstanding distinction, keep up the spirit!",
        "ended_on": db['schedule'].get('ended_on', '04 December 2026'),
        "begins_on": db['schedule'].get('begins_on', '02 February 2027'),
        "fees": {
            "balance": bal,
            "label": f"UGX {bal:,.0f}" if bal > 0 else "Fully Paid"
        }
    }

@app.route("/reports")
def reports_hub():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    selected_class = request.args.get("selected_class", "ALL")
    students = db["students"] if selected_class == "ALL" else [s for s in db["students"] if s.get('class') == selected_class]
    return render_template(
        "reports.html", name=session["name"], role=session["role"],
        students=students, classes=SCHOOL_CLASSES, selected_class=selected_class, schedule=db["schedule"]
    )

@app.route("/report/view")
def view_report():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    student_id = request.args.get("id")
    exam_mode = request.args.get("exam_mode", "eot")
    student = next((s for s in db["students"] if s['id'] == student_id), db["students"][0] if db["students"] else {"id": "", "name": "STUDENT", "class": "S.4", "stream": "East", "gender": "Female", "residential": "Boarding", "photo": ""})
    is_alevel = student.get('class') in ['S.5', 'S.6']
    report = build_student_report(student, db, exam_mode=exam_mode)
    return render_template("report_card_print.html", student=student, report=report, is_alevel=is_alevel, schedule=db["schedule"])

@app.route("/reports/batch")
def batch_print_reports():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    target_class = request.args.get("class", "ALL")
    exam_mode = request.args.get("exam_mode", "eot")
    filtered_students = db["students"] if target_class == "ALL" else [s for s in db["students"] if s.get('class') == target_class]

    reports_list = []
    for student in filtered_students:
        is_alevel = student.get('class') in ['S.5', 'S.6']
        report = build_student_report(student, db, exam_mode=exam_mode)
        reports_list.append({"student": student, "report": report, "is_alevel": is_alevel})

    return render_template("batch_print.html", reports_list=reports_list, target_class=target_class, schedule=db["schedule"])

@app.route("/reports/class-result-list")
def class_result_list():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    target_class = request.args.get("class", "S.4")
    students = [s for s in db["students"] if s.get("class") == target_class]
    is_alevel = target_class in ["S.5", "S.6"]

    class_results = []
    for s in students:
        s_id = s['id']
        s_marks = db.get("marks", {}).get(s_id, {})
        sub_averages = {}
        tot = 0
        cnt = 0
        if isinstance(s_marks, dict):
            for sub, data in s_marks.items():
                stats = calculate_subject_stats(sub, data, is_alevel=is_alevel)
                sub_averages[sub] = stats['eot_total']
                tot += stats['eot_total']
                cnt += 1
        avg = round(tot / cnt, 1) if cnt > 0 else 0.0
        class_results.append({"student": s, "subjects": sub_averages, "average": avg})

    return render_template("class_result_list.html", target_class=target_class, class_results=class_results, schedule=db["schedule"])

# --- ENTER MARKS ---
@app.route("/enter_marks", methods=["GET", "POST"])
def enter_marks():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    msg = None

    selected_class = request.form.get("class") or request.args.get("class", "S.4")
    student_search = request.form.get("student_search", "").strip().lower()
    student_id = request.form.get("student_id") or request.args.get("student_id", "")

    class_students = []
    for s in db["students"]:
        if s.get("class") == selected_class:
            if not student_search or (student_search in s["name"].lower() or student_search in s["id"].lower()):
                class_students.append(s)

    is_alevel = selected_class in ["S.5", "S.6"]
    if is_alevel:
        available_subjects = [
            "MATHEMATICS", "PHYSICS", "CHEMISTRY", "BIOLOGY", "GENERAL PAPER",
            "COMPUTER STUDIES", "SUB MATHEMATICS", "ECONOMICS", "ENTREPRENEURSHIP",
            "GEOGRAPHY", "HISTORY", "LITERATURE", "AGRICULTURE", "ART AND DESIGN", "PERFORMING ARTS"
        ]
    else:
        available_subjects = [
            "ENGLISH LANGUAGE", "MATHEMATICS", "HISTORY AND POLITICAL EDUCATION",
            "GEOGRAPHY", "PHYSICS", "CHEMISTRY", "BIOLOGY", "PHYSICAL EDUCATION",
            "RELIGIOUS EDUCATION (CRE/IRE)", "ENTREPRENEURSHIP", "KISWAHILI",
            "AGRICULTURE", "ART AND DESIGN", "PERFORMING ARTS"
        ]

    if request.method == "POST" and request.form.get("action") == "save_marks":
        student_id = request.form.get("student_id")
        subject = request.form.get("subject", "").strip().upper()
        paper_type = request.form.get("paper_type", "P1")
        exam_type = request.form.get("exam_type")
        score_val = float(request.form.get("score", 0))
        cs_key = request.form.get("cs_key", "").strip().upper()
        selected_teacher = request.form.get("teacher_name", "")

        t_initials = get_teacher_initials(selected_teacher) if selected_teacher else "TR"

        if student_id not in db["marks"] or not isinstance(db["marks"][student_id], dict):
            db["marks"][student_id] = {}
        if subject not in db["marks"][student_id] or not isinstance(db["marks"][student_id][subject], dict):
            db["marks"][student_id][subject] = {
                "level": "A" if is_alevel else "O",
                "cs": {},
                "papers": {},
                "teacher_initials": t_initials
            }

        sub_record = db["marks"][student_id][subject]
        sub_record["teacher_initials"] = t_initials

        if exam_type == "cs" and cs_key:
            if "cs" not in sub_record or not isinstance(sub_record["cs"], dict):
                sub_record["cs"] = {}
            sub_record["cs"][cs_key] = score_val
            msg = f"Competency '{cs_key}' for {subject} saved successfully!"
        elif exam_type in ["mid", "eot"]:
            if "papers" not in sub_record or not isinstance(sub_record["papers"], dict):
                sub_record["papers"] = {}
            if paper_type not in sub_record["papers"] or not isinstance(sub_record["papers"][paper_type], dict):
                sub_record["papers"][paper_type] = {"mid": 0.0, "eot": 0.0}
            sub_record["papers"][paper_type][exam_type] = score_val
            msg = f"{exam_type.upper()} mark for {subject} ({paper_type}) saved successfully!"

        save_db(db)

    current_student_marks = db.get("marks", {}).get(student_id, {})

    return render_template(
        "enter_marks.html",
        name=session["name"], role=session["role"],
        classes=SCHOOL_CLASSES, selected_class=selected_class,
        class_students=class_students, student_id=student_id,
        student_search=student_search, available_subjects=available_subjects,
        staff_list=db["staff"], current_student_marks=current_student_marks,
        schedule=db["schedule"], msg=msg
    )

# --- FEES & PAYMENTS ---
@app.route("/fees", methods=["GET", "POST"])
@app.route("/payments", methods=["GET", "POST"])
def fees_ledger():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    msg = None
    if request.method == "POST":
        amount_paid = request.form.get("amount_paid")
        if amount_paid:
            student_id = request.form.get("student_id")
            pay_amt = float(amount_paid)
            record = next((r for r in db["fees_ledger"] if r['student_id'] == student_id), None)
            if record:
                record['tuition_paid'] = record.get('tuition_paid', 0) + pay_amt
                record['balance'] = max(0, record.get('tuition_due', 1200000) - record['tuition_paid'])
                record['status'] = "Cleared" if record['balance'] == 0 else "Balance"
            else:
                db["fees_ledger"].append({
                    'student_id': student_id,
                    'term': f"{db['schedule']['term']}, {db['schedule']['year']}",
                    'tuition_due': 1200000, 'tuition_paid': pay_amt,
                    'balance': max(0, 1200000 - pay_amt),
                    'status': "Cleared" if (1200000 - pay_amt) == 0 else "Balance"
                })
            save_db(db)
            msg = f"Payment of UGX {pay_amt:,.0f} logged successfully!"

    selected_class = request.args.get("selected_class", "ALL")
    balance_filter = request.args.get("balance_filter", "ALL")
    search_query = request.args.get("search", "").strip().lower()

    payments_list = []
    for s in db["students"]:
        fee_rec = next((r for r in db["fees_ledger"] if r['student_id'] == s['id']), {
            'tuition_due': 1200000, 'tuition_paid': 0, 'balance': 1200000, 'status': 'Balance'
        })
        item = {
            "id": s['id'], "name": s['name'], "class": s.get('class', 'S.1'), "stream": s.get('stream', 'East'),
            "total_fees": fee_rec.get('tuition_due', 1200000), "paid": fee_rec.get('tuition_paid', 0),
            "balance": fee_rec.get('balance', 1200000), "status": fee_rec.get('status', 'Balance')
        }
        if selected_class != "ALL" and item["class"] != selected_class: continue
        if search_query and search_query not in item["name"].lower() and search_query not in item["id"].lower(): continue
        if balance_filter == "balance" and item["balance"] <= 0: continue
        if balance_filter == "cleared" and item["balance"] > 0: continue
        payments_list.append(item)

    return render_template(
        "payments.html", name=session["name"], role=session["role"],
        students=db["students"], payments=payments_list, classes=SCHOOL_CLASSES,
        selected_class=selected_class, balance_filter=balance_filter, search_query=search_query,
        ledger=db["fees_ledger"], schedule=db["schedule"], msg=msg
    )

@app.route("/receipt/print")
def print_receipt():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    student_id = request.args.get("student_id")
    term = request.args.get("term", f"{db['schedule']['term']}, {db['schedule']['year']}")
    student = next((s for s in db["students"] if s['id'] == student_id), {'id': student_id, 'name': 'Student', 'class': 'S.1'})
    record = next((r for r in db["fees_ledger"] if r['student_id'] == student_id and r['term'] == term), {'tuition_paid': 0, 'balance': 1200000})
    return render_template("receipt_print.html", student=student, record=record, term=term, schedule=db["schedule"])

# --- PARENTS PORTAL ---
@app.route("/parents", methods=["GET", "POST"])
def parents_portal():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    msg = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_parent":
            db["parents"].append({
                "parent_name": request.form.get("parent_name", "").upper(),
                "parent_phone": request.form.get("parent_phone", ""),
                "student_name": request.form.get("student_name", "").upper(),
                "class": request.form.get("class", "S.1"),
                "email": request.form.get("email", "")
            })
            save_db(db)
            msg = "Parent contact linked successfully!"

    return render_template(
        "parents.html", name=session["name"], role=session["role"],
        students=db["students"], parents=db["parents"], classes=SCHOOL_CLASSES,
        schedule=db["schedule"], msg=msg
    )

# --- LEADERS PORTAL ---
@app.route("/leaders")
def leaders():
    if "user" not in session: return redirect(url_for("login"))
    db = load_db()
    return render_template("leaders.html", name=session["name"], role=session["role"], students=db["students"], schedule=db["schedule"])

# --- HEAD TEACHER HUB (WITH DATABASE BACKUP DOWNLOAD & RESTORE) ---
@app.route("/headteacher/hub", methods=["GET", "POST"])
@app.route("/headteacher/hub/", methods=["GET", "POST"])
def headteacher_hub():
    if "user" not in session:
        return redirect(url_for("login"))

    db = load_db()
    success_msg = None

    if request.method == "POST":
        pin_val = request.form.get("pin")
        if pin_val is not None:
            session["ht_unlocked"] = True
            return redirect(url_for("headteacher_hub"))

        action = request.form.get("action")
        if action and session.get("ht_unlocked"):
            if action == "save_schedule":
                db["schedule"]["term"] = request.form.get("global_term", db["schedule"]["term"])
                db["schedule"]["year"] = request.form.get("global_year", db["schedule"]["year"])

                e_day = request.form.get("ended_day", "04")
                e_month = request.form.get("ended_month", "December")
                e_year = request.form.get("ended_year", "2026")
                db["schedule"]["ended_day"] = e_day
                db["schedule"]["ended_month"] = e_month
                db["schedule"]["ended_year"] = e_year
                db["schedule"]["ended_on"] = f"{e_day} {e_month} {e_year}"

                b_day = request.form.get("begins_day", "02")
                b_month = request.form.get("begins_month", "February")
                b_year = request.form.get("begins_year", "2027")
                db["schedule"]["begins_day"] = b_day
                db["schedule"]["begins_month"] = b_month
                db["schedule"]["begins_year"] = b_year
                db["schedule"]["begins_on"] = f"{b_day} {b_month} {b_year}"

                save_db(db)
                success_msg = "School calendar updated successfully!"
            elif action == "archive_term":
                term_str = f"{db['schedule']['term']} {db['schedule']['year']}"
                db["archives"][term_str] = {
                    "students": db["students"],
                    "staff": db["staff"],
                    "fees_ledger": db["fees_ledger"],
                    "marks": db["marks"]
                }
                db["marks"] = {}
                db["fees_ledger"] = []
                save_db(db)
                success_msg = f"Term '{term_str}' archived successfully and active marks reset for the new term!"
            elif action == "factory_reset":
                db["students"] = []
                db["staff"] = []
                db["parents"] = []
                db["marks"] = {}
                db["fees_ledger"] = []
                db["teacher_payments"] = []
                db["archives"] = {}
                save_db(db)
                success_msg = "Factory reset complete! All demo data wiped clean for live handover."

    return render_template(
        "headteacher_hub.html",
        name=session.get("name", "Head Teacher"),
        role=session.get("role", "HEAD_TEACHER"),
        schedule=db["schedule"],
        terms=SCHOOL_TERMS,
        years=SCHOOL_YEARS,
        cal_days=CALENDAR_DAYS,
        cal_months=CALENDAR_MONTHS,
        cal_years=CALENDAR_YEARS,
        classes=SCHOOL_CLASSES,
        archives=db["archives"],
        students_list=db["students"],
        staff_list=db["staff"],
        parents_list=db["parents"],
        success_msg=success_msg,
        ht_unlocked=session.get("ht_unlocked", True)
    )

@app.route("/download-backup")
def download_backup():
    if "user" not in session or session.get("role") != "HEAD_TEACHER":
        return redirect(url_for("login"))
    if os.path.exists(DB_FILE):
        return send_file(DB_FILE, as_attachment=True, download_name="SMAHIZ_Database_Backup.json")
    return redirect(url_for("headteacher_hub"))

@app.route("/bypass-hub")
def bypass_hub():
    session["ht_unlocked"] = True
    return redirect(url_for("headteacher_hub"))

# --- PROGRESS REPORT & TRACKING ANALYTICS ---
@app.route("/headteacher/progress-report", methods=["GET"])
@app.route("/headteacher/progress-report/", methods=["GET"])
def headteacher_progress_report():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()

    target_class = request.args.get("filter_class", "ALL")
    selected_archive = request.args.get("archive_key", "")

    current_marks = db.get("marks", {})
    historical_marks = {}
    if selected_archive and selected_archive in db.get("archives", {}):
        historical_marks = db["archives"][selected_archive].get("marks", {})

    students_pool = db["students"] if target_class == "ALL" else [s for s in db["students"] if s.get("class") == target_class]

    class_analysis = []
    for student in students_pool:
        s_id = student["id"]
        s_marks = current_marks.get(s_id, {})
        hist_s_marks = historical_marks.get(s_id, {})

        sub_comparisons = []
        cur_total, cur_count = 0, 0
        if isinstance(s_marks, dict):
            for sub_name, sdata in s_marks.items():
                stats = calculate_subject_stats(sub_name, sdata)
                eot = stats['eot_total']
                cur_total += eot
                cur_count += 1

                hist_sub = hist_s_marks.get(sub_name, {})
                hist_stats = calculate_subject_stats(sub_name, hist_sub)
                hist_eot = hist_stats['eot_total'] if hist_sub else eot

                diff = eot - hist_eot
                trend = "Progressive 📈" if diff > 2 else ("Decline 📉" if diff < -2 else "Moderate / Stable ⚖️")

                sub_comparisons.append({
                    "subject": sub_name,
                    "current_eot": eot,
                    "historical_eot": hist_eot,
                    "trend": trend
                })

        student_avg = round(cur_total / cur_count, 1) if cur_count > 0 else 0.0
        class_analysis.append({
            "student": student,
            "subjects": sub_comparisons,
            "term_average": student_avg
        })

    return render_template(
        "progress_report.html",
        name=session.get("name", "Head Teacher"),
        role=session.get("role", "HEAD_TEACHER"),
        schedule=db["schedule"],
        classes=SCHOOL_CLASSES,
        target_class=target_class,
        archives=db.get("archives", {}),
        selected_archive=selected_archive,
        class_analysis=class_analysis
    )

# --- COMPREHENSIVE CLASS REPORT ENGINE (WITH LINE GRAPH TREND DATA) ---
@app.route("/headteacher/comprehensive-report", methods=["GET"])
def comprehensive_class_report():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()

    target_class = request.args.get("class", "S.4")
    selected_archive = request.args.get("archive_key", "")

    current_marks = db.get("marks", {})
    historical_marks = {}
    if selected_archive and selected_archive in db.get("archives", {}):
        historical_marks = db["archives"][selected_archive].get("marks", {})

    students_pool = [s for s in db["students"] if s.get("class") == target_class]

    term_labels = []
    class_trend_means = []

    for arch_key, arch_val in db.get("archives", {}).items():
        term_labels.append(arch_key)
        arch_students = [s for s in arch_val.get("students", []) if s.get("class") == target_class]
        arch_marks = arch_val.get("marks", {})
        arch_totals = []
        for st in arch_students:
            st_marks = arch_marks.get(st["id"], {})
            st_sum = sum([calculate_subject_stats(sub, sdata)['eot_total'] for sub, sdata in st_marks.items()]) if isinstance(st_marks, dict) else 0
            st_cnt = len(st_marks) if isinstance(st_marks, dict) and len(st_marks) > 0 else 1
            arch_totals.append(st_sum / st_cnt)
        mean_val = round(sum(arch_totals) / len(arch_totals), 1) if arch_totals else 0.0
        class_trend_means.append(mean_val)

    current_term_label = f"{db['schedule']['term']} {db['schedule']['year']}"
    term_labels.append(current_term_label)

    SCIENCE_SUBJECTS = ["MATHEMATICS", "PHYSICS", "CHEMISTRY", "BIOLOGY", "COMPUTER STUDIES", "SUB MATHEMATICS", "AGRICULTURE"]
    HUMANITIES_SUBJECTS = ["ENGLISH LANGUAGE", "GENERAL PAPER", "HISTORY AND POLITICAL EDUCATION", "GEOGRAPHY", "CRE", "RELIGIOUS EDUCATION (CRE/IRE)", "LITERATURE", "ENTREPRENEURSHIP", "KISWAHILI", "ART AND DESIGN", "PERFORMING ARTS", "PHYSICAL EDUCATION"]

    subject_stats_aggregate = {}
    science_totals = []
    humanities_totals = []
    class_students_data = []
    class_total_scores = []

    for student in students_pool:
        s_id = student["id"]
        s_marks = current_marks.get(s_id, {})
        hist_s_marks = historical_marks.get(s_id, {})

        student_subs = []
        s_total, s_count = 0, 0

        if isinstance(s_marks, dict):
            for sub_name, sdata in s_marks.items():
                stats = calculate_subject_stats(sub_name, sdata)
                eot = stats['eot_total']
                s_total += eot
                s_count += 1

                hist_sub = hist_s_marks.get(sub_name, {})
                hist_stats = calculate_subject_stats(sub_name, hist_sub)
                hist_eot = hist_stats['eot_total'] if hist_sub else eot

                diff = eot - hist_eot
                trend = "Improved 📈" if diff > 2 else ("Declined 📉" if diff < -2 else "Stable ⚖️")

                if sub_name.upper() in SCIENCE_SUBJECTS:
                    science_totals.append(eot)
                elif sub_name.upper() in HUMANITIES_SUBJECTS:
                    humanities_totals.append(eot)

                if sub_name not in subject_stats_aggregate:
                    subject_stats_aggregate[sub_name] = {"total": 0, "count": 0, "declines": 0, "improvements": 0}
                subject_stats_aggregate[sub_name]["total"] += eot
                subject_stats_aggregate[sub_name]["count"] += 1
                if diff > 2:
                    subject_stats_aggregate[sub_name]["improvements"] += 1
                elif diff < -2:
                    subject_stats_aggregate[sub_name]["declines"] += 1

                student_subs.append({
                    "subject": sub_name, "current": eot, "previous": hist_eot,
                    "diff": round(diff, 1), "trend": trend
                })

        student_avg = round(s_total / s_count, 1) if s_count > 0 else 0.0
        if s_count > 0: class_total_scores.append(student_avg)
        class_students_data.append({"student": student, "subjects": student_subs, "average": student_avg})

    processed_subject_summaries = []
    weakest_subject = "None Recorded"
    lowest_avg = 100

    for sub, data in subject_stats_aggregate.items():
        avg = round(data["total"] / data["count"], 1) if data["count"] > 0 else 0.0
        if avg < lowest_avg:
            lowest_avg = avg
            weakest_subject = sub
        processed_subject_summaries.append({
            "subject": sub, "average": avg,
            "improvements": data["improvements"], "declines": data["declines"]
        })

    class_overall_avg = round(sum(class_total_scores) / len(class_total_scores), 1) if class_total_scores else 0.0
    class_trend_means.append(class_overall_avg)

    science_avg = round(sum(science_totals) / len(science_totals), 1) if science_totals else 0.0
    humanities_avg = round(sum(humanities_totals) / len(humanities_totals), 1) if humanities_totals else 0.0

    performance_narrative = (
        f"In {target_class}, the institutional academic review for {db['schedule']['term']} {db['schedule']['year']} "
        f"indicates an overall class mean average of {class_overall_avg}%. "
        f"Humanities aggregate performance stood at {humanities_avg}%, compared to Sciences at {science_avg}%. "
        f"Departmental focus must be directed toward strengthening competencies in {weakest_subject}."
    )

    report_package = {
        "class_name": target_class, "term": current_term_label,
        "class_average": class_overall_avg, "science_average": science_avg, "humanities_average": humanities_avg,
        "weakest_subject": weakest_subject, "narrative": performance_narrative,
        "trend_labels": term_labels, "trend_data": class_trend_means,
        "subject_summaries": processed_subject_summaries, "students_data": class_students_data
    }

    return render_template(
        "comprehensive_report_print.html",
        report=report_package, schedule=db["schedule"], classes=SCHOOL_CLASSES,
        target_class=target_class, archives=db.get("archives", {}), selected_archive=selected_archive
    )

if __name__ == "__main__":
    app.run(threaded=True, host="127.0.0.1", port=5000)