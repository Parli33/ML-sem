from enum import IntEnum

from pydantic import BaseModel, Field


class Gender(IntEnum):
    MALE = 1
    FEMALE = 2


class Alcohol(IntEnum):
    NO = 0
    HAD_CONSUMED_BEFORE = 1
    YES = 2


class Profession(IntEnum):
    """
    1 = ведение домашнего хозяйства\n
    2 = вооруженные силы\n
    3 = лица свободных профессий\n
    4 = низкоквалифицированные и неквалифицированные работники, рабочие, ручной труд\n
    5 = операторы и монтажники установок и машинного оборудования\n
    6 = служащие, сфера обслуживания, работники среднего звена\n
    7 = никогда не работающие домохозяйки\n
    8 = дипломированные специалисты, умственный труд\n
    9 = другое, \n
    10 = квалифицированные специалисты сельского хозяйства и рыболовного\n
    11 = пенсионеры\n
    12 = ремесленники и представители других отраслей промышленности\n
    13 = техники и младшие специалисты\n
    14 = представители законодад. органов власти,  высокопосталенные долж. лица, менеджеры и руководители \n
    """

    HOUSEWIFE_MGMNT = 1
    ARMED_FORCES = 2
    FREE_PROFESSIONS = 3
    UNSKILLED_LABOR = 4
    OPERATORS_INSTALLERS = 5
    SERVICE_CLERKS = 6
    NEVER_WORKED = 7
    PROFESSIONALS_MENTAL = 8
    OTHER = 9
    AGRICULTURE_FISH = 10
    PENSIONERS = 11
    CRAFTSMEN_INDUSTRY = 12
    TECHNICIANS_JUNIOR = 13
    MANAGERS_OFFICIALS = 14


class Region(IntEnum):
    RUDNICHNY = 1
    CENTRAL = 2
    ZAVODSKOY = 3
    KIROVSKY = 4
    LENINSKY = 5
    RURAL = 6


class DiseaseStatus(IntEnum):
    PRESENT = 1
    ABSENT = 0


class PredictRequest(BaseModel):
    gender: Gender = Field(..., description="Пол")
    age: int = Field(..., ge=0, le=120, description="Возраст")
    height: float = Field(..., gt=0, le=250, description="Рост")
    weight: float = Field(..., gt=0, le=200, description="Вес")
    hip_measurement: float = Field(..., description="Объем бедер")
    alcohol: Alcohol = Field(
        ...,
        description="Употребление алкоголя: 1 - нет, 2 - употреблял ранее, 3 - да, в настоящее время",
    )
    profession: Profession = Field(
        ...,
        description=(
            "Профессия пациента. Основные группы:\n"
            "1-Домохозяйство; 2-ВС; 3-Свободные проф.; 4-Рабочие;\n"
            "5-Операторы; 6-Служащие; 7-Домохозяйки (не раб.);\n"
            "8-Умств. труд; 9-Другое; 10-Сельхоз; 11-Пенсионеры;\n"
            "12-Ремесленники; 13-Техники; 14-Руководители"
        ),
    )
    region: Region = Field(
        ...,
        description=(
            "Район города или село."
            "1 - рудничный; 2 - центральный; 3 - заводский;\n"
            "4 - кировский; 5 - ленинский; 6 - сельская местность"
        ),
    )
    glucose: float | None = Field(None, description="Уровень глюкозы")
    cholesterol: float | None = Field(None, description="Уровень холестерина")
    non_hdl_cholesterol: float | None = Field(
        None, description="Уровень холестерина не-ЛПВП"
    )
    vldl_cholesterol: float | None = Field(
        None, description="Уровень холестерина ЛПОНП"
    )
    hdl_cholesterol: float | None = Field(None, description="Уровень холестерина ЛПВП")
    ldl_cholesterol: float | None = Field(None, description="Уровень холестерина ЛПНП")
    apolipoprotein_a: float | None = Field(
        None, description="Уровень аполипопротеина А"
    )
    apolipoprotein_b: float | None = Field(
        None, description="Уровень аполипопротеина В"
    )
    triglycerides: float | None = Field(None, description="Уровень триглицеридов")
    stroke: DiseaseStatus | None = Field(
        None, description="Диагностировался ли раньше инсульт: 1 - да, 0 - нет"
    )
    stroke_year: int | None = Field(
        None,
        ge=1950,
        le=2026,
        description="Год диагностирования инсульта",
    )
    heart_failure: DiseaseStatus | None = Field(
        None,
        description="Диагностировалась ли сердечная недостаточность: 1 - да, 0 - нет",
    )
    heart_failure_year: int | None = Field(
        None,
        ge=1950,
        le=2026,
        description="Год диагностирования сердечной недостаточности",
    )
    cad_chd_ihd: DiseaseStatus | None = Field(
        None,
        description="Диагностировалось ли нарушение ритма или другие ишемические болезни сердца (ИБС): 1 - да, 0 - нет",
    )
    cad_chd_ihd_year: int | None = Field(
        None,
        ge=1950,
        le=2026,
        description="Год диагностирования нарушения ритма или других ИБС",
    )
    angine: DiseaseStatus | None = Field(
        None, description="Диагностировалось ли стенокардия: 1 - да, 0 - нет"
    )
    angine_year: int | None = Field(
        None,
        ge=1950,
        le=2026,
        description="Год диагностирования стенокардии",
    )
    myocardial_infarction: DiseaseStatus | None = Field(
        None, description="Диагностировался ли инфаркт миокарда 1 - да, 0 - нет"
    )
    myocardial_infarction_year: int | None = Field(
        None,
        ge=1950,
        le=2026,
        description="Год диагностирования инфаркта миокарда",
    )
    arterial_hypertension: DiseaseStatus | None = Field(
        None,
        description="Диагностировалась ли артериальная гипертензия (АГ) 1 - да, 0 - нет",
    )
    arterial_hypertension_year: int | None = Field(
        None,
        ge=1950,
        le=2026,
        description="Год диагностирования артериальной гипертензии",
    )


class PredictResponse(BaseModel):
    predictions: list[str] = Field(
        description='Список строк формата "модель:вероятность заболевания"'
    )
    model_version: str = Field(description="Версия модели")


class RegionStats(BaseModel):
    total_cancer_risk: float
    iza_concentration_f: float
    non_cancer_risk_ammonia: float
    non_cancer_risk_particulate_matter: float
    avg_annual_conc_am_form: float
    non_cancer_risk_carbon_monoxide: float
    non_cancer_risk_sulfur_dioxide: float
    pdk_excess_nitrogen_oxide_pct: float
    non_cancer_risk_formaldehyde: float
    non_cancer_risk_hydrochloride: float
    non_cancer_risk_aniline: float
    non_cancer_risk_carbon_soot: float
    non_cancer_risk_benzopyrene: float
    cardiac_concentration_f: float
    non_cancer_risk_phenol: float
    non_cancer_risk_nitrogen_dioxide: float
