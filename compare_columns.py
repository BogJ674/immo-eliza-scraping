#split the cleaned_combined_properties3.csv into two dataframes and compare the columns
import pandas as pd

def compare_csv_columns(file_path):
    """
    Compare the columns of the cleaned combined CSV file.

    Parameters:
    - file_path: Path to the cleaned combined CSV file
    """
    df = pd.read_csv(file_path)
    print(f"Loaded {len(df)} rows")

    # Separate dataframes based on property_type
    df_houses = df[df['property_type'] == 'house']
    df_apartments = df[df['property_type'] == 'apartment']

    #drop columns that are completely empty in both dataframes
    df_houses = df_houses.dropna(axis=1, how='all')
    df_apartments = df_apartments.dropna(axis=1, how='all')

    print(f"\nHouse DataFrame:")
    print(f"  - Rows: {len(df_houses)}")
    print(f"  - Columns: {len(df_houses.columns)}")

    print(f"\nApartment DataFrame:")
    print(f"  - Rows: {len(df_apartments)}")
    print(f"  - Columns: {len(df_apartments.columns)}")

    # Compare columns
    house_columns = set(df_houses.columns)
    apartment_columns = set(df_apartments.columns)

    common_columns = house_columns & apartment_columns
    house_only_columns = house_columns - apartment_columns
    apartment_only_columns = apartment_columns - house_columns

    print(f"\nColumn comparison:")
    print(f"  - Common columns: {len(common_columns)}")
    print(f"  - Columns only in houses: {len(house_only_columns)}")
    print(f"  - Columns only in apartments: {len(apartment_only_columns)}")

if __name__ == "__main__":
    cleaned_combined_csv = "data/combined_properties3.csv"
    compare_csv_columns(cleaned_combined_csv)