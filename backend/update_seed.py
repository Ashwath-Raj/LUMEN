import os

def update_seed():
    seed_path = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\seed.py"
    
    with open(seed_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add imports for new models
    imports_to_add = """
    StateORM, DistrictORM, UnitTypeORM, UnitORM,
    CaseCategoryORM, GravityOffenceORM, CaseStatusMasterORM,
    RankORM, DesignationORM, ActORM, SectionORM,
"""
    content = content.replace("from app.db.models import (", f"from app.db.models import ({imports_to_add}")

    # Add seed call
    content = content.replace("_seed_roles(session)", "_seed_datathon_scaffold(session)\n    _seed_roles(session)")

    # Add the function definition at the end
    scaffold_func = """

def _seed_datathon_scaffold(session: Session) -> None:
    # State
    state = StateORM(id="29", name="Karnataka", active=True)
    session.add(state)
    
    # District
    bengaluru = DistrictORM(id="0443", name="Bengaluru City", state_id="29", active=True)
    session.add(bengaluru)
    
    # UnitType
    ps_type = UnitTypeORM(id="1", name="Police Station", city_dist_state="City")
    session.add(ps_type)
    
    # Unit
    peenya_ps = UnitORM(id="0006", name="Peenya PS", type_id="1", state_id="29", district_id="0443", active=True)
    session.add(peenya_ps)
    
    # Ranks & Designations
    sp_rank = RankORM(id="10", name="Superintendent of Police", hierarchy=10, active=True)
    session.add(sp_rank)
    sp_desig = DesignationORM(id="20", name="SP", sort_order=1, active=True)
    session.add(sp_desig)
    
    # Case Categories
    session.add(CaseCategoryORM(id="1", name="FIR"))
    session.add(CaseCategoryORM(id="2", name="UDR"))
    
    # Master Lookups
    session.add(CaseStatusMasterORM(id="1", name="Under Investigation"))
    session.add(CaseStatusMasterORM(id="2", name="Charge Sheeted"))
    session.add(GravityOffenceORM(id="1", lookup_value="Heinous"))
    
    # BNS Act & Section
    bns = ActORM(id="BNS2023", description="Bharatiya Nyaya Sanhita, 2023", short_name="BNS", active=True)
    session.add(bns)
    session.add(SectionORM(id="103", act_code="BNS2023", section_code="103", description="Murder", active=True))
    session.add(SectionORM(id="109", act_code="BNS2023", section_code="109", description="Attempt to Murder", active=True))
    
    session.commit()
"""
    if "def _seed_datathon_scaffold" not in content:
        content += scaffold_func

    with open(seed_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_seed()
