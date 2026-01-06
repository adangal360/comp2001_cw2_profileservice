import connexion
from config import db, ma, build_db_uri

# Connexion wraps Flask and binds routes directly from the OpenAPI (swagger.yml) file.
app = connexion.App(__name__, specification_dir="./")
app.add_api("swagger.yml")

flask_app = app.app

# Database configuration is built from environment variables.
flask_app.config["SQLALCHEMY_DATABASE_URI"] = build_db_uri()
flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialise shared extensions against the Flask app
db.init_app(flask_app)
ma.init_app(flask_app)


# Simple root endpoint to confirm the service is running.
# Swagger UI is available at /api/ui.
@flask_app.route("/")
def home():
    return "COMP2001 CW2 ProfileService running. Visit /api/ui"


# In Docker, this file is launched via entrypoint.sh.
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=8000, debug=True)