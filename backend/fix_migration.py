import os

def fix_migration():
    path = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\alembic\versions\32d37657c489_add_datathon_er_models.py"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    header = """from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '32d37657c489'
down_revision = 'cc0125b00a68'
branch_labels = None
depends_on = None"""

    content = content.replace("from alembic import op\nimport sqlalchemy as sa", header)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
if __name__ == "__main__":
    fix_migration()
