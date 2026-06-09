from flask_wtf import FlaskForm
from typing import Any

from wtforms import (
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    EqualTo,
    InputRequired,
    Length,
    NumberRange,
    Optional,
)


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


DISEASE_CHOICES = [
    ("", "Не указано"),
    ("0", "Нет"),
    ("1", "Да"),
]


class PredictionForm(FlaskForm):
    gender = SelectField("Пол", choices=[("1", "Мужской"), ("2", "Женский")])
    age = IntegerField(
        "Возраст",
        validators=[InputRequired(), NumberRange(min=0, max=120)],
    )
    height = FloatField(
        "Рост, см",
        validators=[InputRequired(), NumberRange(min=1, max=250)],
    )
    weight = FloatField(
        "Вес, кг",
        validators=[InputRequired(), NumberRange(min=1, max=200)],
    )
    hip_measurement = FloatField(
        "Объём бёдер, см",
        validators=[InputRequired(), NumberRange(min=1)],
    )
    alcohol = SelectField(
        "Употребление алкоголя",
        choices=[
            ("0", "Нет"),
            ("1", "Употреблял ранее"),
            ("2", "Да, в настоящее время"),
        ],
    )
    profession = SelectField(
        "Профессия",
        choices=[
            ("1", "Ведение домашнего хозяйства"),
            ("2", "Вооружённые силы"),
            ("3", "Свободные профессии"),
            ("4", "Рабочие и ручной труд"),
            ("5", "Операторы и монтажники"),
            ("6", "Служащие и сфера обслуживания"),
            ("7", "Никогда не работал"),
            ("8", "Дипломированные специалисты"),
            ("9", "Другое"),
            ("10", "Сельское хозяйство и рыболовство"),
            ("11", "Пенсионеры"),
            ("12", "Ремесленники и промышленность"),
            ("13", "Техники и младшие специалисты"),
            ("14", "Руководители"),
        ],
    )
    region = SelectField(
        "Район",
        choices=[
            ("1", "Рудничный"),
            ("2", "Центральный"),
            ("3", "Заводской"),
            ("4", "Кировский"),
            ("5", "Ленинский"),
            ("6", "Сельская местность"),
        ],
    )

    glucose = FloatField("Глюкоза", validators=[Optional(), NumberRange(min=0)])
    cholesterol = FloatField("Холестерин", validators=[Optional(), NumberRange(min=0)])
    non_hdl_cholesterol = FloatField(
        "Холестерин не-ЛПВП",
        validators=[Optional(), NumberRange(min=0)],
    )
    vldl_cholesterol = FloatField(
        "Холестерин ЛПОНП",
        validators=[Optional(), NumberRange(min=0)],
    )
    hdl_cholesterol = FloatField(
        "Холестерин ЛПВП",
        validators=[Optional(), NumberRange(min=0)],
    )
    ldl_cholesterol = FloatField(
        "Холестерин ЛПНП",
        validators=[Optional(), NumberRange(min=0)],
    )
    apolipoprotein_a = FloatField(
        "Аполипопротеин A",
        validators=[Optional(), NumberRange(min=0)],
    )
    apolipoprotein_b = FloatField(
        "Аполипопротеин B",
        validators=[Optional(), NumberRange(min=0)],
    )
    triglycerides = FloatField(
        "Триглицериды",
        validators=[Optional(), NumberRange(min=0)],
    )

    stroke = SelectField("Инсульт", choices=DISEASE_CHOICES, validate_choice=False)
    stroke_year = IntegerField(
        "Год диагностирования инсульта",
        validators=[Optional(), NumberRange(min=1950, max=2026)],
    )
    heart_failure = SelectField(
        "Сердечная недостаточность",
        choices=DISEASE_CHOICES,
        validate_choice=False,
    )
    heart_failure_year = IntegerField(
        "Год диагностирования сердечной недостаточности",
        validators=[Optional(), NumberRange(min=1950, max=2026)],
    )
    cad_chd_ihd = SelectField(
        "Нарушение ритма или ИБС",
        choices=DISEASE_CHOICES,
        validate_choice=False,
    )
    cad_chd_ihd_year = IntegerField(
        "Год диагностирования нарушения ритма или ИБС",
        validators=[Optional(), NumberRange(min=1950, max=2026)],
    )
    angine = SelectField("Стенокардия", choices=DISEASE_CHOICES, validate_choice=False)
    angine_year = IntegerField(
        "Год диагностирования стенокардии",
        validators=[Optional(), NumberRange(min=1950, max=2026)],
    )
    myocardial_infarction = SelectField(
        "Инфаркт миокарда",
        choices=DISEASE_CHOICES,
        validate_choice=False,
    )
    myocardial_infarction_year = IntegerField(
        "Год диагностирования инфаркта миокарда",
        validators=[Optional(), NumberRange(min=1950, max=2026)],
    )
    arterial_hypertension = SelectField(
        "Артериальная гипертензия",
        choices=DISEASE_CHOICES,
        validate_choice=False,
    )
    arterial_hypertension_year = IntegerField(
        "Год диагностирования артериальной гипертензии",
        validators=[Optional(), NumberRange(min=1950, max=2026)],
    )
    submit = SubmitField("Получить предсказание")

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for name, field in self._fields.items():
            if name in {"csrf_token", "submit"} or field.data in (None, ""):
                continue
            payload[name] = field.data

        for name in (
            "gender",
            "alcohol",
            "profession",
            "region",
            "stroke",
            "heart_failure",
            "cad_chd_ihd",
            "angine",
            "myocardial_infarction",
            "arterial_hypertension",
        ):
            if name in payload:
                payload[name] = int(payload[name])
        return payload
