import io
import os
import re
import html
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)

from analytics.root_cause import get_driver_summary
from analytics.evidence import build_evidence_overview
from analytics.recommendations import (
    build_recommendations,
    get_recommendation_summary,
)


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="HR Attrition Final Report",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Final Report")
st.caption(
    "Automated HR Attrition Analytics | Executive Summary, Evidence, "
    "What-If Analysis and HR Action Plan"
)


# ==================================================
# 2. LOAD DATA
# ==================================================
df = st.session_state.get("cleaned_dataset")

if not isinstance(df, pd.DataFrame) or df.empty:
    df = st.session_state.get("uploaded_dataset")

if not isinstance(df, pd.DataFrame) or df.empty:
    st.warning(
        "No HR dataset found. Upload your HR data and complete "
        "Data Quality and Data Cleaning first."
    )
    st.stop()

df = df.copy()


# ==================================================
# 3. HELPER FUNCTIONS
# ==================================================
def normalise_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def find_column(data, candidates):
    lookup = {
        normalise_name(column): column
        for column in data.columns
    }

    for candidate in candidates:
        key = normalise_name(candidate)
        if key in lookup:
            return lookup[key]

    return None


def normalise_attrition(series):
    values = series.astype(str).str.strip().str.lower()

    left_values = {
        "yes", "left", "true", "1", "1.0",
        "resigned", "exited", "attrition",
    }

    stayed_values = {
        "no", "stayed", "false", "0", "0.0",
        "retained", "active",
    }

    result = pd.Series(
        index=series.index,
        dtype="object",
    )

    result.loc[values.isin(left_values)] = "Left"
    result.loc[values.isin(stayed_values)] = "Stayed"

    return result


def safe_text(value):
    if value is None:
        return "Not available"

    try:
        if pd.isna(value):
            return "Not available"
    except (TypeError, ValueError):
        pass

    return str(value)


def format_number(value):
    try:
        if pd.isna(value):
            return "Not available"
        return f"{float(value):,.0f}"
    except (ValueError, TypeError):
        return safe_text(value)


def format_percent(value):
    try:
        if pd.isna(value):
            return "Not available"
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return "Not available"


def get_attrition_data(data):
    attrition_col = find_column(
        data,
        [
            "Attrition",
            "Attrition_Status",
            "Employee_Attrition",
            "Left",
        ],
    )

    if attrition_col is None:
        return None, None

    attrition = normalise_attrition(data[attrition_col])
    valid = attrition.isin(["Left", "Stayed"])

    if not valid.any():
        return attrition_col, None

    return attrition_col, attrition[valid]


def calculate_group_summary(data, driver):
    attrition_col, attrition = get_attrition_data(data)

    if attrition_col is None or attrition is None:
        return pd.DataFrame()

    driver_aliases = {
        "Department": ["Department", "Dept"],
        "Job Role": ["JobRole", "Job_Role", "Role"],
        "Overtime": ["OverTime", "Overtime", "Over_Time"],
        "Job Satisfaction": [
            "JobSatisfaction",
            "Job_Satisfaction",
        ],
    }

    driver_col = find_column(
        data,
        driver_aliases.get(driver, [driver]),
    )

    if driver_col is None:
        return pd.DataFrame()

    working = pd.DataFrame({
        "Group": data.loc[attrition.index, driver_col],
        "Attrition": attrition,
    })

    working["Group"] = (
        working["Group"].fillna("Unknown").astype(str)
    )

    summary = (
        working.groupby("Group")
        .agg(
            Employees=("Attrition", "size"),
            Employees_Left=(
                "Attrition",
                lambda values: (values == "Left").sum(),
            ),
        )
        .reset_index()
    )

    summary["Attrition Rate (%)"] = (
        summary["Employees_Left"]
        / summary["Employees"]
        * 100
    )

    return summary.sort_values(
        "Attrition Rate (%)",
        ascending=False,
    )


# ==================================================
# 4. CALCULATE REPORT METRICS
# ==================================================
total_rows, total_columns = df.shape

attrition_column, attrition = get_attrition_data(df)

if attrition is not None:
    total_employees = len(attrition)
    employees_left = int((attrition == "Left").sum())
    employees_stayed = int((attrition == "Stayed").sum())

    attrition_rate = (
        employees_left / total_employees * 100
        if total_employees
        else 0
    )
else:
    total_employees = total_rows
    employees_left = None
    employees_stayed = None
    attrition_rate = None


# Existing analysis modules
try:
    root_causes = get_driver_summary(df)
    if root_causes is None:
        root_causes = pd.DataFrame()
except Exception as exc:
    root_causes = pd.DataFrame()
    root_cause_error = str(exc)
else:
    root_cause_error = None


try:
    evidence = build_evidence_overview(df)
    if evidence is None:
        evidence = pd.DataFrame()
except Exception:
    evidence = pd.DataFrame()


try:
    recommendations = build_recommendations(df)
    if recommendations is None:
        recommendations = pd.DataFrame()
except Exception as exc:
    recommendations = pd.DataFrame()
    recommendation_error = str(exc)
else:
    recommendation_error = None


recommendation_summary = get_recommendation_summary(
    recommendations
)

what_if_results = st.session_state.get("what_if_results")
what_if_driver = st.session_state.get("what_if_driver")


# ==================================================
# 5. EXECUTIVE SUMMARY
# ==================================================
st.header("1. Executive Summary")

if attrition_rate is not None:
    st.write(
        f"The dataset contains **{total_employees:,} valid employee "
        f"records**. Of these, **{employees_left:,} employees left** "
        f"and **{employees_stayed:,} stayed**, giving an observed "
        f"attrition rate of **{attrition_rate:.1f}%**."
    )
else:
    st.warning(
        "A usable attrition column was not found. Dataset profile "
        "information is available, but attrition KPIs cannot be calculated."
    )

k1, k2, k3, k4 = st.columns(4)

k1.metric("Employee Records", f"{total_employees:,}")

k2.metric(
    "Employees Left",
    format_number(employees_left),
)

k3.metric(
    "Employees Stayed",
    format_number(employees_stayed),
)

k4.metric(
    "Attrition Rate",
    format_percent(attrition_rate),
)

st.divider()


# ==================================================
# 6. DATASET PROFILE
# ==================================================
st.header("2. Dataset Profile")

p1, p2, p3 = st.columns(3)

p1.metric("Rows in Selected Dataset", f"{total_rows:,}")
p2.metric("Columns", f"{total_columns:,}")

p3.metric(
    "Valid Attrition Records",
    format_number(
        total_employees if attrition is not None else None
    ),
)

with st.expander("View dataset columns"):
    st.write(", ".join(map(str, df.columns.tolist())))

st.caption(
    "The report uses the cleaned dataset when available; otherwise, "
    "it uses the uploaded dataset. Counts refer to the dataset selected "
    "for this report."
)

st.divider()


# ==================================================
# 7. ATTRITION ANALYSIS
# ==================================================
st.header("3. Attrition Analysis")

if attrition is not None:
    status_data = pd.DataFrame({
        "Status": ["Left", "Stayed"],
        "Employees": [employees_left, employees_stayed],
    })

    fig_status = px.pie(
        status_data,
        names="Status",
        values="Employees",
        hole=0.58,
        color="Status",
        color_discrete_map={
            "Left": "#E74C3C",
            "Stayed": "#2ECC71",
        },
        title="Employee Attrition Distribution",
    )

    fig_status.update_traces(
        textposition="inside",
        textinfo="label+percent",
    )

    fig_status.update_layout(height=390)

    st.plotly_chart(
        fig_status,
        use_container_width=True,
    )

    available_drivers = [
        driver
        for driver in [
            "Department",
            "Job Role",
            "Overtime",
            "Job Satisfaction",
        ]
        if not calculate_group_summary(df, driver).empty
    ]

    if available_drivers:
        selected_analysis = st.selectbox(
            "Explore attrition by category",
            options=available_drivers,
            key="final_report_group_analysis",
        )

        group_summary = calculate_group_summary(
            df,
            selected_analysis,
        )

        chart_data = group_summary.head(12).copy()

        fig_group = px.bar(
            chart_data,
            x="Group",
            y="Attrition Rate (%)",
            color="Attrition Rate (%)",
            text="Attrition Rate (%)",
            color_continuous_scale="Tealgrn",
            title=f"Observed Attrition by {selected_analysis}",
        )

        fig_group.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
        )

        fig_group.update_layout(
            height=420,
            xaxis_title=selected_analysis,
            yaxis_title="Observed Attrition Rate (%)",
            coloraxis_showscale=False,
        )

        st.plotly_chart(
            fig_group,
            use_container_width=True,
        )

        st.dataframe(
            group_summary,
            use_container_width=True,
            hide_index=True,
        )

else:
    st.info(
        "Attrition charts are unavailable because a usable attrition "
        "column was not detected."
    )

st.divider()


# ==================================================
# 8. ROOT CAUSE AND EVIDENCE
# ==================================================
st.header("4. Root Cause Analysis & Evidence")

if not root_causes.empty:
    st.markdown("### Candidate Drivers")

    st.dataframe(
        root_causes,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info(
        "Root-cause results could not be generated from the current dataset."
    )

if not evidence.empty:
    st.markdown("### Evidence Overview")

    st.dataframe(
        evidence,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No evidence overview is available.")

st.warning(
    "Root-cause candidates and evidence summaries identify observed "
    "associations. They do not, by themselves, establish causal relationships."
)

st.divider()


# ==================================================
# 9. WHAT-IF ANALYSIS
# ==================================================
st.header("5. What-If Analysis")

if isinstance(what_if_results, dict) and what_if_results:
    st.write(f"**Selected driver:** {safe_text(what_if_driver)}")

    risk_change = what_if_results.get("risk_change")

    if risk_change is not None:
        try:
            risk_change = float(risk_change)

            if risk_change > 0:
                st.error(
                    f"Average predicted risk increased by "
                    f"{risk_change:.1f} percentage points."
                )
            elif risk_change < 0:
                st.success(
                    f"Average predicted risk decreased by "
                    f"{abs(risk_change):.1f} percentage points."
                )
            else:
                st.info(
                    "The scenario did not change average predicted risk."
                )

        except (ValueError, TypeError):
            st.write(f"Risk change: {safe_text(risk_change)}")

    with st.expander("View available What-If result details"):
        for key, value in what_if_results.items():
            st.write(
                f"**{key.replace('_', ' ').title()}:** "
                f"{safe_text(value)}"
            )

    st.caption(
        "What-If results are estimates from the model under a simulated "
        "scenario. They are not proof that changing a factor will cause "
        "attrition to increase or decrease."
    )

else:
    st.info(
        "No What-If results are available in the current session. "
        "Run a scenario on the What-If page and return here to include it."
    )

st.divider()


# ==================================================
# 10. RECOMMENDATIONS AND ACTION PLAN
# ==================================================
st.header("6. HR Recommendations & Action Plan")

if not recommendations.empty:
    r1, r2, r3, r4 = st.columns(4)

    r1.metric("Total Actions", recommendation_summary["total"])
    r2.metric("High Priority", recommendation_summary["high"])
    r3.metric("Medium Priority", recommendation_summary["medium"])
    r4.metric("Drivers Covered", recommendation_summary["drivers_covered"])

    action_columns = [
        "Driver",
        "Priority",
        "Focus Group",
        "Focus Employees",
        "Focus Attrition Rate",
        "Recommended Action",
        "Suggested Owner",
        "Suggested Timeframe",
        "Success Metric",
        "Proposed Target Rate",
    ]

    action_columns = [
        column
        for column in action_columns
        if column in recommendations.columns
    ]

    st.dataframe(
        recommendations[action_columns],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Detailed Action Plan")

    selected_recommendation = st.selectbox(
        "Select a recommendation",
        options=recommendations["Driver"].tolist(),
        key="final_report_recommendation",
    )

    action = recommendations.loc[
        recommendations["Driver"] == selected_recommendation
    ].iloc[0]

    st.markdown(f"**Priority:** {safe_text(action.get('Priority'))}")

    st.write(
        f"**Employee group:** {safe_text(action.get('Focus Group'))}"
    )

    st.write(
        f"**Recommended action:** "
        f"{safe_text(action.get('Recommended Action'))}"
    )

    st.write(
        f"**Owner:** {safe_text(action.get('Suggested Owner'))}"
    )

    st.write(
        f"**Timeline:** {safe_text(action.get('Suggested Timeframe'))}"
    )

    st.write(
        f"**Success metric:** {safe_text(action.get('Success Metric'))}"
    )

    steps = action.get("Action Steps", [])

    if isinstance(steps, list):
        for index, step in enumerate(steps, start=1):
            st.write(f"{index}. {step}")

    if pd.notna(action.get("Proposed Target Rate")):
        st.write(
            "**Illustrative planning target:** "
            f"{float(action['Proposed Target Rate']):.1f}%"
        )

    st.caption(
        "Planning targets are illustrative goals, not guaranteed outcomes. "
        "Review actual results after implementation."
    )

else:
    st.info(
        "Recommendations are unavailable. Check the Recommendations page "
        "and confirm the dataset contains the required driver columns."
    )

st.divider()


# ==================================================
# 11. LIMITATIONS
# ==================================================
st.header("7. Limitations & Interpretation")

limitations = [
    "The report reflects the dataset currently selected in the application.",
    "Missing values, data quality issues, and limited sample sizes can affect results.",
    "Observed differences between employee groups do not establish causation.",
    "Model-based What-If results are estimates and may not represent real-world outcomes.",
    "Recommendations and targets require HR review, business context, and follow-up measurement.",
    "Employee data should be handled confidentially and used fairly.",
]

for item in limitations:
    st.markdown(f"- {item}")

st.divider()


# ==================================================
# 12. PDF GENERATION
# ==================================================
def make_pdf(data, summary_data, evidence_data, rec_data, what_if):
    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="AI HR Attrition Analytics - Final Report",
        author="AI HR Attrition Analytics",
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=29,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17365D"),
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#526477"),
        spaceAfter=18,
    ))

    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#17365D"),
        spaceBefore=12,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="SmallCell",
        parent=styles["BodyText"],
        fontSize=7,
        leading=9,
    ))

    def para(value, style="ReportBody"):
        return Paragraph(
            html.escape(safe_text(value)).replace("\n", "<br/>"),
            styles[style],
        )

    def make_table(headers, rows, widths=None):
        table_data = [
            [para(header, "SmallCell") for header in headers]
        ]

        for row in rows:
            table_data.append([
                para(value, "SmallCell")
                for value in row
            ])

        table = Table(
            table_data,
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7DEE8")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#F3F6FA"),
            ]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        return table

    story = []

    # Cover
    story.append(Spacer(1, 22 * mm))

    story.append(para(
        "AI HR ATTRITION ANALYTICS",
        "ReportTitle",
    ))

    story.append(para(
        "Executive Summary & HR Decision-Support Report",
        "ReportSubtitle",
    ))

    story.append(Spacer(1, 10 * mm))

    cover_rows = [
        ["Dataset rows", f"{len(data):,}"],
        ["Dataset columns", f"{len(data.columns):,}"],
        [
            "Report generated",
            datetime.now().strftime("%d %B %Y, %H:%M"),
        ],
    ]

    story.append(make_table(
        ["Report Detail", "Value"],
        cover_rows,
        widths=[65 * mm, 95 * mm],
    ))

    story.append(Spacer(1, 10 * mm))

    story.append(para(
        "Purpose: consolidate workforce attrition patterns, root-cause "
        "candidates, supporting evidence, model-based scenario results, "
        "and proposed HR actions into one report.",
    ))

    story.append(PageBreak())

    # Executive summary
    story.append(para("1. Executive Summary", "SectionHeading"))

    attrition_col, valid_attrition = get_attrition_data(data)

    if valid_attrition is not None:
        count = len(valid_attrition)
        left_count = int((valid_attrition == "Left").sum())
        stayed_count = int((valid_attrition == "Stayed").sum())
        rate = left_count / count * 100 if count else 0

        executive_rows = [
            ["Valid employee records", f"{count:,}"],
            ["Employees who left", f"{left_count:,}"],
            ["Employees who stayed", f"{stayed_count:,}"],
            ["Observed attrition rate", f"{rate:.1f}%"],
        ]

        story.append(make_table(
            ["Metric", "Result"],
            executive_rows,
            widths=[85 * mm, 75 * mm],
        ))

    else:
        story.append(para(
            "A usable attrition column was not detected, so attrition "
            "KPIs could not be calculated.",
        ))

    # Status chart
    if valid_attrition is not None:
        chart_buffer = io.BytesIO()

        fig, ax = plt.subplots(figsize=(6.2, 3.3))

        ax.bar(
            ["Left", "Stayed"],
            [
                int((valid_attrition == "Left").sum()),
                int((valid_attrition == "Stayed").sum()),
            ],
            color=["#E74C3C", "#2ECC71"],
        )

        ax.set_title("Employee Attrition Distribution")
        ax.set_ylabel("Employee Count")
        ax.grid(axis="y", alpha=0.25)

        fig.tight_layout()

        fig.savefig(
            chart_buffer,
            format="png",
            dpi=160,
            bbox_inches="tight",
        )

        plt.close(fig)
        chart_buffer.seek(0)

        story.append(Spacer(1, 5 * mm))

        story.append(Image(
            chart_buffer,
            width=145 * mm,
            height=75 * mm,
        ))

    # Dataset profile
    story.append(para("2. Dataset Profile", "SectionHeading"))

    story.append(para(
        f"The selected dataset contains {len(data):,} rows and "
        f"{len(data.columns):,} columns.",
    ))

    # Root cause and evidence
    story.append(para(
        "3. Root Cause Candidates & Evidence",
        "SectionHeading",
    ))

    if not summary_data.empty:
        cols = list(summary_data.columns[:5])

        rows = (
            summary_data[cols]
            .head(12)
            .fillna("Not available")
            .values.tolist()
        )

        story.append(make_table(cols, rows))

    else:
        story.append(para(
            "Root-cause summary was unavailable for this report.",
        ))

    if not evidence_data.empty:
        cols = [
            col for col in [
                "Driver",
                "Evidence",
                "What the data shows",
            ]
            if col in evidence_data.columns
        ]

        if cols:
            rows = (
                evidence_data[cols]
                .fillna("Not available")
                .values.tolist()
            )

            story.append(Spacer(1, 5 * mm))
            story.append(make_table(cols, rows))

    story.append(para(
        "Interpretation: observed associations are useful for investigation, "
        "but they do not establish that a factor causes employee attrition.",
    ))

    # What-If
    story.append(para("4. What-If Analysis", "SectionHeading"))

    if isinstance(what_if, dict) and what_if:
        what_if_rows = [
            [
                str(key).replace("_", " ").title(),
                safe_text(value),
            ]
            for key, value in what_if.items()
        ]

        story.append(para(
            "Selected driver: "
            + safe_text(st.session_state.get("what_if_driver")),
        ))

        story.append(make_table(
            ["Scenario Metric", "Value"],
            what_if_rows,
            widths=[65 * mm, 95 * mm],
        ))

        story.append(para(
            "Scenario results are model-based estimates, not proof of "
            "causal impact or guaranteed future outcomes.",
        ))

    else:
        story.append(para(
            "No What-If result was available in the current session "
            "when this report was generated.",
        ))

    # Recommendations
    story.append(para(
        "5. Recommendations & Action Plan",
        "SectionHeading",
    ))

    if not rec_data.empty:
        cols = [
            col for col in [
                "Driver",
                "Priority",
                "Focus Group",
                "Focus Employees",
                "Focus Attrition Rate",
                "Recommended Action",
                "Suggested Owner",
                "Suggested Timeframe",
                "Success Metric",
                "Proposed Target Rate",
            ]
            if col in rec_data.columns
        ]

        rows = (
            rec_data[cols]
            .fillna("Not available")
            .values.tolist()
        )

        story.append(make_table(cols, rows))
        story.append(Spacer(1, 5 * mm))

        story.append(para(
            "Proposed targets are planning goals and should be reviewed "
            "against actual outcomes. They are not guaranteed results.",
        ))

    else:
        story.append(para(
            "Recommendations were unavailable when this report was generated.",
        ))

    # Limitations
    story.append(para(
        "6. Limitations & Responsible Use",
        "SectionHeading",
    ))

    for limitation in [
        "The report reflects the selected dataset and the analysis available at generation time.",
        "Missing data and small group sizes can affect the stability of findings.",
        "Associations do not establish causation.",
        "Model predictions can be uncertain and should be validated.",
        "HR decisions should consider business context, privacy, fairness, and employee feedback.",
    ]:
        story.append(para("• " + limitation))

    story.append(Spacer(1, 5 * mm))

    story.append(para(
        "End of Report",
        "ReportSubtitle",
    ))

    def add_page_number(canvas, doc):
        canvas.saveState()

        canvas.setStrokeColor(colors.HexColor("#D7DEE8"))

        canvas.line(
            18 * mm,
            14 * mm,
            A4[0] - 18 * mm,
            14 * mm,
        )

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#526477"))

        canvas.drawString(
            18 * mm,
            9 * mm,
            "Automated HR Attrition Analytics | Confidential",
        )

        canvas.drawRightString(
            A4[0] - 18 * mm,
            9 * mm,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    document.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    buffer.seek(0)
    return buffer.getvalue()


# ==================================================
# 13. EXPORT, SAVE AND DOWNLOAD FINAL REPORT
# ==================================================
st.header("8. Export Final Report")

st.write(
    "Generate a formatted PDF containing the executive summary, "
    "dataset profile, attrition chart, root-cause candidates, evidence, "
    "What-If results available in this session, recommendations, "
    "and interpretation notes."
)

# --------------------------------------------------
# Generate the PDF
# --------------------------------------------------
if st.button("🔄 Prepare Final PDF Report", type="primary"):
    try:
        pdf_bytes = make_pdf(
            df,
            root_causes,
            evidence,
            recommendations,
            what_if_results,
        )

        # Replace any previous in-session PDF with the latest version
        st.session_state["final_report_pdf"] = pdf_bytes

        # Clear the saved-path display for the new report
        st.session_state.pop("last_saved_report_path", None)

        st.success("Your PDF report has been generated successfully.")

    except Exception as exc:
        st.error(f"Could not generate the PDF report: {exc}")


# --------------------------------------------------
# Save and download the generated PDF
# --------------------------------------------------
pdf_bytes = st.session_state.get("final_report_pdf")

if pdf_bytes:
    st.divider()
    st.subheader("Your Final Report")

    save_col, download_col = st.columns(2)

    # Save a copy to the project's reports folder
    with save_col:
        if st.button(
            "💾 Save Report to Project",
            use_container_width=True,
        ):
            try:
                # In Docker, this is expected to resolve to /app/reports
                reports_dir = os.path.join(
                    os.getcwd(),
                    "reports",
                )

                os.makedirs(
                    reports_dir,
                    exist_ok=True,
                )

                # Unique timestamp helps avoid overwriting previous reports
                timestamp = datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                filename = (
                    "Automated_HR_Attrition_Analytics_Report_"
                    f"{timestamp}.pdf"
                )

                report_path = os.path.join(
                    reports_dir,
                    filename,
                )

                # Save PDF bytes to disk
                with open(report_path, "wb") as report_file:
                    report_file.write(pdf_bytes)

                st.session_state["last_saved_report_path"] = (
                    report_path
                )

                st.success("PDF report saved successfully!")

            except Exception as exc:
                st.error(
                    f"Could not save the PDF report: {exc}"
                )

    # Download a copy to the user's computer
    with download_col:
        st.download_button(
            label="📥 Download PDF to Computer",
            data=pdf_bytes,
            file_name="Automated_HR_Attrition_Analytics_Final_Report.pdf",
            mime="application/pdf",
            key="download_final_report_pdf",
            use_container_width=True,
        )

    # Show the most recently saved report path
    saved_path = st.session_state.get(
        "last_saved_report_path"
    )

    if saved_path and os.path.isfile(saved_path):
        st.info(
            f"Saved report location: `{saved_path}`"
        )

st.divider()

st.caption(
    "Review the report before sharing it. It may contain sensitive "
    "workforce information."
)