from lumen.db.models.legacy_models import StateORM, DistrictORM, PoliceRangeORM, CommissionerateORM

def get_states():
    return [StateORM(id="29", name="Karnataka", active=True)]

def get_ranges():
    return [
        PoliceRangeORM(id="R1", name="Bengaluru Range", state_id="29"),
        PoliceRangeORM(id="R2", name="Mysuru Range", state_id="29"),
        PoliceRangeORM(id="R3", name="Mangaluru Range", state_id="29"),
        PoliceRangeORM(id="R4", name="Belagavi Range", state_id="29"),
        PoliceRangeORM(id="R5", name="Kalaburagi Range", state_id="29"),
        PoliceRangeORM(id="R6", name="Hubballi-Dharwad Range", state_id="29"),
    ]

def get_commissionerates():
    return [
        CommissionerateORM(id="C1", name="Bengaluru City Police", state_id="29"),
        CommissionerateORM(id="C2", name="Mysuru City Police", state_id="29"),
        CommissionerateORM(id="C3", name="Mangaluru City Police", state_id="29"),
    ]

def get_districts():
    # 31 Karnataka Districts + bounding box coordinates for hotspot generation
    districts = [
        ("0443", "Bengaluru City", "C1", None, 12.9716, 77.5946),
        ("0444", "Bengaluru Rural", None, "R1", 13.1989, 77.6250),
        ("0445", "Ramanagara", None, "R1", 12.7150, 77.2813),
        ("0446", "Chikkaballapura", None, "R1", 13.4325, 77.7274),
        ("0447", "Kolar", None, "R1", 13.1367, 78.1292),
        ("0448", "Tumakuru", None, "R1", 13.3379, 77.1173),
        ("0449", "Mysuru City", "C2", None, 12.2958, 76.6394),
        ("0450", "Mysuru District", None, "R2", 12.2958, 76.6394),
        ("0451", "Mandya", None, "R2", 12.5235, 76.8943),
        ("0452", "Hassan", None, "R2", 13.0033, 76.1004),
        ("0453", "Kodagu", None, "R2", 12.3375, 75.8069),
        ("0454", "Chamarajanagar", None, "R2", 11.9261, 76.9400),
        ("0455", "Mangaluru City", "C3", None, 12.9141, 74.8560),
        ("0456", "Dakshina Kannada", None, "R3", 12.9141, 74.8560),
        ("0457", "Udupi", None, "R3", 13.3409, 74.7421),
        ("0458", "Uttara Kannada", None, "R3", 14.8185, 74.1416),
        ("0459", "Chikkamagaluru", None, "R3", 13.3161, 75.7720),
        ("0460", "Belagavi", None, "R4", 15.8497, 74.4977),
        ("0461", "Vijayapura", None, "R4", 16.8302, 75.7100),
        ("0462", "Bagalkote", None, "R4", 16.1691, 75.6615),
        ("0463", "Gadag", None, "R6", 15.4286, 75.6316),
        ("0464", "Haveri", None, "R6", 14.7950, 75.4011),
        ("0465", "Dharwad", None, "R6", 15.4589, 75.0078),
        ("0466", "Hubballi-Dharwad City", None, "R6", 15.3647, 75.1240),
        ("0467", "Kalaburagi", None, "R5", 17.3297, 76.8343),
        ("0468", "Yadgir", None, "R5", 16.7667, 77.1333),
        ("0469", "Raichur", None, "R5", 16.2076, 77.3463),
        ("0470", "Koppal", None, "R5", 15.3464, 76.1557),
        ("0471", "Ballari", None, "R5", 15.1394, 76.9214),
        ("0472", "Bidar", None, "R5", 17.9104, 77.5199),
        ("0473", "Shivamogga", None, "R3", 13.9299, 75.5681),
        ("0474", "Davanagere", None, "R3", 14.4644, 75.9218),
        ("0475", "Chitradurga", None, "R3", 14.2251, 76.3980),
        ("0476", "Vijayanagara", None, "R5", 15.2713, 76.3900),
    ]
    return [DistrictORM(id=d[0], name=d[1], commissionerate_id=d[2], range_id=d[3], state_id="29", active=True) for d in districts]
