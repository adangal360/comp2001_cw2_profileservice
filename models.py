from datetime import datetime
import pytz

from config import db, ma
from marshmallow import fields

LONDON_TZ = pytz.timezone("Europe/London")


# -----------------------------
# ORM Models
# -----------------------------

class Profile(db.Model):
    """
    Profile represents a Trail App user within the CW2 schema.

    This model is used primarily for:
    - authorisation decisions (roles)
    - ORM relationships (favourites)
    Actual CRUD operations for Profile are handled via stored procedures.
    """
    __tablename__ = "Profile"
    __table_args__ = {"schema": "CW2"}

    Email = db.Column(db.String(30), primary_key=True)
    Username = db.Column(db.String(30), nullable=False)

    AboutMe = db.Column(db.Text, nullable=True)
    Location = db.Column(db.String(50), nullable=True)
    Dob = db.Column(db.Date, nullable=True)
    Language = db.Column(db.String(30), nullable=True)

    # Stores a secure password hash only (never plaintext).
    Password = db.Column(db.String(255), nullable=False)

    # Role is used for authorisation checks at the API layer.
    Role = db.Column(db.String(5), nullable=False, default="User")

    # Relationship to FavouriteActivity link table.
    # Cascade rules mirror the ON DELETE CASCADE constraints in the database.
    favourites = db.relationship(
        "FavouriteActivity",
        back_populates="profile",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )


class Activity(db.Model):
    """
    Activity represents a selectable preference (e.g. Running, Swimming).

    Activities are not the main assessed resource in CW2, so they are
    managed directly via the ORM rather than stored procedures.
    """
    __tablename__ = "Activity"
    __table_args__ = {"schema": "CW2"}

    Activity_id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    Activity = db.Column(db.String(30), nullable=False, unique=True)

    # Back-reference to favourites linking profiles to this activity.
    favourites = db.relationship(
        "FavouriteActivity",
        back_populates="activity",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )


class FavouriteActivity(db.Model):
    """
    Link table connecting Profiles to their favourite Activities.

    Uses a composite primary key to ensure:
    - a profile cannot favourite the same activity twice
    """
    __tablename__ = "FavouriteActivity"
    __table_args__ = {"schema": "CW2"}

    Email = db.Column(
        db.String(30),
        db.ForeignKey("CW2.Profile.Email", ondelete="CASCADE"),
        primary_key=True
    )
    Activity_id = db.Column(
        db.SmallInteger,
        db.ForeignKey("CW2.Activity.Activity_id", ondelete="CASCADE"),
        primary_key=True
    )

    # ORM relationships for navigation in code
    profile = db.relationship("Profile", back_populates="favourites")
    activity = db.relationship("Activity", back_populates="favourites")


# -----------------------------
# Marshmallow Schemas
# -----------------------------

class ActivitySchema(ma.SQLAlchemyAutoSchema):
    """
    Schema for serialising Activity objects.
    """
    class Meta:
        model = Activity
        load_instance = True
        sqla_session = db.session


class FavouriteActivitySchema(ma.SQLAlchemyAutoSchema):
    """
    Schema for serialising FavouriteActivity link rows.
    Includes nested Activity data for convenience in API responses.
    """
    class Meta:
        model = FavouriteActivity
        load_instance = True
        sqla_session = db.session
        include_fk = True

    activity = fields.Nested(ActivitySchema)


class ProfileSchema(ma.SQLAlchemyAutoSchema):
    """
    Schema for Profile data.

    Password is marked as load_only to ensure it:
    - can be accepted on create/update
    - is never exposed in API responses
    """
    class Meta:
        model = Profile
        load_instance = True
        sqla_session = db.session
        include_relationships = True

    favourites = fields.Nested(FavouriteActivitySchema, many=True)
    Password = fields.String(load_only=True)


# -----------------------------
# Schema instances
# -----------------------------

profile_schema = ProfileSchema()
profiles_schema = ProfileSchema(many=True)

activity_schema = ActivitySchema()
activities_schema = ActivitySchema(many=True)

fav_schema = FavouriteActivitySchema()
favs_schema = FavouriteActivitySchema(many=True)