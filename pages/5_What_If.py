import streamlit as st
import pandas as pd
import plotly.express as px

from analytics.root_cause import normalize_attrition

from analytics.evidence import (
    get_root_cause_drivers
)

from analytics.what_if import (
    run_what_if,
    get_driver_column
)


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="What-If | AI HR Attrition Analytics",
    page_icon="🔮",
    layout="wide"
)


# ==========================================================
# HEADER
# ==========================================================

st.title("🔮 What-If Analysis")

st.caption(
    "Explore how changing an evidence-backed employee factor "
    "could affect predicted attrition risk."
)

st.markdown(
    """
    This stage uses a machine-learning model to estimate how
    predicted attrition risk changes under a selected scenario.
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

    df = normalize_attrition(
        df
    )

except Exception as e:

    st.error(
        f"❌ What-If analysis could not start: {e}"
    )

    st.stop()


# ==========================================================
# GET ROOT CAUSE DRIVERS
# ==========================================================

root_cause_drivers = (
    get_root_cause_drivers(
        df
    )
)


if root_cause_drivers.empty:

    st.warning(
        "⚠️ No potential drivers were identified."
    )

    st.stop()


# ==========================================================
# GET DRIVER NAMES
# ==========================================================

driver_names = list(
    root_cause_drivers["Driver"]
)


# ==========================================================
# SCENARIO BUILDER
# ==========================================================

st.subheader("🎛️ Scenario Builder")

st.caption(
    "Only drivers identified by Root Cause Analysis are available."
)


selected_driver = st.selectbox(
    "Select an evidence-backed driver",
    driver_names
)


driver_column = get_driver_column(
    df,
    selected_driver
)


if driver_column is None:

    st.error(
        f"Column for {selected_driver} "
        "was not found."
    )

    st.stop()


# ==========================================================
# SCENARIO INPUT
# ==========================================================

scenario_value = None


if selected_driver == "Overtime":

    current_values = (
        df[driver_column]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    preferred = [
        value
        for value in ["Yes", "No"]
        if value in current_values
    ]

    options = (
        preferred
        if preferred
        else sorted(current_values)
    )

    scenario_value = st.selectbox(
        "Scenario Overtime",
        options
    )


elif selected_driver == "Job Satisfaction":

    numeric_values = pd.to_numeric(
        df[driver_column],
        errors="coerce"
    ).dropna()

    if numeric_values.empty:

        st.warning(
            "No numeric Job Satisfaction values available."
        )

        st.stop()

    minimum = int(
        numeric_values.min()
    )

    maximum = int(
        numeric_values.max()
    )

    median = int(
        numeric_values.median()
    )

    scenario_value = st.slider(
        "Scenario Job Satisfaction",
        min_value=minimum,
        max_value=maximum,
        value=median,
        step=1
    )


elif selected_driver == "Department":

    options = (
        df[driver_column]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    options = sorted(options)

    scenario_value = st.selectbox(
        "Scenario Department",
        options
    )


elif selected_driver == "Job Role":

    options = (
        df[driver_column]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    options = sorted(options)

    scenario_value = st.selectbox(
        "Scenario Job Role",
        options
    )


elif selected_driver == "Age":

    age_groups = [
        "18-25",
        "26-35",
        "36-45",
        "46-55",
        "56+"
    ]

    scenario_value = st.selectbox(
        "Scenario Age Group",
        age_groups
    )


elif selected_driver == "Years at Company":

    tenure_groups = [
        "0-2 Years",
        "3-5 Years",
        "6-10 Years",
        "11-20 Years",
        "20+ Years"
    ]

    scenario_value = st.selectbox(
        "Scenario Tenure",
        tenure_groups
    )


elif selected_driver == "Monthly Income":

    numeric_values = pd.to_numeric(
        df[driver_column],
        errors="coerce"
    ).dropna()

    if numeric_values.empty:

        st.warning(
            "No numeric income values available."
        )

        st.stop()

    minimum = float(
        numeric_values.min()
    )

    maximum = float(
        numeric_values.max()
    )

    median = float(
        numeric_values.median()
    )

    scenario_value = st.number_input(
        "Scenario Monthly Income",
        min_value=minimum,
        max_value=maximum,
        value=median,
        step=500.0
    )


# ==========================================================
# RUN BUTTON
# ==========================================================

st.markdown("")

run_scenario = st.button(
    "🔮 Run What-If Scenario",
    type="primary",
    use_container_width=True
)


# ==========================================================
# RUN ANALYSIS
# ==========================================================

if run_scenario:

    with st.spinner(
        "Training the attrition model and running the scenario..."
    ):

        try:

            results = run_what_if(
                df,
                selected_driver,
                scenario_value
            )

            st.session_state[
                "what_if_results"
            ] = results

            st.session_state[
                "what_if_driver"
            ] = selected_driver

            st.session_state[
                "what_if_scenario"
            ] = scenario_value

        except Exception as e:

            st.error(
                f"❌ What-If analysis failed: {e}"
            )

            st.stop()


# ==========================================================
# GET SAVED RESULTS
# ==========================================================

results = st.session_state.get(
    "what_if_results"
)

saved_driver = st.session_state.get(
    "what_if_driver"
)

saved_scenario = st.session_state.get(
    "what_if_scenario"
)


if results is None:

    st.info(
        "👆 Select a driver and scenario, then click "
        "**Run What-If Scenario** to see the estimated impact."
    )

    st.stop()


# ==========================================================
# RESULTS HEADER
# ==========================================================

st.markdown("---")

st.subheader("📊 Scenario Results")

st.info(
    f"Scenario tested: **{saved_driver} → "
    f"{saved_scenario}**"
)


# ==========================================================
# KPI CARDS
# ==========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "🔴 Current High-Risk",
        f"{results['current_high']:,}"
    )

with col2:

    st.metric(
        "🟢 Scenario High-Risk",
        f"{results['scenario_high']:,}"
    )

with col3:

    st.metric(
        "📉 High-Risk Reduction",
        f"{results['high_risk_reduction']:,}"
    )

with col4:

    st.metric(
        "📊 Average Risk Change",
        f"{results['risk_change']:.1f} pp"
    )


# ==========================================================
# RISK COMPARISON
# ==========================================================

st.markdown("### 📈 Current vs Scenario Risk")

comparison_df = pd.DataFrame({
    "Scenario": [
        "Current",
        "What-If"
    ],

    "Average Risk": [
        results["current_average"],
        results["scenario_average"]
    ]
})


fig = px.bar(
    comparison_df,
    x="Scenario",
    y="Average Risk",
    text="Average Risk",
    color="Scenario",
    color_discrete_sequence=(
        px.colors.qualitative.Bold
    ),
    title="Average Predicted Attrition Risk"
)


fig.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="outside"
)


fig.update_layout(
    height=450,
    showlegend=False,
    yaxis_title="Average Predicted Risk (%)",
    xaxis_title=""
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ==========================================================
# HIGH-RISK COMPARISON
# ==========================================================

st.markdown("### 👥 High-Risk Employee Comparison")

high_risk_df = pd.DataFrame({
    "Scenario": [
        "Current",
        "What-If"
    ],

    "High-Risk Employees": [
        results["current_high"],
        results["scenario_high"]
    ]
})


fig2 = px.bar(
    high_risk_df,
    x="Scenario",
    y="High-Risk Employees",
    text="High-Risk Employees",
    color="Scenario",
    color_discrete_sequence=(
        px.colors.qualitative.Safe
    ),
    title="Predicted High-Risk Employees"
)


fig2.update_traces(
    texttemplate="%{text:,}",
    textposition="outside"
)


fig2.update_layout(
    height=450,
    showlegend=False,
    yaxis_title="Employees",
    xaxis_title=""
)


st.plotly_chart(
    fig2,
    use_container_width=True
)


# ==========================================================
# BUSINESS INTERPRETATION
# ==========================================================

st.markdown("---")

st.subheader("🧠 Business Interpretation")


if results["risk_change"] > 0:

    st.success(
        f"""
        The **{saved_driver} → {saved_scenario}** scenario produces
        a lower average predicted attrition risk.

        The model estimates an average reduction of
        **{results['risk_change']:.1f} percentage points**,
        with **{results['high_risk_reduction']:,} fewer employees**
        classified as high-risk.
        """
    )

elif results["risk_change"] < 0:

    st.warning(
        f"""
        The **{saved_driver} → {saved_scenario}** scenario produces
        a higher average predicted attrition risk.

        The model estimates an increase of
        **{abs(results['risk_change']):.1f} percentage points**.
        """
    )

else:

    st.info(
        f"""
        The **{saved_driver} → {saved_scenario}** scenario produces
        little or no change in average predicted attrition risk.
        """
    )


# ==========================================================
# MODEL INFORMATION
# ==========================================================

with st.expander("🤖 View model information"):

    if results["auc"] is not None:

        st.write(
            f"**Model:** Logistic Regression"
        )

        st.write(
            f"**Validation ROC-AUC:** "
            f"{results['auc']:.3f}"
        )

        st.caption(
            "ROC-AUC indicates how well the model separates "
            "employees who left from employees who stayed. "
            "It is a validation metric, not a guarantee of prediction accuracy."
        )

    else:

        st.write(
            "**Model:** Logistic Regression"
        )

        st.caption(
            "Validation ROC-AUC could not be calculated."
        )


# ==========================================================
# IMPORTANT INTERPRETATION
# ==========================================================

st.markdown("---")

st.subheader("⚠️ Important Interpretation")

st.warning(
    """
    What-If results are **model-based scenario estimates**.
    They do not guarantee that changing a factor will actually
    prevent employee attrition.

    The scenario assumes other employee characteristics remain
    unchanged while the selected factor is modified.
    """
)


# ==========================================================
# NEXT STAGE
# ==========================================================

st.markdown("---")

st.success(
    "✅ What-If scenario analysis completed. "
    "Next stage: 💡 Recommendations."
)