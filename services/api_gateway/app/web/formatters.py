MODEL_NAMES: dict[str, str] = {
    "general": "Общий риск",
    "ah": "Артериальная гипертензия",
    "angina": "Стенокардия",
    "arrhythmia_or_ihd": "Нарушение ритма или ИБС",
    "heart_failure": "Сердечная недостаточность",
    "mi": "Инфаркт миокарда",
    "stroke": "Инсульт",
}


def format_prediction(value: object) -> str:
    raw_value = str(value)
    model_code, separator, probability_text = raw_value.partition(":")
    if not separator:
        return raw_value

    model_name = MODEL_NAMES.get(model_code, model_code)
    try:
        probability = float(probability_text)
    except ValueError:
        return f"{model_name}: вероятность {probability_text}"
    return f"{model_name}: вероятность {probability:.1%}"
