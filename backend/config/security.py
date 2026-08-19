"""
Security helpers for PropWise AI.

These helpers complement the existing Flask-Login authentication layer.
They are intentionally independent of the existing route handlers so they
can be imported by controllers or blueprints without replacing established
application logic.
"""
from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*roles):
    """Require an authenticated user whose role is one of `roles`."""
    allowed = {str(role).strip().lower() for role in roles}

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(*args, **kwargs):
            role = str(getattr(current_user, "role", "")).strip().lower()
            if role not in allowed:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def admin_required_api(view_func):
    """Admin-only API decorator that returns HTTP 403 instead of redirecting."""
    return role_required("admin")(view_func)


def owner_required(model_attr="user_id", url_kwarg="prediction_id"):
    """
    Protect a resource whose owner is stored in `model_attr`.

    The wrapped view must accept the resource identifier as `url_kwarg`.
    A loader callable can be supplied through `view_func.resource_loader`
    after decoration, or the view can perform its own lookup and pass the
    object through `kwargs["_resource"]`.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(*args, **kwargs):
            resource = kwargs.pop("_resource", None)

            if resource is None:
                loader = getattr(view_func, "resource_loader", None)
                if loader is None:
                    # The route can still enforce ownership itself by passing
                    # the resource as `_resource`.
                    abort(500, description="Owner resource loader not configured")
                resource_id = kwargs.get(url_kwarg)
                resource = loader(resource_id)

            if resource is None:
                abort(404)

            owner_id = getattr(resource, model_attr, None)
            if owner_id != getattr(current_user, "id", None):
                abort(403)

            kwargs["_resource"] = resource
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def enforce_owner(resource, owner_attr="user_id"):
    """Raise 403 unless the supplied resource belongs to current_user."""
    if not current_user.is_authenticated:
        abort(401)

    if getattr(resource, owner_attr, None) != getattr(current_user, "id", None):
        abort(403)

    return resource
