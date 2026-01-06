from flask import abort
from config import db
from models import Activity, activity_schema, activities_schema
from authz import require_admin


def read_all():
    activities = Activity.query.order_by(Activity.Activity.asc()).all()
    return activities_schema.dump(activities)

def create(activity):
    require_admin()
    name = activity.get("Activity")
    if not name:
        abort(400, "Activity is required")

    existing = Activity.query.filter(Activity.Activity == name).one_or_none()
    if existing is not None:
        abort(409, f"Activity '{name}' already exists")

    new_activity = activity_schema.load(activity, session=db.session)
    db.session.add(new_activity)
    db.session.commit()
    return activity_schema.dump(new_activity), 201
