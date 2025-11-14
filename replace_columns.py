import os
import re

# Укажите абсолютный путь к корню вашего проекта
project_folder = r'D:\GIO.BOT.002'

# Маппинг старых и новых имён колонок
replace_map = {
    'tp1_price': 'tp1_price',
    'tp2_price': 'tp2_price',
    'tp3_price': 'tp3_price',
    'sl_price': 'sl_price',
}

changed_files = []

for root, dirs, files in os.walk(project_folder):
    for filename in files:
        if filename.endswith('.py'):
            filepath = os.path.join(root, filename)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

            original_content = content

            # Заменяем только целые слова
            for old_name, new_name in replace_map.items():
                pattern = r'\b' + re.escape(old_name) + r'\b'
                content = re.sub(pattern, new_name, content)

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(content)
                changed_files.append(filepath)

if changed_files:
    print("Обновлены файлы:")
    for f in changed_files:
        print(f" - {f}")
else:
    print("Замены не найдены")



# python replace_columns.py
