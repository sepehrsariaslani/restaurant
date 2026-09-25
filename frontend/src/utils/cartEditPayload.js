export function buildEditedCartLine(line, preview) {
  return {
    ...line,
    id: line.id,
    qty: preview.qty,
    customization: preview.customization,
    unit_price_preview: preview.unit_price_preview,
    line_total_preview: preview.line_total_preview,
    ingredient_catalog: preview.ingredient_catalog,
    modifier_groups_catalog: preview.modifier_groups_catalog,
  }
}
