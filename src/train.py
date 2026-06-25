import json
import os

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

EVAL_THRESHOLD = 0.70
DRIFT_THRESHOLD = 0.10

MODEL_PARAM_KEYS = {
    "random_forest": ["n_estimators", "max_depth", "min_samples_split"],
    "gradient_boosting": ["n_estimators", "max_depth", "min_samples_split"],
    "logistic_regression": ["max_iter"],
}


def _filter_params(model_type: str, params: dict) -> dict:
    allowed = MODEL_PARAM_KEYS.get(model_type, [])
    return {k: v for k, v in params.items() if k in allowed and v is not None}


def build_model(model_type: str, params: dict):
    if model_type == "random_forest":
        return RandomForestClassifier(**_filter_params(model_type, params), random_state=42)
    if model_type == "gradient_boosting":
        return GradientBoostingClassifier(**_filter_params(model_type, params), random_state=42)
    if model_type == "logistic_regression":
        lr_params = _filter_params(model_type, params)
        lr_params.setdefault("max_iter", 500)
        return LogisticRegression(**lr_params, random_state=42)
    raise ValueError(f"Unsupported model_type: {model_type}")


def check_label_distribution(y_train: pd.Series) -> tuple[dict, bool]:
    """Bonus 5: tinh ty le nhan va canh bao neu lop nao < 10%."""
    total = len(y_train)
    distribution = {}
    drift_warning = False

    for label in sorted(y_train.unique()):
        ratio = float((y_train == label).sum()) / total
        distribution[str(int(label))] = round(ratio, 4)
        if ratio < DRIFT_THRESHOLD:
            drift_warning = True
            print(
                f"WARNING [data drift]: class {label} chi chiem {ratio:.1%} "
                f"(< {DRIFT_THRESHOLD:.0%} tong mau)"
            )

    if not drift_warning:
        print("Label distribution OK — khong co lop nao < 10%.")

    return distribution, drift_warning


def write_performance_report(y_eval: pd.Series, preds, path: str = "outputs/report.txt") -> None:
    """Bonus 3: confusion matrix + precision/recall tung lop."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cm = confusion_matrix(y_eval, preds, labels=[0, 1, 2])
    report = classification_report(y_eval, preds, labels=[0, 1, 2], digits=4)

    lines = [
        "=== Performance Report ===",
        "",
        "Confusion Matrix (rows=true, cols=pred):",
        f"       pred_0  pred_1  pred_2",
    ]
    for i, row in enumerate(cm):
        lines.append(f"true_{i}  {row[0]:6d}  {row[1]:6d}  {row[2]:6d}")

    lines.extend(["", "Classification Report:", report])
    content = "\n".join(lines)

    with open(path, "w") as f:
        f.write(content)
    print(content)


def train(
    params: dict,
    data_path: str = "data/train_phase1.csv",
    eval_path: str = "data/eval.csv",
) -> float:
    """
    Huan luyen mo hinh va ghi nhan ket qua vao MLflow.

    Tra ve:
        accuracy (float): do chinh xac tren tap danh gia.
    """
    configure_mlflow()
    params = dict(params)
    model_type = params.pop("model_type", "random_forest")

    df_train = pd.read_csv(data_path)
    df_eval = pd.read_csv(eval_path)

    X_train = df_train.drop(columns=["target"])
    y_train = df_train["target"]
    X_eval = df_eval.drop(columns=["target"])
    y_eval = df_eval["target"]

    label_distribution, drift_warning = check_label_distribution(y_train)

    with mlflow.start_run():
        mlflow.log_params({**params, "model_type": model_type})

        model = build_model(model_type, params)
        model.fit(X_train, y_train)

        preds = model.predict(X_eval)
        acc = accuracy_score(y_eval, preds)
        f1 = f1_score(y_eval, preds, average="weighted")

        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)
        mlflow.sklearn.log_model(model, "model")

        print(f"Model: {model_type} | Accuracy: {acc:.4f} | F1: {f1:.4f}")

        write_performance_report(y_eval, preds)

        metrics = {
            "accuracy": acc,
            "f1_score": f1,
            "model_type": model_type,
            "label_distribution": label_distribution,
            "drift_warning": drift_warning,
        }
        os.makedirs("outputs", exist_ok=True)
        with open("outputs/metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/model.pkl")

    return acc


def configure_mlflow() -> None:
    """Bonus 1: dung DagsHub remote neu co env, nguoc lai SQLite local."""
    uri = os.environ.get("MLFLOW_TRACKING_URI", "").strip()
    if not uri:
        os.environ["MLFLOW_TRACKING_URI"] = "sqlite:///mlflow.db"
        os.environ.setdefault("MLFLOW_ARTIFACT_ROOT", "./mlartifacts")


if __name__ == "__main__":
    configure_mlflow()
    with open("params.yaml") as f:
        params = yaml.safe_load(f)
    train(params)
