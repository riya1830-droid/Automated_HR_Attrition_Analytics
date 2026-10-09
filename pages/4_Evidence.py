import streamlit as st
import pandas as pd
import plotly.express as px

from analytics.root_cause import normalize_attrition

from analytics.evidence import (
    get_root_cause_drivers,
    get_driver_evidence,
    build_evidence_overview,
    get_evidence_summary,
    determine_evidence_strength,
    create_evidence_description,
    get_supporting_signals
)


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Evidence | AI HR Attrition Analytics",
    page_icon="🔬",
    layout="wide"
)


# ==========================================================
# HEADER
# ==========================================================

st.title("🔬 Evidence & Investigation")

st.caption(
    "Validate the potential drivers using employee-level evidence"
)

st.markdown(
    """
    This stage validates the potential drivers identified in
    Root Cause Analysis using employee-level comparisons.
    """
)


# ==========================================================
# GET DATA
# ==========================================================

cleaned_dataset = st.session_state.get(
    "cleaned_dataset"
)

uploaded_dataset = st.session_state.get(
    "uploaded_dataset"
)


if cleaned_dataset is not None:

    df = cleaned_dataset.copy()

elif uploaded_dataset is not None:

    df = uploaded_dataset.copy()

else:

    st.info(
        "📤 Please upload an HR dataset and complete "
        "Data Cleaning first."
    )

    st.stop()


# ==========================================================
# NORMALIZE
# ==========================================================

try:

    df = normalize_attrition(df)

except Exception as e:

    st.error(
        f"❌ Evidence analysis could not start: {e}"
    )

    st.stop()


# ==========================================================
# GET ROOT CAUSE DRIVERS
# ==========================================================

root_cause_drivers = get_root_cause_drivers(
    df
)


if root_cause_drivers.empty:

    st.warning(
        "⚠️ No potential drivers were identified "
        "by Root Cause Analysis."
    )

    st.stop()


# ==========================================================
# SUMMARY
# ==========================================================

summary = get_evidence_summary(
    df
)


# ==========================================================
# KPI CARDS
# ==========================================================

st.subheader("📌 Investigation Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "🔎 Drivers Investigated",
        summary["drivers_investigated"]
    )

with col2:

    st.metric(
        "✅ Supported",
        summary["supported"]
    )

with col3:

    st.metric(
        "🟡 Mixed Evidence",
        summary["mixed"]
    )

with col4:

    st.metric(
        "👥 Employees Left",
        f"{summary['employees_left']:,}"
    )


# ==========================================================
# CONNECTION TO ROOT CAUSE
# ==========================================================

st.info(
    f"🔗 Evidence is validating the "
    f"{len(root_cause_drivers)} potential drivers identified "
    f"in Root Cause Analysis."
)


# ==========================================================
# EVIDENCE OVERVIEW
# ==========================================================

st.markdown("---")

st.subheader("📋 Evidence Overview")

st.caption(
    "The same potential drivers identified in Root Cause Analysis "
    "are now being validated using employee-level evidence."
)


overview = build_evidence_overview(
    df
)


if overview.empty:

    st.warning(
        "No evidence could be generated for the identified drivers."
    )

else:

    st.dataframe(
        overview,
        use_container_width=True,
        hide_index=True
    )


# ==========================================================
# EVIDENCE LEGEND
# ==========================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.success(
        "🟢 **Strong Evidence**\n\n"
        "Large observed difference between employee groups."
    )

with col2:

    st.info(
        "🔵 **Moderate Evidence**\n\n"
        "Noticeable difference that deserves investigation."
    )

with col3:

    st.warning(
        "🟡 **Mixed Evidence**\n\n"
        "Differences are relatively small."
    )


# ==========================================================
# EVIDENCE EXPLORER
# ==========================================================

st.markdown("---")

st.subheader("🔎 Evidence Explorer")

st.caption(
    "Explore the employee-level evidence behind each potential driver."
)


driver_names = list(
    root_cause_drivers["Driver"]
)


selected_driver = st.selectbox(
    "Select a potential driver",
    driver_names
)


# ==========================================================
# ROOT CAUSE SIGNAL
# ==========================================================

selected_row = root_cause_drivers[
    root_cause_drivers["Driver"]
    == selected_driver
]


if not selected_row.empty:

    root_cause_strength = selected_row[
        "Strength"
    ].iloc[0]

else:

    root_cause_strength = "Low"


# ==========================================================
# GET EVIDENCE
# ==========================================================

evidence_df = get_driver_evidence(
    df,
    selected_driver
)


if evidence_df is None or evidence_df.empty:

    st.warning(
        "No detailed evidence is available for this driver."
    )

    st.stop()


evidence_strength = determine_evidence_strength(
    evidence_df
)


# ==========================================================
# DRIVER HEADER
# ==========================================================

col1, col2, col3 = st.columns(
    [4, 2, 2]
)

with col1:

    st.markdown(
        f"### {selected_driver}"
    )

with col2:

    st.caption("Root Cause Signal")

    if root_cause_strength == "Strong":

        st.error(
            "🔴 Strong"
        )

    elif root_cause_strength == "Moderate":

        st.warning(
            "🟠 Moderate"
        )

    else:

        st.info(
            "🟡 Low"
        )

with col3:

    st.caption("Evidence")

    if evidence_strength == "Strong":

        st.error(
            "🔴 Strong"
        )

    elif evidence_strength == "Moderate":

        st.warning(
            "🟠 Moderate"
        )

    elif evidence_strength == "Mixed":

        st.warning(
            "🟡 Mixed"
        )

    else:

        st.info(
            "⚪ No Evidence"
        )


# ==========================================================
# CATEGORICAL DRIVER
# ==========================================================

if "Attrition_Rate" in evidence_df.columns:

    display_df = evidence_df.copy()

    value_column = display_df.columns[0]

    display_df["Group"] = (
        display_df[value_column]
        .astype(str)
    )

    display_df = display_df.sort_values(
        "Attrition_Rate",
        ascending=False
    ).reset_index(drop=True)


    # ------------------------------------------------------
    # TOP / BOTTOM GROUPS
    # ------------------------------------------------------

    highest = display_df.iloc[0]

    lowest = display_df.iloc[-1]

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            "#### 🔴 Highest observed attrition"
        )

        st.metric(
            str(highest["Group"]),
            f"{highest['Attrition_Rate']:.1f}%"
        )

        st.caption(
            f"{int(highest['Employees']):,} employees | "
            f"{int(highest['Employees_Left']):,} left"
        )

    with col2:

        st.markdown(
            "#### 🟢 Lowest observed attrition"
        )

        st.metric(
            str(lowest["Group"]),
            f"{lowest['Attrition_Rate']:.1f}%"
        )

        st.caption(
            f"{int(lowest['Employees']):,} employees | "
            f"{int(lowest['Employees_Left']):,} left"
        )


    # ------------------------------------------------------
    # CHART
    # ------------------------------------------------------

    st.markdown("### 📊 Attrition Comparison")

    fig = px.bar(
        display_df,
        x="Group",
        y="Attrition_Rate",
        text="Attrition_Rate",
        color="Group",
        color_discrete_sequence=(
            px.colors.qualitative.Bold
        ),
        title=(
            f"Observed Attrition by "
            f"{selected_driver}"
        )
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        height=450,
        showlegend=False,
        yaxis_title="Attrition Rate (%)",
        xaxis_title=selected_driver,
        margin=dict(
            t=70,
            l=30,
            r=30,
            b=30
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# NUMERIC DRIVER
# ==========================================================

elif "Average" in evidence_df.columns:

    display_df = evidence_df.copy()

    fig = px.bar(
        display_df,
        x="Attrition_Status",
        y="Average",
        text="Average",
        color="Attrition_Status",
        color_discrete_map={
            "Left": "#e74c3c",
            "Stayed": "#2ecc71"
        },
        title=(
            f"Average {selected_driver}: "
            "Left vs Stayed"
        )
    )

    fig.update_traces(
        texttemplate="%{text:,.1f}",
        textposition="outside"
    )

    fig.update_layout(
        height=450,
        showlegend=False,
        yaxis_title=(
            f"Average {selected_driver}"
        ),
        xaxis_title="Employee Status"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# WHAT THE DATA SHOWS
# ==========================================================

st.markdown("### 💡 What the Data Shows")

description = create_evidence_description(
    selected_driver,
    evidence_df
)

st.info(
    description
)


# ==========================================================
# SUPPORTING SIGNALS
# ==========================================================

st.markdown("### 🔍 Supporting Signals")

signals = get_supporting_signals(
    selected_driver,
    evidence_df
)


if signals:

    for signal in signals:

        st.markdown(
            f"- {signal}"
        )

else:

    st.caption(
        "No additional supporting signals available."
    )


# ==========================================================
# DETAILED EVIDENCE
# ==========================================================

with st.expander(
    "📄 View detailed employee-group evidence"
):

    st.dataframe(
        evidence_df,
        use_container_width=True,
        hide_index=True
    )


# ==========================================================
# BUSINESS CONCLUSION
# ==========================================================

st.markdown("---")

st.subheader("🧠 Business Conclusion")


if evidence_strength == "Strong":

    st.success(
        f"""
        **{selected_driver} shows strong observed evidence
        of an association with employee attrition.**

        This driver deserves priority in further HR investigation
        and What-If scenario analysis.
        """
    )

elif evidence_strength == "Moderate":

    st.info(
        f"""
        **{selected_driver} shows moderate observed evidence
        of an association with employee attrition.**

        The pattern is meaningful enough to investigate alongside
        other employee characteristics.
        """
    )

elif evidence_strength == "Mixed":

    st.warning(
        f"""
        **{selected_driver} shows mixed evidence.**

        The observed difference is relatively small, so this driver
        should not be treated as a primary explanation by itself.
        """
    )

else:

    st.warning(
        f"""
        There is insufficient evidence to draw a meaningful
        conclusion about **{selected_driver}**.
        """
    )


# ==========================================================
# INTERPRETATION NOTE
# ==========================================================

st.markdown("### ⚠️ Important Interpretation")

st.caption(
    "Evidence indicates association, not causation. "
    "A higher attrition rate in one employee group does not prove "
    "that the selected factor directly caused employees to leave."
)


# ==========================================================
# NEXT STAGE
# ==========================================================

st.markdown("---")

st.success(
    "✅ Evidence investigation completed. "
    "Next stage: 🔮 What-If."
)