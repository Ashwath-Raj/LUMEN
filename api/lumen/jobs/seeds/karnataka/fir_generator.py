import random
import uuid
from datetime import datetime, timedelta
import json
from lumen.db.models.legacy_models import (
    CaseORM, EmployeeORM, ComplainantDetailsORM, AccusedORM, VictimORM,
    ActSectionAssociationORM, ArrestSurrenderORM, ArrestSurrenderAccusedORM,
    VehicleORM, EvidenceDetailsORM, OperatorORM, WatchlistEntryORM, HotspotORM,
    PropertyORM
)
from lumen.services.crime_number_service import CrimeNumberService
from lumen.identity.hashing import hash_password
from lumen.jobs.seeds.karnataka.classification import CRIME_PROFILES, DISTRICT_PROFILES

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
        d_profile = DISTRICT_PROFILES.get(district_id, ["Vehicle Theft", "House Break-in", "Attempt to Murder", "Murder"])
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
            evidence = EvidenceDetailsORM(id=f"EVD-{crime_no}", case_master_id=crime_no, description=f"Digital Evidence: Seized Mobile Device {accused_data['phone']}")
            relations.append(evidence)
        elif crime["category"] == "Violent":
            evidence = EvidenceDetailsORM(id=f"EVD-{crime_no}", case_master_id=crime_no, description="Physical Evidence: Recovered Weapon")
            relations.append(evidence)
            
        prop = None
        if crime["category"] == "Property":
            prop = PropertyORM(id=f"PRP-{crime_no}", case_master_id=crime_no, description="Stolen Valuables")
            relations.append(prop)
            if not evidence:
                evidence = EvidenceDetailsORM(id=f"EVD-{crime_no}", case_master_id=crime_no, description="Physical Evidence: Recovered Items")
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
        loc_id = f"LOC-{unit.id}-{int(lat*100)}"
        nodes = [
            {"id": a_orm.id, "label": a_orm.name, "kind": "suspect"},
            {"id": victim.id, "label": victim.name, "kind": "victim"},
            {"id": io.id, "label": io.first_name, "kind": "officer"},
            {"id": loc_id, "label": f"{unit.name} Sector", "kind": "location"}
        ]
        edges = [
            {"source": a_orm.id, "target": victim.id, "relation": "TARGETED"},
            {"source": io.id, "target": crime_no, "relation": "INVESTIGATES"},
            {"source": crime_no, "target": a_orm.id, "relation": "INVOLVES"},
            {"source": loc_id, "target": crime_no, "relation": "CONNECTED_TO"}
        ]
        if accused_data['syndicate']:
            nodes.append({"id": accused_data['syndicate']['name'], "label": accused_data['syndicate']['name'], "kind": "organization"})
            edges.append({"source": a_orm.id, "target": accused_data['syndicate']['name'], "relation": "MEMBER_OF"})
        if vehicle:
            nodes.append({"id": vehicle.id, "label": vehicle.registration_no, "kind": "vehicle"})
            edges.append({"source": a_orm.id, "target": vehicle.id, "relation": "ASSOCIATED_WITH"})
            edges.append({"source": vehicle.id, "target": loc_id, "relation": "RECOVERED_FROM"})
        if prop:
            nodes.append({"id": prop.id, "label": prop.description[:20] + "...", "kind": "property"})
            edges.append({"source": prop.id, "target": loc_id, "relation": "CONNECTED_TO"})
        if evidence:
            nodes.append({"id": evidence.id, "label": evidence.description[:20] + "...", "kind": "evidence"})
            edges.append({"source": crime_no, "target": evidence.id, "relation": "CONNECTED_TO"})
            edges.append({"source": evidence.id, "target": a_orm.id, "relation": "SEIZED_FROM"})
            if prop:
                edges.append({"source": evidence.id, "target": prop.id, "relation": "RECOVERED_FROM"})

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
