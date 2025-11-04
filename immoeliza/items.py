import scrapy


class PropertyItem(scrapy.Item):
    # --- Basic identifiers ---
    property_id = scrapy.Field()
    postal_code = scrapy.Field()
    municipality = scrapy.Field()
    locality = scrapy.Field()
    url = scrapy.Field()

    # --- Financial details ---
    price = scrapy.Field()
    cadastral_income = scrapy.Field()
    monthly_rental_income = scrapy.Field()
    vat = scrapy.Field()

    # --- General info ---
    state_of_the_property = scrapy.Field()
    build_year = scrapy.Field()
    availability = scrapy.Field()

    # --- Interior description ---
    number_of_bedrooms = scrapy.Field()
    surface_bedroom_1 = scrapy.Field()
    surface_bedroom_2 = scrapy.Field()
    surface_bedroom_3 = scrapy.Field()
    surface_bedroom_4 = scrapy.Field()
    livable_surface = scrapy.Field()
    total_surface = scrapy.Field()
    surface_of_living_room = scrapy.Field()
    cellar = scrapy.Field()
    surface_of_the_cellar_s = scrapy.Field()
    attic = scrapy.Field()
    attic_surface = scrapy.Field()
    veranda = scrapy.Field()
    wash_room = scrapy.Field()
    bike_storage = scrapy.Field()
    garage = scrapy.Field()
    number_of_parking_spaces_indoor = scrapy.Field()
    surface_of_the_garage = scrapy.Field()
    motorized_garage_door = scrapy.Field()
    electric_charging_station = scrapy.Field()

    # --- Kitchen and bathrooms ---
    kitchen_equipment = scrapy.Field()
    kitchen_type = scrapy.Field()
    surface_kitchen = scrapy.Field()
    water_softener = scrapy.Field()
    number_of_bathrooms = scrapy.Field()
    surface_of_the_bathroom_s = scrapy.Field()

    # --- Heating and energy ---
    low_energy_house = scrapy.Field()
    solar_panels = scrapy.Field()
    type_of_heating = scrapy.Field()
    floor_heating = scrapy.Field()
    heat_pump = scrapy.Field()
    type_of_glazing = scrapy.Field()
    bi_hourly_counter = scrapy.Field()

    # --- Equipment ---
    air_conditioning = scrapy.Field()
    domotica = scrapy.Field()
    entry_phone = scrapy.Field()
    alarm = scrapy.Field()
    security_door = scrapy.Field()
    elevator = scrapy.Field()
    hammam_sauna_jacuzzi = scrapy.Field()
    fireplace = scrapy.Field()

    # --- Outdoor description ---
    orientation_of_the_front_facade = scrapy.Field()
    number_of_facades = scrapy.Field()
    number_of_parking_places_outdoor = scrapy.Field()
    garden = scrapy.Field()
    garden_orientation = scrapy.Field()
    terrace = scrapy.Field()
    total_land_surface = scrapy.Field()
    sewer_connection = scrapy.Field()
    gas = scrapy.Field()
    running_water = scrapy.Field()
    rain_water_tank = scrapy.Field()
    swimming_pool = scrapy.Field()

    # --- Certificates and compliance ---
    specific_primary_energy_consumption = scrapy.Field()
    yearly_total_primary_energy_consumption = scrapy.Field()
    epc_peb_reference = scrapy.Field()
    validity_date_epc_peb = scrapy.Field()
    certification_electrical_installation = scrapy.Field()
    certification_electrical_installation_validity = scrapy.Field()
    certification_gasoil_tank = scrapy.Field()

    # --- Town planning and environmental risks ---
    building_permission_granted = scrapy.Field()
    planning_permission_granted = scrapy.Field()
    preemption_right = scrapy.Field()
    description_of_urbanism_infraction = scrapy.Field()
    certification_as_build = scrapy.Field()
    flooding_area_type = scrapy.Field()
    demarcated_flooding_area = scrapy.Field()
    water_sensitive_open_space_areas = scrapy.Field()
    the_property_and_or_its_surroundings_are_protected = scrapy.Field()

    # --- Misc or derived ---
    property_type = scrapy.Field()
    subtype = scrapy.Field()
