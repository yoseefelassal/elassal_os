import os
import re
import hmac
import secrets
import sqlite3
from pathlib import Path
from functools import wraps

from flask import (
    Blueprint, current_app, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def configure_auth(app):
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    secret_file = Path(app.instance_path) / "session_secret"

    if not secret_file.exists():
        secret_file.write_text(secrets.token_hex(32), encoding="utf-8")
        try:
            secret_file.chmod(0o600)
        except OSError:
            pass

    app.secret_key = os.environ.get(
        "ELASSAL_SECRET_KEY",
        secret_file.read_text(encoding="utf-8").strip()
    )
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["AUTH_DB"] = str(Path(app.instance_path) / "elassal_accounts.sqlite3")

    with sqlite3.connect(app.config["AUTH_DB"]) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def db_connect():
    db = sqlite3.connect(current_app.config["AUTH_DB"])
    db.row_factory = sqlite3.Row
    return db


def valid_csrf():
    sent = request.form.get("csrf_token", "")
    saved = session.get("_auth_csrf", "")
    return bool(sent and saved and hmac.compare_digest(sent, saved))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("account_id"):
            flash("سجّل دخولك الأول.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    session.setdefault("_auth_csrf", secrets.token_urlsafe(32))

    if request.method == "POST":
        if not valid_csrf():
            flash("انتهت صلاحية النموذج. حاول مرة أخرى.", "error")
            return redirect(url_for("auth.register"))

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not re.fullmatch(r"[A-Za-z0-9_\u0600-\u06FF]{3,24}", username):
            flash("اسم المستخدم يجب أن يكون من 3 إلى 24 خانة، بحروف عربية أو إنجليزية أو أرقام أو _.", "error")
        elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("اكتب بريدًا إلكترونيًا صحيحًا.", "error")
        elif len(password) < 10:
            flash("كلمة المرور يجب أن تكون 10 أحرف على الأقل.", "error")
        else:
            try:
                with db_connect() as db:
                    db.execute(
                        "INSERT INTO accounts(username,email,password_hash) VALUES(?,?,?)",
                        (username, email, generate_password_hash(password))
                    )
                flash("تم إنشاء الحساب. تسجيل الدخول متاح الآن.", "success")
                return redirect(url_for("auth.login"))
            except sqlite3.IntegrityError:
                flash("اسم المستخدم أو البريد مستخدم بالفعل.", "error")

    return render_template("auth_register.html", csrf_token=session["_auth_csrf"])


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    session.setdefault("_auth_csrf", secrets.token_urlsafe(32))

    if request.method == "POST":
        if not valid_csrf():
            flash("انتهت صلاحية النموذج. حاول مرة أخرى.", "error")
            return redirect(url_for("auth.login"))

        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")

        with db_connect() as db:
            account = db.execute(
                "SELECT * FROM accounts WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE",
                (identity, identity)
            ).fetchone()

        if account and check_password_hash(account["password_hash"], password):
            session.clear()
            session["account_id"] = account["id"]
            session["username"] = account["username"]
            return redirect(url_for("auth.profile"))

        flash("بيانات الدخول غير صحيحة.", "error")

    return render_template("auth_login.html", csrf_token=session["_auth_csrf"])


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("auth_profile.html", username=session.get("username", "ELASSAL"))


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    if not valid_csrf():
        flash("تعذر تنفيذ الطلب. حاول مرة أخرى.", "error")
        return redirect(url_for("auth.profile"))
    session.clear()
    return redirect(url_for("auth.login"))
