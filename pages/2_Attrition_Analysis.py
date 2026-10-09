import streamlit as st
import pandas as pd
import plotly.express as px

from analytics.attrition_analysis import (
    calculate_attrition_summary,
    get_attrition_distribution,
    get_hr_analysis,
    generate_attrition_findings
)


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Attrition Analysis | AI HR Attrition Analytics",
    page_icon="📊",
    layout="wide"
)


# ==========================================================
# HEADER
# ==========================================================

st.title("📊 Attrition Analysis")

st.caption(
    "What is happening with employee attrition?"
)


# ==========================================================
# CHECK DATA
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

    st.warning(
        "⚠️ Cleaned dataset is not available. "
        "The uploaded dataset is being used instead."
    )

    df = uploaded_dataset.copy()

else:

    st.info(
        "📤 Please upload an HR dataset and complete "
        "Data Cleaning before starting Attrition Analysis."
    )

    st.stop()


# ==========================================================
# SUMMARY
# ==========================================================

try:

    summary = calculate_attrition_summary(df)

except Exception as e:

    st.error(
        f"❌ Unable to perform attrition analysis: {e}"
    )

    st.stop()


# ==========================================================
# WORKFORCE OVERVIEW
# ==========================================================

st.subheader("📌 Workforce Overview")

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        label="👥 Total Employees",
        value=f'{summary["total_employees"]:,}'
    )


with col2:

    st.metric(
        label="🔴 Employees Left",
        value=f'{summary["employees_left"]:,}'
    )


with col3:

    st.metric(
        label="🟢 Employees Stayed",
        value=f'{summary["employees_stayed"]:,}'
    )


with col4:

    st.metric(
        label="📈 Attrition Rate",
        value=f'{summary["attrition_rate"]:.1f}%'
    )


st.markdown("---")


# ==========================================================
# ATTRITION DISTRIBUTION
# ==========================================================

st.subheader("🔴 Attrition Distribution")

distribution = get_attrition_distribution(df)

col1, col2 = st.columns([1, 1])


with col1:

    fig = px.pie(
        distribution,
        names="Attrition_Status",
        values="Employee_Count",
        hole=0.45,
        title="Employees: Stayed vs Left",
        color="Attrition_Status",
        color_discrete_map={
            "Stayed": "#2ecc71",
            "Left": "#e74c3c"
        }
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    fig.update_layout(
        height=430,
        margin=dict(
            t=60,
            b=20,
            l=20,
            r=20
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    st.markdown("### 💡 Overall Observation")

    st.info(
        f"""
        **{summary["employees_left"]:,} employees** have left
        the organization out of **{summary["total_employees"]:,} employees**.

        The observed overall attrition rate is
        **{summary["attrition_rate"]:.1f}%**.

        This stage identifies workforce patterns.
        Potential drivers will be investigated in the
        **Root Cause** and **Evidence** stages.
        """
    )


# ==========================================================
# GET HR ANALYSIS
# ==========================================================

analysis = get_hr_analysis(df)


# ==========================================================
# DEPARTMENT
# ==========================================================

if "department" in analysis:

    st.markdown("---")

    st.subheader("🏢 Attrition by Department")

    department_df = analysis["department"]

    department_column = department_df.columns[0]

    fig = px.bar(
        department_df,
        x=department_column,
        y="Attrition_Rate",
        text="Attrition_Rate",
        title="Attrition Rate by Department",
        color=department_column,
        color_discrete_sequence=px.colors.qualitative.Bold
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        yaxis_title="Attrition Rate (%)",
        xaxis_title="Department",
        height=450,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# JOB ROLE
# ==========================================================

if "job_role" in analysis:

    st.markdown("---")

    st.subheader("💼 Attrition by Job Role")

    job_role_df = analysis["job_role"]

    job_role_column = job_role_df.columns[0]

    fig = px.bar(
        job_role_df,
        x="Attrition_Rate",
        y=job_role_column,
        orientation="h",
        text="Attrition_Rate",
        title="Attrition Rate by Job Role",
        color="Attrition_Rate",
        color_continuous_scale="Turbo"
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        xaxis_title="Attrition Rate (%)",
        yaxis_title="Job Role",
        height=max(
            450,
            len(job_role_df) * 45
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# OVERTIME
# ==========================================================

if "overtime" in analysis:

    st.markdown("---")

    st.subheader("⏰ Attrition by Overtime")

    overtime_df = analysis["overtime"]

    overtime_column = overtime_df.columns[0]

    fig = px.bar(
        overtime_df,
        x=overtime_column,
        y="Attrition_Rate",
        text="Attrition_Rate",
        title="Attrition Rate by Overtime Status",
        color=overtime_column,
        color_discrete_sequence=[
            "#e74c3c",
            "#3498db",
            "#2ecc71"
        ]
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        yaxis_title="Attrition Rate (%)",
        xaxis_title="Overtime",
        height=430,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# AGE GROUP
# ==========================================================

if "age_group" in analysis:

    st.markdown("---")

    st.subheader("🎂 Attrition by Age Group")

    age_df = analysis["age_group"]

    fig = px.bar(
        age_df,
        x="Age_Group",
        y="Attrition_Rate",
        text="Attrition_Rate",
        title="Attrition Rate by Age Group",
        color="Age_Group",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        yaxis_title="Attrition Rate (%)",
        xaxis_title="Age Group",
        height=430,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# TENURE
# ==========================================================

if "tenure" in analysis:

    st.markdown("---")

    st.subheader("📅 Attrition by Years at Company")

    tenure_df = analysis["tenure"]

    fig = px.bar(
        tenure_df,
        x="Years_At_Company_Group",
        y="Attrition_Rate",
        text="Attrition_Rate",
        title="Attrition Rate by Employee Tenure",
        color="Years_At_Company_Group",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        yaxis_title="Attrition Rate (%)",
        xaxis_title="Years at Company",
        height=430,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# JOB SATISFACTION
# ==========================================================

if "job_satisfaction" in analysis:

    st.markdown("---")

    st.subheader("😊 Attrition by Job Satisfaction")

    satisfaction_df = analysis[
        "job_satisfaction"
    ]

    satisfaction_column = (
        satisfaction_df.columns[0]
    )

    fig = px.bar(
        satisfaction_df,
        x=satisfaction_column,
        y="Attrition_Rate",
        text="Attrition_Rate",
        title="Attrition Rate by Job Satisfaction",
        color=satisfaction_column,
        color_continuous_scale="Plasma"
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        yaxis_title="Attrition Rate (%)",
        xaxis_title="Job Satisfaction",
        height=430,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# MONTHLY INCOME
# ==========================================================

if "monthly_income" in analysis:

    st.markdown("---")

    st.subheader("💰 Monthly Income vs Attrition")

    income_df = analysis[
        "monthly_income"
    ]

    fig = px.bar(
        income_df,
        x="Attrition_Status",
        y="Average",
        text="Average",
        title="Average Monthly Income: Left vs Stayed",
        color="Attrition_Status",
        color_discrete_map={
            "Left": "#e74c3c",
            "Stayed": "#2ecc71"
        }
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        yaxis_title="Average Monthly Income",
        xaxis_title="Employee Status",
        height=430,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# KEY BUSINESS FINDINGS
# ==========================================================

st.markdown("---")

st.subheader("💡 Key Business Findings")

findings = generate_attrition_findings(df)

if findings:

    for finding in findings:

        st.info(
            f"🔎 {finding}"
        )

else:

    st.info(
        "No findings could be generated from the "
        "available HR columns."
    )


# ==========================================================
# NEXT STAGE
# ==========================================================

st.markdown("---")

st.success(
    "✅ Attrition Analysis completed. "
    "Next stage: 🕵️ Root Cause Analysis."
)