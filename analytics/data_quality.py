import pandas as pd
import numpy as np


# ==========================================================
# 1. CHECK MISSING VALUES
# ==========================================================

def check_missing_values(df):

    missing_count = df.isnull().sum()

    missing_percentage = (
        missing_count / len(df) * 100
        if len(df) > 0
        else 0
    )

    result = pd.DataFrame({
        "column": df.columns,
        "missing_count": missing_count.values,
        "missing_percentage": missing_percentage.values
    })

    return result


# ==========================================================
# 2. CHECK DUPLICATE ROWS
# ==========================================================

def check_duplicate_rows(df):

    duplicate_count = int(
        df.duplicated().sum()
    )

    total_rows = len(df)

    duplicate_percentage = (
        duplicate_count / total_rows * 100
        if total_rows > 0
        else 0
    )

    return {
        "duplicate_count": duplicate_count,
        "duplicate_percentage": duplicate_percentage
    }


# ==========================================================
# 3. CHECK DATA TYPES
# ==========================================================

def check_data_types(df):

    result = pd.DataFrame({
        "column": df.columns,
        "data_type": [
            str(dtype)
            for dtype in df.dtypes
        ]
    })

    return result


# ==========================================================
# 4. CHECK CONSTANT COLUMNS
# ==========================================================

def check_constant_columns(df):

    constant_columns = []

    for column in df.columns:

        if df[column].nunique(
            dropna=False
        ) <= 1:

            constant_columns.append(
                column
            )

    return constant_columns


# ==========================================================
# 5. CHECK OUTLIERS
# ==========================================================

def check_outliers(df):

    numeric_columns = df.select_dtypes(
        include=np.number
    ).columns

    results = []

    for column in numeric_columns:

        series = df[column].dropna()

        if series.empty:

            outlier_count = 0

        else:

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)

            iqr = q3 - q1

            lower_bound = (
                q1 - 1.5 * iqr
            )

            upper_bound = (
                q3 + 1.5 * iqr
            )

            outlier_count = int(
                (
                    (series < lower_bound)
                    |
                    (series > upper_bound)
                ).sum()
            )

        total_values = len(series)

        outlier_percentage = (
            outlier_count / total_values * 100
            if total_values > 0
            else 0
        )

        results.append({
            "column": column,
            "outlier_count": outlier_count,
            "outlier_percentage": outlier_percentage
        })

    return pd.DataFrame(
        results,
        columns=[
            "column",
            "outlier_count",
            "outlier_percentage"
        ]
    )


# ==========================================================
# 6. CHECK DUPLICATE IDs
# ==========================================================

def check_duplicate_ids(df):

    id_columns = []

    for column in df.columns:

        column_lower = (
            column.strip().lower()
        )

        if (
            column_lower == "id"
            or column_lower.endswith("_id")
            or column_lower.endswith("id")
            or "employee" in column_lower
            or "customer" in column_lower
            or "order" in column_lower
            or "invoice" in column_lower
        ):

            id_columns.append(column)

    results = []

    for column in id_columns:

        duplicate_count = int(
            df[column].duplicated().sum()
        )

        if duplicate_count > 0:

            results.append({
                "column": column,
                "duplicate_count": duplicate_count
            })

    return pd.DataFrame(
        results,
        columns=[
            "column",
            "duplicate_count"
        ]
    )


# ==========================================================
# 7. OVERALL DATA QUALITY SCORE
# ==========================================================

def calculate_data_quality_score(
    missing_df,
    duplicate_result,
    constant_columns,
    outlier_df,
    duplicate_id_df
):

    score = 100


    # ------------------------------------------------------
    # Missing Values
    # ------------------------------------------------------

    total_missing = int(
        missing_df["missing_count"].sum()
    )

    if total_missing > 0:

        score -= 25


    # ------------------------------------------------------
    # Duplicate Rows
    # ------------------------------------------------------

    duplicate_count = (
        duplicate_result["duplicate_count"]
    )

    if duplicate_count > 0:

        score -= 15


    # ------------------------------------------------------
    # Constant Columns
    # ------------------------------------------------------

    if len(constant_columns) > 0:

        score -= 10


    # ------------------------------------------------------
    # Outliers
    # ------------------------------------------------------

    if (
        not outlier_df.empty
        and outlier_df["outlier_count"].sum() > 0
    ):

        score -= 20


    # ------------------------------------------------------
    # Duplicate IDs
    # ------------------------------------------------------

    if (
        not duplicate_id_df.empty
        and duplicate_id_df["duplicate_count"].sum() > 0
    ):

        score -= 30


    # ------------------------------------------------------
    # Keep Score Between 0 and 100
    # ------------------------------------------------------

    score = max(
        0,
        min(100, score)
    )

    return score