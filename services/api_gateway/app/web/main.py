from flask import Blueprint, render_template
from flask_login import login_required

main_blueprint = Blueprint("main", __name__)


@main_blueprint.get("/")
@login_required
def index() -> str:
    return render_template("index.html")
