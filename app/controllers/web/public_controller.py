"""Browser authentication and public-page controller."""

from datetime import datetime

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import bcrypt, db
from app.models import User
from app.services.activity_service import record_activity


def landing():
    return render_template("landing.html")


def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return render_template("register.html")

        user = User(
            username=username,
            email=email,
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
            role="user",
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            session.permanent = True
            session["login_time"] = datetime.utcnow().isoformat()
            record_activity(user_id=user.id, activity_type="login", details="User logged in", commit=False)
            db.session.commit()

            if role == "admin" and user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("dashboard"))

        flash("Invalid credentials", "error")
    return render_template("login.html")


@login_required
def logout():
    record_activity(
        user_id=current_user.id,
        activity_type="logout",
        details="User logged out",
        commit=False,
    )
    db.session.commit()
    logout_user()
    return redirect(url_for("landing"))


def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = User.query.filter_by(email=email).first()
        if user:
            flash(
                "Password reset link sent to your email (demo - not implemented)",
                "success",
            )
        else:
            flash("Email not found", "error")
    return render_template("forgot_password.html")
