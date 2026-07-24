import os

def build_intelligence_seeds():
    base_dir = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\seeds\karnataka"
    os.makedirs(base_dir, exist_ok=True)
    
    # -----------------------------------------
    # 1. GEOGRAPHY
    # -----------------------------------------
    with open(os.path.join(base_dir, 'geography.py'), 'w', encoding='utf-8') as f:
        f.write('''from app.db.models import StateORM, DistrictORM, PoliceRangeORM, CommissionerateORM

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
''')

    # -----------------------------------------
    # 2. UNITS
    # -----------------------------------------
    with open(os.path.join(base_dir, 'units.py'), 'w', encoding='utf-8') as f:
        f.write('''from app.db.models import UnitTypeORM, UnitORM

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
''')

    # -----------------------------------------
    # 3. CLASSIFICATION & INTELLIGENCE MAPS
    # -----------------------------------------
    with open(os.path.join(base_dir, 'classification.py'), 'w', encoding='utf-8') as f:
        f.write('''from app.db.models import (
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
''')

    # -----------------------------------------
    # 4. RANKS
    # -----------------------------------------
    with open(os.path.join(base_dir, 'ranks.py'), 'w', encoding='utf-8') as f:
        f.write('''from app.db.models import RankORM, DesignationORM

def get_ranks():
    ranks = [
        ("1", "DGP", 1), ("2", "ADGP", 2), ("3", "IGP", 3), ("4", "DIGP", 4),
        ("5", "SSP", 5), ("6", "SP", 6), ("7", "DySP", 7), ("8", "Inspector", 8),
        ("9", "Sub-Inspector", 9), ("10", "Assistant Sub-Inspector", 10),
        ("11", "Head Constable", 11), ("12", "Police Constable", 12)
    ]
    return [RankORM(id=r[0], name=r[1], hierarchy=r[2], active=True) for r in ranks]

def get_designations():
    desigs = [
        ("1", "DGP", 1), ("2", "ADGP", 2), ("3", "IGP", 3), ("4", "DIGP", 4),
        ("5", "SSP", 5), ("6", "SP", 6), ("7", "DySP", 7), ("8", "PI", 8),
        ("9", "PSI", 9), ("10", "ASI", 10), ("11", "HC", 11), ("12", "PC", 12)
    ]
    return [DesignationORM(id=d[0], name=d[1], sort_order=d[2], active=True) for d in desigs]
''')

    # -----------------------------------------
    # 5. FIR GENERATOR
    # -----------------------------------------
    with open(os.path.join(base_dir, 'fir_generator.py'), 'w', encoding='utf-8') as f:
        f.write('''import random
import uuid
from datetime import datetime, timedelta
import json
from app.db.models import (
    CaseORM, EmployeeORM, ComplainantDetailsORM, AccusedORM, VictimORM,
    ActSectionAssociationORM, ArrestSurrenderORM, ArrestSurrenderAccusedORM,
    VehicleORM, EvidenceDetailsORM, OperatorORM, WatchlistEntryORM, HotspotORM
)
from app.services.crime_number_service import CrimeNumberService
from app.core.hashing import hash_password
from app.db.seeds.karnataka.classification import CRIME_PROFILES, DISTRICT_PROFILES

NAMES_FIRST = ["Rahul", "Priya", "Amit", "Sneha", "Kiran", "Deepak", "Anjali", "Suresh", "Ramesh", "Kavita", "Vikas", "Pooja", "Arun", "Divya", "Sanjay", "Mohammed", "Imran", "Syed", "Abdul"]
NAMES_LAST = ["Sharma", "Patil", "Gowda", "Reddy", "Kumar", "Singh", "Rao", "Hegde", "Bhat", "Desai", "Kulkarni", "Nayak", "Shetty", "Jain", "Iyer", "Khan", "Ahmed"]

def _generate_name(): return f"{random.choice(NAMES_FIRST)} {random.choice(NAMES_LAST)}"
def _generate_ka_vehicle(): return f"KA-{random.randint(1, 68):02d}-{random.choice(['A','M','N','P','Z'])}{random.randint(1000, 9999)}"
def _generate_phone(): return f"9{random.randint(100000000, 999999999)}"
def _generate_bank(): return f"HDFC{random.randint(1000000, 9999999)}"

# -----------------------------------------
# Criminal Ecosystem
# -----------------------------------------
class Ecosystem:
    def __init__(self, size):
        self.syndicates = [
            {"name": "Peenya Vehicle Network", "type": "Vehicle Theft", "districts": ["0443"]},
            {"name": "Coastal Narcotics Syndicate", "type": "Drug Peddling", "districts": ["0455"]},
            {"name": "Ballari Mining Mafia", "type": "Illegal Mining", "districts": ["0471"]},
            {"name": "Electronic City Cyber Ring", "type": "Cyber Fraud", "districts": ["0443"]},
        ]
        
        self.repeat_offenders = []
        for _ in range(max(10, size // 10)):
            self.repeat_offenders.append({
                "name": _generate_name(),
                "age": random.randint(20, 50),
                "gender": "Male",
                "phone": _generate_phone(),
                "vehicle": _generate_ka_vehicle(),
                "syndicate": random.choice(self.syndicates) if random.random() > 0.5 else None,
                "history": 0
            })

    def get_accused(self, crime_type, district_id):
        # 30% chance to pull a repeat offender if their syndicate matches or district matches
        if random.random() > 0.7:
            valid = [o for o in self.repeat_offenders if o["syndicate"] and o["syndicate"]["type"] == crime_type and district_id in o["syndicate"]["districts"]]
            if valid:
                offender = random.choice(valid)
                offender["history"] += 1
                return offender
        
        # Otherwise new random
        return {
            "name": _generate_name(),
            "age": random.randint(18, 60),
            "gender": random.choice(["Male", "Female"]),
            "phone": _generate_phone() if random.random() > 0.5 else None,
            "vehicle": _generate_ka_vehicle() if random.random() > 0.8 else None,
            "syndicate": None,
            "history": 0
        }

# -----------------------------------------
# Employee Generation & Workload Tracker
# -----------------------------------------
class WorkloadManager:
    def __init__(self):
        self.caseloads = {}
        self.employees = []
        self.operators = []
        self.specializations = {}

    def generate(self, districts, units, ranks, designations, count):
        cmd_emp = EmployeeORM(id="EMP-CMD", kgid="KGID99999", first_name="KSP Command (OP-7729)",
                              district_id="0443", unit_id="0001", rank_id="4", designation_id="4")
        cmd_op = OperatorORM(id="OP-7729", name="KSP Command", role="command", clearance="TS/SCI",
                             unit="KSP Headquarters", rank="DIGP", date_of_entry="2010-01-01",
                             operator_id="LMN-OP-7729-X", assigned_unit="KSP HQ", status="ACTIVE",
                             kgid="KGID99999", first_name="KSP Command", district_id="0443", unit_id="0001",
                             rank_id="4", designation_id="4", biometric_hash="cmd", hashed_password=hash_password("lumen2024"))
        self.employees.append(cmd_emp)
        self.operators.append(cmd_op)

        for i in range(count):
            emp_id = f"EMP-{i:04d}"
            d = random.choice(districts)
            unit_choices = [u for u in units if u.district_id == d.id]
            unit = random.choice(unit_choices) if unit_choices else None
            
            rank = random.choice(ranks)
            desig = next((des for des in designations if des.id == rank.id), designations[-1])
            
            emp = EmployeeORM(
                id=emp_id, kgid=f"KGID{random.randint(10000, 99999)}",
                first_name=_generate_name(), district_id=d.id, unit_id=unit.id if unit else None,
                rank_id=rank.id, designation_id=desig.id
            )
            self.employees.append(emp)
            self.caseloads[emp.id] = 0
            
            # Specialization
            spec = random.choice(["Cyber", "Narcotics", "Violent", "Property", "General"])
            self.specializations[emp.id] = spec

            if i < 20:  # Create operators
                self.operators.append(OperatorORM(
                    id=f"OP-{i:04d}", name=emp.first_name, role=random.choice(["analyst", "field"]),
                    clearance="SECRET", unit="Karnataka Police", rank=rank.name, date_of_entry="2015-05-15",
                    operator_id=f"LMN-OP-{i:04d}", assigned_unit="Local PS", status="ACTIVE",
                    kgid=emp.kgid, first_name=emp.first_name, district_id=emp.district_id, unit_id=emp.unit_id,
                    rank_id=emp.rank_id, designation_id=emp.designation_id,
                    biometric_hash=f"bio{i}", hashed_password=hash_password("lumen2024")
                ))

    def assign_io(self, unit_id, crime_category):
        # 1. Filter by unit
        eligible = [e for e in self.employees if e.unit_id == unit_id and e.id in self.caseloads]
        if not eligible:
            eligible = [e for e in self.employees if e.id in self.caseloads]
        
        # 2. Try specialization
        specialized = [e for e in eligible if self.specializations.get(e.id) == crime_category]
        pool = specialized if specialized else eligible
        
        # 3. Lowest workload
        pool.sort(key=lambda x: self.caseloads[x.id])
        selected = pool[0]
        self.caseloads[selected.id] += 1
        return selected

# -----------------------------------------
# FIR GENERATOR
# -----------------------------------------
def generate_firs(count, districts, units, workload_manager: WorkloadManager):
    cases = []
    relations = []
    ecosystem = Ecosystem(count)
    
    # Pre-calculate district center bounds
    geo_bounds = {d.id: (d.latitude, d.longitude) for d in districts if hasattr(d, 'latitude') and d.latitude}
    
    now = datetime.now()
    
    for i in range(count):
        unit = random.choice(units)
        district_id = unit.district_id
        
        # 1. Crime Profile Selection
        d_profile = DISTRICT_PROFILES.get(district_id, ["Vehicle Theft", "House Break-in", "Assault", "Murder"])
        crime_name = random.choice(d_profile)
        crime = next(c for c in CRIME_PROFILES if c["name"] == crime_name)
        
        # 2. IO Assignment
        io = workload_manager.assign_io(unit.id, crime["category"])
        
        # 3. Temporal Intelligence
        # Weekends have higher probability of certain crimes
        days_ago = random.randint(1, 365)
        incident_date = now - timedelta(days=days_ago, hours=random.randint(1, 24))
        complaint_date = incident_date + timedelta(hours=random.randint(1, 48))
        fir_date = complaint_date + timedelta(hours=random.randint(1, 6))
        
        year = fir_date.year
        running = i + 1
        crime_no = CrimeNumberService.generate_crime_number(1, int(unit.district_id), int(unit.id), year, running)
        case_no = CrimeNumberService.generate_case_number(year, running)
        
        # 4. Geographic Intelligence
        center_lat, center_lon = geo_bounds.get(district_id, (12.9716, 77.5946))
        lat = random.gauss(center_lat, 0.05)
        lon = random.gauss(center_lon, 0.05)
        
        # 5. Entity Generation
        accused_data = ecosystem.get_accused(crime_name, district_id)
        
        a_orm = AccusedORM(
            id=f"ACC-{crime_no}-1", case_master_id=crime_no, name=accused_data["name"],
            age_year=accused_data["age"], gender=accused_data["gender"]
        )
        relations.append(a_orm)
        
        victim = VictimORM(id=f"VIC-{crime_no}", case_master_id=crime_no, name=_generate_name(), age_year=random.randint(18, 65), gender=random.choice(["Male", "Female"]), is_police=False)
        relations.append(victim)
        
        comp = ComplainantDetailsORM(id=f"CMP-{crime_no}", case_master_id=crime_no, name=_generate_name(), age_year=random.randint(25, 70), gender=random.choice(["Male", "Female"]))
        relations.append(comp)
        
        vehicle = None
        if accused_data["vehicle"] or crime["category"] in ["Property", "Violent"]:
            v_reg = accused_data["vehicle"] or _generate_ka_vehicle()
            vehicle = VehicleORM(id=f"VEH-{crime_no}", case_master_id=crime_no, registration_no=v_reg)
            relations.append(vehicle)
            
        evidence = None
        if crime["category"] == "Cyber":
            evidence = EvidenceDetailsORM(id=f"EVD-{crime_no}", case_master_id=crime_no, evidence_type="Digital", description=f"Seized Mobile Device {accused_data['phone']}")
            relations.append(evidence)
        elif crime["category"] == "Violent":
            evidence = EvidenceDetailsORM(id=f"EVD-{crime_no}", case_master_id=crime_no, evidence_type="Physical", description="Recovered Weapon")
            relations.append(evidence)

        # 6. Procedural Timeline & Lifecycle
        timeline_events = [
            {"date": incident_date.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": f"Incident: {crime['name']}"},
            {"date": complaint_date.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": f"Complaint received from {comp.name}"},
            {"date": fir_date.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": f"FIR Registered u/s {crime['sec']} {crime['act']}"},
            {"date": (fir_date + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": f"Investigation Assigned to {io.first_name}"}
        ]
        
        status_id = "1"
        status_text = "Under Investigation"
        
        # Arrest logic
        if random.random() > 0.4 and days_ago > 7:
            arr_date = fir_date + timedelta(days=random.randint(2, 7))
            arr = ArrestSurrenderORM(
                id=f"ARR-{crime_no}", case_master_id=crime_no, event_type="Arrest",
                event_date=arr_date, state_id="29", district_id=unit.district_id,
                police_station_id=unit.id, io_id=io.id
            )
            relations.append(arr)
            relations.append(ArrestSurrenderAccusedORM(id=f"ARRA-{crime_no}", arrest_surrender_id=arr.id, accused_id=a_orm.id, is_accused=True))
            timeline_events.append({"date": arr_date.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": f"Arrest of Accused: {a_orm.name}"})
            
            # Chargesheet logic
            if days_ago > 60 and random.random() > 0.5:
                cs_date = arr_date + timedelta(days=random.randint(30, 80))
                timeline_events.append({"date": cs_date.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": "Chargesheet Filed in Court"})
                status_id = "2"
                status_text = "Charge Sheeted"
                
        # 7. NLP Narrative Generation
        syn = f" suspected to be associated with the {accused_data['syndicate']['name']}." if accused_data['syndicate'] else "."
        narrative = f"On {incident_date.strftime('%d %B %Y')} at approximately {incident_date.strftime('%H:%M')} hours, a {crime['name'].lower()} incident occurred near coordinate ({lat:.4f}, {lon:.4f}). "
        narrative += f"The complainant, {comp.name}, reported the incident to {unit.name}. "
        narrative += f"Preliminary investigation by {io.first_name} identified {a_orm.name} as the primary suspect{syn} "
        if vehicle:
            narrative += f"A vehicle bearing registration {vehicle.registration_no} was involved. "
        if evidence:
            narrative += f"Key evidence collected: {evidence.description}. "
        narrative += f"Case registered under section {crime['sec']} of {crime['act']}."

        # 8. Neo4j Graph Intelligence Payload
        nodes = [
            {"id": a_orm.id, "label": a_orm.name, "kind": "suspect"},
            {"id": victim.id, "label": victim.name, "kind": "victim"},
            {"id": io.id, "label": io.first_name, "kind": "officer"}
        ]
        edges = [
            {"source": a_orm.id, "target": victim.id, "relation": "TARGETED"},
            {"source": io.id, "target": crime_no, "relation": "INVESTIGATES"},
            {"source": crime_no, "target": a_orm.id, "relation": "INVOLVES"}
        ]
        if accused_data['syndicate']:
            nodes.append({"id": accused_data['syndicate']['name'], "label": accused_data['syndicate']['name'], "kind": "organization"})
            edges.append({"source": a_orm.id, "target": accused_data['syndicate']['name'], "relation": "MEMBER_OF"})
        if vehicle:
            nodes.append({"id": vehicle.id, "label": vehicle.registration_no, "kind": "vehicle"})
            edges.append({"source": a_orm.id, "target": vehicle.id, "relation": "ASSOCIATED_WITH"})
        if evidence:
            nodes.append({"id": evidence.id, "label": evidence.evidence_type, "kind": "evidence"})
            edges.append({"source": crime_no, "target": evidence.id, "relation": "CONNECTED_TO"})

        network = {"nodes": nodes, "edges": edges}
        
        # 9. Assembly
        cases.append(CaseORM(
            id=crime_no,
            label=f"{unit.name} Cr.No. {running}/{year} u/s {crime['sec']} {crime['act']}",
            status=status_text,
            updated_at=timeline_events[-1]["date"],
            evidence_count=1 if evidence else 0,
            inspector=io.first_name,
            timeline=timeline_events,
            network=network,
            case_metadata={
                "bns_section": crime['sec'], "district": unit.district_id,
                "ai_structured_facts": {
                    "entities": [a_orm.name, victim.name, comp.name],
                    "locations": [{"lat": lat, "lon": lon}],
                    "vehicles": [vehicle.registration_no] if vehicle else [],
                    "evidence": [evidence.description] if evidence else [],
                    "summary": narrative
                }
            },
            crime_no=crime_no,
            case_no=case_no,
            crime_registered_date=fir_date,
            incident_from_date=incident_date,
            latitude=lat,
            longitude=lon,
            brief_facts=narrative,
            police_person_id=io.id,
            police_station_id=unit.id,
            case_category_id="1",
            gravity_offence_id=crime["gravity"],
            crime_major_head_id=crime["head"],
            case_status_id=status_id
        ))
        
        relations.append(ActSectionAssociationORM(id=f"ASA-{crime_no}", case_master_id=crime_no, act_id=crime['act'], section_id=f"{crime['act']}-{crime['sec']}"))

    return cases, relations

def generate_hotspots(count=20):
    hotspots = []
    for i in range(count):
        # Generate around Bengaluru or Mysuru
        c_lat, c_lon = random.choice([(12.9716, 77.5946), (12.2958, 76.6394)])
        hotspots.append(HotspotORM(
            id=f"HS-{i:04d}",
            label=f"Intel Zone {i}",
            x=random.gauss(c_lat, 0.02),
            y=random.gauss(c_lon, 0.02),
            intensity=random.choice(["critical", "high", "moderate", "low"]),
            probability=random.randint(50, 99),
            incidents=random.randint(5, 50),
            window_hours=72
        ))
    return hotspots

def generate_watchlist(accused_list):
    entries = []
    for i, a in enumerate(accused_list[:30]):
        entries.append(WatchlistEntryORM(
            id=f"WL-{i}", name=a.name, reason="Habitual Offender",
            risk_level=random.choice(["HIGH", "CRITICAL"]), last_seen="Karnataka"
        ))
    return entries
''')

if __name__ == "__main__":
    build_intelligence_seeds()
    print("Intelligence engine built.")
