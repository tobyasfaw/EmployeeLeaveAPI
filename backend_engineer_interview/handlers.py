
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, timedelta, datetime
from typing import Generator, Optional
from flask import g, jsonify, make_response, request, Response
import flask
import pydantic  
from pydantic import ValidationError
from sqlalchemy.orm import Session
import connexion  # type: ignore
from backend_engineer_interview.models import Employee, Application
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
from sqlalchemy.exc import SQLAlchemyError
from backend_engineer_interview.models import Employee
# from backend_engineer_interview.app import create_app


# app = create_app()

# if __name__ == "__main__":
#     # Run the application
#     app.run(debug=True)
# handler_bp = Blueprint('handler_bp', __name__)

class PydanticBaseModel(pydantic.BaseModel):
    class Config:
        orm_mode = True
        from_attributes = True
class EmployeeResponse(PydanticBaseModel):
    id: int
    first_name: str
    last_name: str
    date_of_birth: date

class PatchEmployeeRequest(PydanticBaseModel):
    first_name: Optional[str]
    last_name: Optional[str]

class ApplicationRequest(PydanticBaseModel):
    leave_start_date: date
    leave_end_date: date
    employee_id: int

class ApplicationResponse(PydanticBaseModel):
    id: int
    leave_start_date: date
    leave_end_date: date
    employee_id: int

@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Get a plain SQLAlchemy Session."""
    session = g.get("db")
    if session is None:
        raise Exception("No database session available in application context")

    session.expire_on_commit = False  
    session.begin()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_request():
    return connexion.request


@dataclass
class StartEndDates:
    start_date: date
    end_date: date


"""
In Person Exercise
"""


def split_start_end_dates(start_date: date, end_date: date, split_date: date):
    # ANSWER
    # pass
    if start_date > end_date:
        return None, None
    if split_date < start_date:
        return None, StartEndDates(start_date, end_date)
    elif split_date > end_date:
        return StartEndDates(start_date, end_date), None
    elif split_date == start_date:
        return StartEndDates(start_date=start_date, end_date=start_date), StartEndDates(start_date=start_date + timedelta(days=1), end_date=end_date)
    elif split_date == end_date:
        return StartEndDates(start_date=start_date, end_date=end_date), None
    else:
        return (StartEndDates(start_date=start_date, end_date=split_date),
            StartEndDates(start_date=split_date + timedelta(days=1), end_date=end_date))


"""
Async Exercise
"""


def status():
    with db_session() as session:
        session.execute("SELECT 1;").one()
        return flask.make_response(flask.jsonify({"status": "up"}), 200)


class EmployeeResponse(PydanticBaseModel):
    id: int
    first_name: str
    last_name: str
    date_of_birth: date


# Answer
class PatchEmployeeRequest(PydanticBaseModel):
    first_name: Optional[str]
    last_name: Optional[str]


# @app.route('/employee/<int:id>', methods=['GET'])
def get_employee(id):


    try:
        logging.info(f"Fetching employee with ID: {id}")
        with db_session() as session:
            employee = session.query(Employee).filter(Employee.id == id).first()
            # logging.debug(f"Query result: {employee}")

            if employee is None:
                logging.info(f"No employee found with ID: {id}")
                return make_response(jsonify({"message": "No such employee"}), 404)
            logging.info(f"Employee found: {employee.first_name} {employee.last_name}")
            employee_data = EmployeeResponse.from_orm(employee)
            return jsonify(employee_data.dict())
    except Exception as e:
        # print(f"Error in get_employee: {e}")
        logging.error(f"Error in get_employee: {e}")
        return make_response(jsonify({"message": "Internal Server Error"}), 500)



# @app.route('/employee/<int:id>', methods=['PATCH'])
def patch_employee(id):
    try:
        logging.info(f"Received patch request for employee id: {id}")
        with db_session() as session:
            employee = session.query(Employee).filter_by(id=id).first()
            if not employee:
                logging.warning(f"Employee with id {id} not found.")
                return make_response(jsonify({"message": "No such employee"}), 404)
            
            request_data = request.get_json()
            logging.debug(f"Patch request data: {request_data}")
            patch_request = PatchEmployeeRequest(**request_data)
            
            # Ensure names are not empty
            if patch_request.first_name is not None and patch_request.first_name.strip() == "":
                logging.warning(f"Invalid first_name in request data.")
                return make_response(jsonify({"message": "first_name cannot be blank"}), 400)
            if patch_request.last_name is not None and patch_request.last_name.strip() == "":
                logging.warning(f"Invalid last_name in request data.")
                return make_response(jsonify({"message": "last_name cannot be blank"}), 400)

            # Update the employee
            if patch_request.first_name:
                employee.first_name = patch_request.first_name
            if patch_request.last_name:
                employee.last_name = patch_request.last_name

            session.commit()
            logging.info(f"Employee id {id} successfully patched.")
            # return make_response("", 204)
            return Response(status=204, content_type="application/json")
    except pydantic.ValidationError as ve:
        logging.error(f"Validation error: {ve}")
        return make_response(jsonify({"message": "Invalid request data"}), 400)
    except KeyError as ke:
        logging.error(f"Key error: {ke}")
        return make_response(jsonify({"message": f"Missing key in request: {str(ke)}"}), 400)
    except SQLAlchemyError as e:
        # session.rollback()
        logging.error(f"SQLAlchemy error in patch_employee: {e}")
        return make_response(jsonify({"message": "Database Error"}), 500)
    except Exception as e:
        logging.error(f"Unexpected error in patch_employee: {e}")
        return make_response(jsonify({"message": "Internal Server Error"}), 500)

# @app.route('/application', methods=['POST'])
def post_application():
    """
    Accepts a leave_start_date, leave_end_date, employee_id and creates an Application
    with those properties.  It should then return the new application with a status code of 200.

    If any of the properties are missing in the request body, it should return the new application
    with a status code of 400.

    Verify the handler using the test cases in TestPostApplication.  Add any more tests you think
    are necessary.
    """
    try:
        data = request.get_json()

        logging.debug(f"Received POST data: {data}")

        

        missing_fields = []
        if 'leave_start_date' not in data:
            missing_fields.append('leave_start_date')
        if 'leave_end_date' not in data:
            missing_fields.append('leave_end_date')
        if 'employee_id' not in data:
            missing_fields.append('employee_id')
        

        if missing_fields:
            message = ";".join(f"{field} is missing" for field in missing_fields)
            logging.warning(f"Missing fields in request: {message}")
            # response = jsonify({"message": message})
            # response.status_code = 400
            return make_response(jsonify({"message": message}), 400)

        leave_start_date = datetime.strptime(data["leave_start_date"], "%Y-%m-%d").date()
        leave_end_date = datetime.strptime(data["leave_end_date"], "%Y-%m-%d").date()

        try:

            employee_id = data.get("employee_id")
            logging.debug(f"Looking for employee with ID: {employee_id}")
   
            with db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    logging.warning(f"Employee with ID {employee_id} not found.")
                    return make_response(jsonify({"message": "Employee not found"}), 404)

                new_application = Application(
                    leave_start_date=leave_start_date,
                    leave_end_date=leave_end_date,
                    employee_id=employee_id,
                )
                session.add(new_application)
                session.commit()

                if new_application.id is None:
                    logging.error("Failed to generate application ID.")
                    return make_response(jsonify({"message": "Failed to create application"}), 500)

                application_response = {
                    "id": new_application.id,
                    "leave_start_date": new_application.leave_start_date,
                    "leave_end_date": new_application.leave_end_date,
                    "employee": {
                        "first_name": employee.first_name,
                        "last_name": employee.last_name,
                    },
                }
                return jsonify(application_response), 200

        except Exception as e:
            logging.error(f"Unexpected error in post_application: {e}")
            return make_response(jsonify({"message": "Internal Server Error"}), 500)
    except Exception as e:
        logging.error(f"Unexpected error in post_application: {e}", exc_info=True)
        return make_response(jsonify({"message": "Internal Server Error"}), 500)


