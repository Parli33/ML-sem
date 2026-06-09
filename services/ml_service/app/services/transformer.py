from typing import Any


DIVIDERS = {"вес": 70.0, "возраст": 50.0, "имт": 30.0}


def transform_request_to_vector(
    request_data: dict[str, Any],
    region_stats: dict[str, float],
    feature_order: list[str],
) -> list[Any]:
    age = float(request_data["age"])
    weight = float(request_data["weight"])
    height = float(request_data["height"])
    bmi = weight / ((height / 100) ** 2) if height > 0 else 0

    pool = {
        "пол": request_data["gender_name"],
        "возраст": age,
        "рост": height,
        "вес": weight,
        "имт": bmi,
        "об": request_data.get("hip_measurement", 0),
        "алкоголь": request_data["alcohol_name"],
        "профессия": request_data["job_name"],
        "район": request_data["region_name"],
        "глюкоза": request_data.get("glucose") or 5.7,
        "холестерин": request_data.get("cholesterol") or 5.22,
        "тг": request_data.get("triglycerides") or 1.17,
        "холестерин лпвп": request_data.get("hdl_cholesterol") or 1.55,
        "холестерин лпнп": request_data.get("ldl_cholesterol") or 3.4,
        "лпонп": request_data.get("vldl_cholesterol") or 0.57,
        "не лпвп": request_data.get("non_hdl_cholesterol") or 3.69,
        "липиды apoa": request_data.get("apolipoprotein_a") or 1.7,
        "липиды apo b": request_data.get("apolipoprotein_b") or 1.0,
    }

    pool.update(region_stats)

    final_vector: list[Any] = []
    for col in feature_order:
        if col in pool:
            final_vector.append(pool[col])
        elif "*" in col:
            parts = [p.strip() for p in col.split("*")]
            val = 1.0

            for p in parts:
                base_val = pool.get(p, 0)
                divider = DIVIDERS.get(p, 1.0)
                val *= base_val / divider

            final_vector.append(val)
        else:
            final_vector.append(pool.get(col, 0))

    return final_vector
