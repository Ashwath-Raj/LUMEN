import os

def fix_operator_schema():
    path = r"c:\Users\jaswa\Downloads\LUMEN\LUMEN\backend\app\db\seeds\karnataka\fir_generator.py"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add biometric_hash to command operator
    if "biometric_hash" not in content:
        content = content.replace(
            'status="ACTIVE",\n                         hashed_password',
            'status="ACTIVE",\n                         biometric_hash="hash999",\n                         hashed_password'
        )
        
        # Add biometric_hash to loop operators
        content = content.replace(
            'status="ACTIVE",\n                hashed_password',
            'status="ACTIVE",\n                biometric_hash=f"hash{i}",\n                hashed_password'
        )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_operator_schema()
