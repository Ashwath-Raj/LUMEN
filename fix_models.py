import os

def fix_duplicate_models():
    models_path = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\models.py"
    
    with open(models_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update the original VictimORM (add missing fields)
    original_victim = """class VictimORM(Base):
    __tablename__ = "victims"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True, index=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())"""
    
    updated_victim = """class VictimORM(Base):
    __tablename__ = "victims"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True, index=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # ER Fields
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    age_year = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    is_police = Column(Boolean, nullable=True)"""
    
    content = content.replace(original_victim, updated_victim)
    
    # 2. Remove the duplicate VictimORM
    duplicate_victim = """class VictimORM(Base):
    __tablename__ = "victims"
    id = Column(String, primary_key=True, index=True)
    case_master_id = Column(String, ForeignKey("cases.id"), nullable=True)
    name = Column(String, nullable=False)
    age_year = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    is_police = Column(Boolean, nullable=True)"""
    
    content = content.replace(duplicate_victim, "")
    
    with open(models_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed duplicate models.")

if __name__ == "__main__":
    fix_duplicate_models()
