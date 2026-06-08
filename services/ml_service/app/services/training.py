import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


@dataclass(frozen=True)
class DatasetConfig:
    years: tuple[int, ...] = (2013, 2017, 2019, 2021)
    year_offsets: dict[int, int] = field(
        default_factory=lambda: {2013: 0, 2017: 4, 2019: 6, 2021: 8}
    )


ECO_FEATURES: tuple[str, ...] = (
    "суммарный канцерогенный риск ",
    "f(концентрация) ИЗА ",
    "неканцерогенный риск Аммиак",
    "неканцерогенный риск Взвешенные вещества",
    "среднегодовая концентрация Ам. Форм.",
    "неканцерогенный риск Углерод оксид",
    "неканцерогенный риск Сера диоксид",
    "% проб превышающих пдк Азот оксид",
    "неканцерогенный риск Формальдегид",
    "неканцерогенный риск Гидрохлорид",
    "неканцерогенный риск Анилин",
    "неканцерогенный риск Углерод(сажа)",
    "неканцерогенный риск Бензпирен",
    "f(концентрация) Сердечные ",
    "неканцерогенный риск Фенол",
    "неканцерогенный риск Азот диоксид",
)

_REGION_NAME_TO_KEY: dict[str, str] = {
    "рудничный": "RUDNICHNY",
    "центральный": "CENTRAL",
    "заводский": "ZAVODSKOY",
    "кировский": "KIROVSKY",
    "ленинский": "LENINSKY",
    "сельская местность": "RURAL",
}

_DIVIDERS: dict[str, float] = {"вес": 70.0, "возраст": 50.0, "имт": 30.0}


def _first_year(
    df: pd.DataFrame,
    year_cols: list[tuple[str, int]],
    *,
    summary_col: str | None = None,
    summary_fallback_year: int = 2013,
) -> pd.Series:
    """
    Возвращает первый год постановки диагноза (float / NaN), исходя из набора колонок-годов.
    Если summary_col задан и в нём 1, но по годам нет ни одной единицы, считаем год=summary_fallback_year.
    """
    cols = [c for c, _ in year_cols] + ([summary_col] if summary_col else [])
    x = df[cols].fillna(0)

    out = np.full(shape=(len(x),), fill_value=np.nan, dtype=float)
    for col, year in year_cols:
        mask = (out != out) & (x[col].astype(float) > 0)  # NaN check: out!=out
        out[mask] = float(year)

    if summary_col:
        mask = (out != out) & (x[summary_col].astype(float) > 0)
        out[mask] = float(summary_fallback_year)

    return pd.Series(out, index=df.index)


def _ensure_bmi(df: pd.DataFrame) -> pd.DataFrame:
    if "имт" in df.columns:
        return df
    if "рост" not in df.columns or "вес" not in df.columns:
        raise ValueError("Cannot compute 'имт' without 'рост' and 'вес' columns")
    out = df.copy()
    height_m = (out["рост"].astype(float) / 100.0).replace(0, np.nan)
    out["имт"] = out["вес"].astype(float) / (height_m**2)
    return out


def _ensure_ecology_from_region(
    df: pd.DataFrame,
    *,
    region_data: dict[str, dict[str, float]] | None,
) -> pd.DataFrame:
    missing = [eco for eco in ECO_FEATURES if eco not in df.columns]
    if not missing:
        return df
    if region_data is None:
        raise ValueError(
            "Dataset is missing ecology features and region_data was not provided. "
            f"Missing columns (sample): {missing[:5]}"
        )
    if "район" not in df.columns:
        raise ValueError(
            "Dataset is missing 'район' column required to map ecology from region_data.json"
        )

    region_name = df["район"].astype(str).str.strip().str.lower()
    region_key = region_name.map(_REGION_NAME_TO_KEY)
    if region_key.isna().any():
        bad = sorted(set(region_name[region_key.isna()].tolist()))
        raise ValueError(f"Unknown values in 'район': {bad[:10]}")

    eco_table = pd.DataFrame.from_dict(region_data, orient="index")
    missing_eco_cols = [c for c in ECO_FEATURES if c not in eco_table.columns]
    if missing_eco_cols:
        raise ValueError(
            "region_data.json is missing required ecology keys: "
            + ", ".join(missing_eco_cols)
        )

    out = df.copy()
    out["__region_key"] = region_key.values
    out = out.merge(
        eco_table[list(ECO_FEATURES)],
        left_on="__region_key",
        right_index=True,
        how="left",
    )
    out.drop(columns=["__region_key"], inplace=True)
    return out


def _materialize_interactions(
    X: pd.DataFrame,
    *,
    feature_cols: list[str],
) -> pd.DataFrame:
    """
    Ensures that all `feature_cols` exist as columns in X.

    For interaction cols like "A * вес" computes them from their factors,
    matching app/services/transformer.py logic.
    """
    out = X.copy()
    for col in feature_cols:
        if col in out.columns:
            continue
        if "*" not in col:
            raise KeyError(f"Missing required feature column: {col!r}")

        parts = [p.strip() for p in col.split("*")]
        val: pd.Series | float = 1.0
        for p in parts:
            base_val = out[p] if p in out.columns else pd.Series(0.0, index=out.index)
            divider = _DIVIDERS.get(p, 1.0)
            val = val * (base_val / divider)
        out[col] = val
    return out


def build_city_year_dataset(
    patients: pd.DataFrame,
    *,
    config: DatasetConfig = DatasetConfig(),
) -> pd.DataFrame:
    # Вычисляем "первый год диагноза" по пациенту (используем для формирования y по годам
    # и для будущего маппинга на поля "год диагностирования").
    year_stroke = _first_year(
        patients,
        [
            ("инсульт 2013", 2013),
            ("инсульт 2017", 2017),
            ("инсульт 2019", 2019),
            ("инсульт 2021", 2021),
        ],
        summary_col="инсульт 2016 2021",
    )
    year_hf = _first_year(
        patients,
        [("сн 2013", 2013), ("сн 2017", 2017), ("сн 2019", 2019), ("сн 2021", 2021)],
        summary_col="сн 2016 2021",
    )
    year_arrhythmia = _first_year(
        patients,
        [
            ("нарушения ритма ибс 2013", 2013),
            ("нарушение ритма 2019", 2019),
            ("нарушение ритма 2021", 2021),
        ],
        summary_col="нарушение ритма 2016 2021",
    )
    year_angina = _first_year(
        patients,
        [
            ("ибс 2013", 2013),
            ("ибс стенокардия 2017", 2017),
            ("ибс стенокардия 2019", 2019),
            ("ибс стенокардия 2021", 2021),
        ],
        summary_col="ибс стенокардия 2016 2021",
    )
    # NB: в исходных данных 2013-й год содержит объединённую колонку "им стенокардия 2013".
    # Для "инфаркт миокарда" используем также summary "им 2016 2021" как сигнал "был ИМ",
    # а год фоллбеком считаем 2013 (если ни в одном из 2017/2019/2021 не отмечено).
    year_mi = _first_year(
        patients,
        [
            ("им стенокардия 2013", 2013),
            ("им 2017", 2017),
            ("им 2019", 2019),
            ("им 2021", 2021),
        ],
        summary_col="им 2016 2021",
    )
    year_ah = _first_year(
        patients,
        [
            ("код по аг после измерений 1 2013", 2013),
            ("аг 2017", 2017),
            ("аг 2019", 2019),
            ("аг 2021", 2021),
        ],
        summary_col="аг 2016 2021",
    )

    frames: list[pd.DataFrame] = []
    for year in config.years:
        df = pd.DataFrame({"id": patients["id"].copy()})
        df["year"] = year

        # Категориальные (как в текущих csv: строки)
        df["пол"] = patients["пол 2013"]
        df["алкоголь"] = patients["алкоголь 2013"]
        df["профессия"] = patients["профессия 2013"]
        # Входной словарь "район" включает "сельская местность": берём её из "город 1 /село 2"
        df["район"] = np.where(
            patients["город 1 /село 2"].astype(str) == "2",
            "сельская местность",
            patients["район"],
        )

        # Числовые
        df["возраст"] = patients["возраст 2013"] + config.year_offsets[year]
        if year in (2013, 2017):
            df["рост"] = patients["рост 2013"]
            df["вес"] = patients["вес 2013"]
            df["холестерин"] = patients["холестерин 2013"]
            df["холестерин лпвп"] = patients["холестерин лпвп 2013"]
            df["холестерин лпнп"] = patients["холестерин лпнп 2013"]
            df["тг"] = patients["тг 2013"]
        else:
            df["рост"] = patients["рост 2019 2021"]
            df["вес"] = patients["вес 2019 2021"]
            df["холестерин"] = patients["холестерин 2019 2021"]
            df["холестерин лпвп"] = patients["холестерин лпвп 2019 2021"]
            df["холестерин лпнп"] = patients["холестерин лпнп 2019 2021"]
            df["тг"] = patients["тг 2019 2021"]

        # Колонки, которые в patients.csv есть только для 2019-2021, но нужны в интерфейсе:
        df["об"] = patients["об1 2019 2021"]
        df["глюкоза"] = patients["глюкоза 2019 2021"]

        # Колонки, которые в данных есть только "базовые" (2013):
        df["не лпвп"] = patients["не лпвп 2013"]
        df["лпонп"] = patients["лпонп 2013"]
        df["липиды apoa"] = patients["липиды apoa 2013"]
        df["липиды apo b"] = patients["липиды apo b 2013"]

        # ИМТ (в интерфейсе нет, но нужен для перемножения признаков)
        height_m = (df["рост"].astype(float) / 100.0).replace(0, np.nan)
        df["имт"] = df["вес"].astype(float) / (height_m**2)

        # Диагнозы к указанному году (накопительно) + год диагностирования как фича.
        #
        # Важно: "год диагностирования" должен быть известен только если диагноз уже есть на текущий год.
        # Поэтому для строк более ранних лет, где диагноз появится в будущем, *_год остаётся NaN.
        stroke_flag = (year_stroke.notna()) & (year_stroke <= year)
        hf_flag = (year_hf.notna()) & (year_hf <= year)
        arr_flag = (year_arrhythmia.notna()) & (year_arrhythmia <= year)
        angina_flag = (year_angina.notna()) & (year_angina <= year)
        mi_flag = (year_mi.notna()) & (year_mi <= year)
        ah_flag = (year_ah.notna()) & (year_ah <= year)

        df["инсульт"] = stroke_flag.astype(int)
        df["сн"] = hf_flag.astype(int)
        df["нарушение ритма или ибс"] = arr_flag.astype(int)
        df["стенокардия"] = angina_flag.astype(int)
        df["им"] = mi_flag.astype(int)
        df["аг"] = ah_flag.astype(int)

        df["инсульт_год"] = year_stroke.where(stroke_flag, np.nan)
        df["сн_год"] = year_hf.where(hf_flag, np.nan)
        df["нарушение_ритма_год"] = year_arrhythmia.where(arr_flag, np.nan)
        df["стенокардия_год"] = year_angina.where(angina_flag, np.nan)
        df["им_год"] = year_mi.where(mi_flag, np.nan)
        df["аг_год"] = year_ah.where(ah_flag, np.nan)

        frames.append(df)

    full = pd.concat(frames, axis=0, ignore_index=True)

    return full


def train_models(
    df: pd.DataFrame,
    *,
    out_dir: Path,
    region_data: dict[str, dict[str, float]] | None = None,
    test_size: float = 0.33,
    random_state: int = 1000,
    iterations: int = 200,
    learning_rate: float = 0.1,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Training requested: out_dir={} rows={} cols={} test_size={} random_state={} iterations={} lr={}",
        str(out_dir),
        len(df),
        len(df.columns),
        test_size,
        random_state,
        iterations,
        learning_rate,
    )

    df_2021 = df[df["year"] == 2021][["id"]].copy()
    if len(df_2021) == 0:
        # Allow training on datasets without per-year sampling (e.g. custom/filtered uploads).
        # In this case we split by all unique ids available.
        df_2021 = df[["id"]].drop_duplicates().copy()

    train_2021, test_2021 = train_test_split(
        df_2021, test_size=test_size, random_state=random_state
    )
    train_ids = set(train_2021["id"])
    test_ids = set(test_2021["id"])
    logger.info(
        "Train/test split by id: train_ids={} test_ids={}",
        len(train_ids),
        len(test_ids),
    )

    targets: dict[str, str] = {
        "general": "общий риск (любая болезнь)",
        "инсульт": "инсульт",
        "сн": "сердечная недостаточность",
        "нарушение ритма или ибс": "нарушение ритма / другие ИБС",
        "стенокардия": "стенокардия",
        "им": "инфаркт миокарда",
        "аг": "артериальная гипертензия",
    }

    file_stems: dict[str, str] = {
        "general": "general",
        "инсульт": "stroke",
        "сн": "heart_failure",
        "нарушение ритма или ибс": "arrhythmia_or_ihd",
        "стенокардия": "angina",
        "им": "mi",
        "аг": "ah",
    }

    # Признаки: строго по текущему интерфейсу + экология (и их произведения) + имт (вычисляется).
    base_features = [
        "пол",
        "возраст",
        "рост",
        "вес",
        "об",
        "алкоголь",
        "профессия",
        "район",
        "глюкоза",
        "холестерин",
        "не лпвп",
        "лпонп",
        "холестерин лпвп",
        "холестерин лпнп",
        "липиды apoa",
        "липиды apo b",
        "тг",
        "имт",
    ]

    interaction_features = []
    for eco in ECO_FEATURES:
        interaction_features.extend(
            [
                eco,
                f"{eco} * вес",
                f"{eco} * возраст",
                f"{eco} * имт",
                f"{eco} * возраст * имт",
            ]
        )

    # История заболеваний (флаги + первый год) доступна как вход в отдельных моделях.
    # Для "general" модель это НЕ использует.
    diagnosis_feature_pairs: list[tuple[str, str]] = [
        ("инсульт", "инсульт_год"),
        ("сн", "сн_год"),
        ("нарушение ритма или ибс", "нарушение_ритма_год"),
        ("стенокардия", "стенокардия_год"),
        ("им", "им_год"),
        ("аг", "аг_год"),
    ]

    # Категориальные по CatBoost
    cat_features = ["пол", "алкоголь", "профессия", "район"]

    # If ecology columns are not present, map them from region_data.json using "район".
    df_work = _ensure_bmi(df)
    df_work = _ensure_ecology_from_region(df_work, region_data=region_data)

    # train/test по id
    train_mask = df_work["id"].isin(train_ids)
    test_mask = df_work["id"].isin(test_ids)

    # общий риск — любой из таргетов по болезням
    disease_targets = [
        "инсульт",
        "сн",
        "нарушение ритма или ибс",
        "стенокардия",
        "им",
        "аг",
    ]
    y_general = df_work[disease_targets].any(axis=1).astype(int)

    train_specs: list[tuple[str, pd.Series]] = [("general", y_general)]
    for t in disease_targets:
        train_specs.append((t, df_work[t].astype(int)))

    metrics_rows: list[dict] = []

    for target_name, y in train_specs:
        feature_cols = [*base_features, *interaction_features]
        if target_name != "general":
            for flag_col, year_col in diagnosis_feature_pairs:
                if flag_col == target_name:
                    continue
                feature_cols.extend([flag_col, year_col])

        raw_cols = [c for c in feature_cols if "*" not in c]
        X_raw = df_work[raw_cols].copy()
        X = _materialize_interactions(X_raw, feature_cols=feature_cols)

        X_train = X[train_mask]
        y_train = y[train_mask]
        X_test = X[test_mask]
        y_test = y[test_mask]

        pos = int(y_train.sum())
        neg = int((y_train == 0).sum())
        if pos == 0 or neg == 0:
            raise ValueError(
                f"Target {target_name!r} has invalid class distribution: pos={pos}, neg={neg}"
            )

        class_weights = [1.0, float(neg / pos)]
        model = CatBoostClassifier(
            loss_function="Logloss",
            eval_metric="AUC",
            custom_metric="AUC",
            class_weights=class_weights,
            learning_rate=learning_rate,
            max_depth=8,
            iterations=iterations,
            random_state=random_state,
            use_best_model=True,
            verbose=False,
        )

        train_pool = Pool(X_train, y_train, cat_features=cat_features)
        test_pool = Pool(X_test, y_test, cat_features=cat_features)
        model.fit(train_pool, eval_set=test_pool)

        # Top feature importances (model-driven).
        # NB: CatBoost returns importances aligned with feature order in pool/X_train.
        importances = model.get_feature_importance(train_pool, type="FeatureImportance")
        fi = (
            pd.DataFrame({"feature": feature_cols, "importance": importances})
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )

        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test).astype(int)

        auc = float(roc_auc_score(y_test, y_prob))
        ap = float(average_precision_score(y_test, y_prob))
        acc = float(accuracy_score(y_test, y_pred))
        bacc = float(balanced_accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        cm = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
        tn, fp, fn, tp = (int(cm[0]), int(cm[1]), int(cm[2]), int(cm[3]))

        # Некоторые метрики требуют вероятностей. В logloss/brier "насыщенные" вероятности допустимы.
        ll = float(log_loss(y_test, y_prob, labels=[0, 1]))
        brier = float(brier_score_loss(y_test, y_prob))
        logger.info(
            "Model trained: target={} label={} train_pos={} train_neg={} test_pos={} test_neg={} "
            "roc_auc={:.4f} pr_auc={:.4f} acc={:.4f} bal_acc={:.4f} f1={:.4f} prec={:.4f} rec={:.4f} "
            "logloss={:.4f} brier={:.4f} cm=[tn={} fp={} fn={} tp={}] class_weights={}",
            target_name,
            targets.get(target_name, target_name),
            pos,
            neg,
            int(y_test.sum()),
            int((y_test == 0).sum()),
            auc,
            ap,
            acc,
            bacc,
            f1,
            prec,
            rec,
            ll,
            brier,
            tn,
            fp,
            fn,
            tp,
            class_weights,
        )
        logger.debug(
            "Classification report for target={}:\n{}",
            target_name,
            classification_report(y_test, y_pred, target_names=["0", "1"]),
        )

        top_features = [
            f"{r['importance']:.6f}\t{r['feature']}" for _, r in fi.head(25).iterrows()
        ]
        logger.info("Top features ({}):\n{}", target_name, "\n".join(top_features))

        stem = file_stems.get(target_name, target_name)
        model_path = out_dir / f"{stem}_model.cbm"
        model.save_model(model_path)
        (out_dir / f"{stem}_features.txt").write_text(
            "\n".join(feature_cols), encoding="utf-8"
        )
        fi.to_csv(out_dir / f"{stem}_feature_importance.csv", index=False)
        metrics_rows.append(
            {
                "target": target_name,
                "model_stem": stem,
                "feature_count": int(len(feature_cols)),
                "train_rows": int(len(X_train)),
                "test_rows": int(len(X_test)),
                "train_pos": int(pos),
                "train_neg": int(neg),
                "test_pos": int(int(y_test.sum())),
                "test_neg": int(int((y_test == 0).sum())),
                "class_weight_0": float(class_weights[0]),
                "class_weight_1": float(class_weights[1]),
                "roc_auc": auc,
                "pr_auc": ap,
                "accuracy": acc,
                "balanced_accuracy": bacc,
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "logloss": ll,
                "brier": brier,
                "tn": tn,
                "fp": fp,
                "fn": fn,
                "tp": tp,
            }
        )
        logger.info("Saved model artifact: {}", str(model_path))

    metrics_path_json = out_dir / "metrics.json"
    metrics_path_csv = out_dir / "metrics.csv"
    metrics_path_json.write_text(
        json.dumps(metrics_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame(metrics_rows).to_csv(metrics_path_csv, index=False)
    logger.info("Saved metrics: {}", str(metrics_path_json))
    logger.info("Saved metrics: {}", str(metrics_path_csv))


def main() -> None:
    # Keep CLI paths relative to the app package root (../), not services/.
    base_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Train multiple CatBoost models for Patients dataset (ecology from region_data.json)."
    )
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--test-size", type=float, default=0.33)
    parser.add_argument("--random-state", type=int, default=1000)
    parser.add_argument(
        "--out-dir",
        type=str,
        default="models",
        help="Output directory (relative to this script).",
    )
    parser.add_argument("--patients-csv", type=str, default="patients.csv")
    args = parser.parse_args()

    # CLI helper only: the FastAPI service imports train_models() directly.
    try:
        from app.logging import setup_logging

        setup_logging()
    except Exception:
        # Allow running in ad-hoc environments without the app package installed.
        pass

    patients_path = (base_dir / args.patients_csv).resolve()
    logger.info("Loading training sources: patients_csv={}", str(patients_path))
    patients = pd.read_csv(patients_path)

    df = build_city_year_dataset(patients)
    out_dir = base_dir / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Сохраняем датасет, чтобы проще было отлаживать под систему/инпуты
    df.to_csv(out_dir / "train_dataset.csv", index=False)
    logger.info("Saved train_dataset.csv to {}", str(out_dir / "train_dataset.csv"))

    # Load ecology stats (same source as the running service uses for inference).
    region_data: dict[str, dict[str, float]] | None = None
    try:
        from app.config import settings

        region_data = json.loads(
            Path(settings.REGION_DATA_PATH).read_text(encoding="utf-8")
        )
    except Exception:
        fallback = base_dir / "data" / "region_data.json"
        if fallback.exists():
            region_data = json.loads(fallback.read_text(encoding="utf-8"))

    train_models(
        df,
        out_dir=out_dir,
        region_data=region_data,
        test_size=args.test_size,
        random_state=args.random_state,
        iterations=args.iterations,
        learning_rate=args.learning_rate,
    )


if __name__ == "__main__":
    main()
