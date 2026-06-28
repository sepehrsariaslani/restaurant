import {
  Beef,
  CakeSlice,
  Coffee,
  CupSoda,
  Drumstick,
  Fish,
  GlassWater,
  Pizza,
  Salad,
  Sandwich,
  Soup,
  Utensils,
  Wheat,
} from 'lucide-vue-next'

export const MENU_ICON_OPTIONS = [
  { value: 'Utensils', label: 'عمومی', keywords: ['menu', 'food', 'غذا', 'منو'], component: Utensils },
  { value: 'Coffee', label: 'قهوه', keywords: ['coffee', 'cafe', 'قهوه', 'کافه'], component: Coffee },
  { value: 'CupSoda', label: 'نوشیدنی', keywords: ['drink', 'juice', 'نوشیدنی', 'آبمیوه'], component: CupSoda },
  { value: 'GlassWater', label: 'چای و دمنوش', keywords: ['tea', 'water', 'چای', 'دمنوش', 'آب'], component: GlassWater },
  { value: 'Sandwich', label: 'ساندویچ', keywords: ['sandwich', 'ساندویچ'], component: Sandwich },
  { value: 'CakeSlice', label: 'دسر', keywords: ['dessert', 'cake', 'کیک', 'دسر', 'شیرینی'], component: CakeSlice },
  { value: 'Salad', label: 'سالاد', keywords: ['salad', 'starter', 'سالاد', 'پیش غذا'], component: Salad },
  { value: 'Soup', label: 'سوپ', keywords: ['soup', 'سوپ', 'آش'], component: Soup },
  { value: 'Pizza', label: 'پیتزا', keywords: ['pizza', 'پیتزا'], component: Pizza },
  { value: 'Drumstick', label: 'مرغ', keywords: ['chicken', 'مرغ', 'سوخاری'], component: Drumstick },
  { value: 'Beef', label: 'گوشت', keywords: ['beef', 'steak', 'kebab', 'گوشت', 'استیک', 'کباب'], component: Beef },
  { value: 'Fish', label: 'دریایی', keywords: ['fish', 'seafood', 'ماهی', 'میگو', 'دریایی'], component: Fish },
  { value: 'Wheat', label: 'نان', keywords: ['bread', 'wheat', 'نان', 'غلات'], component: Wheat },
]

export const MENU_ICON_COMPONENTS = MENU_ICON_OPTIONS.reduce((acc, option) => {
  acc[option.value] = option.component
  return acc
}, {})

export function sanitizeMenuIcon(value = '') {
  const normalized = String(value || '').trim()
  return MENU_ICON_COMPONENTS[normalized] ? normalized : ''
}

export function getMenuIconComponent(value = '', fallback = Utensils) {
  return MENU_ICON_COMPONENTS[sanitizeMenuIcon(value)] || fallback
}

export function inferMenuIconFromText(value = '') {
  const text = String(value || '').toLowerCase()
  const matched = MENU_ICON_OPTIONS.find((option) =>
    option.keywords.some((keyword) => text.includes(String(keyword).toLowerCase())),
  )
  return matched?.component || Utensils
}
