# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re


class DataCleaningPipeline:
    """
    Pipeline to clean scraped data before storage.
    Converts fields to appropriate formats as per project requirements.
    """

    # Fields that should be binary (0/1)
    BINARY_FIELDS = [
        'furnished', 'attic', 'garage', 'elevator',
        'vat', 'currently_leased', 'running_water',
        'preemption_right', 'certification_as_build_',
        'cellar', 'diningroom', 'swimming_pool',
        'access_for_disabled', 'sewer_connection', 'gas',
        'building_permission_granted', 'planning_permission_granted'
    ]

    # Fields that contain area measurements (m²)
    AREA_FIELDS = [
        'livable_surface', 'garden', 'terrace', 'total_land_surface',
        'surface_bedroom_1', 'surface_bedroom_2', 'surface_bedroom_3',
        'surface_bedroom_4', 'surface_bedroom_5', 'surface_of_living_room',
        'surface_of_the_cellar_s_', 'surface_of_the_diningroom',
        'surface_kitchen', 'surface_terrace'
    ]

    # Fields that contain energy values
    ENERGY_FIELDS = [
        'specific_primary_energy_consumption',
        'yearly_total_primary_energy_consumption'
    ]

    # Fields that contain currency values
    CURRENCY_FIELDS = [
        'price', 'cadastral_income'
    ]

    # Fields that should be integers
    INTEGER_FIELDS = [
        'number_of_bedrooms', 'number_of_garages', 'number_of_bathrooms',
        'number_of_toilets', 'number_of_facades', 'number_of_parking_places_outdoor_',
        'build_year', 'postal_code'
    ]

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Clean each field
        for field in adapter.field_names():
            value = adapter.get(field)

            # Convert binary fields
            if field in self.BINARY_FIELDS:
                adapter[field] = self._clean_binary(value)

            # Clean area fields
            elif field in self.AREA_FIELDS:
                adapter[field] = self._clean_area(value)

            # Clean energy fields
            elif field in self.ENERGY_FIELDS:
                adapter[field] = self._clean_energy(value)

            # Clean currency fields
            elif field in self.CURRENCY_FIELDS:
                adapter[field] = self._clean_currency(value)

            # Clean integer fields
            elif field in self.INTEGER_FIELDS:
                adapter[field] = self._clean_integer(value)

            # Clean generic empty values
            else:
                adapter[field] = self._clean_empty(value)

        return item

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
