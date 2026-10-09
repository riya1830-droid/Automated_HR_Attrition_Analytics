import re
import pandas as pd

from analytics.evidence import (
    get_root_cause_drivers,
    build_evidence_overview,
)


RECOMMENDATION_LIBRARY = {
    "Overtime": {
        "action": "Review workload, overtime frequency, staffing, and employee feedback.",
        "reason": "Determine whether workload pressure is associated with higher attrition.",
        "owner": "HR and Department Managers",
        "timeframe": "30–60 days",
        "steps": [
            "Investigate overtime patterns and workload distribution.",
            "Discuss workload concerns with affected teams.",
            "Test appropriate workload or staffing changes.",
            "Review overtime and attrition trends after implementation.",
        ],
        "metric": "Overtime frequency and subsequent attrition rate",
    },
    "Job Satisfaction": {
        "action": "Investigate satisfaction concerns involving management, workload, recognition, and career development.",
        "reason": "Identify workplace concerns that may be associated with employee exits.",
        "owner": "HR and People Managers",
        "timeframe": "30–60 days",
        "steps": [
            "Review satisfaction scores and response counts.",
            "Collect confidential employee feedback.",
            "Agree on improvements with the relevant managers.",
            "Repeat the satisfaction review and monitor attrition.",
        ],
        "metric": "Satisfaction score and subsequent attrition rate",
    },
    "Department": {
        "action": "Compare staffing, workload, management practices, and development opportunities across departments.",
        "reason": "Identify department-specific retention challenges.",
        "owner": "HR Business Partner",
        "timeframe": "30–60 days",
        "steps": [
            "Compare department-level attrition and employee counts.",
            "Review staffing and employee feedback in priority departments.",
            "Agree on department-specific actions.",
            "Compare subsequent attrition across departments.",
        ],
        "metric": "Department-level attrition and employee feedback",
    },
    "Job Role": {
        "action": "Review role-specific workload, career progression, training, and compensation.",
        "reason": "Identify retention challenges that differ by job role.",
        "owner": "HR and Functional Managers",
        "timeframe": "30–90 days",
        "steps": [
            "Identify roles with elevated attrition and adequate sample sizes.",
            "Review role expectations, workload, and development options.",
            "Agree on targeted improvements with role managers.",
            "Track retention and internal mobility.",
        ],
        "metric": "Role-level attrition and internal mobility",
    },
    "Age": {
        "action": "Review career development, onboarding, flexibility, and employee feedback across age groups.",
        "reason": "Explore whether observed differences coincide with career stage or other workplace factors.",
        "owner": "HR",
        "timeframe": "30–90 days",
        "steps": [
            "Check age-group counts and attrition rates.",
            "Review relevant tenure and job-role differences.",
            "Offer fair, consistent support based on employee needs.",
            "Monitor retention without stereotyping employees.",
        ],
        "metric": "Retention and development participation by group",
    },
    "Years at Company": {
        "action": "Review onboarding, recognition, career progression, and support across tenure groups.",
        "reason": "Identify retention challenges at particular stages of employment.",
        "owner": "HR and People Managers",
        "timeframe": "30–90 days",
        "steps": [
            "Identify tenure groups with elevated attrition.",
            "Review onboarding and career progression experiences.",
            "Develop suitable support or development plans.",
            "Track retention by tenure group.",
        ],
        "metric": "Retention by tenure group and internal promotions",
    },
    "Monthly Income": {
        "action": "Review compensation fairness by role, experience, responsibility, and relevant market benchmarks.",
        "reason": "Check whether pay differences coincide with attrition patterns.",
        "owner": "HR and Compensation Team",
        "timeframe": "30–90 days",
        "steps": [
            "Compare income bands, employee counts, and attrition.",
            "Account for job role, experience, and responsibility.",
            "Review pay-equity and market-benchmark findings.",
            "Monitor retention after any justified changes.",
        ],
        "metric": "Pay-equity indicators and subsequent attrition",
    },
}


ALIASES = {
    "Attrition": ["attrition", "attrition_status", "left", "employee_attrition"],
    "Overtime": ["overtime", "over_time"],
    "Job Satisfaction": ["jobsatisfaction", "job_satisfaction", "satisfaction"],
    "Department": ["department", "dept"],
    "Job Role": ["jobrole", "job_role", "role"],
    "Age": ["age"],
    "Years at Company": ["yearsatcompany", "years_at_company", "tenure"],
    "Monthly Income": ["monthlyincome", "monthly_income", "income"],
}


def _normalise_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _find_column(df, aliases):
    lookup = {_normalise_name(col): col for col in df.columns}

    for alias in aliases:
        if _normalise_name(alias) in lookup:
            return lookup[_normalise_name(alias)]

    return None


def _find_driver_column(df, driver):
    return _find_column(df, ALIASES.get(driver, [driver]))


def _normalise_attrition(series):
    values = series.astype(str).str.strip().str.lower()

    left_values = {
        "yes", "left", "true", "1", "1.0",
        "attrition", "resigned", "exited"
    }
    stayed_values = {
        "no", "stayed", "false", "0", "0.0",
        "retained", "active"
    }

    result = pd.Series(index=series.index, dtype="object")
    result.loc[values.isin(left_values)] = "Left"
    result.loc[values.isin(stayed_values)] = "Stayed"

    return result


def _display_group(driver, value, unique_values):
    if pd.isna(value):
        return "Unknown"

    if driver == "Job Satisfaction":
        try:
            number = float(value)
            observed = sorted(
                pd.to_numeric(pd.Series(unique_values), errors="coerce")
                .dropna().unique()
            )

            # Use descriptive labels only when the data confirms a 1–4 scale.
            if observed == [1, 2, 3, 4]:
                labels = {
                    1: "1 — Lowest satisfaction",
                    2: "2 — Low-to-moderate satisfaction",
                    3: "3 — Moderate-to-high satisfaction",
                    4: "4 — Highest satisfaction",
                }
                return labels.get(int(number), str(value))
        except (ValueError, TypeError):
            pass

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)


def _get_focus_group(df, driver, attrition_col):
    driver_col = _find_driver_column(df, driver)

    if driver_col is None or attrition_col is None:
        return {
            "Focus Group": "Not available",
            "Focus Employees": 0,
            "Focus Employees Left": 0,
            "Focus Attrition Rate": None,
            "Focus Group Note": "Required columns were not found.",
        }

    working = pd.DataFrame({
        "group": df[driver_col],
        "attrition": _normalise_attrition(df[attrition_col]),
    })

    working = working.dropna(subset=["attrition"])
    working["group"] = working["group"].where(
        working["group"].notna(), "Unknown"
    )

    # Group numeric drivers into readable bands when they have many values.
    if (
        pd.api.types.is_numeric_dtype(df[driver_col])
        and working["group"].nunique() > 8
    ):
        numeric = pd.to_numeric(working["group"], errors="coerce")
        try:
            working["group"] = pd.qcut(
                numeric,
                q=4,
                duplicates="drop",
            ).astype(str)
            working.loc[numeric.isna(), "group"] = "Unknown"
        except (ValueError, TypeError):
            working["group"] = working["group"].astype(str)
    else:
        unique_values = working["group"].dropna().unique()
        working["group"] = working["group"].apply(
            lambda value: _display_group(driver, value, unique_values)
        )

    summary = (
        working.groupby("group", observed=True)
        .agg(
            Employees=("attrition", "size"),
            Employees_Left=("attrition", lambda x: (x == "Left").sum()),
        )
        .reset_index()
    )

    if summary.empty:
        return {
            "Focus Group": "Not available",
            "Focus Employees": 0,
            "Focus Employees Left": 0,
            "Focus Attrition Rate": None,
            "Focus Group Note": "No usable attrition records were found.",
        }

    summary["Attrition Rate"] = (
        summary["Employees_Left"] / summary["Employees"] * 100
    )

    # Prefer groups with at least 10 employees to reduce tiny-group noise.
    eligible = summary[summary["Employees"] >= 10]
    if eligible.empty:
        eligible = summary

    # Rank by observed rate; retain the group size so the rate is not
    # interpreted without its supporting sample.
    focus = eligible.sort_values(
        ["Attrition Rate", "Employees"],
        ascending=[False, False],
    ).iloc[0]

    return {
        "Focus Group": str(focus["group"]),
        "Focus Employees": int(focus["Employees"]),
        "Focus Employees Left": int(focus["Employees_Left"]),
        "Focus Attrition Rate": round(float(focus["Attrition Rate"]), 1),
        "Focus Group Note": (
            "Highest observed rate among the eligible groups; "
            "this is an association, not proof of causation."
        ),
    }


def assign_priority(root_signal, evidence, focus_employees):
    root_signal = str(root_signal).strip().title()
    evidence = str(evidence).strip().title()

    if (
        root_signal == "Strong"
        and evidence == "Strong"
        and focus_employees >= 30
    ):
        return "High"

    if (
        root_signal in {"Strong", "Moderate"}
        and evidence in {"Strong", "Moderate"}
        and focus_employees >= 15
    ):
        return "Medium"

    return "Monitor"


def build_recommendations(df):
    if df is None or df.empty:
        return pd.DataFrame()

    drivers = get_root_cause_drivers(df)
    evidence_overview = build_evidence_overview(df)

    if drivers is None or drivers.empty:
        return pd.DataFrame()

    if evidence_overview is None or evidence_overview.empty:
        return pd.DataFrame()

    evidence_columns = [
        col for col in ["Driver", "Evidence", "What the data shows"]
        if col in evidence_overview.columns
    ]

    merged = drivers.merge(
        evidence_overview[evidence_columns],
        on="Driver",
        how="left",
    )

    attrition_col = _find_column(df, ALIASES["Attrition"])
    valid_attrition = (
        _normalise_attrition(df[attrition_col])
        if attrition_col else pd.Series(dtype="object")
    )
    valid_attrition = valid_attrition[valid_attrition.isin(["Left", "Stayed"])]

    overall_rate = (
        float((valid_attrition == "Left").mean() * 100)
        if not valid_attrition.empty else None
    )

    rows = []

    for _, row in merged.iterrows():
        driver = row["Driver"]
        recommendation = RECOMMENDATION_LIBRARY.get(driver)

        if recommendation is None:
            continue

        focus = _get_focus_group(df, driver, attrition_col)
        root_signal = str(row.get("Strength", "Low"))
        evidence = str(row.get("Evidence", "Mixed"))

        priority = assign_priority(
            root_signal,
            evidence,
            focus["Focus Employees"],
        )

        focus_rate = focus["Focus Attrition Rate"]

        # Planning goal only: a 10% relative reduction from the observed
        # focus-group baseline. This is not a forecast or guarantee.
        proposed_target = (
            round(focus_rate * 0.90, 1)
            if focus_rate is not None else None
        )

        rows.append({
            "Driver": driver,
            "Root Cause Signal": root_signal,
            "Evidence": evidence,
            "Priority": priority,
            "What the Data Shows": row.get(
                "What the data shows",
                "Evidence summary unavailable.",
            ),
            "Focus Group": focus["Focus Group"],
            "Focus Employees": focus["Focus Employees"],
            "Focus Employees Left": focus["Focus Employees Left"],
            "Focus Attrition Rate": focus_rate,
            "Focus Group Note": focus["Focus Group Note"],
            "Overall Attrition Rate": (
                round(overall_rate, 1)
                if overall_rate is not None else None
            ),
            "Proposed Target Rate": proposed_target,
            "Target Note": (
                "Illustrative planning goal: 10% relative reduction "
                "from the observed focus-group rate; validate feasibility."
            ),
            "Recommended Action": recommendation["action"],
            "Reason": recommendation["reason"],
            "Action Steps": recommendation["steps"],
            "Success Metric": recommendation["metric"],
            "Suggested Owner": recommendation["owner"],
            "Suggested Timeframe": recommendation["timeframe"],
        })

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    priority_order = {"High": 0, "Medium": 1, "Monitor": 2}
    result["_priority_order"] = result["Priority"].map(priority_order)

    return (
        result.sort_values(
            ["_priority_order", "Driver"]
        )
        .drop(columns="_priority_order")
        .reset_index(drop=True)
    )


def get_recommendation_summary(recommendations):
    if recommendations is None or recommendations.empty:
        return {
            "total": 0,
            "high": 0,
            "medium": 0,
            "monitor": 0,
            "drivers_covered": 0,
        }

    return {
        "total": len(recommendations),
        "high": int((recommendations["Priority"] == "High").sum()),
        "medium": int((recommendations["Priority"] == "Medium").sum()),
        "monitor": int((recommendations["Priority"] == "Monitor").sum()),
        "drivers_covered": int(recommendations["Driver"].nunique()),
    }