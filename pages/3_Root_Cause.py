import streamlit as st
import pandas as pd
import plotly.express as px

from analytics.root_cause import (
    normalize_attrition,
    get_driver_summary,
    get_driver_details
)


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Root Cause | AI HR Attrition Analytics",
    page_icon="🕵️",
    layout="wide"
)


# ==========================================================
# HEADER
# ==========================================================

st.title("🕵️ Root Cause Analysis")

st.caption(
    "Which factors appear to be associated with employee attrition?"
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
        f"❌ Root Cause Analysis could not start: {e}"
    )

    st.stop()


# ==========================================================
# DRIVER SUMMARY
# ==========================================================

driver_summary = get_driver_summary(df)


if driver_summary.empty:

    st.warning(
        "⚠️ No suitable HR drivers were found in the dataset."
    )

    st.stop()


# ==========================================================
# KPI CALCULATIONS
# ==========================================================

total_drivers = len(
    driver_summary
)

strong_drivers = int(
    (
        driver_summary["Strength"]
        == "Strong"
    ).sum()
)

moderate_drivers = int(
    (
        driver_summary["Strength"]
        == "Moderate"
    ).sum()
)

employees_left = int(
    (
        df["Attrition_Status"]
        == "Left"
    ).sum()
)


# ==========================================================
# KPI CARDS
# ==========================================================

st.subheader("📌 Investigation Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "🎯 Potential Drivers",
        total_drivers
    )

with col2:

    st.metric(
        "🔴 Strong Drivers",
        strong_drivers
    )

with col3:

    st.metric(
        "🟠 Moderate Drivers",
        moderate_drivers
    )

with col4:

    st.metric(
        "👥 Employees Left",
        f"{employees_left:,}"
    )


# ==========================================================
# DRIVER RANKING
# ==========================================================

st.markdown("---")

st.subheader("🔥 Potential Attrition Drivers")

chart_df = driver_summary.copy()

strength_score = {
    "Strong": 3,
    "Moderate": 2,
    "Low": 1
}

chart_df["Strength_Score"] = (
    chart_df["Strength"]
    .map(strength_score)
)

fig = px.bar(
    chart_df,
    x="Difference",
    y="Driver",
    orientation="h",
    text="Difference",
    color="Strength",
    color_discrete_map={
        "Strong": "#e74c3c",
        "Moderate": "#f39c12",
        "Low": "#3498db"
    },
    title="Relative Strength of Observed Driver Patterns"
)

fig.update_traces(
    texttemplate="%{text:.1f}",
    textposition="outside"
)

fig.update_layout(
    xaxis_title="Observed Difference",
    yaxis_title="Potential Driver",
    height=max(
        400,
        len(chart_df) * 55
    ),
    legend_title="Driver Strength"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ==========================================================
# DRIVER DEEP DIVE
# ==========================================================

st.markdown("---")

st.subheader("🔎 Driver Deep Dive")

top_drivers = driver_summary.head(3)

tabs = st.tabs(
    [
        driver
        for driver in top_drivers["Driver"]
    ]
)


for tab, driver_name in zip(
    tabs,
    top_drivers["Driver"]
):

    with tab:

        details = get_driver_details(
            df,
            driver_name
        )

        if details is None:

            st.info(
                "No detailed analysis is available."
            )

            continue

        # --------------------------------------------------
        # CATEGORICAL DRIVER
        # --------------------------------------------------

        if (
            "Attrition_Rate" in details.columns
        ):

            display_df = details.copy()

            value_column = display_df.columns[0]

            fig = px.bar(
                display_df,
                x=value_column,
                y="Attrition_Rate",
                text="Attrition_Rate",
                color=value_column,
                color_discrete_sequence=(
                    px.colors.qualitative.Bold
                ),
                title=(
                    f"Attrition Rate by "
                    f"{driver_name}"
                )
            )

            fig.update_traces(
                texttemplate="%{text:.1f}%",
                textposition="outside"
            )

            fig.update_layout(
                yaxis_title="Attrition Rate (%)",
                xaxis_title=driver_name,
                height=420,
                showlegend=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # --------------------------------------------------
        # NUMERIC DRIVER
        # --------------------------------------------------

        else:

            display_df = details.copy()

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
                    f"Average {driver_name}: "
                    f"Left vs Stayed"
                )
            )

            fig.update_traces(
                texttemplate="%{text:,.0f}",
                textposition="outside"
            )

            fig.update_layout(
                yaxis_title=f"Average {driver_name}",
                xaxis_title="Employee Status",
                height=420,
                showlegend=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


# ==========================================================
# CANDIDATE MATRIX
# ==========================================================

st.markdown("---")

st.subheader("🧩 Root Cause Candidates")

matrix_df = driver_summary.copy()

matrix_df["Priority"] = (
    matrix_df["Strength"]
    .map({
        "Strong": "🔴 High",
        "Moderate": "🟠 Medium",
        "Low": "🟡 Monitor"
    })
)

matrix_df["Observed Pattern"] = (
    matrix_df["Strength"]
    .map({
        "Strong": "Strong observed association",
        "Moderate": "Moderate observed association",
        "Low": "Limited observed difference"
    })
)

matrix_df = matrix_df[
    [
        "Driver",
        "Observed Pattern",
        "Difference",
        "Priority"
    ]
]

st.dataframe(
    matrix_df,
    use_container_width=True,
    hide_index=True
)


# ==========================================================
# INTERPRETATION NOTE
# ==========================================================

st.markdown("---")

st.warning(
    "⚠️ Potential drivers represent observed associations "
    "in the HR data. They do not prove that a factor directly "
    "causes employee attrition."
)


# ==========================================================
# NEXT STAGE
# ==========================================================

st.markdown("---")

st.success(
    "✅ Root Cause Analysis completed. "
    "Next stage: 🔬 Evidence."
)