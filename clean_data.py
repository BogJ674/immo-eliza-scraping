import pandas as pd

def extract_from_url(url):
    """
    Extract subtype, postal code, and municipality from URL.
    Example: https://immovlan.be/en/detail/villa/for-sale/2610/wilrijk/rbu51896
    Returns: (villa, 2610, wilrijk)
    """
    if pd.isna(url) or url == 'None':
        return None, None, None
    try:
        parts = url.split('/')
        # URL format: https://immovlan.be/en/detail/{subtype}/for-sale/{postal_code}/{municipality}/{property_id}
        subtype = parts[5] if len(parts) >= 6 else None
        postal_code = parts[7] if len(parts) >= 8 else None
        municipality = parts[8] if len(parts) >= 9 else None
        return subtype, postal_code, municipality
    except:
        return None, None, None


def combine_terrace_column(row):
    if pd.notna(row.get('surface_terrace')) and row.get('surface_terrace') not in ['None', '', 0, '0']:
        return row['surface_terrace']
    elif pd.notna(row.get('terrace')) and row.get('terrace') not in ['None', '', 0, '0']:
        return row['terrace']
    return None


def combine_garden_column(row):
    if pd.notna(row.get('surface_garden')) and row.get('surface_garden') not in ['None', '', 0, '0']:
        return row['surface_garden']
    elif pd.notna(row.get('garden')) and row.get('garden') not in ['None', '', 0, '0']:
        return row['garden']
    return None


def convert_to_binary(value):
    if pd.isna(value) or value in ['None', '', 'none']:
        return 0

    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ['yes', 'true', '1', '1.0']:
            return 1
        elif value_lower in ['no', 'false', '0', '0.0', 'not equipped']:
            return 0
        elif 'equipped' in value_lower and value_lower != 'not equipped':
            return 1

    try:
        num_val = float(value)
        return 1 if num_val > 0 else 0
    except:
        return 0


def clean_and_transform_data(input_path, output_path):
    df = pd.read_csv(input_path, low_memory=False, on_bad_lines='warn')
    initial_count = len(df)
    print(f"Loaded {initial_count:,} rows")

    # 1. Remove duplicates
    df = df.drop_duplicates(subset='property_id', keep='first')
    duplicates_removed = initial_count - len(df)
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed:,} duplicates ({len(df):,} remaining)")

    # 2. Extract subtype, postal code, municipality
    df[['subtype', 'postal_code_from_url', 'municipality_from_url']] = df['url'].apply(
        lambda x: pd.Series(extract_from_url(x))
    )

    # 3. Combine terrace and garden
    df['terrace_combined'] = df.apply(combine_terrace_column, axis=1)
    df['garden_combined'] = df.apply(combine_garden_column, axis=1)

    # 4. Convert binary fields
    df['kitchen_binary'] = df['kitchen_equipment'].apply(convert_to_binary)
    df['furnished_binary'] = df['furnished'].apply(convert_to_binary)
    df['fireplace_binary'] = df['fireplace'].apply(convert_to_binary)
    df['swimming_pool_binary'] = df['swimming_pool'].apply(convert_to_binary)

    # 5. Final cleaned DataFrame
    final_df = pd.DataFrame({
        'Property ID': df['property_id'],
        'Locality name': df['municipality_from_url'],
        'Postal code': df['postal_code_from_url'],
        'Price': df['price'],
        'Type of property': df['property_type'],
        'Subtype of property': df['subtype'],
        'Type of sale': 'standard',
        'Number of rooms': df['number_of_bedrooms'],
        'Living area': df['livable_surface'],
        'Equipped kitchen': df['kitchen_binary'],
        'Furnished': df['furnished_binary'],
        'Open fire': df['fireplace_binary'],
        'Terrace': df['terrace_combined'],
        'Garden': df['garden_combined'],
        'Number of facades': df['number_of_facades'],
        'Swimming pool': df['swimming_pool_binary'],
        'State of building': df['state_of_the_property'],
        'Url': df['url']
    })

    final_df.to_csv(output_path, index=False)
    print(f"Saved {len(final_df):,} cleaned properties to {output_path}")
    return final_df


if __name__ == "__main__":
    input_csv = "data/immo_all_properties.csv"
    output_csv = "data/final_properties.csv"
    clean_and_transform_data(input_csv, output_csv)
