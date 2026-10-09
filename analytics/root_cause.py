import pandas as pd
import numpy as np


# ==========================================================
# FIND COLUMN BY NORMALIZED NAME
# ==========================================================

def find_column(df, possible_names):

    for column in df.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
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
        )

        if normalized == "attrition":
            return column

    return None


# ==========================================================
# NORMALIZE ATTRITION
# ==========================================================

def normalize_attrition(df):

    df = df.copy()

    attrition_column = find_attrition_column(df)

    if attrition_column is None:
        raise ValueError(
            "Attrition column was not found."
        )

    df["Attrition_Status"] = (
        df[attrition_column]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({
            "yes": "Left",
            "y": "Left",
            "1": "Left",
            "true": "Left",
            "left": "Left",

            "no": "Stayed",
            "n": "Stayed",
            "0": "Stayed",
            "false": "Stayed",
            "stayed": "Stayed"
        })
    )

    df = df[
        df["Attrition_Status"].isin(
            ["Left", "Stayed"]
        )
    ].copy()

    return df


# ==========================================================
# CATEGORICAL DRIVER ANALYSIS
# ==========================================================

def analyze_categorical_driver(df, column):

    working_df = normalize_attrition(df)

    if column not in working_df.columns:
        return None

    working_df = working_df[
        working_df[column].notna()
    ].copy()

    if working_df.empty:
        return None

    result = (
        working_df
        .groupby(column, dropna=False)
        .agg(
            Employees=(
                "Attrition_Status",
                "size"
            ),
            Employees_Left=(
                "Attrition_Status",
                lambda x: (
                    x == "Left"
                ).sum()
            )
        )
        .reset_index()
    )

    result["Attrition_Rate"] = (
        result["Employees_Left"]
        / result["Employees"]
        * 100
    )

    return result


# ==========================================================
# CATEGORICAL DRIVER STRENGTH
# ==========================================================

def categorical_driver_strength(
    df,
    column
):

    result = analyze_categorical_driver(
        df,
        column
    )

    if result is None or result.empty:
        return None

    max_rate = result["Attrition_Rate"].max()
    min_rate = result["Attrition_Rate"].min()

    difference = max_rate - min_rate

    if difference >= 15:
        strength = "Strong"

    elif difference >= 7:
        strength = "Moderate"

    else:
        strength = "Low"

    return {
        "driver": column,
        "difference": difference,
        "strength": strength,
        "data": result
    }


# ==========================================================
# NUMERIC DRIVER ANALYSIS
# ==========================================================

def analyze_numeric_driver(df, column):

    working_df = normalize_attrition(df)

    if column not in working_df.columns:
        return None

    working_df[column] = pd.to_numeric(
        working_df[column],
        errors="coerce"
    )

    working_df = working_df.dropna(
        subset=[column]
    )

    if working_df.empty:
        return None

    result = (
        working_df
        .groupby("Attrition_Status")[column]
        .agg(
            Employee_Count="count",
            Average="mean",
            Median="median"
        )
        .reset_index()
    )

    if len(result) < 2:
        return None

    left_row = result[
        result["Attrition_Status"] == "Left"
    ]

    stayed_row = result[
        result["Attrition_Status"] == "Stayed"
    ]

    if left_row.empty or stayed_row.empty:
        return None

    left_average = float(
        left_row["Average"].iloc[0]
    )

    stayed_average = float(
        stayed_row["Average"].iloc[0]
    )

    difference = abs(
        left_average - stayed_average
    )

    percentage_difference = (
        difference
        / stayed_average
        * 100
        if stayed_average != 0
        else 0
    )

    if percentage_difference >= 20:
        strength = "Strong"

    elif percentage_difference >= 10:
        strength = "Moderate"

    else:
        strength = "Low"

    return {
        "driver": column,
        "difference": difference,
        "percentage_difference": percentage_difference,
        "strength": strength,
        "data": result
    }


# ==========================================================
# CREATE DRIVER SUMMARY
# ==========================================================

def get_driver_summary(df):

    df = normalize_attrition(df)

    candidates = []

    # ------------------------------------------------------
    # CATEGORICAL DRIVERS
    # ------------------------------------------------------

    categorical_candidates = {
        "Overtime": {
            "names": {"overtime"}
        },

        "Job Satisfaction": {
            "names": {
                "jobsatisfaction",
                "satisfaction"
            }
        },

        "Department": {
            "names": {
                "department"
            }
        },

        "Job Role": {
            "names": {
                "jobrole",
                "jobtitle",
                "role"
            }
        }
    }

    for display_name, config in (
        categorical_candidates.items()
    ):

        column = find_column(
            df,
            config["names"]
        )

        if column is None:
            continue

        result = categorical_driver_strength(
            df,
            column
        )

        if result:

            result["display_name"] = (
                display_name
            )

            result["type"] = "Categorical"

            candidates.append(result)

    # ------------------------------------------------------
    # AGE GROUP
    # ------------------------------------------------------

    age_column = find_column(
        df,
        {"age"}
    )

    if age_column:

        age_values = pd.to_numeric(
            df[age_column],
            errors="coerce"
        )

        temp = df.copy()

        temp["Age_Group"] = pd.cut(
            age_values,
            bins=[
                0,
                25,
                35,
                45,
                55,
                np.inf
            ],
            labels=[
                "18-25",
                "26-35",
                "36-45",
                "46-55",
                "56+"
            ],
            include_lowest=True
        )

        result = categorical_driver_strength(
            temp,
            "Age_Group"
        )

        if result:

            result["display_name"] = "Age"

            result["type"] = "Categorical"

            candidates.append(result)

    # ------------------------------------------------------
    # TENURE
    # ------------------------------------------------------

    tenure_column = find_column(
        df,
        {"yearsatcompany"}
    )

    if tenure_column:

        years = pd.to_numeric(
            df[tenure_column],
            errors="coerce"
        )

        temp = df.copy()

        temp["Tenure_Group"] = pd.cut(
            years,
            bins=[
                -1,
                2,
                5,
                10,
                20,
                np.inf
            ],
            labels=[
                "0-2 Years",
                "3-5 Years",
                "6-10 Years",
                "11-20 Years",
                "20+ Years"
            ]
        )

        result = categorical_driver_strength(
            temp,
            "Tenure_Group"
        )

        if result:

            result["display_name"] = (
                "Years at Company"
            )

            result["type"] = "Categorical"

            candidates.append(result)

    # ------------------------------------------------------
    # NUMERIC INCOME
    # ------------------------------------------------------

    income_column = find_column(
        df,
        {
            "monthlyincome",
            "income",
            "salary",
            "monthlysalary"
        }
    )

    if income_column:

        result = analyze_numeric_driver(
            df,
            income_column
        )

        if result:

            result["display_name"] = (
                "Monthly Income"
            )

            result["type"] = "Numeric"

            candidates.append(result)

    # ------------------------------------------------------
    # CREATE FINAL SUMMARY
    # ------------------------------------------------------

    if not candidates:
        return pd.DataFrame()

    summary = []

    for candidate in candidates:

        summary.append({
            "Driver": candidate["display_name"],
            "Strength": candidate["strength"],
            "Difference": round(
                candidate["difference"],
                2
            )
        })

    summary_df = pd.DataFrame(
        summary
    )

    strength_order = {
        "Strong": 3,
        "Moderate": 2,
        "Low": 1
    }

    summary_df["Strength_Score"] = (
        summary_df["Strength"]
        .map(strength_order)
    )

    summary_df = (
        summary_df
        .sort_values(
            [
                "Strength_Score",
                "Difference"
            ],
            ascending=False
        )
        .drop(
            columns=["Strength_Score"]
        )
        .reset_index(drop=True)
    )

    return summary_df


# ==========================================================
# GET DRIVER DATA
# ==========================================================

def get_driver_details(df, driver_name):

    df = normalize_attrition(df)

    if driver_name == "Overtime":

        column = find_column(
            df,
            {"overtime"}
        )

        return analyze_categorical_driver(
            df,
            column
        )

    if driver_name == "Job Satisfaction":

        column = find_column(
            df,
            {
                "jobsatisfaction",
                "satisfaction"
            }
        )

        return analyze_categorical_driver(
            df,
            column
        )

    if driver_name == "Department":

        column = find_column(
            df,
            {"department"}
        )

        return analyze_categorical_driver(
            df,
            column
        )

    if driver_name == "Job Role":

        column = find_column(
            df,
            {
                "jobrole",
                "jobtitle",
                "role"
            }
        )

        return analyze_categorical_driver(
            df,
            column
        )

    if driver_name == "Age":

        age_column = find_column(
            df,
            {"age"}
        )

        if age_column is None:
            return None

        temp = df.copy()

        age_values = pd.to_numeric(
            temp[age_column],
            errors="coerce"
        )

        temp["Age_Group"] = pd.cut(
            age_values,
            bins=[
                0,
                25,
                35,
                45,
                55,
                np.inf
            ],
            labels=[
                "18-25",
                "26-35",
                "36-45",
                "46-55",
                "56+"
            ],
            include_lowest=True
        )

        return analyze_categorical_driver(
            temp,
            "Age_Group"
        )

    if driver_name == "Years at Company":

        tenure_column = find_column(
            df,
            {"yearsatcompany"}
        )

        if tenure_column is None:
            return None

        temp = df.copy()

        years = pd.to_numeric(
            temp[tenure_column],
            errors="coerce"
        )

        temp["Tenure_Group"] = pd.cut(
            years,
            bins=[
                -1,
                2,
                5,
                10,
                20,
                np.inf
            ],
            labels=[
                "0-2 Years",
                "3-5 Years",
                "6-10 Years",
                "11-20 Years",
                "20+ Years"
            ]
        )

        return analyze_categorical_driver(
            temp,
            "Tenure_Group"
        )

    if driver_name == "Monthly Income":

        column = find_column(
            df,
            {
                "monthlyincome",
                "income",
                "salary",
                "monthlysalary"
            }
        )

        return analyze_numeric_driver(
            df,
            column
        )["data"]

    return None