# AI HR Attrition Analytics

An automated HR analytics application built with **Python, Streamlit, MySQL, Machine Learning, and Docker** to analyze employee attrition, investigate potential risk factors, and support data-driven retention decisions.

## Business Problem

Employee attrition is a significant business challenge because it can increase recruitment and training costs, disrupt team productivity, and result in the loss of experienced employees. However, organizations may struggle to identify the factors associated with employee turnover and determine which employee groups require greater retention support.

Analyzing HR data manually can also make it difficult to identify patterns, validate findings, and translate analytical results into actionable decisions.

### Business Questions

* What is the overall employee attrition rate?
* Which departments and job roles experience higher attrition?
* How are overtime, job satisfaction, age, tenure, and income associated with attrition?
* Which findings provide evidence for potential attrition drivers?
* Can machine learning estimate attrition risk?
* What retention actions should HR teams prioritize?

### Project Objective

Develop an interactive analytics platform that transforms HR data into actionable insights through data quality assessment, attrition analysis, evidence-based investigation, machine learning, scenario analysis, and targeted recommendations.

## Key Features

1. **Data Upload:** Import HR datasets in CSV format and store dataset information in MySQL.
2. **Data Quality:** Detect missing values, duplicates, data type issues, constant columns, outliers, and duplicate employee IDs.
3. **Data Cleaning:** Standardize columns, remove duplicates, convert data types, and handle missing values.
4. **Attrition Analysis:** Explore attrition patterns using KPIs and interactive visualizations.
5. **Root Cause Investigation:** Compare employee groups and identify potential attrition drivers.
6. **Evidence Analysis:** Examine statistical signals supporting observed patterns.
7. **What-If Analysis:** Train a Logistic Regression model, evaluate performance, and compare hypothetical scenarios.
8. **Recommendations:** Generate prioritized retention actions with suggested owners, timelines, and monitoring metrics.
9. **Final Report:** Generate and download a PDF executive report containing key findings and recommendations.

## Workflow

**Upload Data → Data Quality → Data Cleaning → Attrition Analysis → Root Cause → Evidence → What-If → Recommendations → Final Report**

## Technology Stack

| Technology             | Application                                |
| ---------------------- | ------------------------------------------ |
| Python                 | Core programming and analytics             |
| Pandas, NumPy          | Data manipulation and numerical operations |
| Streamlit              | Interactive web application                |
| Plotly                 | Interactive visualizations                 |
| Scikit-learn           | Machine learning and evaluation            |
| MySQL                  | Database storage                           |
| Docker, Docker Compose | Containerization and service orchestration |
| ReportLab, Matplotlib  | PDF report generation and charts           |

## Project Structure

```text
AI_HR_Attrition_Analytics/
├── app.py
│
├── analytics/
│   ├── attrition_analysis.py
│   ├── data_cleaning.py
│   ├── data_quality.py
│   ├── evidence.py
│   ├── recommendations.py
│   ├── root_cause.py
│   └── what_if.py
│
├── database/
│   └── db.py
│
├── pages/
│   ├── 1_Data_Cleaning.py
│   ├── 2_Attrition_Analysis.py
│   ├── 3_Root_Cause.py
│   ├── 4_Evidence.py
│   ├── 5_What_If.py
│   ├── 6_Recommendations.py
│   └── 7_Final_Report.py
│
├── datasets/
├── reports/
├── screenshots/
│
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── .dockerignore
├── .gitignore
└── README.md
```

*Directory contents may vary depending on the final implementation.*

## Getting Started

### Prerequisites

* Docker Desktop
* Git

### Run Locally with Docker

**1. Clone the repository**

```bash
git clone https://github.com/riya1830-droid/Automated_HR_Attrition_Analytics.git
```

**2. Navigate to the project**

```bash
cd Automated_HR_Attrition_Analytics
```

**3. Build and start the application**

```bash
docker compose up --build
```

**4. Open the application**

Visit http://localhost:8501.

**5. Stop the application**

Press `Ctrl + C`. If necessary, run:

```bash
docker compose down
```

Ensure Docker Desktop is running and the database configuration matches the project's environment settings.

## Database Configuration

The application uses MySQL to store dataset information. Docker Compose runs the Streamlit application and MySQL database as separate services and connects them through an internal Docker network.

### Configuration

Before starting the application, verify the following:

* **Database service:** Defined in `docker-compose.yml`.
* **Database credentials:** Configure using environment variables; do not commit passwords or secrets to GitHub.
* **Database host:** Use the MySQL service name defined in `docker-compose.yml` when connecting from the Streamlit container.
* **Database port:** Use `3306` for connections between containers. The host port may be different if configured in Docker Compose.
* **Database initialization:** Ensure the required database and tables are created using the project's database setup logic.

Start the application and database together:

```bash
docker compose up --build
```

To check whether the services are running:

```bash
docker compose ps
```

To inspect MySQL logs:

```bash
docker compose logs mysql
```

Use the actual MySQL service name from `docker-compose.yml` if it is different from `mysql`.


## Business Value

* Identify employee groups with higher attrition.
* Investigate patterns associated with employee turnover.
* Support HR decisions with analytical evidence.
* Estimate attrition risk using machine learning.
* Prioritize potential retention initiatives.
* Communicate findings through executive reporting.

## Limitations

* Associations do not establish causation.
* Model predictions are estimates, not certainties.
* What-If scenarios do not guarantee real-world outcomes.
* Recommendations require organizational context and HR validation.
* Predictions should support fair, human-reviewed decisions rather than determine employment outcomes automatically.

## Future Enhancements

* SHAP-based model explainability.
* Automated exploratory data analysis.
* Comparison of multiple machine learning models.
* Model monitoring and data drift detection.
* User authentication and role-based access control.


