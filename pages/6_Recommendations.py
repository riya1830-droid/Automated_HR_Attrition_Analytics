import streamlit as st
import pandas as pd
import plotly.express as px

from analytics.recommendations import (
    build_recommendations,
    get_recommendation_summary,
)


st.set_page_config(
    page_title="HR Recommendations",
    page_icon="💡",
    layout="wide",
)

st.title("💡 HR Recommendations & Action Plan")
st.caption(
    "Turn observed attrition patterns into evidence-informed HR actions "
    "with owners, timelines, and measurable review goals."
)

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------
df = st.session_state.get("cleaned_dataset")

if df is None or not isinstance(df, pd.DataFrame) or df.empty:
    df = st.session_state.get("uploaded_dataset")

if df is None or not isinstance(df, pd.DataFrame) or df.empty:
    st.warning(
        "No HR dataset is available. Upload a dataset and complete "
        "Data Quality and Data Cleaning first."
    )
    st.stop()

recommendations = build_recommendations(df)

if recommendations is None or recommendations.empty:
    st.warning(
        "Recommendations could not be generated. Check that the dataset "
        "contains an attrition column and the required driver columns."
    )
    st.stop()

summary = get_recommendation_summary(recommendations)

# --------------------------------------------------
# 2. KPI CARDS
# --------------------------------------------------
k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Actions", summary["total"])
k2.metric("High Priority", summary["high"])
k3.metric("Medium Priority", summary["medium"])
k4.metric("Drivers Covered", summary["drivers_covered"])

st.divider()

# --------------------------------------------------
# 3. PRIORITY OVERVIEW
# --------------------------------------------------
st.subheader("📊 Recommendation Priority Overview")

priority_order = ["High", "Medium", "Monitor"]
priority_counts = (
    recommendations["Priority"]
    .value_counts()
    .reindex(priority_order, fill_value=0)
    .rename_axis("Priority")
    .reset_index(name="Recommendations")
)

fig = px.bar(
    priority_counts,
    x="Priority",
    y="Recommendations",
    color="Priority",
    text="Recommendations",
    category_orders={"Priority": priority_order},
    color_discrete_map={
        "High": "#E74C3C",
        "Medium": "#F39C12",
        "Monitor": "#3498DB",
    },
    title="Actions by Priority",
)

fig.update_traces(textposition="outside")
fig.update_layout(
    height=350,
    showlegend=False,
    xaxis_title="Priority Level",
    yaxis_title="Number of Recommendations",
    yaxis=dict(dtick=1),
    margin=dict(l=20, r=20, t=60, b=20),
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Priority is a screening aid based on root-cause signal, evidence "
    "strength, and focus-group size. It is not a measure of certainty "
    "that a factor causes attrition."
)

# --------------------------------------------------
# 4. ACTION REGISTER
# --------------------------------------------------
st.subheader("📋 HR Action Register")

display_columns = [
    "Driver",
    "Priority",
    "Root Cause Signal",
    "Evidence",
    "Focus Group",
    "Focus Employees",
    "Focus Attrition Rate",
    "Suggested Owner",
    "Suggested Timeframe",
]

available_columns = [
    col for col in display_columns
    if col in recommendations.columns
]

st.dataframe(
    recommendations[available_columns],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Focus Attrition Rate": st.column_config.NumberColumn(
            "Focus Attrition (%)",
            format="%.1f%%",
        ),
    },
)

st.caption(
    "Focus-group rates are calculated from the observed dataset. "
    "Check the employee count before acting on a high rate."
)

# --------------------------------------------------
# 5. RECOMMENDATION EXPLORER
# --------------------------------------------------
st.divider()
st.subheader("🔎 Recommendation Explorer")

selected_driver = st.selectbox(
    "Choose a driver to investigate",
    options=recommendations["Driver"].tolist(),
    key="recommendation_driver",
)

selected = recommendations.loc[
    recommendations["Driver"] == selected_driver
].iloc[0]

# Status labels
priority = str(selected["Priority"])
if priority == "High":
    st.error("Priority: High — investigate promptly.")
elif priority == "Medium":
    st.warning("Priority: Medium — validate and plan action.")
else:
    st.info("Priority: Monitor — gather more evidence before escalating.")

# Evidence and focus group
left, right = st.columns(2)

with left:
    st.markdown("### 🧾 Evidence")
    st.write(f"**Root Cause Signal:** {selected['Root Cause Signal']}")
    st.write(f"**Evidence Strength:** {selected['Evidence']}")
    st.write(f"**Observed Pattern:** {selected['What the Data Shows']}")

with right:
    st.markdown("### 🎯 Employee Group to Focus On")
    st.write(f"**Group:** {selected['Focus Group']}")
    st.write(f"**Employees in Group:** {selected['Focus Employees']}")
    st.write(
        f"**Employees Who Left:** {selected['Focus Employees Left']}"
    )

    focus_rate = selected["Focus Attrition Rate"]
    if pd.notna(focus_rate):
        st.metric(
            "Observed Group Attrition",
            f"{float(focus_rate):.1f}%",
        )
    else:
        st.write("**Observed Group Attrition:** Not available")

    st.caption(selected["Focus Group Note"])

# Recommended action
st.markdown("### 💡 Recommended HR Action")
st.write(selected["Recommended Action"])
st.write(f"**Why it matters:** {selected['Reason']}")

# Practical action steps
st.markdown("### 🛠️ Suggested Action Plan")

steps = selected["Action Steps"]
for index, step in enumerate(steps, start=1):
    st.markdown(f"**Step {index}.** {step}")

owner_col, time_col = st.columns(2)

with owner_col:
    st.markdown("### 👤 Suggested Owner")
    st.write(selected["Suggested Owner"])

with time_col:
    st.markdown("### 🗓️ Suggested Timeline")
    st.write(selected["Suggested Timeframe"])

# --------------------------------------------------
# 6. SUCCESS TRACKING
# --------------------------------------------------
st.divider()
st.subheader("📈 Success Tracking")

baseline = selected["Focus Attrition Rate"]
target = selected["Proposed Target Rate"]

metric_col, baseline_col, target_col = st.columns(3)

metric_col.markdown("**Metric to Track**")
metric_col.write(selected["Success Metric"])

baseline_col.markdown("**Observed Baseline**")
if pd.notna(baseline):
    baseline_col.metric("Group Attrition", f"{float(baseline):.1f}%")
else:
    baseline_col.write("Not available")

target_col.markdown("**Proposed Planning Goal**")
if pd.notna(target):
    target_col.metric("Illustrative Target", f"{float(target):.1f}%")
else:
    target_col.write("Set a baseline before defining a target.")

st.info(
    f"**Target note:** {selected['Target Note']} "
    "Compare results over a defined review period and account for changes "
    "in workforce composition. This target is not a prediction or guarantee."
)

st.markdown("**Suggested review checkpoints**")
st.markdown(
    "- **Baseline:** Record the current rate and group size.\n"
    "- **30 days:** Confirm investigation findings and agreed actions.\n"
    "- **60–90 days:** Review the metric and compare with the baseline.\n"
    "- **Follow-up:** Continue monitoring before concluding that an action helped."
)

# --------------------------------------------------
# 7. WHAT-IF RESULT INTERPRETATION
# --------------------------------------------------
st.divider()
st.subheader("🔮 What-If Scenario Context")

what_if_results = st.session_state.get("what_if_results")
what_if_driver = st.session_state.get("what_if_driver")

if (
    isinstance(what_if_results, dict)
    and what_if_driver == selected_driver
    and what_if_results.get("risk_change") is not None
):
    risk_change = float(what_if_results["risk_change"])

    if risk_change > 0:
        st.error(
            f"⚠️ The selected scenario increased average predicted risk "
            f"by {risk_change:.1f} percentage points."
        )
        st.write(
            "Interpretation: this particular simulated change is "
            "unfavourable in the current model. It should not be presented "
            "as an improvement."
        )
    elif risk_change < 0:
        st.success(
            f"📉 The selected scenario decreased average predicted risk "
            f"by {abs(risk_change):.1f} percentage points."
        )
        st.write(
            "Interpretation: this scenario is favourable according to the "
            "model estimate, but its real-world effect is not established."
        )
    else:
        st.info(
            "The selected scenario did not change average predicted risk "
            "in the current model."
        )

    st.caption(
        "What-If results are model-based estimates. They do not establish "
        "causality and should be validated before making HR decisions."
    )
else:
    st.info(
        "No matching What-If result is available for this driver in the "
        "current session. Open the What-If page, run a scenario, and return "
        "here to see its interpretation."
    )

# --------------------------------------------------
# 8. DOWNLOAD ACTION REGISTER
# --------------------------------------------------
st.divider()
st.subheader("📥 Export Recommendations")

export_df = recommendations.copy()

# Convert action steps into a readable CSV cell.
if "Action Steps" in export_df.columns:
    export_df["Action Steps"] = export_df["Action Steps"].apply(
        lambda steps: " | ".join(steps)
        if isinstance(steps, list)
        else str(steps)
    )

csv_data = export_df.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="Download HR Action Plan (CSV)",
    data=csv_data,
    file_name="hr_attrition_action_plan.csv",
    mime="text/csv",
)

# --------------------------------------------------
# 9. INTERPRETATION AND NAVIGATION
# --------------------------------------------------
st.divider()
st.markdown("### ⚠️ Important Interpretation Notes")

st.markdown(
    "- Attrition patterns show associations, not proven causes.\n"
    "- Small employee groups can produce unstable rates.\n"
    "- Proposed targets are planning assumptions, not guaranteed results.\n"
    "- HR actions should be fair, privacy-conscious, and reviewed with "
    "appropriate business context.\n"
    "- Validate any model-based recommendation with employee feedback "
    "and real-world results."
)

st.success(
    "Recommendations are ready. Continue to the Final Report page "
    "to consolidate the analysis."
)
