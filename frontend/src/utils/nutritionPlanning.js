export const NUTRITION_MEAL_SLOTS = ['صبحانه', 'میان‌وعده', 'ناهار', 'شام']
export const NUTRITION_WEEKDAYS = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']

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
    for (const key of ['kcal', 'protein_g', 'carb_g', 'fat_g']) {
      const value = product?.nutrition?.[key]
      if (!product?.nutrition_verified || value === null || value === undefined || value === '') {
        if (key === 'kcal' || key === 'protein_g') unknownNutrition.push(product?.title || row.item_code || 'محصول')
      } else totals[key] += Number(value) * qty
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
    restaurantItems,
    manualItems,
  }
}

export function localWeekdayIndex(date = new Date()) {
  return (date.getDay() + 1) % 7
}
