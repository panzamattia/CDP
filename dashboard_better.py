import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import base64
import plotly.graph_objects as go

# Set page config
st.set_page_config(page_title="Family Health Dashboard", layout="wide")

# Initialize session state
if "current_row" not in st.session_state:
    st.session_state["current_row"] = {f"Family Member {i}": 0 for i in range(1, 5)}

if "goals" not in st.session_state:
    st.session_state["goals"] = {"steps_daily": 10000, "calories": 2500, "water": 2.0}

if "goal_progress" not in st.session_state:
    st.session_state["goal_progress"] = {"steps_daily": 0, "calories": 0, "water": 0.0}

if "vital_data_history" not in st.session_state:
    st.session_state["vital_data_history"] = {f"Family Member {i}": pd.DataFrame() for i in range(1, 5)}

if "alerts" not in st.session_state:
    st.session_state["alerts"] = []

if "thresholds" not in st.session_state:
    st.session_state["thresholds"] = {
        "Heartrate (bpm)": {"low": 60, "high": 100},
        "Zucker (mmol/l)": {"low": 4.0, "high": 7.0},
        "Sauerstoffsättigung (%)": {"low": 92, "high": 100},
        "Heartratevariability (ms)": {"low": 20, "high": 80},
    }

# Patient details
patients = {
    "Family Member 1": {"name": "Sophia Smith", "age": 32, "blood_type": "A+", "allergies": ["Peanuts"], "conditions": ["Diabetes"], "image": "frau.png"},
    "Family Member 2": {"name": "James Brown", "age": 45, "blood_type": "B+", "allergies": [], "conditions": ["Hypertension"], "image": "mann.jpg"},
    "Family Member 3": {"name": "Emily Davis", "age": 28, "blood_type": "O-", "allergies": ["Pollen"], "conditions": ["Asthma"], "image": "frau.png"},
    "Family Member 4": {"name": "Michael Johnson", "age": 50, "blood_type": "AB+", "allergies": ["Shellfish"], "conditions": ["Cancer"], "image": "mann.jpg"},
}

# Helper to encode images
def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except:
        return ""

# Load CSV files
@st.cache_data
def load_csv_data():
    return {
        "Family Member 1": pd.read_csv("person_1_health_data.csv"),
        "Family Member 2": pd.read_csv("person_2_health_data.csv"),
        "Family Member 3": pd.read_csv("person_3_health_data.csv"),
        "Family Member 4": pd.read_csv("person_4_health_data.csv"),
    }

# Function to display activity circles
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

# Function to trigger alerts based on thresholds
def trigger_alerts(member_name, row_data):
    alerts = []
    thresholds = st.session_state["thresholds"]
    for key, limits in thresholds.items():
        if key in row_data:
            value = row_data[key]
            if value < limits["low"]:
                alerts.append(f"⚠️ {member_name}: {key} is TOO LOW ({value})!")
            elif value > limits["high"]:
                alerts.append(f"⚠️ {member_name}: {key} is TOO HIGH ({value})!")
    if "alerts" not in st.session_state:
        st.session_state["alerts"] = []
    st.session_state["alerts"].extend(alerts)
    for alert in alerts:
        st.error(alert)

# Function to display health data and trigger alerts
def display_health_data(member_name, df, row):
    st.markdown(f"## {member_name}")
    patient = patients[member_name]
    image_base64 = image_to_base64(patient['image'])
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <img src="data:image/png;base64,{image_base64}" alt="{member_name}" style="width: 80px; height: 80px; border-radius: 50%; margin-right: 15px;">
            <div>
                <h4 style="margin: 0;">{patient['name']}</h4>
                <p>Age: {patient['age']} | Blood Type: {patient['blood_type']}</p>
                <p>Conditions: {', '.join(patient['conditions'])}</p>
                <p>Allergies: {', '.join(patient['allergies']) if patient['allergies'] else 'None'}</p>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    row_data = {
        "Heartrate (bpm)": df['Heartrate (bpm)'][row],
        "Zucker (mmol/l)": df['Zucker (mmol/l)'][row],
        "Sauerstoffsättigung (%)": df['Sauerstoffsättigung (%)'][row],
        "Heartratevariability (ms)": df['Heartratevariability (ms)'][row],
    }
    st.write(f"**Timestamp:** {df['Timestamp'][row]}")
    for key, value in row_data.items():
        st.write(f"**{key}:** {value}")
    trigger_alerts(member_name, row_data)

# Display historical graphs
def display_historical_graph(member_name):
    history_df = st.session_state["vital_data_history"][member_name]
    if not history_df.empty:
        st.line_chart(
            history_df.set_index("Timestamp")[
                ["Heartrate (bpm)", "Zucker (mmol/l)", "Sauerstoffsättigung (%)", "Heartratevariability (ms)"]
            ]
        )
    else:
        st.info("No historical data available yet.")

# Function to display and customize goals
def display_goals(member_name):
    st.markdown("### Goals Progress")
    if "celebrated_goals" not in st.session_state:
        st.session_state["celebrated_goals"] = {goal: False for goal in st.session_state["goals"]}
    for goal, target in st.session_state["goals"].items():
        progress = st.session_state["goal_progress"][goal]
        display_activity_circle(goal, progress, target, member_name)
        percentage = (progress / target) * 100
        st.write(f"Progress: {percentage:.2f}%")
        new_target = st.number_input(
            f"Set Target for {goal.replace('_', ' ').capitalize()} (for {member_name}):",
            min_value=0.1, value=float(target), step=0.1, key=f"target_{goal}_{member_name}"
        )
        st.session_state["goals"][goal] = new_target
        increment = st.number_input(
            f"Add Progress to {goal.replace('_', ' ').capitalize()} (for {member_name}):",
            min_value=0.1, value=1.0, step=0.1, key=f"input_{goal}_{member_name}"
        )
        if st.button(f"Update {goal.replace('_', ' ').capitalize()} for {member_name}", key=f"button_{goal}_{member_name}"):
            new_progress = min(st.session_state["goal_progress"][goal] + increment, target)
            if new_progress >= target and not st.session_state["celebrated_goals"][goal]:
                st.success(f"🎉 {goal.replace('_', ' ').capitalize()} Goal Reached for {member_name}! 🎉")
                st.snow()
                st.session_state["celebrated_goals"][goal] = True
            st.session_state["goal_progress"][goal] = new_progress
            st.rerun()

# Function to display alerts and customize thresholds
def display_alerts_and_thresholds():
    st.sidebar.title("⚠️ Alerts & Notifications")
    thresholds = st.session_state["thresholds"]
    st.sidebar.subheader("Set Alert Thresholds")
    for metric, limits in thresholds.items():
        col1, col2 = st.sidebar.columns(2)
        thresholds[metric]["low"] = col1.number_input(
            f"{metric} Low", value=float(limits["low"]), step=0.1, key=f"low_{metric}"
        )
        thresholds[metric]["high"] = col2.number_input(
            f"{metric} High", value=float(limits["high"]), step=0.1, key=f"high_{metric}"
        )
    if "alerts" in st.session_state and st.session_state["alerts"]:
        st.sidebar.subheader("Active Alerts")
        for alert in st.session_state["alerts"]:
            st.sidebar.warning(alert)
    else:
        st.sidebar.info("No alerts currently.")


# Main function
def main():
    st.title("Family Health Dashboard")
    data = load_csv_data()
    tabs = st.tabs(["Family Member 1", "Family Member 2", "Family Member 3", "Family Member 4"])
    for idx, (member_name, df) in enumerate(data.items()):
        with tabs[idx]:
            row = st.session_state["current_row"][member_name]
            if row < len(df):
                display_health_data(member_name, df, row)
                st.session_state["vital_data_history"][member_name] = pd.concat(
                    [st.session_state["vital_data_history"][member_name], df.iloc[[row]]]
                ).reset_index(drop=True)
                if st.button(f"Next Data for {member_name}", key=f"next_{member_name}"):
                    st.session_state["current_row"][member_name] += 1
                    st.rerun()
                st.write("### Historical Data")
                display_historical_graph(member_name)
                st.write("### Goals")
                display_goals(member_name)
            else:
                st.write("All data has been displayed for this family member.")
    display_alerts_and_thresholds()

if __name__ == "__main__":
    main()
