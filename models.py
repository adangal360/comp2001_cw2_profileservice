from datetime import datetime
import pytz

from config import db, ma
from marshmallow_sqlalchemy import fields


LONDON_TZ = pytz.timezone("Europe/London")


class Profile(db.Model):
    __tablename__ = "Profile"
    __table_args__ = {"schema": "CW2"}

    Email = db.Column(db.String(30), primary_key=True)
    Username = db.Column(db.String(30), nullable=False)

    AboutMe = db.Column(db.Text, nullable=True)          
    Location = db.Column(db.String(50), nullable=True)
    Dob = db.Column(db.Date, nullable=True)
    Language = db.Column(db.String(30), nullable=True)

    Password = db.Column(db.String(30), nullable=False)
    Role = db.Column(db.String(5), nullable=False, default="User")


    favourites = db.relationship(
        "FavouriteActivity",
        back_populates="profile",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )


class Activity(db.Model):
    __tablename__ = "Activity"
    __table_args__ = {"schema": "CW2"}

    Activity_id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True) 
    Activity = db.Column(db.String(30), nullable=False, unique=True)

  
    favourites = db.relationship(
        "FavouriteActivity",
        back_populates="activity",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )


class FavouriteActivity(db.Model):
    __tablename__ = "FavouriteActivity"
    __table_args__ = {"schema": "CW2"}

    Email = db.Column(db.String(30), db.ForeignKey("CW2.Profile.Email", ondelete="CASCADE"), primary_key=True)
    Activity_id = db.Column(
        db.SmallInteger,
        db.ForeignKey("CW2.Activity.Activity_id", ondelete="CASCADE"),
        primary_key=True
    )

    profile = db.relationship("Profile", back_populates="favourites")
    activity = db.relationship("Activity", back_populates="favourites")



class ActivitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Activity
        load_instance = True
        sqla_session = db.session


class FavouriteActivitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FavouriteActivity
        load_instance = True
        sqla_session = db.session
        include_fk = True

    activity = fields.Nested(ActivitySchema)


class ProfileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Profile
        load_instance = True
        sqla_session = db.session
        include_relationships = True

    favourites = fields.Nested(FavouriteActivitySchema, many=True)
    Password = fields.String(load_only=True)


profile_schema = ProfileSchema()
profiles_schema = ProfileSchema(many=True)

activity_schema = ActivitySchema()
activities_schema = ActivitySchema(many=True)

fav_schema = FavouriteActivitySchema()
favs_schema = FavouriteActivitySchema(many=True)
