from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length


class LoginForm(FlaskForm):
    username = StringField(
        "Логин",
        validators=[DataRequired(), Length(min=3, max=80)],
    )
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Логин",
        validators=[DataRequired(), Length(min=3, max=80)],
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    password_confirmation = PasswordField(
        "Повторите пароль",
        validators=[
            DataRequired(),
            EqualTo("password", message="Пароли должны совпадать."),
        ],
    )
    submit = SubmitField("Зарегистрироваться")
