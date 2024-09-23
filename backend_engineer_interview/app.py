    # app.py

import logging
import os
import time
from typing import List
import connexion  # type: ignore
import connexion.mock  # type: ignore
import flask
from flask import g, Flask, jsonify
from pydantic import ValidationError
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from backend_engineer_interview.handlers import get_employee, patch_employee, post_application



logger = logging.getLogger(__name__)



def init_db(db_name):
    engine = create_engine(f"sqlite:///{db_name}.db")
    session_factory = scoped_session(
    sessionmaker(bind=engine, autoflush=True, autocommit=False)
    )

    engine.dispose()
    return session_factory


def openapi_filenames() -> List[str]:
    return ["openapi.yaml"]


def get_project_root_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "../")


def create_app(db_name: str = "app"):
    logger.info("Starting API")

    db_session_factory = init_db(db_name)

# took out options=options
    app = connexion.FlaskApp(
        __name__, specification_dir=get_project_root_dir()
    )
    app.add_api(
        openapi_filenames()[0],
        # resolver=resolver,
        strict_validation=True,
        validate_responses=True,
    )

    flask_app = app.app
 
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

    @flask_app.before_request
    def push_db():
        g.db = db_session_factory
        g.start_time = time.monotonic()
        g.connexion_flask_app = app

    @flask_app.teardown_request
    def close_db(exception=None):
        try:
            logger.debug("Closing DB session")
            db = g.pop("db", None)

            if db is not None:
                db.remove()
        except Exception:
            logger.exception("Exception while closing DB session")
            pass

    @flask_app.after_request
    def access_log_end(response):
        response_time_ms = 1000 * (time.monotonic() - g.get("start_time"))
        logger.info(
            "%s %s %s",
            response.status_code,
            flask.request.method,
            flask.request.full_path,
            extra={
                "remote_addr": flask.request.remote_addr,
                "response_length": response.content_length,
                "response_type": response.content_type,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
            },
        )
        return response

    return app
if __name__ == "__main__":
    # Run the application
    # app = create_app()
    # app.run(debug=True, host="0.0.0.0", port=5000)
    app = create_app()
    app.run(port=5000)

app = create_app()


# Define your routes here
app.add_url_rule('/employee/<int:id>', view_func=get_employee, methods=['GET'])
app.add_url_rule('/employee/<int:id>', view_func=patch_employee, methods=['PATCH'])
app.add_url_rule('/application', view_func=post_application, methods=['POST'])