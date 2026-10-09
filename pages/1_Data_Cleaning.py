import streamlit as st
import pandas as pd
import os

from analytics.data_cleaning import clean_dataset


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Data Cleaning | AI HR Attrition Analytics",
    page_icon="🧹",
    layout="wide"
)


# ==========================================================
# PAGE HEADER
# ==========================================================

st.title("🧹 Data Cleaning")

st.caption(
    "Fix identified HR data quality problems while "
    "keeping the original dataset unchanged."
)


# ==========================================================
# CHECK SELECTED DATASET
# ==========================================================

if "selected_dataset_path" not in st.session_state:

    st.warning(
        "⚠️ No HR dataset selected. "
        "Please upload a dataset from the Home page first."
    )

    st.stop()


file_path = st.session_state[
    "selected_dataset_path"
]


# ==========================================================
# CHECK FILE
# ==========================================================

if not os.path.exists(file_path):

    st.error(
        "❌ Selected dataset file could not be found."
    )

    st.stop()


# ==========================================================
# LOAD DATASET
# ==========================================================

try:

    df = pd.read_csv(file_path)

except Exception as e:

    st.error(
        "❌ Could not load the selected HR dataset."
    )

    st.code(str(e))

    st.stop()


# ==========================================================
# DATASET INFORMATION
# ==========================================================

st.write(
    f"📂 **Dataset:** "
    f"{os.path.basename(file_path)}"
)

st.write(
    f"👥 **Employees:** "
    f"{len(df):,}"
)

st.divider()


# ==========================================================
# BEFORE CLEANING
# ==========================================================

st.subheader("📊 Before Cleaning")


before_rows = len(df)

before_columns = len(df.columns)

before_missing = int(
    df.isna().sum().sum()
)

before_duplicates = int(
    df.duplicated().sum()
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Total Employees",
        f"{before_rows:,}"
    )


with col2:

    st.metric(
        "Columns",
        f"{before_columns:,}"
    )


with col3:

    st.metric(
        "Missing Cells",
        f"{before_missing:,}"
    )


with col4:

    st.metric(
        "Duplicate Rows",
        f"{before_duplicates:,}"
    )


# ==========================================================
# DATASET PREVIEW
# ==========================================================

st.write("### 👀 Original Dataset Preview")


st.dataframe(
    df.head(10),
    use_container_width=True,
    hide_index=True
)


st.divider()


# ==========================================================
# AUTOMATIC CLEANING
# ==========================================================

st.subheader("🧹 Automatic HR Data Cleaning")


st.write(
    """
The cleaning engine applies conservative operations to the
uploaded HR dataset.

It can standardize column names, remove exact duplicate rows,
remove completely empty columns, convert safe numeric/date
columns, and handle missing values.

Potential outliers are **not automatically deleted** because
an unusual employee value is not necessarily incorrect.
"""
)


if st.button(
    "🧹 Clean Dataset",
    type="primary"
):

    try:

        cleaned_df, cleaning_report = (
            clean_dataset(df)
        )

        # --------------------------------------------------
        # Store cleaned dataset
        # --------------------------------------------------

        st.session_state[
            "cleaned_dataset"
        ] = cleaned_df

        st.session_state[
            "cleaning_report"
        ] = cleaning_report

        st.session_state[
            "cleaning_completed"
        ] = True

        st.success(
            "✅ HR dataset cleaned successfully!"
        )

    except Exception as e:

        st.error(
            "❌ Dataset cleaning failed."
        )

        st.code(str(e))


# ==========================================================
# SHOW RESULTS
# ==========================================================

if st.session_state.get(
    "cleaning_completed",
    False
):

    cleaned_df = st.session_state[
        "cleaned_dataset"
    ]

    cleaning_report = st.session_state[
        "cleaning_report"
    ]


    st.divider()


    # ======================================================
    # CLEANING SUMMARY
    # ======================================================

    st.subheader("📋 Cleaning Summary")


    after_rows = len(
        cleaned_df
    )

    after_columns = len(
        cleaned_df.columns
    )

    after_missing = int(
        cleaned_df.isna().sum().sum()
    )

    after_duplicates = int(
        cleaned_df.duplicated().sum()
    )


    total_values_changed = 0

    if not cleaning_report.empty:

        numeric_changes = pd.to_numeric(
            cleaning_report[
                "Values Changed"
            ],
            errors="coerce"
        )

        total_values_changed = int(
            numeric_changes
            .fillna(0)
            .sum()
        )


    col1, col2, col3, col4, col5 = (
        st.columns(5)
    )


    with col1:

        st.metric(
            "Rows Before",
            f"{before_rows:,}"
        )


    with col2:

        st.metric(
            "Rows After",
            f"{after_rows:,}",
            delta=(
                after_rows
                - before_rows
            )
        )


    with col3:

        st.metric(
            "Missing Cells",
            f"{after_missing:,}",
            delta=(
                after_missing
                - before_missing
            )
        )


    with col4:

        st.metric(
            "Duplicate Rows",
            f"{after_duplicates:,}",
            delta=(
                after_duplicates
                - before_duplicates
            )
        )


    with col5:

        st.metric(
            "Values Changed",
            f"{total_values_changed:,}"
        )


    # ======================================================
    # BEFORE VS AFTER
    # ======================================================

    st.write("### 🔄 Before vs After")


    comparison_df = pd.DataFrame({

        "Metric": [
            "Rows",
            "Columns",
            "Missing Cells",
            "Duplicate Rows"
        ],

        "Before": [
            before_rows,
            before_columns,
            before_missing,
            before_duplicates
        ],

        "After": [
            after_rows,
            after_columns,
            after_missing,
            after_duplicates
        ]
    })


    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True
    )


    # ======================================================
    # CLEANING ACTIONS
    # ======================================================

    st.write("### 🛠️ Cleaning Actions")


    if not cleaning_report.empty:

        st.dataframe(
            cleaning_report,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "✅ No cleaning actions were required."
        )


    # ======================================================
    # CLEANED DATASET PREVIEW
    # ======================================================

    st.write(
        "### 👀 Cleaned HR Dataset Preview"
    )


    st.dataframe(
        cleaned_df.head(10),
        use_container_width=True,
        hide_index=True
    )


    # ======================================================
    # COMPLETION MESSAGE
    # ======================================================

    st.success(
        "✅ Cleaned HR dataset is ready for "
        "Employee Attrition Analysis."
    )


    st.info(
        "💡 The original CSV remains unchanged. "
        "The cleaned version is stored separately in "
        "the current Streamlit session."
    )