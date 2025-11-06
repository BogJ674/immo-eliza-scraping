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
    print(f"Reading {file1_path}...")
    df1 = pd.read_csv(file1_path)
    # Only set property_type if it's empty (NaN or doesn't exist)
    if 'property_type' not in df1.columns:
        df1['property_type'] = type1_name
    else:
        df1['property_type'] = df1['property_type'].fillna(type1_name)
    print(f"  - Loaded {len(df1)} rows with type '{type1_name}'")

    print(f"\nReading {file2_path}...")
    df2 = pd.read_csv(file2_path)
    # Only set property_type if it's empty (NaN or doesn't exist)
    if 'property_type' not in df2.columns:
        df2['property_type'] = type2_name
    else:
        df2['property_type'] = df2['property_type'].fillna(type2_name)
    print(f"  - Loaded {len(df2)} rows with type '{type2_name}'")

    print("\nCombining datasets...")
    # Combine the dataframes, aligning columns
    combined_df = pd.concat([df1, df2], ignore_index=True, sort=False)
    print(f"  - Total rows before deduplication: {len(combined_df)}")

    # Remove duplicates based on property_id
    initial_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset='property_id', keep='first')
    duplicates_removed = initial_count - len(combined_df)
    print(f"  - Duplicates removed: {duplicates_removed}")
    print(f"  - Total rows after deduplication: {len(combined_df)}")

    # Show column info
    print(f"  - Total columns: {len(combined_df.columns)}")
    print(f"\nColumn distribution:")
    print(f"  - Columns in both files: {len(set(df1.columns) & set(df2.columns))}")
    print(f"  - Columns only in {type1_name}: {len(set(df1.columns) - set(df2.columns))}")
    print(f"  - Columns only in {type2_name}: {len(set(df2.columns) - set(df1.columns))}")

    print(f"\nSaving combined data to {output_path}...")
    combined_df.to_csv(output_path, index=False)
    print("Done!")

    return combined_df

if __name__ == "__main__":
    # Define paths
    houses_csv = "data/combined_properties3.csv"
    apartments_csv = "data/immo_apartments_by_municipality_step3.csv"
    output_csv = "data/combined_properties3.csv"

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

    # Show property type counts
    print("\nProperty type distribution:")
    print(combined_df['property_type'].value_counts())

    # Create bar plot of property type counts
    print("\nGenerating bar plot...")
    plt.figure(figsize=(10, 6))
    sns.countplot(data=combined_df, x='property_type', palette='viridis')
    plt.title('Property Type Distribution', fontsize=16, fontweight='bold')
    plt.xlabel('Property Type', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.xticks(rotation=45)

    # Add count labels on top of bars
    ax = plt.gca()
    for container in ax.containers:
        ax.bar_label(container, fontsize=10)

    plt.tight_layout()
    plt.savefig('data/property_type_distribution.png', dpi=300, bbox_inches='tight')
    print("Bar plot saved to: data/property_type_distribution.png")
    plt.show()
