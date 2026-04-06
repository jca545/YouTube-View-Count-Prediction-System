import os
import pandas as pd

def check_csv_missing_values(directory="."):
    """
    Reads all CSV files in the given directory,
    checks for missing values, and reports which files have them.
    """
    csv_files = [f for f in os.listdir(directory) if f.lower().endswith(".csv")]

    if not csv_files:
        print("No CSV files found in directory.")
        return

    for file in csv_files:
        file_path = os.path.join(directory, file)
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"❌ Could not read {file}: {e}")
            continue

        if df.isnull().values.any():
            missing_info = df.isnull().sum()
            print(f"⚠ Missing values found in: {file}")
            print(missing_info[missing_info > 0])
            print("-" * 50)
        else:
            print(f"✅ No missing values in: {file}")

# Example usage:
check_csv_missing_values(".")
