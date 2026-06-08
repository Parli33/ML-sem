import logging

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user

from app.services.authentication import authenticate_user, register_user
from app.web.forms import LoginForm, RegistrationForm

logger = logging.getLogger(__name__)
auth_blueprint = Blueprint("auth", __name__)


@auth_blueprint.route("/register", methods=["GET", "POST"])
def register() -> str:
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = register_user(form.username.data, form.password.data)
        if user is None:
            flash("Пользователь с таким логином уже существует.", "danger")
        else:
            logger.info("Registered user id=%s username=%s", user.id, user.username)
            flash("Регистрация завершена. Теперь войдите.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login() -> str:
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = authenticate_user(form.username.data, form.password.data)
        if user is None:
            logger.info("Rejected login for username=%s", form.username.data)
            flash("Неверный логин или пароль.", "danger")
        else:
            login_user(user)
            logger.info("User logged in id=%s", user.id)
            return redirect(url_for("main.index"))

    return render_template("auth/login.html", form=form)


@auth_blueprint.post("/logout")
def logout() -> str:
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.login"))
