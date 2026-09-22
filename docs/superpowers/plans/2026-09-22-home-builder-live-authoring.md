# سازنده صفحه اصلی و پیش‌نمایش زنده — برنامه پیاده‌سازی

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** اصلاح کامل authoring صفحه‌ها برای حفظ مقدارهای خالی/فاصله، مزیت‌های تصویری، ویرایش درباره‌ما، preview زنده و ذخیره مستقیم روی سرور.

**Architecture:** قرارداد داده‌ی مزیت در `homeBuilder.js` گسترش پیدا می‌کند؛ فرم و renderer از همان نرمال‌ساز با حالت authoring/display استفاده می‌کنند. preview بصری در یک کامپوننت مستقل با کامپوننت‌های واقعی صفحات رندر می‌شود و صفحه مدیریت فقط state و تنظیمات را به آن می‌دهد. ذخیره مستقیم در handler اصلی سایت‌تنظیمات انجام می‌شود و layout از API مستقل خودش استفاده می‌کند.

**Tech Stack:** Vue 3, Vite, `lucide-vue-next`, `ManagementImageDropzone`, Frappe API، Node test runner.

## Global Constraints

- از کامپوننت‌ها و design tokenهای موجود استفاده شود؛ کتابخانه UI جدید اضافه نشود.
- متن فارسی نباید به شکل literal `\\uXXXX` در فرم مدیریت نمایش داده شود.
- داده‌های legacy مزیت بدون migration اجباری سازگار بمانند.
- هر تغییر رفتاری ابتدا با تست regression پوشش داده شود.
- خروجی build در `restaurant/public/frontend/assets` مطابق convention پروژه بازسازی شود.

---

### Task 1: قرارداد داده مزیت‌ها و مقدارهای خالی

**Files:**
- Modify: `frontend/src/utils/homeBuilder.js`
- Modify: `frontend/src/components/management/builder/BlockPropsForm.vue`
- Modify: `frontend/src/components/blocks/FeaturesBlock.vue`
- Modify: `frontend/src/utils/blockRegistry.js`
- Test: `frontend/tests/home-builder-authoring.test.mjs`

**Steps:**

- [ ] تست نرمال‌سازی را برای `image`, `icon: ''` و `preserveWhitespace` اضافه کن.
- [ ] `normalizeFeatureItems(items, { preserveWhitespace })` را طوری تغییر بده که icon خالی بماند و image حفظ شود.
- [ ] فرم مزیت را با `preserveWhitespace: true`، گزینه‌ی «بدون آیکن» و dropzone تصویر به‌روزرسانی کن.
- [ ] renderer فقط وقتی icon وجود دارد آن را رندر کند و image را با overlay به‌عنوان پس‌زمینه کارت استفاده کند.
- [ ] `CategoriesBlock.toProps` برای متن‌های صریحاً خالی fallback نگذارد.
- [ ] تست هدفمند را اجرا کن و سپس commit فارسی بساز.

### Task 2: Hero واقعی و preview زنده تمام صفحه‌ها

**Files:**
- Create: `frontend/src/components/management/ManagementLivePagePreview.vue`
- Modify: `frontend/src/pages/management/ManagementSiteSettingsPage.vue`
- Modify: `frontend/src/components/blocks/HeroBlock.vue`
- Modify: `frontend/src/components/management/ManagementPageBuilderWorkspace.vue`
- Test: `frontend/tests/home-builder-authoring.test.mjs`

**Steps:**

- [ ] تست source contract را برای live preview component، page mapping و `100svh` اضافه کن.
- [ ] کامپوننت live preview را با `PublicHeader`, `HomePageRenderer`, `AboutUsPage`, `FaqPage`, `ProductGroupsPage`, `MenuItemCard` و `SiteFooter` بساز.
- [ ] boot فعلی، branding، header/footer variant و preview device را به آن وصل کن.
- [ ] preview placeholder فعلی را با live preview جایگزین کن و about/faq/product groups را به داده‌ی واقعی draft وصل کن.
- [ ] صفحه درباره‌ما را طوری تنظیم کن که `aboutSections` در فهرست componentها قابل انتخاب باشد.
- [ ] Hero تمام‌صفحه را به حداقل `100svh` برسان و در viewport Builder عرض preview را حفظ کن.
- [ ] تست هدفمند و build را اجرا کن و commit فارسی بساز.

### Task 3: ذخیره مستقیم و اصلاح editor درباره‌ما

**Files:**
- Modify: `frontend/src/pages/management/ManagementSiteSettingsPage.vue`
- Modify: `frontend/src/utils/siteAuthoringDraft.js` فقط در صورت نیاز برای fallback
- Test: `frontend/tests/home-builder-authoring.test.mjs`

**Steps:**

- [ ] تست source contract را اضافه کن که handler ذخیره مستقیم `setManagementSiteSettings` را فراخوانی می‌کند و فقط draft local را پیام موفقیت اصلی نمی‌کند.
- [ ] handler مرحله‌های identity/content را به `setManagementSiteSettings(currentSiteSettingsPayload())` وصل کن.
- [ ] بعد از پاسخ سرور `liveSiteSettingsPayload`, boot، layout revision و state فرم را همگام کن.
- [ ] خطای API را در state `error` نگه دار و مقدارهای فرم را حفظ کن.
- [ ] ویرایش درباره‌ما را از هر دو مسیر visual/content به یک handler قابل مشاهده متصل کن و بعد از ثبت preview را bump کن.
- [ ] تست هدفمند را اجرا کن و commit فارسی بساز.

### Task 4: verification و تحویل

**Files:**
- Modify: `frontend/public` generated assets after build

**Steps:**

- [ ] `npm test` را اجرا کن و انتظار داشته باش همه تست‌ها سبز باشند.
- [ ] `npm run build` را اجرا کن و انتظار داشته باش exit code صفر باشد.
- [ ] `git diff --check` و audit خاموش بودن literal escape/ورودی تصویر را اجرا کن.
- [ ] branch را commit و push کن و clean بودن workspace را تأیید کن.
