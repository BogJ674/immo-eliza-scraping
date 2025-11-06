# Clean a csv file by removing duplicates and handling missing values
import pandas as pd

def clean_csv(input_path, output_path):
    """
    Clean the CSV file by removing duplicates and handling missing values.

    Parameters:
    - input_path: Path to the input CSV file
    - output_path: Path where the cleaned CSV will be saved
    """
    print(f"Reading {input_path}...")
    df = pd.read_csv(input_path)
    print(f"  - Loaded {len(df)} rows")

    print("Cleaning data...")
    # Remove duplicates based on property_id
    initial_count = len(df)
    df = df.drop_duplicates(subset='property_id', keep='first')
    duplicates_removed = initial_count - len(df)
    print(f"  - Duplicates removed: {duplicates_removed}")
    print(f"  - Total rows after deduplication: {len(df)}")

    # Handle missing values (example: fill NaNs with 'None' for all columns)
    for column in df.columns:
        missing_count = df[column].isna().sum()
        if missing_count > 0:
            df[column] = df[column].fillna('None')
            print(f"  - Filled {missing_count} missing values in column '{column}' with 'None'")

    print(f"\nSaving cleaned data to {output_path}...")
    df.to_csv(output_path, index=False)
    print("Done!")

    return df

if __name__ == "__main__":
    input_csv = "data/cleaned_combined_properties3.csv"
    output_csv = "data/cleaned_combined_properties3.csv"

    clean_csv(input_csv, output_csv)