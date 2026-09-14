import {
  AlertCircle,
  CheckCircle2,
  CircleHelp,
  Clock3,
  Heart,
  Layers3,
  Package,
  Palette,
  Plus,
  Search,
  Settings2,
  ShoppingCart,
  Sparkles,
  UtensilsCrossed,
} from 'lucide-vue-next'

export const designSystemTabs = Object.freeze([
  { id: 'theme', label: 'تم و توکن‌ها', caption: 'رنگ، تایپوگرافی و ریتم' },
  { id: 'icons', label: 'آیکون‌ها', caption: 'خانواده و اندازه‌ها' },
  { id: 'components', label: 'کامپوننت‌ها', caption: 'قطعات قابل استفاده' },
  { id: 'patterns', label: 'پترن‌ها', caption: 'الگوهای عملیاتی' },
  { id: 'templates', label: 'تمپلیت‌ها', caption: 'صفحه‌های مرجع' },
])

export const iconCatalog = Object.freeze([
  { name: 'Search', label: 'جستجو', component: Search, token: 'icon-md' },
  { name: 'Plus', label: 'افزودن', component: Plus, token: 'icon-md' },
  { name: 'Package', label: 'محصول', component: Package, token: 'icon-md' },
  { name: 'UtensilsCrossed', label: 'رستوران', component: UtensilsCrossed, token: 'icon-lg' },
  { name: 'ShoppingCart', label: 'سبد خرید', component: ShoppingCart, token: 'icon-md' },
  { name: 'Heart', label: 'علاقه‌مندی', component: Heart, token: 'icon-md' },
  { name: 'Layers3', label: 'فرمول و لایه‌ها', component: Layers3, token: 'icon-md' },
  { name: 'Palette', label: 'تم و رنگ', component: Palette, token: 'icon-md' },
  { name: 'Settings2', label: 'تنظیمات', component: Settings2, token: 'icon-md' },
  { name: 'Sparkles', label: 'ویژه', component: Sparkles, token: 'icon-md' },
  { name: 'Clock3', label: 'زمان آماده‌سازی', component: Clock3, token: 'icon-sm' },
  { name: 'CheckCircle2', label: 'آماده / موفق', component: CheckCircle2, token: 'icon-md' },
  { name: 'AlertCircle', label: 'هشدار', component: AlertCircle, token: 'icon-md' },
  { name: 'CircleHelp', label: 'راهنما', component: CircleHelp, token: 'icon-md' },
])

export const designSystemCatalog = Object.freeze({
  components: Object.freeze([
    { id: 'button', title: 'دکمه‌ها', description: 'عمل اصلی، ثانویه، کم‌اهمیت و خطرناک با حالت‌های focus و loading.', kind: 'primitive' },
    { id: 'surface', title: 'سطح و کارت', description: 'سطوح مدیریت با hierarchy مشخص و بدون تزئین اضافه.', kind: 'primitive' },
    { id: 'status', title: 'Badge و وضعیت', description: 'وضعیت موجودی، انتشار، خطا و موفقیت با متن و رنگ معنایی.', kind: 'primitive' },
    { id: 'product-card', title: 'کارت محصول', description: 'مرجع نمایش محصول در منوی مشتری با image، قیمت و اقدام.', source: 'components/MenuProductCard.vue', kind: 'reference' },
    { id: 'product-detail', title: 'جزئیات محصول', description: 'هدر، رسانه، قیمت، وضعیت، تغذیه و تنظیمات محصول.', source: 'pages/management/ManagementProductDetailPage.vue', kind: 'reference' },
    { id: 'readiness', title: 'آمادگی محصول', description: 'چک‌لیست تکمیل محصول قبل از انتشار در منو.', source: 'components/management/ManagementProductReadinessPanel.vue', kind: 'domain' },
  ]),
  patterns: Object.freeze([
    { id: 'product-search', title: 'جستجو و ایجاد محصول', description: 'جستجوی سروری، فیلتر سریع، نماهای ذخیره‌شده و اقدام ایجاد.' },
    { id: 'product-collection', title: 'مجموعه محصولات', description: 'لیست، گالری، کانبان، شیت، تقویم، درخت و بارگذاری صفحه‌ای.' },
    { id: 'product-availability', title: 'وضعیت فروش', description: 'فعال، به‌زودی، ناموجود و اتمام با مسیر اصلاح واضح.' },
    { id: 'product-detail-sections', title: 'بخش‌بندی جزئیات', description: 'تب‌های اطلاعات، رسانه، قیمت، BOM، صفت‌ها، گزارش و فعالیت.' },
    { id: 'async-feedback', title: 'بازخورد عملیات', description: 'بارگذاری، خطا، موفقیت و retry در همان context عملیاتی.' },
  ]),
  templates: Object.freeze([
    { id: 'products-list', title: 'تمپلیت مدیریت محصولات', description: 'صفحه مرجع برای جستجو، نماها و مدیریت جمعی.', source: 'pages/management/ManagementProductsPage.vue', href: '/management/products' },
    { id: 'product-detail-editor', title: 'تمپلیت ویرایش محصول', description: 'جزئیات کامل یک محصول و مسیر آماده‌سازی آن.', source: 'pages/management/ManagementProductDetailPage.vue', href: '/management/product' },
    { id: 'public-menu-card', title: 'تمپلیت کارت منوی مشتری', description: 'نمای محصول برای کشف، انتخاب و افزودن به سبد.', source: 'components/MenuProductCard.vue', href: '/menu' },
    { id: 'public-product-detail', title: 'تمپلیت جزئیات مشتری', description: 'گالری، تغذیه، سفارشی‌سازی و اقدام خرید.', source: 'pages/ItemDetailPage.vue', href: '/item' },
  ]),
})
