from flask import request
from flask_login import current_user


ACTIONS = {
    "/admin": (
        "view_admin_dashboard",
        "Viewed the admin dashboard"
    ),
    "/admin/users": (
        "view_admin_users",
        "Viewed admin user management"
    ),
    "/admin/analytics": (
        "view_admin_analytics",
        "Viewed admin analytics"
    ),
    "/admin/audit": (
        "view_admin_audit",
        "Viewed the audit log"
    ),
}


def register_admin_audit_hooks(app):
    @app.before_request
    def _audit_admin_pages():
        path = request.path.rstrip("/") or "/"

        if (
            path in ACTIONS
            and current_user.is_authenticated
            and getattr(current_user, "role", None) == "admin"
        ):
            try:
                from app import db, AuditLog

                action, details = ACTIONS[path]

                db.session.add(
                    AuditLog(
                        admin_id=current_user.id,
                        action=action,
                        details=details
                    )
                )

                db.session.commit()

            except Exception:
                try:
                    from app import db
                    db.session.rollback()
                except Exception:
                    pass
