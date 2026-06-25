import frappe

NUTRITION_FIXES = {
    '\u0641\u06cc\u0644\u0647 \u0627\u0633\u062a\u06cc\u06a9 \u0645\u0631\u06cc\u0646\u06cc\u062a \u0634\u062f\u0647': (230, 25, 15, 0),
    '\u0641\u06cc\u0644\u0647 \u0628\u0648\u0642\u0644\u0645\u0648\u0646 \u0645\u0631\u06cc\u0646\u06cc\u062a \u0634\u062f\u0647 \u062f\u0648\u062f\u06cc': (145, 30, 2, 0),
    '\u0645\u0631\u063a \u0645\u0631\u06cc\u0646\u06cc\u062a \u0634\u062f\u0647 \u067e\u0627\u0631\u06cc\u0633': (170, 30, 5, 0),
    '\u0645\u0631\u063a \u0645\u0631\u06cc\u0646\u06cc\u062a \u0634\u062f\u0647 \u067e\u0633\u062a\u0648': (175, 29, 6, 0),
    '\u0645\u0631\u063a \u0645\u0631\u06cc\u0646\u06cc\u062a \u0634\u062f\u0647 \u062a\u0631\u06cc\u0627\u06a9\u06cc': (165, 30, 4, 0),
    '\u0633\u06cc\u0646\u0647 \u0645\u0631\u063a \u0622\u0628\u067e\u0632 \u0634\u062f\u0647': (165, 31, 3, 0),
    '\u0645\u06cc\u06af\u0648 \u0645\u0631\u06cc\u0646\u06cc\u062a \u0634\u062f\u0647': (99, 24, 1, 0),
    '\u0633\u0633 \u067e\u0633\u062a\u0648': (250, 5, 20, 8),
    '\u0633\u0633 \u0633\u06cc\u0631': (180, 2, 15, 5),
    '\u0633\u0633 \u062e\u0631\u062f\u0644 \u0648 \u0634\u0648\u06cc\u062f': (60, 1, 1, 8),
    '\u0633\u0633 \u0633\u0628\u0632\u06cc\u062c\u0627\u062a': (50, 2, 1, 8),
    '\u0633\u0633 \u0627\u0633\u062a\u06cc\u06a9': (120, 1, 8, 10),
    '\u0633\u0633 \u0627\u0633\u067e\u0627\u06cc\u0633\u06cc': (90, 1, 6, 8),
    '\u0633\u0633 \u06a9\u0627\u0631\u0627\u0645\u0644\u06cc': (100, 1, 5, 12),
    '\u0633\u0633 \u062f\u0645\u0648\u06af\u0644\u0627\u0633': (50, 1, 1, 8),
    '\u0633\u0633 \u0633\u0648\u06cc\u0627 \u062f\u0633\u062a \u0633\u0627\u0632': (30, 2, 0, 4),
    '\u0633\u0633 \u06a9\u0627\u0641\u0647 \u062f \u067e\u0627\u0631\u06cc\u0633': (45, 0, 3, 5),
    '\u0645\u0627\u06cc\u0648 \u0622\u062c\u06cc': (680, 1, 75, 1),
    '\u0645\u0627\u06cc\u0648 \u062a\u0631\u06cc\u0627\u06a9\u06cc': (680, 1, 75, 1),
    '\u062f\u06cc\u067e \u0644\u0648\u0628\u06cc\u0627 \u0633\u0641\u06cc\u062f': (130, 24, 2, 0),
    '\u0646\u0627\u0646 \u067e\u0633\u062a\u0648': (270, 9, 5, 48),
}

updated = 0
errors = []

for item_name, (kcal, protein, fat, carbs) in NUTRITION_FIXES.items():
    try:
        frappe.db.set_value('Item', item_name, {
            'restaurant_nutrition_kcal': kcal,
            'restaurant_nutrition_protein_g': protein,
            'restaurant_nutrition_fat_g': fat,
            'restaurant_nutrition_carb_g': carbs,
        })
        frappe.db.commit()
        updated += 1
        print('OK: ' + item_name + ' -> kcal=' + str(kcal) + ' P=' + str(protein) + ' F=' + str(fat) + ' C=' + str(carbs))
    except Exception as e:
        errors.append(item_name + ': ' + str(e))
        print('ERR: ' + item_name + ' -> ' + str(e))

print('\nUpdated: ' + str(updated) + '/' + str(len(NUTRITION_FIXES)))
if errors:
    print('Errors:')
    for e in errors:
        print('  ' + e)
