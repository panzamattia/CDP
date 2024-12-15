import sqlite3
import pandas as pd

# Function to initialize the database
def initialize_database():
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    # Create the patients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        blood_type TEXT,
        allergies TEXT,
        conditions TEXT,
        image TEXT
    )
    ''')

    # Create the historical data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historical_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        timestamp TEXT,
        heartrate REAL,
        blood_sugar REAL,
        oxygen_saturation REAL,
        hr_variability REAL,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    )
    ''')

    # Insert sample patient data if table is empty
    cursor.execute("SELECT COUNT(*) FROM patients")
    if cursor.fetchone()[0] == 0:
        sample_patients = [
            ("Sophia Smith", 32, "A+", "Peanuts", "Diabetes", "frau.png"),
            ("James Brown", 45, "B+", "None", "Hypertension", "mann.jpg"),
            ("Emily Davis", 28, "O-", "Pollen", "Asthma", "frau.png"),
            ("Michael Johnson", 50, "AB+", "Shellfish", "Cancer", "mann.jpg")
        ]
        cursor.executemany('''
        INSERT INTO patients (name, age, blood_type, allergies, conditions, image)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_patients)
        print("Patient data initialized.")

    conn.commit()
    conn.close()

# Function to load historical data from CSV into the database
def load_csv_to_database():
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()

    # Map CSV files to patient IDs
    csv_files = {
        1: "person_1_fixed.csv",
        2: "person_2_fixed.csv",
        3: "person_3_fixed.csv",
        4: "person_4_fixed.csv"
    }

    # Insert data from CSV into the historical_data table
    for patient_id, file in csv_files.items():
        try:
            # Load CSV file
            df = pd.read_csv(file)
            df = df.rename(columns={
                "Timestamp": "timestamp",
                "Heartrate (bpm)": "heartrate",
                "Zucker (mmol/l)": "blood_sugar",
                "Sauerstoffsättigung (%)": "oxygen_saturation",
                "Heartratevariability (ms)": "hr_variability"
            })

            # Insert rows into the database
            for _, row in df.iterrows():
                cursor.execute('''
                INSERT INTO historical_data (patient_id, timestamp, heartrate, blood_sugar, oxygen_saturation, hr_variability)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (patient_id, row['timestamp'], row['heartrate'], row['blood_sugar'], row['oxygen_saturation'], row['hr_variability']))

            print(f"Data from {file} loaded successfully!")
        except Exception as e:
            print(f"Error loading {file}: {e}")

    conn.commit()
    conn.close()

# Main function to set up the database
def setup_database():
    print("Initializing the database...")
    initialize_database()
    print("Loading CSV data into the database...")
    load_csv_to_database()
    print("Database setup complete!")

# Run the setup
if __name__ == "__main__":
    setup_database()
