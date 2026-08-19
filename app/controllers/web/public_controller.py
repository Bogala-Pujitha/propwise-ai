"""Browser authentication and public-page controller."""

from datetime import datetime

from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)

from app.extensions import bcrypt, db
from app.models import User
from app.services.activity_service import record_activity


def landing():
    """Public landing page."""
    return render_template("landing.html")


def register():
    """Register a normal user."""

    if request.method == "POST":

        username = (
            request.form.get(
                "username",
                "",
            )
            .strip()
        )

        email = (
            request.form.get(
                "email",
                "",
            )
            .strip()
            .lower()
        )

        password = request.form.get(
            "password",
            "",
        )


        # ---------------------------------------------------------
        # VALIDATION
        # ---------------------------------------------------------

        if not username or not email or not password:

            flash(
                "All fields are required.",
                "error",
            )

            return render_template(
                "register.html"
            )


        if len(password) < 6:

            flash(
                "Password must be at least 6 characters.",
                "error",
            )

            return render_template(
                "register.html"
            )


        # ---------------------------------------------------------
        # DUPLICATE USERNAME
        # ---------------------------------------------------------

        existing_username = (
            User.query
            .filter_by(
                username=username
            )
            .first()
        )

        if existing_username:

            flash(
                "Username already exists.",
                "error",
            )

            return render_template(
                "register.html"
            )


        # ---------------------------------------------------------
        # DUPLICATE EMAIL
        # ---------------------------------------------------------

        existing_email = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )

        if existing_email:

            flash(
                "Email already registered.",
                "error",
            )

            return render_template(
                "register.html"
            )


        # ---------------------------------------------------------
        # CREATE USER
        # ---------------------------------------------------------

        user = User(
            username=username,
            email=email,
            password_hash=(
                bcrypt
                .generate_password_hash(
                    password
                )
                .decode("utf-8")
            ),
            role="user",
        )

        db.session.add(user)
        db.session.commit()


        flash(
            "Account created! Please login.",
            "success",
        )

        return redirect(
            url_for("login")
        )


    # IMPORTANT:
    # GET /register MUST return the page.
    return render_template(
        "register.html"
    )


def login():
    """Authenticate normal users and administrators."""

    if request.method == "POST":

        username_or_email = (
            request.form.get(
                "username",
                "",
            )
            .strip()
        )

        password = request.form.get(
            "password",
            "",
        )

        requested_role = (
            request.form.get(
                "role",
                "user",
            )
            .strip()
            .lower()
        )


        # ---------------------------------------------------------
        # BASIC VALIDATION
        # ---------------------------------------------------------

        if (
            not username_or_email
            or not password
        ):

            flash(
                "Please enter your username and password.",
                "error",
            )

            return render_template(
                "login.html"
            )


        # ---------------------------------------------------------
        # FIND USER
        #
        # Supports both username and email.
        # ---------------------------------------------------------

        user = (
            User.query
            .filter(
                db.or_(
                    User.username ==
                    username_or_email,

                    User.email ==
                    username_or_email.lower(),
                )
            )
            .first()
        )


        # ---------------------------------------------------------
        # USER NOT FOUND
        # ---------------------------------------------------------

        if user is None:

            flash(
                "Invalid credentials.",
                "error",
            )

            return render_template(
                "login.html"
            )


        # ---------------------------------------------------------
        # PASSWORD CHECK
        # ---------------------------------------------------------

        try:

            password_valid = (
                bcrypt.check_password_hash(
                    user.password_hash,
                    password,
                )
            )

        except Exception:

            password_valid = False


        if not password_valid:

            flash(
                "Invalid credentials.",
                "error",
            )

            return render_template(
                "login.html"
            )


        # ---------------------------------------------------------
        # STORED ROLE
        # ---------------------------------------------------------

        actual_role = (
            getattr(
                user,
                "role",
                "user",
            )
            or "user"
        ).strip().lower()


        # ---------------------------------------------------------
        # ADMIN LOGIN CHECK
        # ---------------------------------------------------------

        if requested_role == "admin":

            if actual_role != "admin":

                flash(
                    "This account does not have administrator access.",
                    "error",
                )

                return render_template(
                    "login.html"
                )


        # ---------------------------------------------------------
        # LOGIN
        # ---------------------------------------------------------

        login_user(
            user,
            remember=(
                request.form.get(
                    "remember"
                ) == "on"
            ),
        )

        session.permanent = True

        session[
            "login_time"
        ] = datetime.utcnow().isoformat()


        record_activity(
            user_id=user.id,
            activity_type="login",
            details="User logged in",
            commit=False,
        )

        db.session.commit()


        # ---------------------------------------------------------
        # REDIRECT BY STORED ROLE
        # ---------------------------------------------------------

        if actual_role == "admin":

            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )


        return redirect(
            url_for(
                "dashboard"
            )
        )


    # =========================================================
    # THIS WAS THE MISSING RETURN IN YOUR LOCAL FILE
    # GET /login MUST RETURN login.html
    # =========================================================

    return render_template(
        "login.html"
    )


@login_required
def logout():
    """Logout current user."""

    record_activity(
        user_id=current_user.id,
        activity_type="logout",
        details="User logged out",
        commit=False,
    )

    db.session.commit()

    logout_user()

    return redirect(
        url_for("landing")
    )


def forgot_password():
    """Password reset page."""

    if request.method == "POST":

        email = (
            request.form.get(
                "email",
                "",
            )
            .strip()
            .lower()
        )

        user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )

        if user:

            flash(
                "Password reset link sent to your email "
                "(demo - not implemented).",
                "success",
            )

        else:

            flash(
                "Email not found.",
                "error",
            )


    return render_template(
        "forgot_password.html"
    )