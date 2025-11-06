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
    output_csv = "data/properties.csv"

    # clean_csv(input_csv, output_csv)

    #now let's delete some columns that are not needed for the analysis
    df = pd.read_csv(input_csv)
    columns_to_drop = ['61b91a4b75064bec8e90edc245196cae_pdf', '3db7d3c8c5b0480fbe5874334949d458_pdf', 'imag609af22983804603bea6649c89f568ac_pdf', '0aa4be20656b4c69943fca725b87c92c_jpg', '4316af2f60b841a6be640faa59e71f6e_jpg', 'opportunity_for_professional']

    df.head()

    for col in columns_to_drop:
        if col not in df.columns:
            print(f"Column '{col}' not found in DataFrame. Skipping drop for this column.")
        else:
            print(f"Dropping column '{col}'.")
            df = df.drop(columns=[col])

    df.to_csv(output_csv, index=False)

