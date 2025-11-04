#!/usr/bin/env python3
"""
Test script for the DataCleaningPipeline
Verifies that data is cleaned correctly according to project requirements
Tests DYNAMIC field detection - no hardcoded field lists!
"""

from immoeliza.pipelines import DataCleaningPipeline
from immoeliza.items import PropertyItem


def test_pipeline():
    """Test the data cleaning pipeline with sample data"""
    pipeline = DataCleaningPipeline()

    # Create a sample item with raw scraped data
    item = PropertyItem()
    item['price'] = '245 000 €'
    item['cadastral_income'] = '758 €'
    item['livable_surface'] = '144 m²'
    item['garden'] = 'Yes'
    item['terrace'] = 'Yes'
    item['total_land_surface'] = '220 m²'
    item['furnished'] = 'No'
    item['attic'] = 'Yes'
    item['garage'] = 'Yes'
    item['number_of_bedrooms'] = '3'
    item['number_of_garages'] = '1'
    item['number_of_bathrooms'] = '1'
    item['number_of_toilets'] = '1'
    item['number_of_facades'] = '3'
    item['number_of_parking_places_outdoor_'] = '2'
    item['specific_primary_energy_consumption'] = '629 kWh/m²/year'
    item['vat'] = 'No'
    item['currently_leased'] = 'No'
    item['running_water'] = 'Yes'
    item['elevator'] = 'No'
    item['build_year'] = '1957'
    item['postal_code'] = '2480'
    item['municipality'] = 'dessel'
    item['property_id'] = 'RBU60928'
    item['url'] = 'https://immovlan.be/en/detail/residence/for-sale/2480/dessel/rbu60928'
    item['epc_peb_reference'] = '20250205-0003522307-RES-1'
    item['certification_electrical_installation'] = 'No, certificate does not comply'
    item['preemption_right'] = 'No'
    item['certification_as_build_'] = 'No'
    item['flooding_area_type'] = 'no flooding area'
    item['demarcated_flooding_area'] = '(information not available)'

    # Process the item through the pipeline
    cleaned_item = pipeline.process_item(item, None)

    # Print results
    print("=" * 80)
    print("DATA CLEANING PIPELINE TEST RESULTS")
    print("=" * 80)
    print()

    # Test currency fields
    print("CURRENCY FIELDS:")
    print(f"  price: '{item['price']}' → {cleaned_item['price']}")
    assert cleaned_item['price'] == 245000, f"Expected 245000, got {cleaned_item['price']}"
    print(f"  cadastral_income: '{item['cadastral_income']}' → {cleaned_item['cadastral_income']}")
    assert cleaned_item['cadastral_income'] == 758, f"Expected 758, got {cleaned_item['cadastral_income']}"
    print("  ✓ Currency fields cleaned correctly")
    print()

    # Test area fields
    print("AREA FIELDS:")
    print(f"  livable_surface: '{item['livable_surface']}' → {cleaned_item['livable_surface']}")
    assert cleaned_item['livable_surface'] == 144, f"Expected 144, got {cleaned_item['livable_surface']}"
    print(f"  total_land_surface: '{item['total_land_surface']}' → {cleaned_item['total_land_surface']}")
    assert cleaned_item['total_land_surface'] == 220, f"Expected 220, got {cleaned_item['total_land_surface']}"
    print("  ✓ Area fields cleaned correctly")
    print()

    # Test binary fields
    print("BINARY FIELDS:")
    print(f"  furnished: '{item['furnished']}' → {cleaned_item['furnished']}")
    assert cleaned_item['furnished'] == 0, f"Expected 0, got {cleaned_item['furnished']}"
    print(f"  attic: '{item['attic']}' → {cleaned_item['attic']}")
    assert cleaned_item['attic'] == 1, f"Expected 1, got {cleaned_item['attic']}"
    print(f"  garage: '{item['garage']}' → {cleaned_item['garage']}")
    assert cleaned_item['garage'] == 1, f"Expected 1, got {cleaned_item['garage']}"
    print(f"  elevator: '{item['elevator']}' → {cleaned_item['elevator']}")
    assert cleaned_item['elevator'] == 0, f"Expected 0, got {cleaned_item['elevator']}"
    print("  ✓ Binary fields cleaned correctly")
    print()

    # Test integer fields
    print("INTEGER FIELDS:")
    print(f"  number_of_bedrooms: '{item['number_of_bedrooms']}' → {cleaned_item['number_of_bedrooms']}")
    assert cleaned_item['number_of_bedrooms'] == 3, f"Expected 3, got {cleaned_item['number_of_bedrooms']}"
    print(f"  build_year: '{item['build_year']}' → {cleaned_item['build_year']}")
    assert cleaned_item['build_year'] == 1957, f"Expected 1957, got {cleaned_item['build_year']}"
    print(f"  postal_code: '{item['postal_code']}' → {cleaned_item['postal_code']}")
    assert cleaned_item['postal_code'] == 2480, f"Expected 2480, got {cleaned_item['postal_code']}"
    print("  ✓ Integer fields cleaned correctly")
    print()

    # Test energy fields
    print("ENERGY FIELDS:")
    print(f"  specific_primary_energy_consumption: '{item['specific_primary_energy_consumption']}' → {cleaned_item['specific_primary_energy_consumption']}")
    assert cleaned_item['specific_primary_energy_consumption'] == 629, f"Expected 629, got {cleaned_item['specific_primary_energy_consumption']}"
    print("  ✓ Energy fields cleaned correctly")
    print()

    # Test empty value handling
    print("EMPTY VALUE HANDLING:")
    print(f"  demarcated_flooding_area: '{item['demarcated_flooding_area']}' → {cleaned_item['demarcated_flooding_area']}")
    assert cleaned_item['demarcated_flooding_area'] is None, f"Expected None, got {cleaned_item['demarcated_flooding_area']}"
    print("  ✓ Empty values converted to None correctly")
    print()

    # Test text fields (should remain unchanged)
    print("TEXT FIELDS (unchanged):")
    print(f"  municipality: '{item['municipality']}' → {cleaned_item['municipality']}")
    assert cleaned_item['municipality'] == 'dessel', f"Expected 'dessel', got {cleaned_item['municipality']}"
    print(f"  property_id: '{item['property_id']}' → {cleaned_item['property_id']}")
    assert cleaned_item['property_id'] == 'RBU60928', f"Expected 'RBU60928', got {cleaned_item['property_id']}"
    print("  ✓ Text fields preserved correctly")
    print()

    print("=" * 80)
    print("ALL TESTS PASSED! ✓")
    print("=" * 80)
    print()
    print("The DataCleaningPipeline is working correctly and will:")
    print("  • Convert currency values (€) to integers")
    print("  • Convert area values (m²) to integers/floats")
    print("  • Convert Yes/No to 1/0 for binary fields")
    print("  • Convert string numbers to integers")
    print("  • Convert energy values (kWh/m²/year) to integers")
    print("  • Convert '(information not available)' and similar to None")
    print("  • Preserve text fields as-is")
    print()
    print("=" * 80)
    print("TESTING DYNAMIC FIELD DETECTION")
    print("=" * 80)
    print()
    print("Testing with UNKNOWN field names (not in any hardcoded list):")
    print()

    # Test with completely new field names that weren't hardcoded
    dynamic_item = PropertyItem()
    dynamic_item['sale_price_euros'] = '350 000 €'  # Should detect € and clean
    dynamic_item['bedroom_1_surface_area'] = '18 m²'  # Should detect m² and clean
    dynamic_item['has_solar_panels'] = 'Yes'  # Should detect Yes/No and clean
    dynamic_item['number_of_windows'] = '12'  # Should detect number_ prefix and clean
    dynamic_item['annual_energy_usage'] = '450 kWh/year'  # Should detect kWh and clean
    dynamic_item['property_description'] = 'Beautiful house'  # Should preserve text

    cleaned_dynamic = pipeline.process_item(dynamic_item, None)

    # Test dynamic detection
    print(f"  sale_price_euros: '{dynamic_item['sale_price_euros']}' → {cleaned_dynamic['sale_price_euros']}")
    assert cleaned_dynamic['sale_price_euros'] == 350000, "Dynamic currency detection failed"

    print(f"  bedroom_1_surface_area: '{dynamic_item['bedroom_1_surface_area']}' → {cleaned_dynamic['bedroom_1_surface_area']}")
    assert cleaned_dynamic['bedroom_1_surface_area'] == 18, "Dynamic area detection failed"

    print(f"  has_solar_panels: '{dynamic_item['has_solar_panels']}' → {cleaned_dynamic['has_solar_panels']}")
    assert cleaned_dynamic['has_solar_panels'] == 1, "Dynamic binary detection failed"

    print(f"  number_of_windows: '{dynamic_item['number_of_windows']}' → {cleaned_dynamic['number_of_windows']}")
    assert cleaned_dynamic['number_of_windows'] == 12, "Dynamic integer detection failed"

    print(f"  annual_energy_usage: '{dynamic_item['annual_energy_usage']}' → {cleaned_dynamic['annual_energy_usage']}")
    assert cleaned_dynamic['annual_energy_usage'] == 450, "Dynamic energy detection failed"

    print(f"  property_description: '{dynamic_item['property_description']}' → '{cleaned_dynamic['property_description']}'")
    assert cleaned_dynamic['property_description'] == 'Beautiful house', "Text preservation failed"

    print()
    print("  ✓ Dynamic field detection works! No hardcoded lists needed!")
    print()


if __name__ == '__main__':
    test_pipeline()
