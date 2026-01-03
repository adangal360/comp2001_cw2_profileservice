import connexion

from config import db, build_db_uri

app = connexion.App(__name__, specification_dir="./")
app.add_api("swagger.yml")

flask_app = app.app
flask_app.config["SQLALCHEMY_DATABASE_URI"] = build_db_uri()
flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(flask_app)

@flask_app.route("/")
def home():
    return "COMP2001 CW2 ProfileService running. Visit /api/ui"

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=8000, debug=True)
