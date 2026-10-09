import streamlit as st
import pandas as pd
import os

from database.db import get_connection

from analytics.data_quality import (
    check_missing_values,
    check_duplicate_rows,
    check_data_types,
    check_constant_columns,
    check_outliers,
    check_duplicate_ids,
    calculate_data_quality_score
)


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Automated HR Attrition Analytics",
    page_icon="👥",
    layout="wide"
)


# ==========================================================
# APPLICATION TITLE
# ==========================================================

st.title("👥 Automated HR Attrition Analytics")

st.write(
    "Analyze employee HR data to understand attrition patterns, "
    "identify potential attrition drivers, and support HR decision-making."
)

st.divider()


# ==========================================================
# 📤 UPLOAD HR DATASET
# ==========================================================

st.subheader("📤 Upload HR Dataset")

st.write(
    "Upload an employee HR dataset in CSV format to begin the "
    "attrition investigation."
)

uploaded_file = st.file_uploader(
    "Upload a CSV file",
    type=["csv"]
)


if uploaded_file is not None:

    try:

        # ==================================================
        # READ CSV
        # ==================================================

        df = pd.read_csv(uploaded_file)


        # ==================================================
        # VALIDATE DATASET
        # ==================================================

        if df.empty:

            st.error(
                "❌ The uploaded CSV file is empty."
            )

            st.stop()


        # ==================================================
        # CREATE DATASETS FOLDER
        # ==================================================

        os.makedirs(
            "datasets",
            exist_ok=True
        )


        # ==================================================
        # FILE PATH
        # ==================================================

        file_path = os.path.join(
            "datasets",
            uploaded_file.name
        )


        # ==================================================
        # SAVE CSV FILE
        # ==================================================

        with open(
            file_path,
            "wb"
        ) as file:

            file.write(
                uploaded_file.getbuffer()
            )


        # ==================================================
        # DATASET INFORMATION
        # ==================================================

        row_count = df.shape[0]
        column_count = df.shape[1]


        # ==================================================
        # SAVE SELECTED DATASET
        # ==================================================

        st.session_state[
            "selected_dataset_path"
        ] = file_path

        st.session_state[
            "uploaded_dataset"
        ] = df


        # ==================================================
        # RESET PREVIOUS ANALYSIS STATE
        # ==================================================

        st.session_state[
            "data_quality_completed"
        ] = False

        st.session_state[
            "data_quality_score"
        ] = None

        st.session_state[
            "data_quality_results"
        ] = None

        st.session_state[
            "cleaned_dataset"
        ] = None

        st.session_state[
            "cleaning_report"
        ] = None

        st.session_state[
            "cleaning_completed"
        ] = False


        # ==================================================
        # CHECK ATTRITION COLUMN
        # ==================================================

        attrition_columns = [
            column
            for column in df.columns
            if column.strip().lower() == "attrition"
        ]

        attrition_detected = (
            len(attrition_columns) > 0
        )


        st.session_state[
            "attrition_detected"
        ] = attrition_detected


        # ==================================================
        # CREATE DATASETS TABLE IF NOT EXISTS
        # ==================================================

        connection = get_connection()

        cursor = connection.cursor()

        create_table_query = """
            CREATE TABLE IF NOT EXISTS datasets
            (
                dataset_id INT AUTO_INCREMENT PRIMARY KEY,
                dataset_name VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                row_count INT NOT NULL,
                column_count INT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """

        cursor.execute(
            create_table_query
        )


        # ==================================================
        # SAVE DATASET METADATA
        # ==================================================

        insert_query = """
            INSERT INTO datasets
            (
                dataset_name,
                file_path,
                row_count,
                column_count
            )
            VALUES (%s, %s, %s, %s)
        """

        values = (
            uploaded_file.name,
            file_path,
            row_count,
            column_count
        )

        cursor.execute(
            insert_query,
            values
        )

        connection.commit()

        cursor.close()
        connection.close()


        # ==================================================
        # SUCCESS MESSAGE
        # ==================================================

        st.success(
            "✅ HR dataset uploaded and saved successfully!"
        )


        # ==================================================
        # 📊 DATASET OVERVIEW
        # ==================================================

        st.subheader("📊 Dataset Overview")

        col1, col2, col3, col4 = st.columns(4)


        with col1:

            st.metric(
                "Total Employees",
                f"{row_count:,}"
            )


        with col2:

            st.metric(
                "Columns",
                f"{column_count:,}"
            )


        with col3:

            st.metric(
                "Attrition Target",
                "Detected"
                if attrition_detected
                else "Not Detected"
            )


        with col4:

            st.metric(
                "File Type",
                "CSV"
            )


        # ==================================================
        # ATTRITION TARGET MESSAGE
        # ==================================================

        if attrition_detected:

            st.success(
                "✅ Attrition column detected. "
                "The dataset is ready for employee attrition analysis."
            )

        else:

            st.warning(
                "⚠️ No column named 'Attrition' was detected. "
                "Please verify that the uploaded HR dataset contains "
                "an employee attrition target."
            )


        # ==================================================
        # 👀 DATASET PREVIEW
        # ==================================================

        st.subheader("👀 Dataset Preview")

        st.dataframe(
            df.head(10),
            use_container_width=True,
            hide_index=True
        )


        # ==================================================
        # 🔎 DATA QUALITY
        # ==================================================

        st.divider()

        st.header("🔎 Data Quality")

        st.write(
            "Check whether the HR dataset is reliable enough "
            "for employee attrition analysis."
        )


        # ==================================================
        # 1️⃣ MISSING VALUES
        # ==================================================

        st.subheader("1️⃣ Missing Values")

        missing_df = check_missing_values(df)

        total_missing = int(
            missing_df["missing_count"].sum()
        )


        if total_missing == 0:

            st.success(
                "✅ No missing values found."
            )

        else:

            st.warning(
                f"⚠️ {total_missing:,} "
                "missing values found."
            )

            st.dataframe(
                missing_df[
                    missing_df["missing_count"] > 0
                ],
                use_container_width=True,
                hide_index=True
            )


        # ==================================================
        # 2️⃣ DUPLICATE ROWS
        # ==================================================

        st.subheader("2️⃣ Duplicate Rows")

        duplicate_result = check_duplicate_rows(df)

        duplicate_count = (
            duplicate_result["duplicate_count"]
        )


        if duplicate_count == 0:

            st.success(
                "✅ No duplicate rows found."
            )

        else:

            st.warning(
                f"⚠️ {duplicate_count:,} "
                "duplicate rows found."
            )

            st.write(
                f"Duplicate percentage: "
                f"{duplicate_result['duplicate_percentage']:.2f}%"
            )


        # ==================================================
        # 3️⃣ DATA TYPES
        # ==================================================

        st.subheader("3️⃣ Data Types")

        data_types_df = check_data_types(df)

        st.dataframe(
            data_types_df,
            use_container_width=True,
            hide_index=True
        )


        # ==================================================
        # 4️⃣ CONSTANT COLUMNS
        # ==================================================

        st.subheader("4️⃣ Constant Columns")

        constant_columns = check_constant_columns(df)


        if len(constant_columns) == 0:

            st.success(
                "✅ No constant columns found."
            )

        else:

            st.warning(
                f"⚠️ {len(constant_columns)} "
                "constant column(s) found."
            )

            st.write(
                constant_columns
            )


        # ==================================================
        # 5️⃣ OUTLIERS
        # ==================================================

        st.subheader("5️⃣ Outliers")

        outlier_df = check_outliers(df)


        if outlier_df.empty:

            st.info(
                "ℹ️ No numeric columns available "
                "for outlier analysis."
            )

        elif (
            outlier_df["outlier_count"].sum() == 0
        ):

            st.success(
                "✅ No significant outliers detected."
            )

            st.dataframe(
                outlier_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.warning(
                f"⚠️ "
                f"{outlier_df['outlier_count'].sum():,} "
                "potential outlier values detected."
            )

            st.dataframe(
                outlier_df,
                use_container_width=True,
                hide_index=True
            )


        # ==================================================
        # 6️⃣ DUPLICATE IDs
        # ==================================================

        st.subheader("6️⃣ Duplicate IDs")

        duplicate_id_df = check_duplicate_ids(df)


        if duplicate_id_df.empty:

            st.success(
                "✅ No duplicate IDs detected."
            )

        else:

            st.warning(
                "⚠️ Duplicate ID values detected."
            )

            st.dataframe(
                duplicate_id_df,
                use_container_width=True,
                hide_index=True
            )


        # ==================================================
        # 7️⃣ OVERALL DATA QUALITY SCORE
        # ==================================================

        st.divider()

        st.subheader(
            "7️⃣ Overall Data Quality Score"
        )


        quality_score = calculate_data_quality_score(
            missing_df,
            duplicate_result,
            constant_columns,
            outlier_df,
            duplicate_id_df
        )


        if quality_score >= 80:

            st.success(
                f"🟢 Data Quality Score: "
                f"{quality_score}/100"
            )

        elif quality_score >= 60:

            st.warning(
                f"🟡 Data Quality Score: "
                f"{quality_score}/100"
            )

        else:

            st.error(
                f"🔴 Data Quality Score: "
                f"{quality_score}/100"
            )


        # ==================================================
        # SAVE QUALITY RESULTS
        # ==================================================

        st.session_state[
            "data_quality_score"
        ] = quality_score


        st.session_state[
            "data_quality_results"
        ] = {

            "missing": missing_df,

            "duplicates": duplicate_result,

            "data_types": data_types_df,

            "constant_columns": constant_columns,

            "outliers": outlier_df,

            "duplicate_ids": duplicate_id_df
        }


        # ==================================================
        # MARK DATA QUALITY AS COMPLETED
        # ==================================================

        st.session_state[
            "data_quality_completed"
        ] = True


        # ==================================================
        # NEXT STEP
        # ==================================================

        st.divider()

        st.info(
            "➡️ Data Quality analysis is complete. "
            "Proceed to Data Cleaning to fix the identified data issues "
            "before continuing with Employee Attrition Analysis."
        )


        # ==================================================
        # 📁 FILE LOCATION
        # ==================================================

        st.subheader("📁 File Location")

        st.code(
            file_path
        )


    except Exception as e:

        st.error(
            "❌ Could not process the HR dataset."
        )

        st.code(
            str(e)
        )


# ==========================================================
# 📁 MY DATASETS
# ==========================================================

st.divider()

st.subheader("📁 My Datasets")

st.write(
    "Previously uploaded HR datasets stored by the application."
)


try:

    connection = get_connection()

    # ------------------------------------------------------
    # ENSURE DATASETS TABLE EXISTS
    # ------------------------------------------------------

    cursor = connection.cursor()

    create_table_query = """
        CREATE TABLE IF NOT EXISTS datasets
        (
            dataset_id INT AUTO_INCREMENT PRIMARY KEY,
            dataset_name VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            row_count INT NOT NULL,
            column_count INT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """

    cursor.execute(
        create_table_query
    )

    connection.commit()

    cursor.close()


    # ------------------------------------------------------
    # LOAD DATASETS
    # ------------------------------------------------------

    query = """
        SELECT
            dataset_id,
            dataset_name,
            row_count,
            column_count,
            uploaded_at
        FROM datasets
        ORDER BY uploaded_at DESC
    """

    datasets_df = pd.read_sql(
        query,
        connection
    )

    connection.close()


    # ------------------------------------------------------
    # DISPLAY DATASETS
    # ------------------------------------------------------

    if datasets_df.empty:

        st.info(
            "No HR datasets uploaded yet."
        )

    else:

        datasets_df["uploaded_at"] = (
            pd.to_datetime(
                datasets_df["uploaded_at"]
            )
            .dt.strftime(
                "%d %b %Y, %I:%M %p"
            )
        )


        st.dataframe(
            datasets_df,
            use_container_width=True,
            hide_index=True
        )


except Exception as e:

    st.error(
        "❌ Could not load datasets."
    )

    st.code(
        str(e)
    )