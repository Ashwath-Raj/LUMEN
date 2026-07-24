from lumen.db.models.legacy_models import UnitTypeORM, UnitORM

def get_unit_types():
    return [UnitTypeORM(id="1", name="Police Station", city_dist_state="District")]

def get_units():
    # Hardcoded prominent units for the main districts to allow intelligent assignments
    return [
        # Bengaluru City
        UnitORM(id="0001", name="Vidhana Soudha PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0002", name="High Grounds PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0003", name="Cubbon Park PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0004", name="Indiranagar PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0005", name="Koramangala PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0006", name="Peenya PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0007", name="Whitefield PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0008", name="Electronic City PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0009", name="Cyber Crime PS", type_id="1", state_id="29", district_id="0443", active=True),
        
        # Mysuru City
        UnitORM(id="0101", name="Devaraja PS", type_id="1", state_id="29", district_id="0449", active=True),
        UnitORM(id="0102", name="Krishnaraja PS", type_id="1", state_id="29", district_id="0449", active=True),
        UnitORM(id="0103", name="Saraswathipuram PS", type_id="1", state_id="29", district_id="0449", active=True),
        
        # Mangaluru City
        UnitORM(id="0201", name="Mangaluru North PS", type_id="1", state_id="29", district_id="0455", active=True),
        UnitORM(id="0202", name="Mangaluru South PS", type_id="1", state_id="29", district_id="0455", active=True),
        UnitORM(id="0203", name="Panambur PS", type_id="1", state_id="29", district_id="0455", active=True),
        
        # Belagavi
        UnitORM(id="0301", name="Market PS", type_id="1", state_id="29", district_id="0460", active=True),
        UnitORM(id="0302", name="Camp PS", type_id="1", state_id="29", district_id="0460", active=True),
        
        # Hubballi-Dharwad
        UnitORM(id="0401", name="Hubballi Town PS", type_id="1", state_id="29", district_id="0466", active=True),
        UnitORM(id="0402", name="Dharwad Suburban PS", type_id="1", state_id="29", district_id="0466", active=True),

        # Ballari
        UnitORM(id="0501", name="Brucepet PS", type_id="1", state_id="29", district_id="0471", active=True),
        
        # Kodagu
        UnitORM(id="0601", name="Madikeri Town PS", type_id="1", state_id="29", district_id="0453", active=True),
    ]
