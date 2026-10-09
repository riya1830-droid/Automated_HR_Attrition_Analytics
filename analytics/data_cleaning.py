import pandas as pd
import numpy as np


# ==========================================================
# REMOVE DUPLICATE ROWS
# ==========================================================

def remove_duplicate_rows(df):
    """
    Removes exact duplicate rows from the dataset.
    """

    cleaned_df = df.copy()

    before = len(cleaned_df)

    cleaned_df = cleaned_df.drop_duplicates()

    after = len(cleaned_df)

    removed = before - after

    return cleaned_df, removed


# ==========================================================
# STANDARDIZE COLUMN NAMES
# ==========================================================

def standardize_column_names(df):
    """
    Standardizes column names for easier analysis.

    Example:
    Employee ID → employee_id
    Monthly Income → monthly_income
    Attrition → attrition
    """

    cleaned_df = df.copy()

    cleaned_df.columns = (
        cleaned_df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^\w]", "", regex=True)
    )

    return cleaned_df


# ==========================================================
# CONVERT NUMERIC COLUMNS
# ==========================================================

def convert_numeric_columns(df):
    """
    Converts object columns to numeric only when
    at least 95% of their non-null values can safely
    be converted.
    """

    cleaned_df = df.copy()

    converted_columns = []

    for column in cleaned_df.columns:

        if cleaned_df[column].dtype == "object":

            converted = pd.to_numeric(
                cleaned_df[column],
                errors="coerce"
            )

            original_non_null = (
                cleaned_df[column].notna().sum()
            )

            converted_non_null = (
                converted.notna().sum()
            )

            if (
                original_non_null > 0
                and
                converted_non_null
                / original_non_null >= 0.95
            ):

                cleaned_df[column] = converted

                converted_columns.append(column)

    return cleaned_df, converted_columns


# ==========================================================
# CONVERT DATE COLUMNS
# ==========================================================

def convert_date_columns(df):
    """
    Converts columns that clearly appear to contain dates.

    The conversion is conservative to avoid incorrectly
    converting normal HR numeric/categorical fields.
    """

    cleaned_df = df.copy()

    converted_columns = []

    for column in cleaned_df.columns:

        if cleaned_df[column].dtype != "object":
            continue

        column_name = column.lower()

        date_keywords = [
            "date",
            "time",
            "timestamp"
        ]

        if not any(
            keyword in column_name
            for keyword in date_keywords
        ):
            continue

        converted = pd.to_datetime(
            cleaned_df[column],
            errors="coerce"
        )

        original_non_null = (
            cleaned_df[column].notna().sum()
        )

        converted_non_null = (
            converted.notna().sum()
        )

        if (
            original_non_null > 0
            and
            converted_non_null
            / original_non_null >= 0.80
        ):

            cleaned_df[column] = converted

            converted_columns.append(column)

    return cleaned_df, converted_columns


# ==========================================================
# HANDLE MISSING NUMERIC VALUES
# ==========================================================

def fill_numeric_missing_values(df):
    """
    Fills missing numeric values using the median.

    Returns the number of values filled in each column.
    """

    cleaned_df = df.copy()

    filled_columns = []

    filled_values = {}

    numeric_columns = cleaned_df.select_dtypes(
        include=np.number
    ).columns

    for column in numeric_columns:

        missing_count = int(
            cleaned_df[column].isna().sum()
        )

        if missing_count > 0:

            median_value = cleaned_df[column].median()

            if pd.notna(median_value):

                cleaned_df[column] = (
                    cleaned_df[column]
                    .fillna(median_value)
                )

                filled_columns.append(column)

                filled_values[column] = missing_count

    return (
        cleaned_df,
        filled_columns,
        filled_values
    )


# ==========================================================
# HANDLE MISSING CATEGORICAL VALUES
# ==========================================================

def fill_categorical_missing_values(df):
    """
    Fills missing categorical values with 'Unknown'.

    Returns the number of values filled in each column.
    """

    cleaned_df = df.copy()

    filled_columns = []

    filled_values = {}

    categorical_columns = (
        cleaned_df
        .select_dtypes(
            include=["object", "category"]
        )
        .columns
    )

    for column in categorical_columns:

        missing_count = int(
            cleaned_df[column].isna().sum()
        )

        if missing_count > 0:

            cleaned_df[column] = (
                cleaned_df[column]
                .fillna("Unknown")
            )

            filled_columns.append(column)

            filled_values[column] = missing_count

    return (
        cleaned_df,
        filled_columns,
        filled_values
    )


# ==========================================================
# REMOVE EMPTY COLUMNS
# ==========================================================

def remove_empty_columns(df):
    """
    Removes columns containing no usable values.
    """

    cleaned_df = df.copy()

    empty_columns = [
        column
        for column in cleaned_df.columns
        if cleaned_df[column].isna().all()
    ]

    cleaned_df = cleaned_df.drop(
        columns=empty_columns
    )

    return cleaned_df, empty_columns


# ==========================================================
# CLEAN DATASET
# ==========================================================

def clean_dataset(df):
    """
    Runs the complete safe HR data cleaning pipeline.

    The original dataframe is never modified.

    Returns:
        cleaned dataframe
        detailed cleaning report
    """

    cleaned_df = df.copy()

    report = []

    # ======================================================
    # 1. STANDARDIZE COLUMN NAMES
    # ======================================================

    original_columns = list(
        cleaned_df.columns
    )

    cleaned_df = standardize_column_names(
        cleaned_df
    )

    standardized_columns = [
        {
            "Action": "Standardized column name",
            "Column": old,
            "Details": f"{old} → {new}",
            "Values Changed": "-"
        }
        for old, new in zip(
            original_columns,
            cleaned_df.columns
        )
        if old != new
    ]

    report.extend(
        standardized_columns
    )

    # ======================================================
    # 2. REMOVE EMPTY COLUMNS
    # ======================================================

    cleaned_df, empty_columns = (
        remove_empty_columns(
            cleaned_df
        )
    )

    for column in empty_columns:

        report.append({
            "Action": "Removed completely empty column",
            "Column": column,
            "Details": "Column contained no usable values",
            "Values Changed": "-"
        })

    # ======================================================
    # 3. REMOVE DUPLICATE ROWS
    # ======================================================

    before_duplicates = len(
        cleaned_df
    )

    cleaned_df = cleaned_df.drop_duplicates()

    removed_duplicates = (
        before_duplicates
        - len(cleaned_df)
    )

    if removed_duplicates > 0:

        report.append({
            "Action": "Removed duplicate rows",
            "Column": "-",
            "Details": (
                f"{removed_duplicates:,} duplicate rows removed"
            ),
            "Values Changed": removed_duplicates
        })

    # ======================================================
    # 4. CONVERT NUMERIC COLUMNS
    # ======================================================

    cleaned_df, numeric_columns = (
        convert_numeric_columns(
            cleaned_df
        )
    )

    for column in numeric_columns:

        report.append({
            "Action": "Converted column to numeric",
            "Column": column,
            "Details": "Safe numeric conversion",
            "Values Changed": "-"
        })

    # ======================================================
    # 5. CONVERT DATE COLUMNS
    # ======================================================

    cleaned_df, date_columns = (
        convert_date_columns(
            cleaned_df
        )
    )

    for column in date_columns:

        report.append({
            "Action": "Converted column to date",
            "Column": column,
            "Details": "Safe date conversion",
            "Values Changed": "-"
        })

    # ======================================================
    # 6. FILL NUMERIC MISSING VALUES
    # ======================================================

    (
        cleaned_df,
        numeric_missing_columns,
        numeric_missing_values
    ) = fill_numeric_missing_values(
        cleaned_df
    )

    for column in numeric_missing_columns:

        report.append({
            "Action": (
                "Filled missing numeric values"
            ),
            "Column": column,
            "Details": "Median imputation",
            "Values Changed": (
                numeric_missing_values[column]
            )
        })

    # ======================================================
    # 7. FILL CATEGORICAL MISSING VALUES
    # ======================================================

    (
        cleaned_df,
        categorical_missing_columns,
        categorical_missing_values
    ) = fill_categorical_missing_values(
        cleaned_df
    )

    for column in categorical_missing_columns:

        report.append({
            "Action": (
                "Filled missing categorical values"
            ),
            "Column": column,
            "Details": "Replaced with 'Unknown'",
            "Values Changed": (
                categorical_missing_values[column]
            )
        })

    # ======================================================
    # FINAL REPORT
    # ======================================================

    cleaning_report = pd.DataFrame(
        report,
        columns=[
            "Action",
            "Column",
            "Details",
            "Values Changed"
        ]
    )

    return cleaned_df, cleaning_report