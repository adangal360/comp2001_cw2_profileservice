from flask import abort
from config import db
from models import Activity, activity_schema, activities_schema
from authz import require_admin

# Read-only endpoint for listing all available activities.
def read_all():
    # Simple ordered query for consistent output
    activities = Activity.query.order_by(Activity.Activity.asc()).all()
    return activities_schema.dump(activities)

# Create a new activity.
# Restricted to Admin users to prevent uncontrolled growth of global activity data.
def create(activity):
    require_admin()

    name = activity.get("Activity")
    name = name.strip()
    if not name:
        abort(400, "Activity is required")

    # Enforce uniqueness at the API layer before hitting the DB constraint,
    # so we can return a clear 409 Conflict instead of a generic DB error.
    existing = Activity.query.filter(Activity.Activity == name).one_or_none()
    if existing is not None:
        abort(409, f"Activity '{name}' already exists")

    activity["Activity"] = name

    # Activities are managed via ORM (not stored procedures)
    new_activity = activity_schema.load(activity, session=db.session)
    db.session.add(new_activity)
    db.session.commit()

    return activity_schema.dump(new_activity), 201