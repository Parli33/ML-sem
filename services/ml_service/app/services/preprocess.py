from typing import Any

from app.schemas.predict import Alcohol, Gender, PredictRequest, Profession, Region
from app.services.transformer import transform_request_to_vector


_GENDER_NAME: dict[Gender, str] = {Gender.MALE: "муж", Gender.FEMALE: "жен"}
_ALCOHOL_NAME: dict[Alcohol, str] = {
    Alcohol.NO: "нет",
    Alcohol.HAD_CONSUMED_BEFORE: "употреблял ранее",
    Alcohol.YES: "да в настоящее время",
}
_REGION_NAME: dict[Region, str] = {
    Region.RUDNICHNY: "рудничный",
    Region.CENTRAL: "центральный",
    Region.ZAVODSKOY: "заводский",
    Region.KIROVSKY: "кировский",
    Region.LENINSKY: "ленинский",
    Region.RURAL: "сельская местность",
}
_PROFESSION_NAME: dict[Profession, str] = {
    Profession.HOUSEWIFE_MGMNT: "ведение домашнего хозяйства",
    Profession.ARMED_FORCES: "вооруженные силы",
    Profession.FREE_PROFESSIONS: "лица свободных профессий",
    Profession.UNSKILLED_LABOR: "низкоквалифицированные  и неквалифицированные работники, рабочие, ручной труд",
    Profession.OPERATORS_INSTALLERS: "операторы и монтажники установок и машинного оборудования",
    Profession.SERVICE_CLERKS: "служащие, сфера обслуживания, работники среднего звена",
    Profession.NEVER_WORKED: "никогда не работающие домохозяйки",
    Profession.PROFESSIONALS_MENTAL: "дипломированные специалисты, умственный труд",
    Profession.OTHER: "другое",
    Profession.AGRICULTURE_FISH: "квалифицированные специалисты сельского хозяйства и рыболовного",
    Profession.PENSIONERS: "пенсионеры",
    Profession.CRAFTSMEN_INDUSTRY: "ремесленники и представители других отраслей промышленности",
    Profession.TECHNICIANS_JUNIOR: "техники и младшие специалисты",
    Profession.MANAGERS_OFFICIALS: "представители законодад. органов власти,  высокопосталенные долж. лица, менеджеры и руководители",
}


def request_to_vector(
    request: PredictRequest,
    *,
    feature_order: list[str],
    region_stats: dict[str, float],
) -> list[Any]:
    data = request.model_dump()

    data["gender_name"] = _GENDER_NAME[request.gender]
    data["alcohol_name"] = _ALCOHOL_NAME[request.alcohol]
    data["job_name"] = _PROFESSION_NAME[request.profession]
    data["region_name"] = _REGION_NAME[request.region]

    # Disease history features (the current shipped models use only flags; years are absent).
    nan = float("nan")

    stroke = int(request.stroke or 0)
    heart_failure = int(request.heart_failure or 0)
    arrhythmia_or_ihd = int(request.cad_chd_ihd or 0)
    angina = int(request.angine or 0)
    myocardial_infarction = int(request.myocardial_infarction or 0)
    arterial_hypertension = int(request.arterial_hypertension or 0)

    data["инсульт"] = stroke
    data["сн"] = heart_failure
    data["нарушение ритма или ибс"] = arrhythmia_or_ihd
    data["стенокардия"] = angina
    data["им"] = myocardial_infarction
    data["аг"] = arterial_hypertension

    data["инсульт_год"] = (
        float(request.stroke_year) if stroke and request.stroke_year else nan
    )
    data["сн_год"] = (
        float(request.heart_failure_year)
        if heart_failure and request.heart_failure_year
        else nan
    )
    data["нарушение_ритма_год"] = (
        float(request.cad_chd_ihd_year)
        if arrhythmia_or_ihd and request.cad_chd_ihd_year
        else nan
    )
    data["стенокардия_год"] = (
        float(request.angine_year) if angina and request.angine_year else nan
    )
    data["им_год"] = (
        float(request.myocardial_infarction_year)
        if myocardial_infarction and request.myocardial_infarction_year
        else nan
    )
    data["аг_год"] = (
        float(request.arterial_hypertension_year)
        if arterial_hypertension and request.arterial_hypertension_year
        else nan
    )

    return transform_request_to_vector(data, region_stats, feature_order)
