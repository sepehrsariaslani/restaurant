import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    content = f.read()

# Add editingOriginalOrder.isEditing = false to addToCart
content = content.replace(
    "function addToCart(item, qty = 1, customizationPayload = null, hasCustomization = false, unitPrice = null, options = {}) {",
    "function addToCart(item, qty = 1, customizationPayload = null, hasCustomization = false, unitPrice = null, options = {}) {\n  editingOriginalOrder.isEditing = false\n  editingOriginalOrder.name = ''"
)

# Add editingOriginalOrder.isEditing = false to setCartQty
content = content.replace(
    "function setCartQty(line, val) {",
    "function setCartQty(line, val) {\n  if (line.qty !== Number(val)) {\n    editingOriginalOrder.isEditing = false\n    editingOriginalOrder.name = ''\n  }"
)

# Add editingOriginalOrder.isEditing = false to editLineNote
content = content.replace(
    "line.note = String(next || '').trim()",
    "line.note = String(next || '').trim()\n  editingOriginalOrder.isEditing = false\n  editingOriginalOrder.name = ''"
)

with open('frontend/src/pages/management/ManagementPosPage.vue', 'w') as f:
    f.write(content)
