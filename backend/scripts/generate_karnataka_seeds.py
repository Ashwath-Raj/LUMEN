import os

def create_seeds():
    base_dir = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\seeds\karnataka"
    os.makedirs(base_dir, exist_ok=True)
    
    # 1. __init__.py
    with open(os.path.join(base_dir, '__init__.py'), 'w') as f:
        f.write("")
        
    # 2. Master Data: States & Districts
    with open(os.path.join(base_dir, 'geography.py'), 'w') as f:
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
    # 31 Karnataka Districts
    districts = [
        ("0443", "Bengaluru City", "C1", None),
        ("0444", "Bengaluru Rural", None, "R1"),
        ("0445", "Ramanagara", None, "R1"),
        ("0446", "Chikkaballapura", None, "R1"),
        ("0447", "Kolar", None, "R1"),
        ("0448", "Tumakuru", None, "R1"),
        ("0449", "Mysuru City", "C2", None),
        ("0450", "Mysuru District", None, "R2"),
        ("0451", "Mandya", None, "R2"),
        ("0452", "Hassan", None, "R2"),
        ("0453", "Kodagu", None, "R2"),
        ("0454", "Chamarajanagar", None, "R2"),
        ("0455", "Mangaluru City", "C3", None),
        ("0456", "Dakshina Kannada", None, "R3"),
        ("0457", "Udupi", None, "R3"),
        ("0458", "Uttara Kannada", None, "R3"),
        ("0459", "Chikkamagaluru", None, "R3"),
        ("0460", "Belagavi", None, "R4"),
        ("0461", "Vijayapura", None, "R4"),
        ("0462", "Bagalkote", None, "R4"),
        ("0463", "Gadag", None, "R6"),
        ("0464", "Haveri", None, "R6"),
        ("0465", "Dharwad", None, "R6"),
        ("0466", "Hubballi-Dharwad City", None, "R6"),
        ("0467", "Kalaburagi", None, "R5"),
        ("0468", "Yadgir", None, "R5"),
        ("0469", "Raichur", None, "R5"),
        ("0470", "Koppal", None, "R5"),
        ("0471", "Ballari", None, "R5"),
        ("0472", "Bidar", None, "R5"),
        ("0473", "Shivamogga", None, "R3"),
        ("0474", "Davanagere", None, "R3"),
        ("0475", "Chitradurga", None, "R3"),
        ("0476", "Vijayanagara", None, "R5"),
    ]
    return [DistrictORM(id=d[0], name=d[1], commissionerate_id=d[2], range_id=d[3], state_id="29", active=True) for d in districts]
''')

    # 3. Units & Stations
    with open(os.path.join(base_dir, 'units.py'), 'w') as f:
        f.write('''from app.db.models import UnitTypeORM, UnitORM

def get_unit_types():
    return [
        UnitTypeORM(id="1", name="Police Station", city_dist_state="District"),
        UnitTypeORM(id="2", name="Circle Office", city_dist_state="District"),
        UnitTypeORM(id="3", name="Sub-Division Office", city_dist_state="District"),
    ]

def get_units():
    # Representative stations for Bengaluru (0443) and Mysuru (0449)
    return [
        UnitORM(id="0001", name="Vidhana Soudha PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0002", name="High Grounds PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0003", name="Cubbon Park PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0004", name="Indiranagar PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0005", name="Koramangala PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0006", name="Peenya PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0007", name="Whitefield PS", type_id="1", state_id="29", district_id="0443", active=True),
        UnitORM(id="0008", name="Electronic City PS", type_id="1", state_id="29", district_id="0443", active=True),
        
        UnitORM(id="0101", name="Devaraja PS", type_id="1", state_id="29", district_id="0449", active=True),
        UnitORM(id="0102", name="Krishnaraja PS", type_id="1", state_id="29", district_id="0449", active=True),
        UnitORM(id="0103", name="Saraswathipuram PS", type_id="1", state_id="29", district_id="0449", active=True),
    ]
''')

    # 4. Ranks & Roles
    with open(os.path.join(base_dir, 'ranks.py'), 'w') as f:
        f.write('''from app.db.models import RankORM, DesignationORM

def get_ranks():
    ranks = [
        ("1", "Director General of Police", 1),
        ("2", "Additional Director General of Police", 2),
        ("3", "Inspector General of Police", 3),
        ("4", "Deputy Inspector General of Police", 4),
        ("5", "Senior Superintendent of Police", 5),
        ("6", "Superintendent of Police", 6),
        ("7", "Deputy Superintendent of Police", 7),
        ("8", "Inspector of Police", 8),
        ("9", "Sub-Inspector of Police", 9),
        ("10", "Assistant Sub-Inspector", 10),
        ("11", "Head Constable", 11),
        ("12", "Police Constable", 12),
    ]
    return [RankORM(id=r[0], name=r[1], hierarchy=r[2], active=True) for r in ranks]

def get_designations():
    desigs = [
        ("1", "DGP", 1),
        ("2", "ADGP", 2),
        ("3", "IGP", 3),
        ("4", "DIGP", 4),
        ("5", "SSP", 5),
        ("6", "SP", 6),
        ("7", "DySP", 7),
        ("8", "PI", 8),
        ("9", "PSI", 9),
        ("10", "ASI", 10),
        ("11", "HC", 11),
        ("12", "PC", 12),
        ("13", "Station House Officer", 8),
        ("14", "Investigating Officer", 9),
    ]
    return [DesignationORM(id=d[0], name=d[1], sort_order=d[2], active=True) for d in desigs]
''')

    # 5. Crime Classification (BNS)
    with open(os.path.join(base_dir, 'classification.py'), 'w') as f:
        f.write('''from app.db.models import (
    ActORM, SectionORM, CrimeHeadORM, CrimeSubHeadORM, CrimeHeadActSectionORM,
    CaseCategoryORM, GravityOffenceORM, CaseStatusMasterORM
)

def get_acts():
    return [
        ActORM(id="BNS2023", description="Bharatiya Nyaya Sanhita, 2023", short_name="BNS", active=True),
        ActORM(id="IPC1860", description="Indian Penal Code, 1860", short_name="IPC", active=True),
        ActORM(id="NDPS1985", description="Narcotic Drugs and Psychotropic Substances Act, 1985", short_name="NDPS", active=True),
    ]

def get_sections():
    return [
        SectionORM(id="BNS-103", act_code="BNS2023", section_code="103", description="Murder", active=True),
        SectionORM(id="BNS-109", act_code="BNS2023", section_code="109", description="Attempt to Murder", active=True),
        SectionORM(id="BNS-303", act_code="BNS2023", section_code="303", description="Theft", active=True),
        SectionORM(id="BNS-305", act_code="BNS2023", section_code="305", description="Extortion", active=True),
        SectionORM(id="BNS-309", act_code="BNS2023", section_code="309", description="Robbery", active=True),
        SectionORM(id="BNS-310", act_code="BNS2023", section_code="310", description="Dacoity", active=True),
        SectionORM(id="BNS-111", act_code="BNS2023", section_code="111", description="Organised Crime", active=True),
        SectionORM(id="NDPS-21", act_code="NDPS1985", section_code="21", description="Punishment for contravention in relation to manufactured drugs and preparations", active=True),
    ]

def get_crime_heads():
    return [
        CrimeHeadORM(id="1", group_name="Murder", active=True),
        CrimeHeadORM(id="2", group_name="Attempt to Murder", active=True),
        CrimeHeadORM(id="3", group_name="Theft", active=True),
        CrimeHeadORM(id="4", group_name="Robbery", active=True),
        CrimeHeadORM(id="5", group_name="Dacoity", active=True),
        CrimeHeadORM(id="6", group_name="Organised Crime", active=True),
        CrimeHeadORM(id="7", group_name="Narcotics", active=True),
    ]

def get_crime_sub_heads():
    return [
        CrimeSubHeadORM(id="1", head_id="1", name="Murder for Gain", seq_id=1),
        CrimeSubHeadORM(id="2", head_id="1", name="Murder due to Rivalry", seq_id=2),
        CrimeSubHeadORM(id="3", head_id="3", name="Automobile Theft", seq_id=1),
        CrimeSubHeadORM(id="4", head_id="3", name="House Theft", seq_id=2),
        CrimeSubHeadORM(id="5", head_id="7", name="Drug Peddling", seq_id=1),
    ]

def get_master_lookups():
    return [
        CaseCategoryORM(id="1", name="FIR"),
        CaseCategoryORM(id="2", name="UDR"),
        CaseCategoryORM(id="3", name="PAR"),
    ] + [
        GravityOffenceORM(id="1", lookup_value="Heinous"),
        GravityOffenceORM(id="2", lookup_value="Non-Heinous"),
    ] + [
        CaseStatusMasterORM(id="1", name="Under Investigation"),
        CaseStatusMasterORM(id="2", name="Charge Sheeted"),
        CaseStatusMasterORM(id="3", name="Closed (B Report)"),
        CaseStatusMasterORM(id="4", name="Closed (C Report)"),
    ]
''')

    # 6. Generator
    with open(os.path.join(base_dir, 'fir_generator.py'), 'w') as f:
        f.write('''import random
from datetime import datetime, timedelta
import json
from app.db.models import (
    CaseORM, EmployeeORM, ComplainantDetailsORM, AccusedORM, VictimORM,
    ActSectionAssociationORM, ArrestSurrenderORM, ArrestSurrenderAccusedORM,
    VehicleORM, EvidenceDetailsORM, OperatorORM, WatchlistEntryORM
)
from app.services.crime_number_service import CrimeNumberService

# Realistic Indian Data Pools
NAMES_FIRST = ["Rahul", "Priya", "Amit", "Sneha", "Kiran", "Deepak", "Anjali", "Suresh", "Ramesh", "Kavita", "Vikas", "Pooja", "Arun", "Divya", "Sanjay"]
NAMES_LAST = ["Sharma", "Patil", "Gowda", "Reddy", "Kumar", "Singh", "Rao", "Hegde", "Bhat", "Desai", "Kulkarni", "Nayak", "Shetty", "Jain", "Iyer"]
LOCATIONS = ["MG Road", "Indiranagar", "Koramangala", "Jayanagar", "Whitefield", "Electronic City", "Malleswaram", "Rajajinagar", "Hebbal", "Yelahanka", "Peenya Industrial Area"]

def _generate_name():
    return f"{random.choice(NAMES_FIRST)} {random.choice(NAMES_LAST)}"

def _generate_ka_vehicle():
    return f"KA-{random.randint(1, 68):02d}-{random.choice(['A','B','C','D','E','F','G','H','J','K'])}{random.choice(['A','B','C','D','E','F','G','H','J','K'])}-{random.randint(1000, 9999)}"

def generate_employees(districts, units, ranks, designations, count=50):
    employees = []
    operators = []
    
    # Specific Command Operator for UI
    cmd_emp = EmployeeORM(id="EMP-CMD", kgid="KGID99999", first_name="KSP Command (OP-7729)",
                          district_id="0443", unit_id="0001", rank_id="4", designation_id="4")
    cmd_op = OperatorORM(id="OP-7729", name="KSP Command (OP-7729)", role="command", clearance="TS/SCI",
                         unit="KSP Headquarters", rank="DIGP", date_of_entry="2010-01-01",
                         operator_id="LMN-OP-7729-X", assigned_unit="KSP HQ", status="ACTIVE",
                         kgid="KGID99999", first_name="KSP Command", district_id="0443", unit_id="0001",
                         rank_id="4", designation_id="4")
    employees.append(cmd_emp)
    operators.append(cmd_op)

    for i in range(count):
        emp_id = f"EMP-{i:04d}"
        d = random.choice(districts)
        unit = random.choice([u for u in units if u.district_id == d.id]) if any(u.district_id == d.id for u in units) else None
        
        emp = EmployeeORM(
            id=emp_id,
            kgid=f"KGID{random.randint(10000, 99999)}",
            first_name=_generate_name(),
            district_id=d.id,
            unit_id=unit.id if unit else None,
            rank_id=random.choice(ranks).id,
            designation_id=random.choice(designations).id
        )
        employees.append(emp)
        
        if i < 10:  # Create operators for first 10
            op = OperatorORM(
                id=f"OP-{i:04d}",
                name=emp.first_name,
                role=random.choice(["command", "analyst", "field"]),
                clearance="SECRET",
                unit="Karnataka Police",
                rank="Inspector",
                date_of_entry="2015-05-15",
                operator_id=f"LMN-OP-{i:04d}",
                assigned_unit="Local PS",
                status="ACTIVE",
                kgid=emp.kgid,
                first_name=emp.first_name,
                district_id=emp.district_id,
                unit_id=emp.unit_id,
                rank_id=emp.rank_id,
                designation_id=emp.designation_id
            )
            operators.append(op)
            
    return employees, operators

def generate_firs(count=50, units=[], employees=[], sections=[], crime_heads=[]):
    cases = []
    relations = []
    
    now = datetime.now()
    
    for i in range(count):
        unit = random.choice(units)
        io = random.choice(employees)
        section = random.choice(sections)
        head = random.choice(crime_heads)
        
        # Generation Logic
        year = random.choice([2025, 2026])
        running = i + 1
        
        crime_no = CrimeNumberService.generate_crime_number(1, int(unit.district_id), int(unit.id), year, running)
        case_no = CrimeNumberService.generate_case_number(year, running)
        
        registered_date = now - timedelta(days=random.randint(1, 365), hours=random.randint(1, 24))
        
        timeline_events = [
            {"date": (registered_date - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": "Incident Occurred"},
            {"date": registered_date.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": f"FIR {crime_no} Registered under {section.act_code} {section.section_code}"}
        ]
        
        accused_list = []
        for j in range(random.randint(1, 3)):
            a = AccusedORM(
                id=f"ACC-{crime_no}-{j}",
                case_master_id=crime_no,
                name=_generate_name(),
                age_year=random.randint(18, 65),
                gender=random.choice(["Male", "Female", "Other"])
            )
            accused_list.append(a)
            relations.append(a)
            
            # Arrest record 50%
            if random.random() > 0.5:
                arr = ArrestSurrenderORM(
                    id=f"ARR-{crime_no}-{j}",
                    case_master_id=crime_no,
                    event_type="Arrest",
                    event_date=registered_date + timedelta(days=random.randint(1, 10)),
                    state_id="29",
                    district_id=unit.district_id,
                    police_station_id=unit.id,
                    io_id=io.id
                )
                relations.append(arr)
                relations.append(ArrestSurrenderAccusedORM(
                    id=f"ARRA-{crime_no}-{j}",
                    arrest_surrender_id=arr.id,
                    accused_id=a.id,
                    is_accused=True
                ))
                timeline_events.append({"date": arr.event_date.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": f"Arrest of {a.name}"})

        victim = VictimORM(
            id=f"VIC-{crime_no}",
            case_master_id=crime_no,
            name=_generate_name(),
            age_year=random.randint(18, 65),
            gender=random.choice(["Male", "Female"]),
            is_police=False
        )
        relations.append(victim)
        
        comp = ComplainantDetailsORM(
            id=f"CMP-{crime_no}",
            case_master_id=crime_no,
            name=_generate_name(),
            age_year=random.randint(25, 70),
            gender=random.choice(["Male", "Female"])
        )
        relations.append(comp)
        
        veh = VehicleORM(
            id=f"VEH-{crime_no}",
            case_master_id=crime_no,
            registration_no=_generate_ka_vehicle()
        )
        relations.append(veh)
        
        network = {
            "nodes": [
                {"id": a.id, "label": a.name, "kind": "suspect"} for a in accused_list
            ] + [{"id": victim.id, "label": victim.name, "kind": "victim"}],
            "edges": [
                {"source": a.id, "target": victim.id, "relation": "TARGETED"} for a in accused_list
            ]
        }
        
        cases.append(CaseORM(
            id=crime_no,
            label=f"{unit.name} Cr.No. {running}/{year} u/s {section.section_code} {section.act_code}",
            status="Under Investigation",
            updated_at=registered_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            evidence_count=random.randint(0, 5),
            inspector=io.first_name,
            timeline=timeline_events,
            network=network,
            case_metadata={"bns_section": section.section_code, "district": unit.district_id},
            # CaseMaster integration
            crime_no=crime_no,
            case_no=case_no,
            crime_registered_date=registered_date,
            incident_from_date=registered_date - timedelta(hours=2),
            latitude=12.9716 + random.uniform(-0.1, 0.1),
            longitude=77.5946 + random.uniform(-0.1, 0.1),
            brief_facts=f"Incident reported near {random.choice(LOCATIONS)} involving {veh.registration_no}.",
            police_person_id=io.id,
            police_station_id=unit.id,
            case_category_id="1",
            gravity_offence_id="1",
            crime_major_head_id=head.id,
            case_status_id="1"
        ))
        
        # Link Section
        relations.append(ActSectionAssociationORM(
            id=f"ASA-{crime_no}",
            case_master_id=crime_no,
            act_id=section.act_code,
            section_id=section.id
        ))

    return cases, relations

def generate_watchlist(accused_list):
    entries = []
    for i, a in enumerate(accused_list[:20]):
        entries.append(WatchlistEntryORM(
            id=f"WL-{i}",
            name=a.name,
            reason="Habitual Offender",
            risk_level=random.choice(["HIGH", "CRITICAL"]),
            last_seen=f"{random.choice(LOCATIONS)}, Bengaluru"
        ))
    return entries
''')

    print("Karnataka Seed Scripts generated successfully.")

if __name__ == "__main__":
    create_seeds()
