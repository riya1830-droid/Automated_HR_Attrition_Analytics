import pandas as pd
import numpy as np

from analytics.root_cause import (
    find_column,
    normalize_attrition,
    get_driver_summary,
    get_driver_details
)


# ==========================================================
# EVIDENCE STRENGTH
# ==========================================================

def determine_evidence_strength(evidence_df):

    if evidence_df is None or evidence_df.empty:
        return "No Evidence"

    if "Attrition_Rate" in evidence_df.columns:

        rates = pd.to_numeric(
            evidence_df["Attrition_Rate"],
            errors="coerce"
        ).dropna()

        if len(rates) < 2:
            return "No Evidence"

        difference = rates.max() - rates.min()

    elif "Average" in evidence_df.columns:

        averages = pd.to_numeric(
            evidence_df["Average"],
            errors="coerce"
        ).dropna()

        if len(averages) < 2:
            return "No Evidence"

        difference = abs(
            averages.max() - averages.min()
        )

        mean_value = averages.mean()

        if mean_value != 0:
            difference = (
                difference
                / abs(mean_value)
                * 100
            )
        else:
            difference = 0

    else:
        return "No Evidence"

    if difference >= 15:
        return "Strong"

    elif difference >= 7:
        return "Moderate"

    else:
        return "Mixed"


# ==========================================================
# GET ROOT CAUSE DRIVERS
# ==========================================================

def get_root_cause_drivers(df):

    """
    Gets the exact same potential drivers
    identified by the Root Cause stage.
    """

    try:

        driver_summary = get_driver_summary(df)

        if driver_summary is None:
            return pd.DataFrame()

        if driver_summary.empty:
            return pd.DataFrame()

        return driver_summary.copy()

    except Exception:

        return pd.DataFrame()


# ==========================================================
# GET DRIVER EVIDENCE
# ==========================================================

def get_driver_evidence(df, driver_name):

    """
    Gets detailed evidence for one of the drivers
    already identified by Root Cause.
    """

    try:

        details = get_driver_details(
            df,
            driver_name
        )

        if details is None:
            return None

        return details.copy()

    except Exception:

        return None


# ==========================================================
# CREATE BUSINESS DESCRIPTION
# ==========================================================

def create_evidence_description(
    driver_name,
    evidence_df
):

    if evidence_df is None or evidence_df.empty:

        return (
            f"No sufficient employee-level evidence "
            f"was available for {driver_name}."
        )

    # ------------------------------------------------------
    # CATEGORICAL DRIVER
    # ------------------------------------------------------

    if "Attrition_Rate" in evidence_df.columns:

        value_column = evidence_df.columns[0]

        working_df = evidence_df.copy()

        working_df = working_df.sort_values(
            "Attrition_Rate",
            ascending=False
        ).reset_index(drop=True)

        highest = working_df.iloc[0]
        lowest = working_df.iloc[-1]

        highest_group = str(
            highest[value_column]
        )

        lowest_group = str(
            lowest[value_column]
        )

        highest_rate = float(
            highest["Attrition_Rate"]
        )

        lowest_rate = float(
            lowest["Attrition_Rate"]
        )

        gap = abs(
            highest_rate - lowest_rate
        )

        return (
            f"{highest_group} shows the highest observed "
            f"attrition rate at {highest_rate:.1f}%, "
            f"compared with {lowest_group} at "
            f"{lowest_rate:.1f}%. The observed difference "
            f"is approximately {gap:.1f} percentage points."
        )

    # ------------------------------------------------------
    # NUMERIC DRIVER
    # ------------------------------------------------------

    if "Average" in evidence_df.columns:

        working_df = evidence_df.copy()

        left = working_df[
            working_df["Attrition_Status"] == "Left"
        ]

        stayed = working_df[
            working_df["Attrition_Status"] == "Stayed"
        ]

        if left.empty or stayed.empty:

            return (
                f"Employee-level evidence for "
                f"{driver_name} is limited."
            )

        left_average = float(
            left["Average"].iloc[0]
        )

        stayed_average = float(
            stayed["Average"].iloc[0]
        )

        difference = abs(
            left_average - stayed_average
        )

        if stayed_average != 0:

            percentage_difference = (
                difference
                / abs(stayed_average)
                * 100
            )

        else:

            percentage_difference = 0

        return (
            f"Employees who left had an average "
            f"{driver_name.lower()} of {left_average:,.1f}, "
            f"compared with {stayed_average:,.1f} for employees "
            f"who stayed. The observed difference is "
            f"{percentage_difference:.1f}%."
        )

    return (
        f"Employee-level evidence for {driver_name} "
        f"could not be summarized."
    )


# ==========================================================
# SUPPORTING SIGNALS
# ==========================================================

def get_supporting_signals(
    driver_name,
    evidence_df
):

    signals = []

    if evidence_df is None or evidence_df.empty:

        return signals

    # ------------------------------------------------------
    # CATEGORICAL
    # ------------------------------------------------------

    if "Attrition_Rate" in evidence_df.columns:

        value_column = evidence_df.columns[0]

        working_df = evidence_df.copy()

        working_df = working_df.sort_values(
            "Attrition_Rate",
            ascending=False
        ).reset_index(drop=True)

        highest = working_df.iloc[0]
        lowest = working_df.iloc[-1]

        gap = abs(
            float(highest["Attrition_Rate"])
            - float(lowest["Attrition_Rate"])
        )

        signals.append(
            f"Highest observed group: "
            f"{highest[value_column]} "
            f"({highest['Attrition_Rate']:.1f}% attrition)"
        )

        signals.append(
            f"Lowest observed group: "
            f"{lowest[value_column]} "
            f"({lowest['Attrition_Rate']:.1f}% attrition)"
        )

        signals.append(
            f"Observed gap: {gap:.1f} percentage points"
        )

        if "Employees" in evidence_df.columns:

            total_employees = int(
                evidence_df["Employees"].sum()
            )

            signals.append(
                f"Employees represented: "
                f"{total_employees:,}"
            )

    # ------------------------------------------------------
    # NUMERIC
    # ------------------------------------------------------

    elif "Average" in evidence_df.columns:

        left = evidence_df[
            evidence_df["Attrition_Status"] == "Left"
        ]

        stayed = evidence_df[
            evidence_df["Attrition_Status"] == "Stayed"
        ]

        if not left.empty and not stayed.empty:

            left_average = float(
                left["Average"].iloc[0]
            )

            stayed_average = float(
                stayed["Average"].iloc[0]
            )

            difference = abs(
                left_average - stayed_average
            )

            signals.append(
                f"Average for employees who left: "
                f"{left_average:,.1f}"
            )

            signals.append(
                f"Average for employees who stayed: "
                f"{stayed_average:,.1f}"
            )

            signals.append(
                f"Observed average difference: "
                f"{difference:,.1f}"
            )

    return signals


# ==========================================================
# BUILD EVIDENCE OVERVIEW
# ==========================================================

def build_evidence_overview(df):

    """
    IMPORTANT:
    This function does NOT discover new drivers.

    It validates only the drivers already identified
    by Root Cause Analysis.
    """

    root_cause_drivers = get_root_cause_drivers(
        df
    )

    if root_cause_drivers.empty:

        return pd.DataFrame()

    rows = []

    for _, driver_row in root_cause_drivers.iterrows():

        driver_name = driver_row["Driver"]

        evidence_df = get_driver_evidence(
            df,
            driver_name
        )

        strength = determine_evidence_strength(
            evidence_df
        )

        description = create_evidence_description(
            driver_name,
            evidence_df
        )

        rows.append({
            "Driver": driver_name,
            "Root Cause Signal": driver_row["Strength"],
            "Evidence": strength,
            "What the data shows": description
        })

    return pd.DataFrame(rows)


# ==========================================================
# EVIDENCE SUMMARY
# ==========================================================

def get_evidence_summary(df):

    overview = build_evidence_overview(
        df
    )

    df = normalize_attrition(df)

    employees_left = int(
        (
            df["Attrition_Status"] == "Left"
        ).sum()
    )

    drivers_investigated = len(
        overview
    )

    supported = 0
    mixed = 0

    if not overview.empty:

        supported = int(
            overview["Evidence"]
            .isin(
                ["Strong", "Moderate"]
            )
            .sum()
        )

        mixed = int(
            (
                overview["Evidence"]
                == "Mixed"
            ).sum()
        )

    return {
        "drivers_investigated":
            drivers_investigated,

        "supported":
            supported,

        "mixed":
            mixed,

        "employees_left":
            employees_left
    }