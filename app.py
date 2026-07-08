import os
import json
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ── Supabase client ──────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_client() -> Client:
    if supabase is None:
        raise RuntimeError("Supabase client not initialised. Check env vars.")
    return supabase


# ── Helpers ───────────────────────────────────────────────────
def ok(data=None, status=200):
    return jsonify({"success": True, "data": data}), status


def err(msg, status=400):
    return jsonify({"success": False, "error": msg}), status


# ── Health ────────────────────────────────────────────────────
@app.route("/healthz")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


# ── Serve SPA ─────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ── Mock Login ────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    if email == "admin@nimbark.com" and password == "password123":
        return ok({
            "token": "nimbark_mock_token_2024",
            "user": {"name": "Admin User", "email": email, "role": "Administrator"}
        })
    return err("Invalid credentials", 401)


# ── Generic CRUD factory ──────────────────────────────────────
def make_crud(table: str, required_fields: list):

    def get_all():
        try:
            db = get_client()
            res = db.table(table).select("*").order("created_at", desc=True).execute()
            return ok(res.data)
        except Exception as e:
            return err(str(e), 500)

    def get_one(record_id):
        try:
            db = get_client()
            res = db.table(table).select("*").eq("id", record_id).single().execute()
            return ok(res.data)
        except Exception as e:
            return err(str(e), 404)

    def create():
        try:
            body = request.get_json(silent=True) or {}
            missing = [f for f in required_fields if not body.get(f)]
            if missing:
                return err(f"Missing required fields: {', '.join(missing)}")
            db = get_client()
            res = db.table(table).insert(body).execute()
            return ok(res.data[0] if res.data else {}, 201)
        except Exception as e:
            return err(str(e), 500)

    def update(record_id):
        try:
            body = request.get_json(silent=True) or {}
            if not body:
                return err("No data provided")
            # Partial update — only send fields present in payload
            db = get_client()
            res = db.table(table).update(body).eq("id", record_id).execute()
            return ok(res.data[0] if res.data else {})
        except Exception as e:
            return err(str(e), 500)

    def delete(record_id):
        try:
            db = get_client()
            db.table(table).delete().eq("id", record_id).execute()
            return ok({"deleted": record_id})
        except Exception as e:
            return err(str(e), 500)

    return get_all, get_one, create, update, delete


# ── Departments ───────────────────────────────────────────────
dept_all, dept_one, dept_create, dept_update, dept_delete = make_crud(
    "departments", ["name"]
)
app.add_url_rule("/api/departments", "dept_all", dept_all, methods=["GET"])
app.add_url_rule("/api/departments/<record_id>", "dept_one", dept_one, methods=["GET"])
app.add_url_rule("/api/departments", "dept_create", dept_create, methods=["POST"])
app.add_url_rule("/api/departments/<record_id>", "dept_update", dept_update, methods=["PUT"])
app.add_url_rule("/api/departments/<record_id>", "dept_delete", dept_delete, methods=["DELETE"])


# ── Positions ─────────────────────────────────────────────────
pos_all, pos_one, pos_create, pos_update, pos_delete = make_crud(
    "positions", ["title"]
)
app.add_url_rule("/api/positions", "pos_all", pos_all, methods=["GET"])
app.add_url_rule("/api/positions/<record_id>", "pos_one", pos_one, methods=["GET"])
app.add_url_rule("/api/positions", "pos_create", pos_create, methods=["POST"])
app.add_url_rule("/api/positions/<record_id>", "pos_update", pos_update, methods=["PUT"])
app.add_url_rule("/api/positions/<record_id>", "pos_delete", pos_delete, methods=["DELETE"])


# ── Employees ─────────────────────────────────────────────────
emp_all, emp_one, emp_create, emp_update, emp_delete = make_crud(
    "employees", ["first_name", "last_name", "email"]
)
app.add_url_rule("/api/employees", "emp_all", emp_all, methods=["GET"])
app.add_url_rule("/api/employees/<record_id>", "emp_one", emp_one, methods=["GET"])
app.add_url_rule("/api/employees", "emp_create", emp_create, methods=["POST"])
app.add_url_rule("/api/employees/<record_id>", "emp_update", emp_update, methods=["PUT"])
app.add_url_rule("/api/employees/<record_id>", "emp_delete", emp_delete, methods=["DELETE"])


# ── Attendance ────────────────────────────────────────────────
att_all, att_one, att_create, att_update, att_delete = make_crud(
    "attendance", ["employee_id", "date"]
)
app.add_url_rule("/api/attendance", "att_all", att_all, methods=["GET"])
app.add_url_rule("/api/attendance/<record_id>", "att_one", att_one, methods=["GET"])
app.add_url_rule("/api/attendance", "att_create", att_create, methods=["POST"])
app.add_url_rule("/api/attendance/<record_id>", "att_update", att_update, methods=["PUT"])
app.add_url_rule("/api/attendance/<record_id>", "att_delete", att_delete, methods=["DELETE"])


# ── Leaves ────────────────────────────────────────────────────
lv_all, lv_one, lv_create, lv_update, lv_delete = make_crud(
    "leaves", ["employee_id", "start_date", "end_date"]
)
app.add_url_rule("/api/leaves", "lv_all", lv_all, methods=["GET"])
app.add_url_rule("/api/leaves/<record_id>", "lv_one", lv_one, methods=["GET"])
app.add_url_rule("/api/leaves", "lv_create", lv_create, methods=["POST"])
app.add_url_rule("/api/leaves/<record_id>", "lv_update", lv_update, methods=["PUT"])
app.add_url_rule("/api/leaves/<record_id>", "lv_delete", lv_delete, methods=["DELETE"])


# ── Payroll ───────────────────────────────────────────────────
pay_all, pay_one, pay_create, pay_update, pay_delete = make_crud(
    "payroll", ["employee_id", "pay_period_start", "pay_period_end"]
)
app.add_url_rule("/api/payroll", "pay_all", pay_all, methods=["GET"])
app.add_url_rule("/api/payroll/<record_id>", "pay_one", pay_one, methods=["GET"])
app.add_url_rule("/api/payroll", "pay_create", pay_create, methods=["POST"])
app.add_url_rule("/api/payroll/<record_id>", "pay_update", pay_update, methods=["PUT"])
app.add_url_rule("/api/payroll/<record_id>", "pay_delete", pay_delete, methods=["DELETE"])


# ── Dashboard Stats ───────────────────────────────────────────
@app.route("/api/dashboard/stats")
def dashboard_stats():
    try:
        db = get_client()

        # Counts
        emp_res = db.table("employees").select("id, status, hire_date, department_id, position_id, first_name, last_name, profile_pic").execute()
        employees = emp_res.data or []

        dept_res = db.table("departments").select("id, name").execute()
        departments = dept_res.data or []

        pos_res = db.table("positions").select("id, title").execute()
        positions = pos_res.data or []

        leaves_res = db.table("leaves").select("id, status").execute()
        leaves = leaves_res.data or []

        payroll_res = db.table("payroll").select("id").execute()
        payrolls = payroll_res.data or []

        total_emp = len(employees)
        active_emp = sum(1 for e in employees if e.get("status") == "Active")
        total_dept = len(departments)
        pending_leaves = sum(1 for l in leaves if l.get("status") == "Pending")
        total_payroll = len(payrolls)

        # Hiring trend (last 6 months)
        from collections import Counter
        months_labels = []
        now = datetime.utcnow()
        for i in range(5, -1, -1):
            m = (now.month - i - 1) % 12 + 1
            y = now.year - ((now.month - i - 1) // 12)
            months_labels.append(datetime(y, m, 1).strftime("%b %Y"))

        hire_counts = Counter()
        for e in employees:
            hd = e.get("hire_date")
            if hd:
                try:
                    d = datetime.strptime(hd[:10], "%Y-%m-%d")
                    label = d.strftime("%b %Y")
                    if label in months_labels:
                        hire_counts[label] += 1
                except Exception:
                    pass

        hiring_trend = {
            "labels": months_labels,
            "data": [hire_counts.get(m, 0) for m in months_labels]
        }

        # Department mix
        dept_map = {d["id"]: d["name"] for d in departments}
        dept_emp_count = Counter()
        for e in employees:
            did = e.get("department_id")
            if did:
                dept_emp_count[dept_map.get(did, "Unknown")] += 1

        dept_mix = {
            "labels": list(dept_emp_count.keys()),
            "data": list(dept_emp_count.values())
        }

        # Status breakdown
        status_count = Counter(e.get("status", "Unknown") for e in employees)
        status_breakdown = {
            "labels": list(status_count.keys()),
            "data": list(status_count.values())
        }

        # Employees by position list
        pos_map = {p["id"]: p["title"] for p in positions}
        emp_position_list = []
        for e in employees[:20]:
            pid = e.get("position_id")
            name = f"{e.get('first_name','')} {e.get('last_name','')}".strip()
            emp_position_list.append({
                "name": name,
                "position": pos_map.get(pid, "Unassigned") if pid else "Unassigned",
                "profile_pic": e.get("profile_pic") or f"https://api.dicebear.com/7.x/initials/svg?seed={name}&backgroundColor=6D28D9"
            })

        # Attendance trend (mock last 7 days)
        att_res = db.table("attendance").select("date, status").execute()
        att_records = att_res.data or []
        from datetime import timedelta
        att_labels = [(now - timedelta(days=i)).strftime("%d %b") for i in range(6, -1, -1)]
        att_present = []
        att_absent = []
        for label in att_labels:
            day_records = [a for a in att_records if a.get("date") and datetime.strptime(a["date"][:10], "%Y-%m-%d").strftime("%d %b") == label]
            att_present.append(sum(1 for a in day_records if a.get("status") == "Present"))
            att_absent.append(sum(1 for a in day_records if a.get("status") == "Absent"))

        attendance_trend = {
            "labels": att_labels,
            "present": att_present,
            "absent": att_absent
        }

        return ok({
            "stats": {
                "total_employees": total_emp,
                "active_employees": active_emp,
                "total_departments": total_dept,
                "pending_leaves": pending_leaves,
                "total_payroll": total_payroll
            },
            "hiring_trend": hiring_trend,
            "dept_mix": dept_mix,
            "status_breakdown": status_breakdown,
            "emp_position_list": emp_position_list,
            "attendance_trend": attendance_trend
        })

    except Exception as e:
        return err(str(e), 500)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
