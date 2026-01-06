from flask import abort, make_response
from config import db
from models import Profile, Activity, FavouriteActivity, fav_schema, favs_schema
from authz import require_self_or_admin

# List all favourite activities for a given profile.
# Access is restricted so users can only view their own favourites,
# unless they are an Admin.
def read_all(email):
    require_self_or_admin(email)

    # Ensure the target profile exists before accessing relationships
    profile = Profile.query.get(email)
    if profile is None:
        abort(404, f"Profile with Email '{email}' not found")

    return favs_schema.dump(profile.favourites)


# Add a favourite activity for a profile.
def create(email, favourite):
    require_self_or_admin(email)

    profile = Profile.query.get(email)
    if profile is None:
        abort(404, f"Profile with Email '{email}' not found")

    activity_id = favourite.get("Activity_id")
    if activity_id is None:
        abort(400, "Activity_id is required")

    activity = Activity.query.get(activity_id)
    if activity is None:
        abort(404, f"Activity_id '{activity_id}' not found")

    existing = FavouriteActivity.query.filter_by(
        Email=email,
        Activity_id=activity_id
    ).one_or_none()
    if existing is not None:
        abort(409, "Favourite already exists")

    new_fav = FavouriteActivity(Email=email, Activity_id=activity_id)
    db.session.add(new_fav)
    db.session.commit()

    created = FavouriteActivity.query.filter_by(
        Email=email,
        Activity_id=activity_id
    ).one()
    return fav_schema.dump(created), 201


# Remove a favourite activity from a profile.
# Deletion only affects the link table; Activity and Profile remain intact.
def delete(email, activity_id):
    require_self_or_admin(email)

    fav = FavouriteActivity.query.filter_by(
        Email=email,
        Activity_id=activity_id
    ).one_or_none()
    if fav is None:
        abort(404, "Favourite not found")

    db.session.delete(fav)
    db.session.commit()

    return make_response("Favourite deleted", 200)