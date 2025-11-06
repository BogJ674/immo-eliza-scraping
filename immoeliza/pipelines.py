# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re
from scrapy.exporters import CsvItemExporter


class DataCleaningPipeline:
    """
    Pipeline to clean scraped data before storage.
    Uses pattern matching to dynamically identify and clean field types.
    """

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Clean each field dynamically based on content and field name
        for field in adapter.field_names():
            value = adapter.get(field)

            # Determine cleaning method based on field name patterns and value content
            cleaned_value = self._smart_clean(field, value)
            adapter[field] = cleaned_value

        return item

    def _smart_clean(self, field_name, value):
        """
        Intelligently determine how to clean a field based on its name and value.

        Priority order:
        1. Detect by value content (has €, has m², has kWh, etc.)
        2. Detect by field name patterns (starts with 'number_', contains 'surface', etc.)
        3. Default to empty value cleaning
        """
        if not value or value == '':
            return None

        value_str = str(value).strip()
        field_lower = field_name.lower()

        # 1. CURRENCY DETECTION (by content: contains € or $ symbol)
        if '€' in value_str or '$' in value_str or field_lower in ['price', 'cadastral_income']:
            return self._clean_currency(value_str)

        # 2. AREA/SURFACE DETECTION (by content: contains m² OR field name patterns)
        if 'm²' in value_str or 'm2' in value_str or \
           'surface' in field_lower or \
           field_lower in ['garden', 'terrace', 'total_land_surface', 'livable_surface']:
            return self._clean_area(value_str)

        # 3. ENERGY DETECTION (by content: contains kWh)
        if 'kwh' in value_str.lower() or 'energy' in field_lower or 'consumption' in field_lower:
            return self._clean_energy(value_str)

        # 4. INTEGER/COUNT DETECTION (by field name: starts with 'number_' or is build_year/postal_code)
        if field_lower.startswith('number_') or \
           field_lower in ['build_year', 'postal_code', 'year_of_construction']:
            return self._clean_integer(value_str)

        # 5. BINARY DETECTION (by value content: Yes/No or by field name patterns)
        # Check if value looks like Yes/No first
        if self._looks_like_binary(value_str):
            return self._clean_binary(value_str)

        # Or if field name suggests binary
        binary_keywords = [
            'furnished', 'attic', 'garage', 'elevator', 'vat', 'leased',
            'water', 'preemption', 'cellar', 'diningroom', 'swimming_pool',
            'pool', 'disabled', 'sewer', 'gas', 'permission', 'granted',
            'connection', 'alarm', 'parking'
        ]
        if any(keyword in field_lower for keyword in binary_keywords):
            return self._clean_binary(value_str)

        # 6. DEFAULT: Clean empty representations, otherwise keep as-is
        return self._clean_empty(value_str)

    def _looks_like_binary(self, value_str):
        """Check if value looks like a Yes/No or binary response"""
        v = value_str.lower().strip()
        binary_values = ['yes', 'no', 'y', 'n', 'true', 'false', '0', '1']
        return v in binary_values

    def _clean_binary(self, value):
        """Convert Yes/No to 1/0, handle empty values"""
        if not value or value == '':
            return None

        value_str = str(value).strip().lower()

        if value_str in ['yes', 'y', '1', 'true']:
            return 1
        elif value_str in ['no', 'n', '0', 'false']:
            return 0
        elif value_str == '(information not available)' or value_str == 'not applicable':
            return None
        else:
            return None

    def _clean_area(self, value):
        """Extract numeric value from area strings (e.g., '144 m²' -> 144)"""
        if not value or value == '':
            return None

        value_str = str(value).strip()

        # Check for unavailable info
        if value_str in ['(information not available)', 'Not applicable', '']:
            return None

        # Extract number using regex
        match = re.search(r'([\d\s,]+)', value_str)
        if match:
            # Remove spaces and convert
            number_str = match.group(1).replace(' ', '').replace(',', '')
            try:
                return float(number_str) if '.' in number_str else int(number_str)
            except ValueError:
                return None

        return None

    def _clean_energy(self, value):
        """Extract numeric value from energy strings (e.g., '629 kWh/m²/year' -> 629)"""
        if not value or value == '':
            return None

        value_str = str(value).strip()

        # Check for unavailable info
        if value_str in ['(information not available)', 'Not applicable', '']:
            return None

        # Extract number using regex
        match = re.search(r'([\d\s,]+)', value_str)
        if match:
            # Remove spaces and convert
            number_str = match.group(1).replace(' ', '').replace(',', '')
            try:
                return float(number_str) if '.' in number_str else int(number_str)
            except ValueError:
                return None

        return None

    def _clean_currency(self, value):
        """Extract numeric value from currency strings (e.g., '245 000 €' -> 245000)"""
        if not value or value == '':
            return None

        value_str = str(value).strip()

        # Check for unavailable info
        if value_str in ['(information not available)', 'Not applicable', '']:
            return None

        # Remove currency symbols and spaces
        cleaned = re.sub(r'[€$\s]', '', value_str)

        try:
            return int(cleaned)
        except ValueError:
            return None

    def _clean_integer(self, value):
        """Convert to integer, handle empty values"""
        if not value or value == '':
            return None

        value_str = str(value).strip()

        # Check for unavailable info
        if value_str in ['(information not available)', 'Not applicable', '']:
            return None

        try:
            # Remove any spaces or commas
            cleaned = value_str.replace(' ', '').replace(',', '')
            return int(cleaned)
        except ValueError:
            return None

    def _clean_empty(self, value):
        """Convert various empty representations to None"""
        if not value or value == '':
            return None

        value_str = str(value).strip()

        # List of strings that represent "no data"
        empty_values = [
            '(information not available)',
            'not applicable',
            'no certificate',
            'area info not available',
            ''
        ]

        if value_str.lower() in empty_values:
            return None

        return value


class ImmoelizaPipeline:
    def process_item(self, item, spider):
        return item


class NoneAwareCsvItemExporter(CsvItemExporter):
    """
    Custom CSV exporter that writes 'None' as text instead of empty strings
    for fields that have None values.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def serialize_field(self, field, name, value):
        """Override to write 'None' for None values instead of empty string"""
        if value is None:
            return 'None'
        return super().serialize_field(field, name, value)
