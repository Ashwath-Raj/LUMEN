from app.db.models import (
    ActORM, SectionORM, CrimeHeadORM, CrimeSubHeadORM, CrimeHeadActSectionORM,
    CaseCategoryORM, GravityOffenceORM, CaseStatusMasterORM
)

def get_acts():
    return [
        ActORM(id="BNS2023", description="Bharatiya Nyaya Sanhita, 2023", short_name="BNS", active=True),
        ActORM(id="NDPS1985", description="Narcotic Drugs and Psychotropic Substances Act, 1985", short_name="NDPS", active=True),
        ActORM(id="IT2000", description="Information Technology Act, 2000", short_name="IT Act", active=True),
        ActORM(id="WL1972", description="Wildlife Protection Act, 1972", short_name="WPA", active=True),
        ActORM(id="MMDR1957", description="Mines and Minerals (Development and Regulation) Act, 1957", short_name="MMDR", active=True),
    ]

# Intelligence Dictionary mapping distinct crimes to their BNS/Act section and Crime Head
CRIME_PROFILES = [
    {"head": "1", "sub": "1", "name": "Murder", "act": "BNS2023", "sec": "103", "bns_desc": "Murder", "gravity": "1", "category": "Violent"},
    {"head": "2", "sub": "2", "name": "Attempt to Murder", "act": "BNS2023", "sec": "109", "bns_desc": "Attempt to Murder", "gravity": "1", "category": "Violent"},
    {"head": "3", "sub": "3", "name": "Vehicle Theft", "act": "BNS2023", "sec": "303(2)", "bns_desc": "Theft of Motor Vehicle", "gravity": "2", "category": "Property"},
    {"head": "3", "sub": "4", "name": "House Break-in", "act": "BNS2023", "sec": "305", "bns_desc": "Theft in dwelling house", "gravity": "2", "category": "Property"},
    {"head": "4", "sub": "5", "name": "Chain Snatching", "act": "BNS2023", "sec": "309(4)", "bns_desc": "Robbery / Snatching", "gravity": "1", "category": "Property"},
    {"head": "5", "sub": "6", "name": "Organized Extortion", "act": "BNS2023", "sec": "308", "bns_desc": "Extortion", "gravity": "1", "category": "Organized"},
    {"head": "6", "sub": "7", "name": "Cyber Fraud", "act": "IT2000", "sec": "66D", "bns_desc": "Cheating by personation by using computer resource", "gravity": "2", "category": "Cyber"},
    {"head": "7", "sub": "8", "name": "Drug Peddling", "act": "NDPS1985", "sec": "21", "bns_desc": "Manufactured drugs", "gravity": "1", "category": "Narcotics"},
    {"head": "7", "sub": "9", "name": "Coastal Smuggling", "act": "NDPS1985", "sec": "23", "bns_desc": "Illegal import/export", "gravity": "1", "category": "Narcotics"},
    {"head": "8", "sub": "10", "name": "Illegal Mining", "act": "MMDR1957", "sec": "4(1)", "bns_desc": "Mining without license", "gravity": "2", "category": "Organized"},
    {"head": "9", "sub": "11", "name": "Forest Offences", "act": "WL1972", "sec": "9", "bns_desc": "Prohibition of hunting", "gravity": "2", "category": "Wildlife"},
]

def get_sections():
    return [SectionORM(id=f"{p['act']}-{p['sec']}", act_code=p['act'], section_code=p['sec'], description=p['bns_desc'], active=True) for p in CRIME_PROFILES]

def get_crime_heads():
    # Unique heads
    heads = {p['head']: p['category'] for p in CRIME_PROFILES}
    return [CrimeHeadORM(id=h, group_name=name, active=True) for h, name in heads.items()]

def get_crime_sub_heads():
    return [CrimeSubHeadORM(id=p['sub'], head_id=p['head'], name=p['name'], seq_id=int(p['sub'])) for p in CRIME_PROFILES]

def get_master_lookups():
    return [
        CaseCategoryORM(id="1", name="FIR"), CaseCategoryORM(id="2", name="UDR"),
        GravityOffenceORM(id="1", lookup_value="Heinous"), GravityOffenceORM(id="2", lookup_value="Non-Heinous"),
        CaseStatusMasterORM(id="1", name="Under Investigation"),
        CaseStatusMasterORM(id="2", name="Charge Sheeted"),
        CaseStatusMasterORM(id="3", name="Closed (B Report)"),
    ]

# District weighting
DISTRICT_PROFILES = {
    "0443": ["Cyber Fraud", "Cyber Fraud", "Vehicle Theft", "Chain Snatching", "House Break-in", "Organized Extortion"], # Bengaluru
    "0455": ["Drug Peddling", "Coastal Smuggling", "Murder", "Attempt to Murder"], # Mangaluru
    "0471": ["Illegal Mining", "Organized Extortion", "Attempt to Murder"], # Ballari
    "0453": ["Forest Offences", "House Break-in"], # Kodagu
    "0460": ["Vehicle Theft", "House Break-in", "Murder"], # Belagavi
    "0449": ["House Break-in", "Chain Snatching", "Vehicle Theft"], # Mysuru
}
