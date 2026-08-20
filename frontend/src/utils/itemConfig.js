function uniqStrings(list = []) {
  const seen = new Set()
  const out = []
  for (const entry of list) {
    const key = String(entry || '').trim()
    if (!key || seen.has(key)) {
      continue
    }
    seen.add(key)
    out.push(key)
  }
  return out
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function roundStep(value, step = 0.5) {
  const safeStep = Number(step || 0.5)
  if (!safeStep || safeStep <= 0) {
    return Number(value || 0)
  }
  return Math.round(Number(value || 0) / safeStep) * safeStep
}

const NUTRITION_KEYS = ['kcal', 'protein_g', 'carb_g', 'sugar_g', 'fat_g']

function numeric(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function emptyNutritionTotals() {
  return {
    kcal: 0,
    protein_g: 0,
    carb_g: 0,
    sugar_g: 0,
    fat_g: 0,
  }
}

function normalizedNutritionPayload(raw = {}) {
  const totals = emptyNutritionTotals()
  for (const key of NUTRITION_KEYS) {
    totals[key] = numeric(raw?.[key], 0)
  }

  const payload = {}
  for (const key of NUTRITION_KEYS) {
    if (totals[key] > 0) {
      payload[key] = Number(totals[key].toFixed(4))
    }
  }

  if ((payload.kcal || 0) > 0 && (payload.protein_g || 0) >= 0) {
    const proteinPercent = (numeric(payload.protein_g, 0) * 4 * 100) / numeric(payload.kcal, 1)
    if (Number.isFinite(proteinPercent) && proteinPercent >= 0) {
      payload.protein_percent = Number(Math.min(proteinPercent, 100).toFixed(1))
    }
  }

  return payload
}

function addNutrition(targetTotals = {}, sourceNutrition = {}, factor = 1) {
  const appliedFactor = numeric(factor, 0)
  if (!appliedFactor || appliedFactor <= 0) {
    return
  }

  for (const key of NUTRITION_KEYS) {
    const value = numeric(sourceNutrition?.[key], 0)
    if (!value) {
      continue
    }
    targetTotals[key] = numeric(targetTotals[key], 0) + value * appliedFactor
  }
}

function ingredientBaseMultiplier(ingredient = {}) {
  return Number(ingredient.is_included_by_default) === 1 ? 1 : 0
}

function ingredientMinMultiplier(ingredient = {}) {
  const base = ingredientBaseMultiplier(ingredient)
  const rawMin = Number(ingredient.min_multiplier ?? 0)
  const required = Number(ingredient.is_required) === 1
  const canRemove = Number(ingredient.can_remove) === 1

  if (required || (base > 0 && !canRemove)) {
    return Math.max(rawMin, 1)
  }

  return Math.max(rawMin, 0)
}

function ingredientMaxMultiplier(ingredient = {}) {
  const min = ingredientMinMultiplier(ingredient)
  const rawMax = Number(ingredient.max_multiplier ?? 3)
  return Math.max(rawMax, min)
}

function ingredientStep(ingredient = {}) {
  const step = Number(ingredient.step_multiplier ?? 0.5)
  return step > 0 ? step : 0.5
}

function normalizeIngredientAdjustments(rawAdjustments, ingredients = []) {
  const byKey = new Map()

  if (Array.isArray(rawAdjustments)) {
    for (const row of rawAdjustments) {
      const key = String(row?.ingredient_key || row?.key || row?.name || '').trim()
      if (!key) {
        continue
      }
      byKey.set(key, Number(row.multiplier ?? row.qty ?? 0))
    }
  }

  return (ingredients || []).map((ingredient) => {
    const key = String(ingredient.key || ingredient.name || '').trim()
    const base = ingredientBaseMultiplier(ingredient)
    const min = ingredientMinMultiplier(ingredient)
    const max = ingredientMaxMultiplier(ingredient)
    const step = ingredientStep(ingredient)

    const fromPayload = byKey.has(key) ? Number(byKey.get(key)) : base
    const stepped = roundStep(fromPayload, step)
    const multiplier = clamp(stepped, min, max)

    return {
      ingredient_key: key,
      multiplier,
    }
  })
}

export function createDefaultCustomization(ingredients = [], modifierGroups = []) {
  const selectedModifiers = []

  for (const group of modifierGroups || []) {
    const defaults = (group.options || []).filter(
      (option) => Number(option.is_default) === 1 && Number(option.is_selectable ?? 1) === 1,
    )
    const isVariantSelector = Number(group?.is_variant_attribute_selector || 0) === 1
    if (group.selection_mode === 'single') {
      if (defaults[0]) {
        const baseQty = Number(defaults[0].base_qty ?? defaults[0].option_qty ?? defaults[0].qty_step ?? 1)
        selectedModifiers.push({
          group: group.group_name,
          option: defaults[0].name,
          qty: Number.isFinite(baseQty) && baseQty > 0 ? baseQty : 1,
        })
      } else if (isVariantSelector && Number(group.required || 0) === 1) {
        const firstOption = (group.options || []).find((option) => Number(option.is_selectable ?? 1) === 1)
        if (firstOption?.name) {
          selectedModifiers.push({
            group: group.group_name,
            option: firstOption.name,
            qty: Math.max(Number(firstOption.base_qty ?? firstOption.option_qty ?? 1), 1),
          })
        }
      }
      continue
    }

    for (const option of defaults) {
      const baseQty = Number(option.base_qty ?? option.option_qty ?? option.qty_step ?? 1)
      selectedModifiers.push({
        group: group.group_name,
        option: option.name,
        qty: Number.isFinite(baseQty) && baseQty > 0 ? baseQty : 1,
      })
    }
  }

  return {
    ingredient_adjustments: normalizeIngredientAdjustments([], ingredients),
    selected_modifiers: selectedModifiers,
    selected_alternatives: [],
  }
}

export function sanitizeCustomization(raw = {}, ingredients = []) {
  const removed = uniqStrings(raw.removed_ingredients)
  const added = uniqStrings(raw.added_ingredients)

  const normalized = {
    ingredient_adjustments: normalizeIngredientAdjustments(raw.ingredient_adjustments, ingredients),
    selected_modifiers: Array.isArray(raw.selected_modifiers)
      ? raw.selected_modifiers
          .map((row) => {
            const parsedQty = Number(row.qty ?? 1)
            return {
              group: String(row.group || row.group_name || '').trim(),
              option: String(row.option || row.option_name || '').trim(),
              qty: Number.isFinite(parsedQty) && parsedQty > 0 ? parsedQty : 1,
            }
          })
          .filter((row) => row.group && row.option)
      : [],
    selected_alternatives: Array.isArray(raw.selected_alternatives)
      ? raw.selected_alternatives
          .map((row) => ({
            ingredient_key: String(row.ingredient_key || row.key || row.name || '').trim(),
            alternative_item: String(row.alternative_item || row.item_code || '').trim(),
          }))
          .filter((row) => row.ingredient_key && row.alternative_item)
      : [],
    variant_fixed_attributes:
      raw?.variant_fixed_attributes && typeof raw.variant_fixed_attributes === 'object'
        ? { ...raw.variant_fixed_attributes }
        : {},
  }

  if (!normalized.ingredient_adjustments.length && ingredients.length) {
    const legacyMap = new Map()
    for (const ingredient of ingredients) {
      const key = String(ingredient.key || ingredient.name || '').trim()
      const base = ingredientBaseMultiplier(ingredient)
      let multiplier = base
      if (removed.includes(key)) {
        multiplier = 0
      } else if (added.includes(key)) {
        multiplier = Math.max(base, 1)
      }
      legacyMap.set(key, multiplier)
    }

    normalized.ingredient_adjustments = normalizeIngredientAdjustments(
      Array.from(legacyMap.entries()).map(([ingredient_key, multiplier]) => ({ ingredient_key, multiplier })),
      ingredients,
    )
  }

  return normalized
}

export function getIngredientMultiplier(customization = {}, ingredient = {}) {
  const key = String(ingredient.key || ingredient.name || '').trim()
  const byKey = new Map(
    (customization.ingredient_adjustments || []).map((row) => [String(row.ingredient_key || '').trim(), Number(row.multiplier || 0)]),
  )

  if (byKey.has(key)) {
    return Number(byKey.get(key) || 0)
  }

  return ingredientBaseMultiplier(ingredient)
}

export function ingredientQtyStep(ingredient = {}) {
  const multiplierStep = ingredientStep(ingredient)
  const multiplierQty = Number(ingredient?.multiplier_qty ?? ingredient?.qty_step ?? 0)
  if (Number.isFinite(multiplierQty) && multiplierQty > 0) {
    return multiplierQty
  }
  const baseQty = Number(ingredient?.base_qty || 0)
  if (Number.isFinite(baseQty) && baseQty > 0) {
    return baseQty * multiplierStep
  }
  return multiplierStep
}

function resolvedItemPriceTotal({ unitRate = 0, conversionFactor = 0, qty = 0 } = {}) {
  const rate = numeric(unitRate, 0)
  const factor = numeric(conversionFactor, 0)
  const requestedQty = Math.max(numeric(qty, 0), 0)
  if (!(rate > 0) || !(factor > 0)) {
    return null
  }
  return rate * requestedQty * factor
}

function ingredientResolvedPriceTotal(ingredient = {}, qty = 0) {
  return resolvedItemPriceTotal({
    unitRate: ingredient?.unit_rate,
    conversionFactor: ingredient?.conversion_factor,
    qty,
  })
}

function alternativeResolvedPriceTotal(option = {}, qty = 0) {
  return resolvedItemPriceTotal({
    unitRate: option?.unit_rate,
    conversionFactor: option?.conversion_factor,
    qty,
  })
}

export function estimateIngredientSelection(ingredient = {}, customization = {}) {
  const key = String(ingredient.key || ingredient.name || '').trim()
  const base = ingredientBaseMultiplier(ingredient)
  const selected = getIngredientMultiplier(customization, ingredient)
  const baseQty = numeric(ingredient.base_qty, 0)
  const deltaMultiplier = selected - base
  const selectedAlternativeMap = new Map(
    (customization.selected_alternatives || []).map((row) => [
      String(row.ingredient_key || '').trim(),
      String(row.alternative_item || '').trim(),
    ]),
  )
  const selectedAlternativeItem = selectedAlternativeMap.get(key) || ''
  const selectedAlternativeOption = (ingredient.alternative_options || []).find(
    (option) => String(option?.alternative_item || '').trim() === selectedAlternativeItem,
  )
  const selectedAlternativeLabel = String(
    selectedAlternativeOption?.item_name || selectedAlternativeItem || '',
  ).trim()
  const alternativeQtyMultiplier = numeric(selectedAlternativeOption?.qty_multiplier, 1)
  const alternativeQtyAddition = numeric(selectedAlternativeOption?.qty_addition, 0)
  const selectedBaseQty = selectedAlternativeOption
    ? Math.max(0, baseQty * alternativeQtyMultiplier + alternativeQtyAddition)
    : baseQty
  const baseComponentQty = baseQty * base
  const selectedComponentQty = selectedBaseQty * selected
  const baseTotalPrice = ingredientResolvedPriceTotal(ingredient, baseComponentQty)
  const selectedTotalPrice = selectedAlternativeOption
    ? alternativeResolvedPriceTotal(selectedAlternativeOption, selectedComponentQty)
    : ingredientResolvedPriceTotal(ingredient, selectedComponentQty)

  let delta = 0
  let priceSource = 'legacy_extra'

  if (baseTotalPrice !== null && selectedTotalPrice !== null) {
    delta = selectedTotalPrice - baseTotalPrice
    priceSource = 'item_price'
  } else if (selectedAlternativeOption) {
    const alternativeScale = base > 0 ? (selected / base) : (selected > 0 ? selected : 1)
    delta = numeric(
      selectedAlternativeOption?.resolved_price_delta ?? selectedAlternativeOption?.price_delta,
      0,
    ) * alternativeScale
    priceSource = numeric(selectedAlternativeOption?.unit_rate, 0) > 0 ? 'item_price' : 'alternative_delta'
  } else {
    delta = deltaMultiplier * numeric(ingredient.extra_when_added, 0)
  }

  return {
    key,
    base,
    selected,
    baseQty,
    selectedBaseQty,
    baseComponentQty,
    selectedComponentQty,
    deltaMultiplier,
    delta,
    priceSource,
    selectedAlternativeItem,
    selectedAlternativeOption,
    selectedAlternativeLabel,
    baseTotalPrice,
    selectedTotalPrice,
  }
}

export function upsertIngredientMultiplier(customization = {}, ingredient = {}, nextMultiplier) {
  const key = String(ingredient.key || ingredient.name || '').trim()
  const list = Array.isArray(customization.ingredient_adjustments) ? [...customization.ingredient_adjustments] : []
  const index = list.findIndex((row) => String(row.ingredient_key || '').trim() === key)

  const min = ingredientMinMultiplier(ingredient)
  const max = ingredientMaxMultiplier(ingredient)
  const step = ingredientStep(ingredient)
  const value = clamp(roundStep(nextMultiplier, step), min, max)

  const row = { ingredient_key: key, multiplier: value }
  if (index >= 0) {
    list[index] = row
  } else {
    list.push(row)
  }

  return {
    ...customization,
    ingredient_adjustments: list,
  }
}

export function estimateLine({ basePrice = 0, qty = 1, ingredients = [], modifierGroups = [], customization = {} }) {
  const clean = sanitizeCustomization(customization, ingredients)
  const groupMap = new Map((modifierGroups || []).map((group) => [group.group_name, group]))

  let unit = Number(basePrice || 0)
  let ingredientDeltaTotal = 0
  let modifierDeltaTotal = 0
  let recipeMultiplier = 1

  const nutritionPerUnitTotals = emptyNutritionTotals()
  const breakdownIngredients = []
  const breakdownModifiers = []
  const breakdownDetails = []
  for (const ingredient of ingredients || []) {
    const selection = estimateIngredientSelection(ingredient, clean)
    const {
      key,
      base,
      selected,
      deltaMultiplier,
      delta,
      selectedAlternativeItem,
      selectedAlternativeOption,
      selectedAlternativeLabel,
      selectedBaseQty,
    } = selection
    const nutritionSource = selectedAlternativeOption || ingredient

    ingredientDeltaTotal += delta
    unit += delta

    addNutrition(
      nutritionPerUnitTotals,
      {
        kcal: nutritionSource?.nutrition_kcal,
        protein_g: nutritionSource?.nutrition_protein_g,
        carb_g: nutritionSource?.nutrition_carb_g,
        sugar_g: nutritionSource?.nutrition_sugar_g,
        fat_g: nutritionSource?.nutrition_fat_g,
      },
      selectedBaseQty * selected,
    )

    breakdownIngredients.push({
      key,
      label: ingredient.customer_label || ingredient.name || key,
      base,
      selected,
      baseQty: numeric(ingredient.base_qty, 0),
      selectedBaseQty,
      delta,
      selectedAlternativeItem,
      selectedAlternativeLabel,
      alternativeDelta: selectedAlternativeItem ? delta : 0,
      priceSource: selection.priceSource,
    })

    if (Math.abs(deltaMultiplier) > 1e-8) {
      breakdownDetails.push({
        key: `ingredient:${key}`,
        label: ingredient.customer_label || ingredient.name || key,
        delta,
      })
    }

    if (selectedAlternativeItem) {
      breakdownDetails.push({
        key: `alternative:${key}:${selectedAlternativeItem}`,
        label: `جایگزین ${ingredient.customer_label || ingredient.name || key} با ${selectedAlternativeLabel || selectedAlternativeItem}`,
        delta,
      })
    }
  }

  for (const selected of clean.selected_modifiers) {
    const group = groupMap.get(selected.group)
    if (!group) {
      continue
    }

    const option = (group.options || []).find((row) => row.name === selected.option)
    if (!option) {
      continue
    }

    const selectedQty = Math.max(Number(selected.qty || 0), 0)
    if (selectedQty <= 0) {
      continue
    }
    const baseQtyRaw = numeric(option.base_qty ?? option.option_qty, 1)
    const baseQty = baseQtyRaw > 0 ? baseQtyRaw : 1
    const conversionFactor = Math.max(numeric(option.conversion_factor, 1), 0)
    const selectedQtyInStock = selectedQty * conversionFactor
    const unitRate = numeric(option.unit_rate, 0)
    // قیمت «یک سرو» از گزینه: سرور base_price = unit_rate × base_qty_in_stock_uom
    // می‌فرستد (مثلاً 0.1 کیلو قارچ با نرخ 350,000 → 35,000). اگر موجود بود از
    // همان استفاده کن؛ در غیر این صورت از unit_rate × base_qty محاسبه می‌شود.
    const basePricePerServing = numeric(option.base_price ?? option.price_delta, 0)
    const delta =
      basePricePerServing > 0
        ? basePricePerServing * selectedQty
        : unitRate > 0
          ? unitRate * selectedQtyInStock * (baseQty > 1 ? 1 / baseQty : 1)
          : basePricePerServing * (selectedQty / baseQty)
    modifierDeltaTotal += delta
    unit += delta
    const optionQty = Math.max(numeric(option.base_qty ?? option.option_qty, 1), 0)
    const groupLabel = String(group.title || group.group_name || selected.group || '').trim()
    const optionLabel = String(option.label || option.name || selected.option || '').trim()
    const optionUom = String(option.option_uom || option.stock_uom || '').trim()
    const qtySuffix = optionUom ? ` ${selectedQty} ${optionUom}` : ` x${selectedQty}`

    addNutrition(
      nutritionPerUnitTotals,
      {
        kcal: option?.nutrition_kcal,
        protein_g: option?.nutrition_protein_g,
        carb_g: option?.nutrition_carb_g,
        sugar_g: option?.nutrition_sugar_g,
        fat_g: option?.nutrition_fat_g,
      },
      selectedQtyInStock || optionQty * (selectedQty / baseQty),
    )

    breakdownModifiers.push({
      key: `${selected.group}:${selected.option}`,
      group: groupLabel,
      option: optionLabel,
      qty: selectedQty,
      delta,
      label: `${groupLabel} - ${optionLabel}${qtySuffix}`,
    })
    breakdownDetails.push({
      key: `modifier:${selected.group}:${selected.option}`,
      label: `${groupLabel} - ${optionLabel}${qtySuffix}`,
      delta,
    })

    const optionRecipeMultiplier = Number(option.recipe_multiplier || 1)
    if (optionRecipeMultiplier > 0) {
      recipeMultiplier *= optionRecipeMultiplier ** (selectedQty / baseQty)
    }
  }

  const quantity = Math.max(Number(qty || 1), 1)
  const nutrition = normalizedNutritionPayload(nutritionPerUnitTotals)
  const nutritionTotals = normalizedNutritionPayload(
    NUTRITION_KEYS.reduce((acc, key) => {
      acc[key] = numeric(nutritionPerUnitTotals[key], 0) * quantity
      return acc
    }, {}),
  )
  return {
    unitPrice: unit,
    lineTotal: unit * quantity,
    qty: quantity,
    nutrition,
    nutritionTotals,
    customization: clean,
    pricingBreakdown: {
      basePrice: Number(basePrice || 0),
      unitPrice: unit,
      ingredientDeltaTotal,
      modifierDeltaTotal,
      extraCharge: unit - Number(basePrice || 0),
      recipeMultiplier,
      qty: quantity,
      nutrition,
      nutrition_totals: nutritionTotals,
      ingredients: breakdownIngredients,
      modifiers: breakdownModifiers,
      details: breakdownDetails,
    },
  }
}

export function summarizeCustomizationForDisplay(customization = {}, ingredients = []) {
  const clean = sanitizeCustomization(customization, ingredients)
  const ingredientMap = new Map((ingredients || []).map((row) => [String(row.key || row.name || '').trim(), row]))
  const lines = []

  for (const row of clean.ingredient_adjustments || []) {
    const key = String(row.ingredient_key || '').trim()
    const ingredient = ingredientMap.get(key)
    if (!ingredient) {
      continue
    }

    const base = ingredientBaseMultiplier(ingredient)
    const selected = Number(row.multiplier || 0)
    const delta = selected - base
    if (Math.abs(delta) < 1e-8) {
      continue
    }

    const label = ingredient.customer_label || ingredient.name || key
    if (selected <= 0) {
      lines.push(`بدون ${label}`)
      continue
    }
    lines.push(`${label}: x${selected}`)
  }

  for (const selected of clean.selected_modifiers) {
    lines.push(`${selected.group} - ${selected.option}`)
  }

  for (const selected of clean.selected_alternatives || []) {
    const ingredient = ingredientMap.get(String(selected.ingredient_key || '').trim())
    const label = ingredient?.customer_label || ingredient?.name || selected.ingredient_key
    const selectedItem = String(selected.alternative_item || '').trim()
    if (!selectedItem) {
      continue
    }

    const optionRow = (ingredient?.alternative_options || []).find(
      (option) => String(option?.alternative_item || '').trim() === selectedItem,
    )
    const selectedLabel = String(optionRow?.item_name || selectedItem).trim()
    lines.push(`جایگزین ${label}: ${selectedLabel}`)
  }

  return lines
}
