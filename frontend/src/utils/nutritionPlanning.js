export const NUTRITION_MEAL_SLOTS = ['صبحانه', 'میان‌وعده', 'ناهار', 'شام']
export const NUTRITION_WEEKDAYS = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']

export function filterNutritionMenuProducts(catalog = [], query = '') {
  const normalizedQuery = String(query || '').trim().toLocaleLowerCase('fa-IR')
  return catalog.filter((item) => {
    const searchable = `${item.title || ''} ${item.name || ''} ${item.category_title || ''} ${item.subcategory_title || ''}`.toLocaleLowerCase('fa-IR')
    return !normalizedQuery || searchable.includes(normalizedQuery)
  })
}

function nutritionText(item = {}) {
  const values = [item.title, item.name, item.category_title, item.subcategory_title, item.category, item.subcategory, item.item_group_path]
  for (const key of ['tags', 'meal_slots']) {
    const raw = item[key]
    if (Array.isArray(raw)) values.push(...raw)
    else if (raw) values.push(raw)
  }
  return values.map((value) => String(value || '')).join(' ').toLocaleLowerCase('fa-IR').replaceAll('ي', 'ی').replaceAll('ك', 'ک')
}

export function isNutritionBeverage(item) {
  const beverageGroups = new Set(['بار', 'بار سرد', 'بار گرم', 'سردنوش', 'دم‌نوش', 'دمنوش', 'آبمیوه', 'نوشیدنی'])
  const categoryValues = [item?.category_title, item?.subcategory_title, item?.category, item?.subcategory].map(normalizedTag)
  if (categoryValues.some((value) => beverageGroups.has(value))) return true
  const text = nutritionText(item)
  return ['بار سرد', 'بار گرم', 'سردنوش', 'گرم نوش', 'گرم‌نوش', 'دم‌نوش', 'دمنوش', 'آبمیوه', 'آب میوه', 'اسموتی', 'میلک شیک', 'آیس تی', 'ماچا', 'نوشیدنی', 'کافه', 'آب معدنی', 'آب واتا', 'واتا', 'نوشابه', 'دلستر', 'دوغ', 'شربت', 'موهیتو', 'لیموناد', 'قهوه', 'چای', 'اسپرسو', 'آمریکانو', 'لته', 'موکاچینو', 'water', 'beverage', 'drink', 'espresso', 'americano', 'latte', 'coffee', 'tea']
    .some((term) => text.includes(term))
}

export function hasNutritionValues(item) {
	const rawKcal = item?.nutrition?.kcal
	const rawProtein = item?.nutrition?.protein_g
	const reviewed = Number(item?.nutrition_verified) === 1
	if (rawKcal === null || rawKcal === undefined || rawKcal === '' || rawProtein === null || rawProtein === undefined || rawProtein === '') return false
	const kcal = Number(rawKcal)
	const protein = Number(rawProtein)
	return Number.isFinite(kcal) && kcal >= 0 && Number.isFinite(protein) && protein >= 0 && (reviewed || kcal > 0 || protein > 0)
}

function hasMealNutrition(item) {
	return hasNutritionValues(item) && Number(item.nutrition.kcal) > 0
}

function inferNutritionMealSlots(item) {
  // Nutrient-bearing drinks can fill a snack; water and other zero-calorie
  // drinks are not meal suggestions.
  if (isNutritionBeverage(item)) return hasMealNutrition(item) ? ['میان‌وعده'] : []
  const configured = Array.isArray(item?.meal_slots) ? item.meal_slots.filter((slot) => NUTRITION_MEAL_SLOTS.includes(slot)) : []
  if (configured.length) return configured
  const text = nutritionText(item)
  if (['صبحانه', 'املت', 'نیمرو', 'عدسی', 'پنکیک', 'اوتمیل', 'تخم مرغ', 'تخممرغ'].some((term) => text.includes(term))) return ['صبحانه']
  if (['میان وعده', 'میان‌وعده', 'اسنک', 'دسر', 'میوه', 'کیک', 'کوکی', 'شیرینی', 'آجیل'].some((term) => text.includes(term))) return ['میان‌وعده']
  if (text.includes('ناهار')) return ['ناهار']
  if (text.includes('شام')) return ['شام']
  return ['ناهار', 'شام']
}

function normalizedTag(value) {
  return String(value || '').trim().toLocaleLowerCase('fa-IR').replaceAll('ي', 'ی').replaceAll('ك', 'ک')
}

export function buildCalorieAwareMealSuggestions({ branch = '', catalog = [], calorieTarget = 0, proteinTarget = 0, allergens = [], dislikedItems = [], dislikedIngredients = [], likedItems = [], likedIngredients = [] } = {}) {
  const targetKcal = Number(calorieTarget)
  if (!Number.isFinite(targetKcal) || targetKcal <= 0) return { suggestions: [], reason: 'هدف کالری برای ساخت ترکیب آماده نیست.' }

  const allergenSet = new Set(allergens.map(normalizedTag))
  const dislikedIngredientSet = new Set(dislikedIngredients.map(normalizedTag))
  const likedIngredientSet = new Set(likedIngredients.map(normalizedTag))
  const eligible = catalog.filter((item) => {
		// The nutrition plan is a dietary plan, so do not hide known macros just
		// because today's branch price or stock has changed. Order preparation
		// rechecks both before anything reaches the cart.
		if (!hasMealNutrition(item)) return false
    const productAllergens = (item.allergens || []).map(normalizedTag)
    if (productAllergens.some((tag) => allergenSet.has(tag))) return false
    const productIngredients = (item.ingredient_tags || []).map(normalizedTag)
    if (productIngredients.some((tag) => allergenSet.has(tag))) return false
    if (allergenSet.size && Number(item.allergen_reviewed) !== 1 && !item.ingredient_composition_available) return false
    if (dislikedItems.includes(item.name)) return false
    if (productIngredients.some((tag) => dislikedIngredientSet.has(tag))) return false
    if (dislikedIngredientSet.size && Number(item.ingredients_reviewed) !== 1 && !item.ingredient_composition_available) return false
    return true
  })

  if (!eligible.length) {
    return {
      suggestions: [],
      reason: catalog.length
        ? 'در این شعبه محصولی با کالریِ بیشتر از صفر و مقدار پروتئین ثبت‌شده پیدا نشد؛ نوشیدنیِ بدون کالری وارد وعده نمی‌شود و اطلاعات سفارش‌پذیری هنگام ثبت سفارش دوباره بررسی خواهد شد.'
        : 'منوی فعالی برای این شعبه پیدا نشد.',
    }
  }

  const slots = [['صبحانه', 0.25], ['ناهار', 0.35], ['شام', 0.3], ['میان‌وعده', 0.1]]
  const suggestions = []
  for (let variant = 0; variant < 3; variant += 1) {
    const items = []
    const selectedCodes = new Set()
    const selectedIngredients = new Set()
    for (const [mealSlot, share] of slots) {
      let candidates = eligible.filter((item) => inferNutritionMealSlots(item).includes(mealSlot))
      const unused = candidates.filter((item) => !selectedCodes.has(item.name))
      if (unused.length) candidates = unused
      if (!candidates.length) continue
      const proteinGoal = Number(proteinTarget || 0) * share
      candidates.sort((a, b) => {
        const score = (item) => {
          const nutrition = item.nutrition || {}
          const ingredients = new Set((item.ingredient_tags || []).map(normalizedTag))
          return Math.abs(Number(nutrition.kcal) - targetKcal * share)
            + 2 * Math.abs(Number(nutrition.protein_g) - proteinGoal)
            + 15 * [...ingredients].filter((tag) => selectedIngredients.has(tag)).length
            - (likedItems.includes(item.name) ? 120 : 0)
            - [...ingredients].filter((tag) => likedIngredientSet.has(tag)).length * 30
        }
        return score(a) - score(b) || String(a.name || '').localeCompare(String(b.name || ''), 'fa')
      })
      const item = candidates[Math.min(variant, candidates.length - 1)]
      selectedCodes.add(item.name)
      for (const tag of item.ingredient_tags || []) selectedIngredients.add(normalizedTag(tag))
		items.push({ meal_slot: mealSlot, source_type: 'وی‌درخت', item_code: item.name, qty: 1, customization: {}, nutrition_known: true, nutrition_verified: Number(item.nutrition_verified) === 1, allergen_reviewed: Number(item.allergen_reviewed) === 1, ingredients_reviewed: Number(item.ingredients_reviewed) === 1 })
    }
    if (!items.length) continue
    const coveredSlots = [...new Set(items.map((item) => item.meal_slot))]
    const fullDay = coveredSlots.length === slots.length
    const title = ['ترکیب متناسب با کالری', 'ترکیب دوم', 'ترکیب سوم'][variant]
		suggestions.push({ title: fullDay ? title : `${title} · ${coveredSlots.length} وعده`, branch, nutrition_complete: true, nutrition_reviewed: items.every((item) => item.nutrition_verified), covered_slots: coveredSlots, full_day: fullDay, items })
  }

  if (!suggestions.length) return { suggestions: [], reason: 'غذای دارای مقادیر کالری و پروتئین با وعدهٔ قابل برنامه‌ریزی پیدا نشد.' }
  const missingSlots = slots.map(([slot]) => slot).filter((slot) => !suggestions.some((suggestion) => suggestion.covered_slots.includes(slot)))
	const hasUnreviewedNutrition = suggestions.some((suggestion) => !suggestion.nutrition_reviewed)
	const hasUnknownSafety = suggestions.some((suggestion) => suggestion.items.some((item) => !item.allergen_reviewed || !item.ingredients_reviewed))
	const messages = []
	if (missingSlots.length) messages.push(`این شعبه غذای مناسبِ «${missingSlots.join('، ')}» ندارد؛ ترکیب همهٔ وعده‌های روز را پوشش نمی‌دهد.`)
	if (hasUnreviewedNutrition) messages.push('پیشنهاد بر پایهٔ کالری و پروتئین ثبت‌شدهٔ محصول چیده شده؛ بعضی مقادیر هنوز توسط مدیریت بازبینی نشده‌اند.')
	if (hasUnknownSafety) messages.push('اطلاعات مواد یا حساسیت‌زای بعضی اقلام کامل نیست و پیش از سفارش دوباره بررسی می‌شود.')
	if (!messages.length) messages.push('هر چهار وعده با کالری و پروتئین موجود در اطلاعات محصولات و متناسب با هدف روزانه چیده شده‌اند.')
  return { suggestions, reason: messages.join(' ') }
}

const activityFactors = {
  'کم‌تحرک': 1.2,
  'فعالیت سبک': 1.375,
  'فعالیت متوسط': 1.55,
  'فعالیت زیاد': 1.725,
}

export function calculateNutritionTargets(profile = {}) {
  const height = Number(profile.height_cm || 0)
  const weight = Number(profile.weight_kg || 0)
  const age = Number(profile.age_years || 0)
  const bmi = age >= 18 && height > 0 && weight > 0 ? Math.round((weight / ((height / 100) ** 2)) * 10) / 10 : null
  const result = {
    bmi,
    protein_reference_g: null,
    maintenance_kcal: null,
    calorie_target_kcal: null,
    estimate_available: false,
    estimate_note: 'برای برآورد، سن، قد، وزن، فعالیت و گزینهٔ محاسبه را کامل کنید.',
  }

  if (profile.needs_specialist) {
    result.estimate_note = 'برای این شرایط، هدف کالری را با متخصص تغذیه تعیین کنید.'
    return result
  }
  if (age && age < 18) {
    result.estimate_note = 'برآورد خودکار این صفحه برای افراد ۱۸ سال به بالا طراحی شده است.'
    return result
  }
  const manualProtein = Number(profile.protein_target_g || 0)
  result.protein_reference_g = manualProtein > 0
    ? Math.round(manualProtein * 10) / 10
    : age >= 18 && weight > 0
      ? Math.round(weight * 0.8 * 10) / 10
      : null
  if (profile.goal === 'کاهش وزن' && bmi !== null && bmi < 18.5) {
    result.estimate_note = 'با توجه به BMI پایین‌تر از بازهٔ مرجع، هدف کاهش وزن را با متخصص تعیین کنید.'
    return result
  }
  if (!age) {
    const manual = Number(profile.calorie_target || 0)
    if (manual > 0) {
      result.calorie_target_kcal = Math.round(manual)
      result.estimate_note = 'هدف کالری دستی ذخیره شده است؛ برای پیشنهاد خودکار، سن بزرگسال را هم ثبت کنید.'
    }
    return result
  }
  if (!(height > 0 && weight > 0 && age > 0) || !activityFactors[profile.activity_level] || !['زن', 'مرد'].includes(profile.formula_sex) || !['کاهش وزن', 'افزایش وزن', 'حفظ وزن'].includes(profile.goal)) {
    const manual = Number(profile.calorie_target || 0)
    if (manual > 0) {
      result.calorie_target_kcal = Math.round(manual)
      result.estimate_available = true
      result.estimate_note = 'هدف کالری دستی شما استفاده می‌شود.'
    }
    return result
  }

  const resting = 10 * weight + 6.25 * height - 5 * age + (profile.formula_sex === 'مرد' ? 5 : -161)
  const maintenance = Math.round(resting * activityFactors[profile.activity_level])
  const ratio = profile.goal === 'کاهش وزن' ? 0.9 : profile.goal === 'افزایش وزن' ? 1.1 : 1
  result.maintenance_kcal = maintenance
  result.calorie_target_kcal = Math.round(Number(profile.calorie_target || 0) || maintenance * ratio)
  result.estimate_available = true
  result.estimate_note = Number(profile.calorie_target || 0) > 0 ? 'هدف کالری دستی شما استفاده می‌شود.' : 'برآورد تقریبی است؛ تغییر وزن به عوامل دیگری هم وابسته است.'
  return result
}

export function calculatePlanTotals(items = [], catalogByCode = {}) {
  const totals = { kcal: 0, protein_g: 0, carb_g: 0, fat_g: 0, price: 0 }
  const unknownNutrition = []
  const unreviewedNutrition = []
  let priceComplete = true
  let restaurantItems = 0
  let manualItems = 0
  for (const row of items) {
    if (row.source_type === 'ثبت دستی') {
      manualItems += 1
      const qty = Number(row.qty || 1)
      for (const key of ['kcal', 'protein_g', 'carb_g', 'fat_g']) {
        const value = row.nutrition?.[key]
        if (value === null || value === undefined || value === '') {
          if (key === 'kcal' || key === 'protein_g') unknownNutrition.push(row.manual_name || 'خوراک ثبت‌شده')
        } else totals[key] += Number(value) * qty
      }
      continue
    }
    restaurantItems += 1
    const product = catalogByCode[row.item_code]
    const qty = Number(row.qty || 1)
    const productNutritionAvailable = hasNutritionValues(product)
    for (const key of ['kcal', 'protein_g', 'carb_g', 'fat_g']) {
      const value = product?.nutrition?.[key]
      if (value === null || value === undefined || value === '' || ((key === 'kcal' || key === 'protein_g') && !productNutritionAvailable)) {
        if (key === 'kcal' || key === 'protein_g') unknownNutrition.push(product?.title || row.item_code || 'محصول')
      } else totals[key] += Number(value) * qty
    }
    if (product && productNutritionAvailable && Number(product.nutrition_verified) !== 1) {
      unreviewedNutrition.push(product.title || row.item_code || 'محصول')
    }
    if (!product || product.base_price === null || product.base_price === undefined || Number(product.base_price) <= 0) {
      priceComplete = false
    } else {
      totals.price += Number(product.base_price) * qty
    }
  }
  return {
    totals: Object.fromEntries(Object.entries(totals).map(([key, value]) => [key, Math.round(value * 10) / 10])),
    complete: unknownNutrition.length === 0,
    priceComplete,
    unknownNutrition: [...new Set(unknownNutrition)],
    unreviewedNutrition: [...new Set(unreviewedNutrition)],
    restaurantItems,
    manualItems,
  }
}

export function localWeekdayIndex(date = new Date()) {
  return (date.getDay() + 1) % 7
}
