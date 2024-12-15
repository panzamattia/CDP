import sqlite3
import streamlit as st
import pandas as pd
import base64
import plotly.graph_objects as go
from database_setup import initialize_database, load_csv_to_database  # Import from setup script

# Set page config
st.set_page_config(page_title="Family Health Dashboard", layout="wide")

# Initialize session state
if "current_row" not in st.session_state:
    st.session_state["current_row"] = {f"Family Member {i}": 0 for i in range(1, 5)}

if "goals" not in st.session_state:
    st.session_state["goals"] = {"steps_daily": 10000, "calories": 2500, "water": 2.0}

if "goal_progress" not in st.session_state:
    st.session_state["goal_progress"] = {"steps_daily": 0, "calories": 0, "water": 0.0}

if "thresholds" not in st.session_state:
    st.session_state["thresholds"] = {
        "Heartrate (bpm)": {"low": 60, "high": 100},
        "Zucker (mmol/l)": {"low": 4.0, "high": 7.0},
        "Sauerstoffsättigung (%)": {"low": 92, "high": 100},
        "Heartratevariability (ms)": {"low": 20, "high": 80},
    }

if "alerts" not in st.session_state:
    st.session_state["alerts"] = []

# Helper to encode images
def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except:
        return ""

# Fetch patient data
def fetch_patient_data(limit=4):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, age, blood_type, allergies, conditions, image 
    FROM patients 
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    # Convert data to a dictionary
    patients = {}
    for idx, row in enumerate(rows, 1):
        patients[f"Family Member {idx}"] = {
            "id": row[0],
            "name": row[1],
            "age": row[2],
            "blood_type": row[3],
            "allergies": row[4].split(", ") if row[4] != "None" else [],
            "conditions": row[5].split(", "),
            "image": row[6]
        }
    return patients

# Fetch historical data for a patient
def fetch_historical_data(patient_id):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute('''
    SELECT timestamp, heartrate, blood_sugar, oxygen_saturation, hr_variability
    FROM historical_data
    WHERE patient_id = ?
    ''', (patient_id,))
    rows = cursor.fetchall()
    conn.close()

    # Convert to DataFrame
    return pd.DataFrame(rows, columns=["Timestamp", "Heartrate (bpm)", "Zucker (mmol/l)", 
                                       "Sauerstoffsättigung (%)", "Heartratevariability (ms)"])

# Display health data
def display_health_data(member_name, patient):
    st.markdown(f"## {member_name}")
    image_base64 = image_to_base64(patient['image'])
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <img src="data:image/png;base64,{image_base64}" alt="{member_name}" 
                style="width: 80px; height: 80px; border-radius: 50%; margin-right: 15px;">
            <div>
                <h4 style="margin: 0;">{patient['name']}</h4>
                <p>Age: {patient['age']} | Blood Type: {patient['blood_type']}</p>
                <p>Conditions: {', '.join(patient['conditions'])}</p>
                <p>Allergies: {', '.join(patient['allergies']) if patient['allergies'] else 'None'}</p>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

# Display historical data graph

def display_historical_graph(member_name, patient_id):
    st.write("### Historical Data")

    # Fetch the complete historical data for the patient
    history_df = fetch_historical_data(patient_id)
    if not history_df.empty:
        # Convert timestamp column to datetime
        history_df["Timestamp"] = pd.to_datetime(history_df["Timestamp"])

        # Set minimum and maximum dates
        min_date, max_date = history_df["Timestamp"].min().date(), history_df["Timestamp"].max().date()
        st.write(f"Data available from **{min_date}** to **{max_date}**")

        if min_date == max_date:
            st.warning("Only one date is available. Displaying the data for that date.")
            filtered_df = history_df  # No date filtering needed
        else:
            # Slider for selecting a date range
            start_date, end_date = st.slider(
                "Select Date Range:",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="YYYY-MM-DD"
            )

            # Filter the data based on the selected date range
            filtered_df = history_df[
                (history_df["Timestamp"] >= pd.Timestamp(start_date)) &
                (history_df["Timestamp"] <= pd.Timestamp(end_date))
            ]

        # Thresholds for each variable
        thresholds = st.session_state["thresholds"]

        # Initialize Plotly figure
        fig = go.Figure()

        # Add line traces and markers for threshold violations
        for variable in ["Heartrate (bpm)", "Zucker (mmol/l)", "Sauerstoffsättigung (%)", "Heartratevariability (ms)"]:
            # Line for normal data
            fig.add_trace(go.Scatter(
                x=filtered_df["Timestamp"],
                y=filtered_df[variable],
                mode='lines+markers',
                name=variable
            ))

            # Add red triangle markers for threshold violations
            high_threshold = thresholds[variable]["high"]
            low_threshold = thresholds[variable]["low"]

            # Highlight points where thresholds are exceeded
            exceeded_df = filtered_df[
                (filtered_df[variable] > high_threshold) | 
                (filtered_df[variable] < low_threshold)
            ]

            if not exceeded_df.empty:
                fig.add_trace(go.Scatter(
                    x=exceeded_df["Timestamp"],
                    y=exceeded_df[variable],
                    mode='markers',
                    marker=dict(size=12, color='red', symbol='triangle-up'),
                    name=f"{variable} Threshold Exceeded"
                ))

        # Update layout for better visuals
        fig.update_layout(
            title=f"Historical Data for {member_name}",
            xaxis_title="Timestamp",
            yaxis_title="Values",
            hovermode="x unified",
            legend=dict(x=0, y=-0.5, orientation="h")
        )

        # Show the graph
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No historical data available yet.")



# Display goal progress with Apple-like rings
def display_activity_circle(goal, progress, target, member_name):
    percentage = min(progress / target * 100, 100)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percentage,
        title={"text": goal.replace('_', ' ').title()},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "green"},
            "steps": [
                {"range": [0, 50], "color": "lightgray"},
                {"range": [50, 100], "color": "gray"}
            ],
        }
    ))
    st.plotly_chart(fig, use_container_width=True, key=f"plot_{goal}_{member_name}")

# Display goals and allow customization
def display_goals(member_name):
    st.markdown("### Goals Progress")
    for goal, target in st.session_state["goals"].items():
        progress = st.session_state["goal_progress"][goal]
        display_activity_circle(goal, progress, target, member_name)
        st.write(f"Progress: {progress}/{target} ({(progress / target) * 100:.2f}%)")

        # Set new target
        new_target = st.number_input(
            f"Set Target for {goal.replace('_', ' ').capitalize()} (for {member_name}):",
            min_value=0.1, value=float(target), step=0.1, key=f"target_{goal}_{member_name}"
        )
        st.session_state["goals"][goal] = new_target

        # Add progress
        increment = st.number_input(
            f"Add Progress to {goal.replace('_', ' ').capitalize()} (for {member_name}):",
            min_value=0.1, value=0.1, step=0.1, key=f"increment_{goal}_{member_name}"
        )
        if st.button(f"Update {goal.replace('_', ' ').capitalize()} for {member_name}", key=f"update_{goal}_{member_name}"):
            st.session_state["goal_progress"][goal] += increment
            st.experimental_rerun()

# Display alerts and customize thresholds
def display_alerts_and_thresholds():
    st.sidebar.title("⚠️ Alerts & Notifications")
    st.sidebar.subheader("Set Alert Thresholds")
    for metric, limits in st.session_state["thresholds"].items():
        st.sidebar.number_input(f"{metric} - Low Threshold", min_value=0.0, value=float(limits["low"]), step=0.1)
        st.sidebar.number_input(f"{metric} - High Threshold", min_value=0.0, value=float(limits["high"]), step=0.1)

# Main dashboard logic
def main():
    st.title("Family Health Dashboard")

    # Ensure database is initialized
    initialize_database()
    load_csv_to_database()

    # Fetch patient data
    patients = fetch_patient_data(limit=4)

    # Tabs for each family member
    tabs = st.tabs(list(patients.keys()))
    for idx, (member_name, patient) in enumerate(patients.items()):
        with tabs[idx]:
            # Display health data
            display_health_data(member_name, patient)

            # Display historical data graph
            display_historical_graph(member_name, patient["id"])

            # Display goals
            display_goals(member_name)

    # Display alerts in the sidebar
    display_alerts_and_thresholds()

if __name__ == "__main__":
    main()
