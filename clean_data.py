import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt

def combine_csv_files(file1_path, file2_path, output_path, type1_name='houses', type2_name='apartments'):
    """
    Combine two CSV files and add a 'property_type' column indicating the source.

    Parameters:
    - file1_path: Path to the first CSV file
    - file2_path: Path to the second CSV file
    - output_path: Path where the combined CSV will be saved
    - type1_name: Name for the type column for file1 (default: 'houses')
    - type2_name: Name for the type column for file2 (default: 'apartments')
    """
    df1 = pd.read_csv(file1_path, low_memory=False)
    # Only set property_type if it's empty (NaN or doesn't exist)
    if 'property_type' not in df1.columns:
        df1['property_type'] = type1_name
    else:
        df1['property_type'] = df1['property_type'].fillna(type1_name)
    print(f"  - Loaded {len(df1)} rows with type '{type1_name}' from {file1_path}")
    print(f"  - Columns in {type1_name}: {len(df1.columns)}")

    df2 = pd.read_csv(file2_path, low_memory=False)
    # Only set property_type if it's empty (NaN or doesn't exist)
    if 'property_type' not in df2.columns:
        df2['property_type'] = type2_name
    else:
        df2['property_type'] = df2['property_type'].fillna(type2_name)
    print(f"  - Loaded {len(df2)} rows with type '{type2_name}' from {file2_path}")
    print(f"  - Columns in {type2_name}: {len(df2.columns)}")

    # Identify column differences
    cols_only_in_df1 = set(df1.columns) - set(df2.columns)
    cols_only_in_df2 = set(df2.columns) - set(df1.columns)

    print(f"\nColumn analysis:")
    print(f"  - Columns only in {type1_name}: {len(cols_only_in_df1)}")
    if cols_only_in_df1:
        print(f"    {sorted(cols_only_in_df1)[:5]}{'...' if len(cols_only_in_df1) > 5 else ''}")
    print(f"  - Columns only in {type2_name}: {len(cols_only_in_df2)}")
    if cols_only_in_df2:
        print(f"    {sorted(cols_only_in_df2)[:5]}{'...' if len(cols_only_in_df2) > 5 else ''}")

    # Add missing columns to both dataframes with NaN values
    for col in cols_only_in_df1:
        df2[col] = None
    for col in cols_only_in_df2:
        df1[col] = None

    # Sort columns by number of non-null values (most data first)
    # property_id always comes first
    print("\nSorting columns by data completeness...")

    # Combine both dataframes temporarily to count non-null values across all data
    temp_combined = pd.concat([df1, df2], ignore_index=True)

    # Count non-null values for each column
    non_null_counts = temp_combined.notna().sum().to_dict()

    # Remove property_id from the dict (we'll add it first manually)
    if 'property_id' in non_null_counts:
        del non_null_counts['property_id']

    # Sort columns by non-null count (descending)
    sorted_cols = sorted(non_null_counts.items(), key=lambda x: x[1], reverse=True)

    # Create final column order: property_id first, then sorted by completeness
    all_columns = ['property_id'] + [col for col, _ in sorted_cols]

    df1 = df1[all_columns]
    df2 = df2[all_columns]

    print(f"  - Columns sorted by completeness (top 10):")
    for i, (col, count) in enumerate(sorted_cols[:10]):
        percentage = (count / len(temp_combined)) * 100
        print(f"    {i+2}. {col}: {count} ({percentage:.1f}%)")

    # First, separate properties that exist in both files vs unique to each file
    df1_ids = set(df1['property_id'])
    df2_ids = set(df2['property_id'])

    common_ids = df1_ids & df2_ids
    unique_to_df1 = df1_ids - df2_ids
    unique_to_df2 = df2_ids - df1_ids

    print(f"  - Properties in {type1_name}: {len(df1_ids)}")
    print(f"  - Properties in {type2_name}: {len(df2_ids)}")
    print(f"  - Common properties (will merge): {len(common_ids)}")
    print(f"  - Unique to {type1_name}: {len(unique_to_df1)}")
    print(f"  - Unique to {type2_name}: {len(unique_to_df2)}")

    # Get unique properties from each file
    df1_unique = df1[df1['property_id'].isin(unique_to_df1)].copy()
    df2_unique = df2[df2['property_id'].isin(unique_to_df2)].copy()

    # For common properties, merge with df2 values taking precedence for non-null values
    if len(common_ids) > 0:
        df1_common = df1[df1['property_id'].isin(common_ids)].copy()
        df2_common = df2[df2['property_id'].isin(common_ids)].copy()

        # Set property_id as index for smart merging
        df1_common = df1_common.set_index('property_id')
        df2_common = df2_common.set_index('property_id')

        # Update df1_common with non-null values from df2_common
        # This fills NaN values in df1 with values from df2
        df1_common = df1_common.combine_first(df2_common)
        df1_common = df1_common.reset_index()

        # Combine all parts
        combined_df = pd.concat([df1_unique, df2_unique, df1_common], ignore_index=True)
    else:
        # No common properties, just concat unique ones
        combined_df = pd.concat([df1_unique, df2_unique], ignore_index=True)

    print(f"  - Total properties after merge: {len(combined_df)}")

    print(f"\nSaving combined data to {output_path}...")
    combined_df.to_csv(output_path, index=False)
    print("Done!")

    return combined_df

if __name__ == "__main__":
    # Define paths
    houses_csv = "data/combined_houses.csv"
    apartments_csv = "data/combined_apartments.csv"
    output_csv = "data/combined_properties1.csv"

    # Check if files exist
    if not os.path.exists(houses_csv):
        print(f"Error: {houses_csv} not found!")
        exit(1)

    if not os.path.exists(apartments_csv):
        print(f"Error: {apartments_csv} not found!")
        exit(1)

    # Combine the files
    combined_df = combine_csv_files(
        houses_csv,
        apartments_csv,
        output_csv,
        type1_name='house',
        type2_name='apartment'
    )

    # Show sample of the combined data
    print("\nSample of combined data:")
    print(combined_df[['property_id', 'price', 'municipality_url', 'property_type']].head(10))

    # # Show property type counts
    print("\nProperty type distribution:")
    print(combined_df['property_type'].value_counts())

    # # check how many swimming pools there are
    if 'swimming_pool' in combined_df.columns:
        pool_counts = combined_df['swimming_pool'].value_counts(dropna=False)
        print("\nSwimming pool distribution:")
        print(pool_counts)
