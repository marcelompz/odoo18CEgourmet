import os
import re

dir_path = '/opt/odoo/odoo9049-migracion-test/addons/attendance_cross'

replacements = [
    ('attendance_cross', 'attendance_cross'),
    ('biometric.device', 'biometric.device'),
    ('model_biometric_device', 'model_biometric_device'),
    ('biometric_device_id', 'biometric_device_id'),
    ('biometric_uploaded', 'biometric_uploaded'),
    ('biometric_', 'biometric_'),
    ('Biometric Device', 'Biometric Device'),
    ('Biometric User', 'Biometric User'),
    ('Biometric Manager', 'Biometric Manager'),
    ('Biometric Attendance', 'Biometric Attendance'),
    ('Biometric', 'Biometric'),
    ('biometric', 'biometric'),
]

for root, dirs, files in os.walk(dir_path):
    # skip .git or something if it exists
    if '.git' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.xml') or file.endswith('.csv') or file.endswith('.md') or file.endswith('.html') or file.endswith('.txt'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            for old, new in replacements:
                content = content.replace(old, new)
                
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated {file_path}")

