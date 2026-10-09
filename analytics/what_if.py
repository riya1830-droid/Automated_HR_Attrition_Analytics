import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score


# ==========================================================
# FIND COLUMN
# ==========================================================

def find_column(df, possible_names):

    for column in df.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

        if normalized in possible_names:
            return column

    return None


# ==========================================================
# FIND ATTRITION COLUMN
# ==========================================================

def find_attrition_column(df):

    for column in df.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

        if normalized == "attrition":

            return column

    return None


# ==========================================================
# NORMALIZE ATTRITION
# ==========================================================

def prepare_target(df):

    df = df.copy()

    attrition_column = find_attrition_column(df)

    if attrition_column is None:

        raise ValueError(
            "Attrition column was not found."
        )

    target = (
        df[attrition_column]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({
            "yes": 1,
            "y": 1,
            "1": 1,
            "true": 1,
            "left": 1,

            "no": 0,
            "n": 0,
            "0": 0,
            "false": 0,
            "stayed": 0
        })
    )

    valid_rows = target.notna()

    df = df.loc[valid_rows].copy()

    df["Attrition_Target"] = target.loc[
        valid_rows
    ].astype(int)

    return df


# ==========================================================
# REMOVE UNSUITABLE COLUMNS
# ==========================================================

def prepare_features(df):

    df = df.copy()

    columns_to_remove = []

    attrition_column = find_attrition_column(df)

    if attrition_column is not None:

        columns_to_remove.append(
            attrition_column
        )

    if "Attrition_Status" in df.columns:

        columns_to_remove.append(
            "Attrition_Status"
        )

    if "Attrition_Target" in df.columns:

        columns_to_remove.append(
            "Attrition_Target"
        )

    # Remove obvious ID columns
    for column in df.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

        if (
            normalized == "id"
            or normalized.endswith("employeeid")
            or normalized == "employeenumber"
        ):

            columns_to_remove.append(
                column
            )

    columns_to_remove = list(
        set(columns_to_remove)
    )

    X = df.drop(
        columns=columns_to_remove,
        errors="ignore"
    )

    # Remove columns containing only one unique value
    constant_columns = [
        column
        for column in X.columns
        if X[column].nunique(
            dropna=False
        ) <= 1
    ]

    X = X.drop(
        columns=constant_columns,
        errors="ignore"
    )

    # Convert date/time columns into useful numeric features
    date_columns = []

    for column in X.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
        )

        if any(
            word in normalized
            for word in [
                "date",
                "timestamp"
            ]
        ):

            date_columns.append(
                column
            )

    for column in date_columns:

        parsed = pd.to_datetime(
            X[column],
            errors="coerce"
        )

        if parsed.notna().sum() > 0:

            X[column + "_Year"] = (
                parsed.dt.year
            )

            X[column + "_Month"] = (
                parsed.dt.month
            )

            X = X.drop(
                columns=[column]
            )

    return X


# ==========================================================
# BUILD MODEL
# ==========================================================

def build_model(df):

    prepared_df = prepare_target(df)

    X = prepare_features(
        prepared_df
    )

    y = prepared_df[
        "Attrition_Target"
    ]

    if X.empty:

        raise ValueError(
            "No suitable features were available."
        )

    if y.nunique() < 2:

        raise ValueError(
            "Attrition target must contain both classes."
        )

    numeric_columns = (
        X.select_dtypes(
            include=np.number
        ).columns.tolist()
    )

    categorical_columns = (
        X.select_dtypes(
            exclude=np.number
        ).columns.tolist()
    )

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                )
            )
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                )
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore"
                )
            )
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                numeric_columns
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_columns
            )
        ]
    )

    model = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42
    )

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),
            (
                "model",
                model
            )
        ]
    )

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y
        )
    )

    pipeline.fit(
        X_train,
        y_train
    )

    probabilities = pipeline.predict_proba(
        X_test
    )[:, 1]

    try:

        auc = roc_auc_score(
            y_test,
            probabilities
        )

    except Exception:

        auc = None

    return (
        pipeline,
        X,
        y,
        auc
    )


# ==========================================================
# CURRENT EMPLOYEE RISK
# ==========================================================

def predict_employee_risk(
    pipeline,
    X
):

    probabilities = (
        pipeline.predict_proba(X)[:, 1]
        * 100
    )

    return probabilities


# ==========================================================
# RISK CATEGORIES
# ==========================================================

def classify_risk(probabilities):

    return np.select(
        [
            probabilities >= 70,
            probabilities >= 40
        ],
        [
            "High",
            "Medium"
        ],
        default="Low"
    )


# ==========================================================
# FIND DRIVER COLUMN
# ==========================================================

def get_driver_column(
    df,
    driver_name
):

    mapping = {

        "Overtime": {
            "overtime"
        },

        "Job Satisfaction": {
            "jobsatisfaction",
            "satisfaction"
        },

        "Department": {
            "department"
        },

        "Job Role": {
            "jobrole",
            "jobtitle",
            "role"
        },

        "Age": {
            "age"
        },

        "Years at Company": {
            "yearsatcompany"
        },

        "Monthly Income": {
            "monthlyincome",
            "monthlysalary",
            "income",
            "salary"
        }
    }

    names = mapping.get(
        driver_name
    )

    if names is None:

        return None

    return find_column(
        df,
        names
    )


# ==========================================================
# AGE SCENARIO VALUES
# ==========================================================

def get_age_groups():

    return [
        "18-25",
        "26-35",
        "36-45",
        "46-55",
        "56+"
    ]


# ==========================================================
# TENURE SCENARIO VALUES
# ==========================================================

def get_tenure_groups():

    return [
        "0-2 Years",
        "3-5 Years",
        "6-10 Years",
        "11-20 Years",
        "20+ Years"
    ]


# ==========================================================
# CREATE SCENARIO DATA
# ==========================================================

def create_scenario(
    df,
    driver_name,
    scenario_value
):

    scenario_df = df.copy()

    column = get_driver_column(
        scenario_df,
        driver_name
    )

    if column is None:

        raise ValueError(
            f"Column for {driver_name} "
            "was not found."
        )

    # ------------------------------------------------------
    # OVERTIME
    # ------------------------------------------------------

    if driver_name == "Overtime":

        scenario_df[column] = (
            scenario_value
        )

    # ------------------------------------------------------
    # JOB SATISFACTION
    # ------------------------------------------------------

    elif driver_name == "Job Satisfaction":

        scenario_df[column] = (
            pd.to_numeric(
                scenario_value,
                errors="coerce"
            )
        )

    # ------------------------------------------------------
    # DEPARTMENT
    # ------------------------------------------------------

    elif driver_name == "Department":

        scenario_df[column] = (
            scenario_value
        )

    # ------------------------------------------------------
    # JOB ROLE
    # ------------------------------------------------------

    elif driver_name == "Job Role":

        scenario_df[column] = (
            scenario_value
        )

    # ------------------------------------------------------
    # AGE
    # ------------------------------------------------------

    elif driver_name == "Age":

        current_age = pd.to_numeric(
            scenario_df[column],
            errors="coerce"
        )

        age_map = {

            "18-25": 22,

            "26-35": 30,

            "36-45": 40,

            "46-55": 50,

            "56+": 58
        }

        replacement = age_map.get(
            scenario_value,
            current_age.median()
        )

        scenario_df[column] = (
            replacement
        )

    # ------------------------------------------------------
    # YEARS AT COMPANY
    # ------------------------------------------------------

    elif driver_name == "Years at Company":

        tenure_map = {

            "0-2 Years": 1,

            "3-5 Years": 4,

            "6-10 Years": 8,

            "11-20 Years": 15,

            "20+ Years": 21
        }

        replacement = tenure_map.get(
            scenario_value
        )

        if replacement is not None:

            scenario_df[column] = (
                replacement
            )

    # ------------------------------------------------------
    # MONTHLY INCOME
    # ------------------------------------------------------

    elif driver_name == "Monthly Income":

        scenario_df[column] = (
            pd.to_numeric(
                scenario_value,
                errors="coerce"
            )
        )

    return scenario_df


# ==========================================================
# PREPARE SCENARIO FEATURES
# ==========================================================

def prepare_scenario_features(
    scenario_df
):

    return prepare_features(
        prepare_target(
            scenario_df
        )
    )


# ==========================================================
# RUN WHAT-IF
# ==========================================================

def run_what_if(
    df,
    driver_name,
    scenario_value
):

    # ------------------------------------------------------
    # BUILD MODEL
    # ------------------------------------------------------

    pipeline, X, y, auc = (
        build_model(df)
    )

    # ------------------------------------------------------
    # CURRENT RISK
    # ------------------------------------------------------

    current_probabilities = (
        predict_employee_risk(
            pipeline,
            X
        )
    )

    current_categories = (
        classify_risk(
            current_probabilities
        )
    )

    # ------------------------------------------------------
    # CREATE SCENARIO
    # ------------------------------------------------------

    scenario_df = create_scenario(
        df,
        driver_name,
        scenario_value
    )

    scenario_features = (
        prepare_scenario_features(
            scenario_df
        )
    )

    # Ensure exactly same columns
    # as training data

    scenario_features = (
        scenario_features
        .reindex(
            columns=X.columns,
            fill_value=np.nan
        )
    )

    # ------------------------------------------------------
    # SCENARIO RISK
    # ------------------------------------------------------

    scenario_probabilities = (
        predict_employee_risk(
            pipeline,
            scenario_features
        )
    )

    scenario_categories = (
        classify_risk(
            scenario_probabilities
        )
    )

    # ------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------

    current_high = int(
        (
            current_categories
            == "High"
        ).sum()
    )

    scenario_high = int(
        (
            scenario_categories
            == "High"
        ).sum()
    )

    current_average = float(
        np.mean(
            current_probabilities
        )
    )

    scenario_average = float(
        np.mean(
            scenario_probabilities
        )
    )

    risk_change = (
        current_average
        - scenario_average
    )

    high_risk_reduction = (
        current_high
        - scenario_high
    )

    return {

        "current_probabilities":
            current_probabilities,

        "scenario_probabilities":
            scenario_probabilities,

        "current_categories":
            current_categories,

        "scenario_categories":
            scenario_categories,

        "current_high":
            current_high,

        "scenario_high":
            scenario_high,

        "current_average":
            current_average,

        "scenario_average":
            scenario_average,

        "risk_change":
            risk_change,

        "high_risk_reduction":
            high_risk_reduction,

        "auc":
            auc
    }