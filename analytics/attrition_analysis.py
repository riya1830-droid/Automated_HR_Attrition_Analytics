import pandas as pd
import numpy as np


# ==========================================================
# 1. FIND ATTRITION COLUMN
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
# 2. NORMALIZE ATTRITION VALUES
# ==========================================================

def normalize_attrition(df):

    df = df.copy()

    attrition_column = find_attrition_column(df)

    if attrition_column is None:
        raise ValueError(
            "Attrition column was not found in the dataset."
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

    return df


# ==========================================================
# 3. OVERALL ATTRITION SUMMARY
# ==========================================================

def calculate_attrition_summary(df):

    df = normalize_attrition(df)

    total_employees = len(df)

    employees_left = int(
        (df["Attrition_Status"] == "Left").sum()
    )

    employees_stayed = int(
        (df["Attrition_Status"] == "Stayed").sum()
    )

    attrition_rate = (
        employees_left / total_employees * 100
        if total_employees > 0
        else 0
    )

    return {
        "total_employees": total_employees,
        "employees_left": employees_left,
        "employees_stayed": employees_stayed,
        "attrition_rate": attrition_rate
    }


# ==========================================================
# 4. ATTRITION DISTRIBUTION
# ==========================================================

def get_attrition_distribution(df):

    df = normalize_attrition(df)

    result = (
        df["Attrition_Status"]
        .value_counts()
        .reindex(
            ["Stayed", "Left"],
            fill_value=0
        )
        .reset_index()
    )

    result.columns = [
        "Attrition_Status",
        "Employee_Count"
    ]

    return result


# ==========================================================
# 5. ATTRITION BY CATEGORY
# ==========================================================

def attrition_by_category(df, column):

    df = normalize_attrition(df)

    if column not in df.columns:
        return pd.DataFrame()

    working_df = df[
        df[column].notna()
    ].copy()

    if working_df.empty:
        return pd.DataFrame()

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

    result["Employees_Stayed"] = (
        result["Employees"]
        - result["Employees_Left"]
    )

    result["Attrition_Rate"] = (
        result["Employees_Left"]
        / result["Employees"]
        * 100
    )

    result = result.sort_values(
        "Attrition_Rate",
        ascending=False
    ).reset_index(drop=True)

    return result


# ==========================================================
# 6. CREATE AGE GROUPS
# ==========================================================

def create_age_groups(df):

    df = df.copy()

    age_column = None

    for column in df.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
        )

        if normalized == "age":
            age_column = column
            break

    if age_column is None:
        return df

    age_values = pd.to_numeric(
        df[age_column],
        errors="coerce"
    )

    df["Age_Group"] = pd.cut(
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

    return df


# ==========================================================
# 7. CREATE TENURE GROUPS
# ==========================================================

def create_tenure_groups(df):

    df = df.copy()

    years_column = None

    for column in df.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
        )

        if normalized == "yearsatcompany":
            years_column = column
            break

    if years_column is None:
        return df

    years = pd.to_numeric(
        df[years_column],
        errors="coerce"
    )

    df["Years_At_Company_Group"] = pd.cut(
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

    return df


# ==========================================================
# 8. ATTRITION BY AGE GROUP
# ==========================================================

def get_attrition_by_age_group(df):

    df = create_age_groups(df)

    if "Age_Group" not in df.columns:
        return pd.DataFrame()

    return attrition_by_category(
        df,
        "Age_Group"
    )


# ==========================================================
# 9. ATTRITION BY TENURE
# ==========================================================

def get_attrition_by_tenure(df):

    df = create_tenure_groups(df)

    if "Years_At_Company_Group" not in df.columns:
        return pd.DataFrame()

    return attrition_by_category(
        df,
        "Years_At_Company_Group"
    )


# ==========================================================
# 10. NUMERIC ATTRITION COMPARISON
# ==========================================================

def numeric_attrition_comparison(df, column):

    df = normalize_attrition(df)

    if column not in df.columns:
        return pd.DataFrame()

    working_df = df.copy()

    working_df[column] = pd.to_numeric(
        working_df[column],
        errors="coerce"
    )

    working_df = working_df.dropna(
        subset=[column]
    )

    if working_df.empty:
        return pd.DataFrame()

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

    result["Average"] = (
        result["Average"].round(2)
    )

    result["Median"] = (
        result["Median"].round(2)
    )

    return result


# ==========================================================
# 11. FIND COLUMN BY NORMALIZED NAME
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
# 12. HR ANALYSIS
# ==========================================================

def get_hr_analysis(df):

    df = normalize_attrition(df)

    analysis = {}

    # ------------------------------------------------------
    # Department
    # ------------------------------------------------------

    department_column = find_column(
        df,
        {"department"}
    )

    if department_column:

        analysis["department"] = (
            attrition_by_category(
                df,
                department_column
            )
        )


    # ------------------------------------------------------
    # Job Role
    # ------------------------------------------------------

    job_role_column = find_column(
        df,
        {
            "jobrole",
            "jobtitle",
            "role"
        }
    )

    if job_role_column:

        analysis["job_role"] = (
            attrition_by_category(
                df,
                job_role_column
            )
        )


    # ------------------------------------------------------
    # Overtime
    # ------------------------------------------------------

    overtime_column = find_column(
        df,
        {"overtime"}
    )

    if overtime_column:

        analysis["overtime"] = (
            attrition_by_category(
                df,
                overtime_column
            )
        )


    # ------------------------------------------------------
    # Age Group
    # ------------------------------------------------------

    age_analysis = (
        get_attrition_by_age_group(df)
    )

    if not age_analysis.empty:

        analysis["age_group"] = age_analysis


    # ------------------------------------------------------
    # Tenure
    # ------------------------------------------------------

    tenure_analysis = (
        get_attrition_by_tenure(df)
    )

    if not tenure_analysis.empty:

        analysis["tenure"] = tenure_analysis


    # ------------------------------------------------------
    # Job Satisfaction
    # ------------------------------------------------------

    satisfaction_column = find_column(
        df,
        {
            "jobsatisfaction",
            "satisfaction"
        }
    )

    if satisfaction_column:

        analysis["job_satisfaction"] = (
            attrition_by_category(
                df,
                satisfaction_column
            )
        )


    # ------------------------------------------------------
    # Monthly Income
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

        analysis["monthly_income"] = (
            numeric_attrition_comparison(
                df,
                income_column
            )
        )


    return analysis


# ==========================================================
# 13. BUSINESS FINDINGS
# ==========================================================

def generate_attrition_findings(df):

    df = normalize_attrition(df)

    findings = []

    summary = calculate_attrition_summary(df)

    # ------------------------------------------------------
    # Overall
    # ------------------------------------------------------

    findings.append(
        f"Overall employee attrition is "
        f"{summary['attrition_rate']:.1f}%, with "
        f"{summary['employees_left']:,} employees leaving."
    )


    # ------------------------------------------------------
    # Department
    # ------------------------------------------------------

    department_column = find_column(
        df,
        {"department"}
    )

    if department_column:

        department_data = (
            attrition_by_category(
                df,
                department_column
            )
        )

        if not department_data.empty:

            highest = department_data.iloc[0]

            findings.append(
                f"{highest[department_column]} has the "
                f"highest department-level attrition rate "
                f"at {highest['Attrition_Rate']:.1f}%."
            )


    # ------------------------------------------------------
    # Overtime
    # ------------------------------------------------------

    overtime_column = find_column(
        df,
        {"overtime"}
    )

    if overtime_column:

        overtime_data = (
            attrition_by_category(
                df,
                overtime_column
            )
        )

        if not overtime_data.empty:

            highest = overtime_data.iloc[0]

            findings.append(
                f"Employees in the "
                f"{highest[overtime_column]} overtime group "
                f"show the highest attrition rate at "
                f"{highest['Attrition_Rate']:.1f}%."
            )


    # ------------------------------------------------------
    # Age
    # ------------------------------------------------------

    age_data = (
        get_attrition_by_age_group(df)
    )

    if not age_data.empty:

        highest_age = age_data.iloc[0]

        findings.append(
            f"The {highest_age['Age_Group']} age group "
            f"has the highest observed attrition rate at "
            f"{highest_age['Attrition_Rate']:.1f}%."
        )


    # ------------------------------------------------------
    # Tenure
    # ------------------------------------------------------

    tenure_data = (
        get_attrition_by_tenure(df)
    )

    if not tenure_data.empty:

        highest_tenure = tenure_data.iloc[0]

        findings.append(
            f"The "
            f"{highest_tenure['Years_At_Company_Group']} "
            f"tenure group has the highest observed "
            f"attrition rate at "
            f"{highest_tenure['Attrition_Rate']:.1f}%."
        )


    return findings