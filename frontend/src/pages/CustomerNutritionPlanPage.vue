<template>
  <div class="customer-page nutrition-page" dir="rtl">
    <CustomerPageHeader eyebrow="تغذیه و سفارش شما" title="برنامهٔ غذایی من" subtitle="غذاهایت را با هدف روزانه‌ات هماهنگ کن و برنامه را برای روزهای هفته نگه دار." fallback-href="/customer/dashboard">
      <template #eyebrow-icon><HeartPulse :size="15" aria-hidden="true" /></template>
      <template #action><a class="nutrition-header-link" href="/customer/dashboard">حساب من</a></template>
    </CustomerPageHeader>

    <main class="nutrition-layout">
      <section v-if="!signedIn" class="nutrition-panel nutrition-empty">
        <UserRound :size="30" /><h2>برنامه‌ات را در حساب خودت نگه دار</h2><p>برای ذخیرهٔ قد، وزن، حساسیت‌ها و برنامه‌ها وارد حساب شو.</p>
        <a class="nutrition-primary" href="/customer/login?redirect=%2Fcustomer%2Fnutrition">ورود یا ثبت‌نام</a>
      </section>

      <template v-else>
        <section v-if="loading" class="nutrition-panel nutrition-empty" role="status"><LoaderCircle :size="24" class="spin" /><p>در حال آماده‌کردن برنامهٔ غذایی…</p></section>
        <section v-else-if="pageError" class="nutrition-panel nutrition-empty" role="alert"><CircleAlert :size="26" /><h2>اطلاعات برنامه دریافت نشد</h2><p>{{ pageError }}</p><button class="nutrition-secondary" type="button" @click="loadWorkspace">تلاش دوباره</button></section>
        <template v-else>
          <section class="nutrition-panel nutrition-intro">
            <div class="nutrition-intro__icon"><HeartPulse :size="22" /></div>
            <div><h2>یک برنامهٔ مناسب خودت بچین</h2><p>BMI و هدف کالری تقریبی‌اند. این صفحه ابزار برنامه‌ریزی عمومی برای بزرگسالان سالم است، نه تشخیص یا رژیم درمانی.</p></div>
          </section>

          <section class="nutrition-panel">
            <div class="nutrition-section-head"><div><p class="nutrition-eyebrow">گام اول</p><h2>اطلاعات و هدف</h2><p>با ثبت اندازه‌ها، BMI و برآورد روزانه فوراً به‌روز می‌شوند.</p></div><span class="nutrition-step">۱</span></div>
            <div class="nutrition-form-grid">
              <label><span>سن</span><input v-model.number="profile.age_years" class="nutrition-input" type="number" min="0" max="120" inputmode="numeric" placeholder="سال" /><small>برای زیر ۱۸ سال، برآورد خودکار انجام نمی‌شود.</small></label>
              <label><span>قد</span><div class="nutrition-input-unit"><input v-model.number="profile.height_cm" class="nutrition-input" type="number" min="100" max="250" step="0.1" inputmode="decimal" placeholder="سانتی‌متر" /><small>cm</small></div></label>
              <label><span>وزن فعلی</span><div class="nutrition-input-unit"><input v-model.number="profile.weight_kg" class="nutrition-input" type="number" min="25" max="350" step="0.1" inputmode="decimal" placeholder="کیلوگرم" /><small>kg</small></div></label>
              <label><span>وزن هدف</span><div class="nutrition-input-unit"><input v-model.number="profile.goal_weight_kg" class="nutrition-input" type="number" min="25" max="350" step="0.1" inputmode="decimal" placeholder="کیلوگرم" /><small>kg</small></div></label>
              <label><span>هدف شما</span><select v-model="profile.goal" class="nutrition-input"><option value="">انتخاب هدف</option><option>کاهش وزن</option><option>حفظ وزن</option><option>افزایش وزن</option></select></label>
              <label><span>سطح فعالیت</span><select v-model="profile.activity_level" class="nutrition-input"><option value="">انتخاب فعالیت</option><option>کم‌تحرک</option><option>فعالیت سبک</option><option>فعالیت متوسط</option><option>فعالیت زیاد</option></select></label>
              <label class="nutrition-form-grid__wide"><span>گزینهٔ محاسبهٔ انرژی</span><select v-model="profile.formula_sex" class="nutrition-input"><option value="">انتخاب کنید</option><option>زن</option><option>مرد</option><option>ترجیح می‌دهم انتخاب نکنم</option></select><small>برای انتخاب‌نکردن، هدف کالری را از متخصص بگیر و دستی وارد کن.</small></label>
              <label><span>هدف کالری دستی <small>اختیاری</small></span><input v-model.number="profile.calorie_target" class="nutrition-input" type="number" min="0" max="10000" inputmode="numeric" placeholder="کیلوکالری" /></label>
              <label><span>هدف پروتئین دستی <small>اختیاری</small></span><input v-model.number="profile.protein_target_g" class="nutrition-input" type="number" min="0" max="1000" step="0.1" inputmode="decimal" placeholder="گرم" /></label>
            </div>
            <fieldset class="nutrition-safety"><legend>برای انتخاب امن‌تر</legend>
              <label><input v-model="profile.needs_specialist" type="checkbox" /> من باردار یا شیرده هستم، زیر ۱۸ سال دارم یا برای بیماری/شرایط پزشکی رژیم خاص لازم دارم.</label>
              <p>در این حالت هدف خودکار و پیشنهاد خودکار غیرفعال می‌شود؛ برای تعیین هدف با متخصص تغذیه مشورت کن.</p>
              <label class="nutrition-consent"><input v-model="profile.consent" type="checkbox" /> با ذخیرهٔ خصوصی این اطلاعات در حساب مشتری خودم موافقم.</label>
            </fieldset>
            <div class="nutrition-metrics" aria-live="polite">
              <article><small>BMI</small><strong>{{ bmiLabel }}</strong><span>{{ targets.bmi ?? '—' }}</span></article>
              <article><small>کالری نگهداشت تقریبی</small><strong>{{ formatNumber(targets.maintenance_kcal) }}</strong><span>کیلوکالری در روز</span></article>
              <article class="nutrition-metrics__accent"><small>هدف روزانه</small><strong>{{ formatNumber(targets.calorie_target_kcal) }}</strong><span>کیلوکالری · {{ targets.estimate_available ? 'برآوردی' : 'هنوز محاسبه نشده' }}</span></article>
              <article><small>مرجع پایهٔ پروتئین</small><strong>{{ formatNumber(targets.protein_reference_g) }}</strong><span>گرم در روز</span></article>
            </div>
            <p class="nutrition-note">{{ targets.estimate_note }} {{ targets.bmi_note || 'BMI شاخص غربالگری است، نه تشخیص پزشکی.' }}</p>
            <div class="nutrition-actions"><button class="nutrition-primary" type="button" :disabled="savingProfile || !profile.consent" @click="saveProfile">{{ savingProfile ? 'در حال ذخیره…' : 'ذخیرهٔ پروفایل' }}<Check :size="17" /></button><button v-if="profileExists" class="nutrition-text-button" type="button" :disabled="savingProfile" @click="deleteProfile">حذف اطلاعات تغذیه‌ای</button></div>
            <p v-if="profileMessage" class="nutrition-success" role="status">{{ profileMessage }}</p><p v-if="profileError" class="nutrition-error" role="alert">{{ profileError }}</p>
          </section>

          <section class="nutrition-panel">
            <div class="nutrition-section-head"><div><p class="nutrition-eyebrow">گام دوم</p><h2>سلیقه و حساسیت‌ها</h2><p>این گزینه‌ها برای فیلتر پیشنهادها استفاده می‌شوند.</p></div><span class="nutrition-step">۲</span></div>
            <div class="nutrition-filter-grid">
              <fieldset><legend>حساسیت غذایی</legend><div v-if="allergenOptions.length" class="nutrition-chips"><label v-for="tag in allergenOptions" :key="tag" class="nutrition-chip" :class="{ selected: profile.allergens.includes(tag) }"><input v-model="profile.allergens" type="checkbox" :value="tag" /><span>{{ tag }}</span></label></div><p v-else class="nutrition-muted">برچسب حساسیت محصولات پس از ثبت و بازبینی مدیریت نمایش داده می‌شود.</p></fieldset>
              <fieldset><legend>موادی که دوست نداری</legend><div v-if="ingredientOptions.length" class="nutrition-chips"><label v-for="tag in ingredientOptions" :key="tag" class="nutrition-chip" :class="{ selected: profile.disliked_ingredients.includes(tag) }"><input v-model="profile.disliked_ingredients" type="checkbox" :value="tag" /><span>{{ tag }}</span></label></div><p v-else class="nutrition-muted">مواد تشکیل‌دهندهٔ تأییدشده هنوز در منوی این شعبه ثبت نشده‌اند.</p></fieldset>
              <fieldset><legend>مواد دلخواه</legend><div v-if="ingredientOptions.length" class="nutrition-chips"><label v-for="tag in ingredientOptions" :key="tag" class="nutrition-chip" :class="{ selected: profile.liked_ingredients.includes(tag) }"><input v-model="profile.liked_ingredients" type="checkbox" :value="tag" /><span>{{ tag }}</span></label></div><p v-else class="nutrition-muted">پس از ثبت مواد محصولات، این فهرست قابل انتخاب می‌شود.</p></fieldset>
              <fieldset class="nutrition-product-preferences"><legend>غذاهای دلخواه</legend><div v-if="catalog.length" class="nutrition-choice-list"><label v-for="item in catalog" :key="item.name" class="nutrition-choice" :class="{ selected: profile.liked_items.includes(item.name) }"><input v-model="profile.liked_items" type="checkbox" :value="item.name" /><span>{{ item.title || item.name }}</span></label></div><p v-else class="nutrition-muted">برای انتخاب غذاهای دلخواه، ابتدا شعبهٔ منو را انتخاب کن.</p></fieldset>
              <fieldset class="nutrition-product-preferences"><legend>غذاهای نامطلوب</legend><div v-if="catalog.length" class="nutrition-choice-list"><label v-for="item in catalog" :key="item.name" class="nutrition-choice" :class="{ selected: profile.disliked_items.includes(item.name) }"><input v-model="profile.disliked_items" type="checkbox" :value="item.name" /><span>{{ item.title || item.name }}</span></label></div><p v-else class="nutrition-muted">برای انتخاب غذاهای نامطلوب، ابتدا شعبهٔ منو را انتخاب کن.</p></fieldset>
            </div>
            <label class="nutrition-branch"><span><Store :size="17" /> شعبهٔ منو</span><select v-model="selectedBranch" class="nutrition-input" @change="loadCatalog"><option value="">انتخاب شعبه</option><option v-for="branch in branches" :key="branch.id || branch.name" :value="branch.id || branch.name">{{ branch.title || branch.name }}</option></select></label>
            <p class="nutrition-note">برای ثبت حساسیت‌های شدید، پیش از سفارش با کارکنان شعبه هماهنگ کن. آلودگی متقاطع در آماده‌سازی آشپزخانه ممکن است.</p>
            <button class="nutrition-secondary" type="button" :disabled="savingProfile || !profile.consent" @click="saveProfile">ذخیرهٔ سلیقه و حساسیت‌ها</button>
          </section>

          <section class="nutrition-panel">
            <div class="nutrition-section-head"><div><p class="nutrition-eyebrow">گام سوم</p><h2>برنامه‌های روزانه</h2><p>محصولات شعبه را انتخاب کن، خوراک بیرونی را دستی اضافه کن و برنامه را برای روزهای هفته ذخیره کن.</p></div><span class="nutrition-step">۳</span></div>
            <div v-if="!selectedBranch" class="nutrition-inline-alert">برای دیدن محصولات و قیمت همین شعبه، ابتدا شعبه را انتخاب کن.</div>
            <div class="nutrition-builder-top"><label><span>نام برنامه</span><input v-model.trim="builder.title" class="nutrition-input" maxlength="120" placeholder="مثلاً برنامهٔ روز تمرین" /></label><div class="nutrition-day-picker"><span>روزهای هفته</span><div><label v-for="day in weekdays" :key="day" :class="{ selected: builder.weekdays.includes(day) }"><input v-model="builder.weekdays" type="checkbox" :value="day" /><span>{{ day.slice(0, 1) }}</span></label></div></div></div>

            <div class="nutrition-suggestion-row"><button class="nutrition-secondary" type="button" :disabled="suggesting || !selectedBranch || !targets.estimate_available" @click="loadSuggestions"><Sparkles :size="16" />{{ suggesting ? 'در حال ساخت پیشنهاد…' : 'پیشنهاد چند ترکیب' }}</button><small v-if="suggestionMessage">{{ suggestionMessage }}</small></div>
            <div v-if="suggestions.length" class="nutrition-suggestions"><button v-for="suggestion in suggestions" :key="suggestion.title" type="button" @click="useSuggestion(suggestion)"><strong>{{ suggestion.title }}</strong><small>{{ suggestion.items.length.toLocaleString('fa-IR') }} محصول پیشنهادی</small><ArrowLeft :size="16" /></button></div>

            <div class="nutrition-slot-list">
              <section v-for="slot in mealSlots" :key="slot" class="nutrition-slot">
                <header><div><span class="nutrition-slot__icon"><component :is="slotIcon(slot)" :size="17" /></span><h3>{{ slot }}</h3><small>{{ itemsForSlot(slot).length.toLocaleString('fa-IR') }} قلم</small></div><button type="button" class="nutrition-add-button" :disabled="!selectedBranch" @click="openPicker(slot)"><Plus :size="16" /> افزودن</button></header>
                <div v-if="itemsForSlot(slot).length" class="nutrition-line-list">
                  <article v-for="(row, index) in itemsForSlot(slot)" :key="`${slot}-${index}`" class="nutrition-line">
                    <div class="nutrition-line__copy"><strong>{{ row.source_type === 'ثبت دستی' ? row.manual_name : productFor(row.item_code)?.title || row.item_code }}</strong><small v-if="row.source_type === 'ثبت دستی'">{{ row.manual_quantity || 'مقدار ثبت‌شده' }} · ثبت‌شده توسط شما · {{ formatNumber(lineNutrition(row, 'kcal')) }} kcal برای این تعداد</small><small v-else>{{ formatNumber(lineNutrition(row, 'kcal')) }} کیلوکالری · {{ formatNumber(lineNutrition(row, 'protein_g')) }} گرم پروتئین برای این تعداد</small></div>
                    <div class="nutrition-line__controls"><select v-model="row.meal_slot" class="nutrition-meal-select" :aria-label="`وعدهٔ ${row.manual_name || productFor(row.item_code)?.title || 'قلم'}`"><option v-for="targetSlot in mealSlots" :key="targetSlot">{{ targetSlot }}</option></select><button type="button" :aria-label="`کم‌کردن تعداد ${row.manual_name || productFor(row.item_code)?.title || 'قلم'}`" @click="changeQty(row, -1)"><Minus :size="15" /></button><span>{{ Number(row.qty || 1).toLocaleString('fa-IR') }}</span><button type="button" :aria-label="`زیادکردن تعداد ${row.manual_name || productFor(row.item_code)?.title || 'قلم'}`" @click="changeQty(row, 1)"><Plus :size="15" /></button><button class="remove" type="button" aria-label="حذف قلم" @click="removeLine(row)"><Trash2 :size="15" /></button></div>
                  </article>
                </div>
                <p v-else class="nutrition-slot-empty">برای این وعده هنوز قلمی انتخاب نکرده‌ای.</p>
              </section>
            </div>

            <details class="nutrition-manual-food"><summary><Plus :size="16" /> افزودن خوراک خارج از وی‌درخت</summary><div class="nutrition-manual-grid"><label><span>نام خوراک</span><input v-model.trim="manualFood.name" class="nutrition-input" placeholder="مثلاً یک عدد سیب" /></label><label><span>مقدار</span><input v-model.trim="manualFood.quantity" class="nutrition-input" placeholder="مثلاً ۱ عدد" /></label><label><span>وعده</span><select v-model="manualFood.slot" class="nutrition-input"><option v-for="slot in mealSlots" :key="slot">{{ slot }}</option></select></label><label><span>کالری</span><input v-model.number="manualFood.kcal" class="nutrition-input" type="number" min="0" max="10000" placeholder="اختیاری" /></label><label><span>پروتئین (گرم)</span><input v-model.number="manualFood.protein_g" class="nutrition-input" type="number" min="0" max="1000" placeholder="اختیاری" /></label><label><span>تعداد</span><input v-model.number="manualFood.qty" class="nutrition-input" type="number" min="1" max="40" /></label><button class="nutrition-secondary" type="button" @click="addManualFood">افزودن به برنامه</button></div></details>
          </section>

          <div v-if="pickerSlot" class="nutrition-picker-backdrop" @click.self="pickerSlot = ''">
            <section class="nutrition-picker" role="dialog" aria-modal="true" aria-label="انتخاب محصول منو">
              <header><div><p class="nutrition-eyebrow">{{ pickerSlot }}</p><h2>انتخاب از منوی {{ branchTitle }}</h2></div><button class="nutrition-icon-button" type="button" aria-label="بستن" @click="pickerSlot = ''"><X :size="18" /></button></header>
              <label class="nutrition-search"><Search :size="17" /><input v-model="productSearch" type="search" placeholder="جستجوی غذا" /></label>
              <div v-if="!safePickerProducts.length" class="nutrition-empty-small">در این شعبه محصول آمادهٔ پیشنهاد پیدا نشد. محصولات باید اطلاعات تغذیه و حساسیت‌زای بازبینی‌شده داشته باشند.</div>
              <div v-else class="nutrition-picker-list"><article v-for="product in safePickerProducts" :key="product.name"><div><strong>{{ product.title }}</strong><small>{{ formatNumber(product.nutrition?.kcal) }} kcal · {{ formatNumber(product.nutrition?.protein_g) }}g پروتئین · {{ formatPrice(product.base_price) }}</small></div><button type="button" class="nutrition-add-button" @click="addProduct(product)"><Plus :size="16" /> افزودن</button></article></div>
            </section>
          </div>

          <section v-if="todayPlan" class="nutrition-panel nutrition-today" aria-labelledby="nutrition-today-title">
            <div class="nutrition-section-head"><div><p class="nutrition-eyebrow">برنامهٔ هفتگی</p><h2 id="nutrition-today-title">برنامهٔ امروز · {{ todayWeekday }}</h2><p>{{ todayPlan.title }} · شعبهٔ مرجع {{ todayPlan.branch }}</p></div><span class="nutrition-today__badge"><Check :size="15" /> امروز</span></div>
            <div class="nutrition-today__items"><div v-for="(row, index) in todayPlan.items" :key="`${todayPlan.name}-${index}`"><span><strong>{{ row.source_type === 'ثبت دستی' ? row.manual_name : productFor(row.item_code)?.title || row.item_code }}</strong><small>{{ row.meal_slot }} · {{ row.source_type === 'ثبت دستی' ? 'ثبت‌شده توسط شما' : `تعداد ${Number(row.qty || 1).toLocaleString('fa-IR')}` }}</small></span><b>{{ formatNumber(lineNutrition(row, 'kcal')) }} kcal</b></div></div>
            <div class="nutrition-today__totals"><span><small>کالری برنامه</small><strong>{{ formatNumber(todayPlanTotals.totals.kcal) }} kcal</strong></span><span><small>پروتئین</small><strong>{{ formatNumber(todayPlanTotals.totals.protein_g) }} g</strong></span><span><small>قیمت اقلام وی‌درخت</small><strong>{{ planPriceLabel(todayPlanTotals) }}</strong></span></div>
            <p v-if="todayPlan.branch !== selectedBranch" class="nutrition-note">سبد فعلی روی شعبهٔ {{ branchTitle || 'دیگر' }} تنظیم شده است. پیش از افزودن، موجودی و قیمت همان شعبه بررسی می‌شود.</p>
            <p v-if="!todayPlanTotals.complete" class="nutrition-note">بخشی از اطلاعات تغذیه‌ای ثبت نشده است؛ جمع بالا فقط مقادیر معلوم را نشان می‌دهد.</p>
            <div class="nutrition-today__actions"><button v-if="todayPlan.last_cart_prepared_date !== todayDate" type="button" class="nutrition-primary" :disabled="savingProfile || orderingPlan === todayPlan.name" @click="orderPlan(todayPlan)">{{ orderingPlan === todayPlan.name ? 'در حال بررسی موجودی و قیمت…' : 'بررسی و افزودن برنامه به سبد' }}<ArrowLeft :size="16" /></button><span v-else class="nutrition-success">برنامهٔ امروز قبلاً به سبد فرستاده شده است.</span><a href="/cart" class="nutrition-header-link">رفتن به سبد</a></div>
          </section>

          <section class="nutrition-panel nutrition-saved-plans">
            <div class="nutrition-section-head"><div><h2>برنامه‌های ذخیره‌شده</h2><p>برای هر روز فقط یک برنامهٔ فعال نگه داشته می‌شود.</p></div><span class="nutrition-step"><Bookmark :size="15" /></span></div>
            <p v-if="planError" class="nutrition-error" role="alert">{{ planError }}</p><p v-if="planMessage" class="nutrition-success" role="status">{{ planMessage }}</p>
            <div v-if="plans.length" class="nutrition-plan-list"><article v-for="plan in plans" :key="plan.name" :class="{ today: isTodayPlan(plan) }"><div class="nutrition-plan-list__main"><strong>{{ plan.title }}</strong><small>{{ plan.weekdays.length ? plan.weekdays.join('، ') : 'بدون زمان‌بندی هفتگی' }} · {{ plan.items.length.toLocaleString('fa-IR') }} قلم</small><small>جمع فعلی: {{ formatNumber(planTotals(plan).totals.kcal) }} kcal · {{ planPriceLabel(planTotals(plan)) }}</small><small v-if="plan.last_cart_prepared_date === todayDate">امروز به سبد فرستاده شده</small></div><div class="nutrition-plan-actions"><button v-if="isTodayPlan(plan) && plan.last_cart_prepared_date !== todayDate" type="button" class="nutrition-primary nutrition-primary--small" :disabled="savingProfile || orderingPlan === plan.name" @click="orderPlan(plan)">{{ orderingPlan === plan.name ? 'در حال بررسی…' : 'افزودن برنامهٔ امروز به سبد' }}<ArrowLeft :size="15" /></button><button type="button" class="nutrition-secondary nutrition-secondary--small" @click="editPlan(plan)"><Pencil :size="15" /> ویرایش</button><button type="button" class="nutrition-icon-button" :aria-label="`حذف ${plan.title}`" @click="deletePlan(plan)"><Trash2 :size="16" /></button></div></article></div>
            <div v-else class="nutrition-empty-small">هنوز برنامه‌ای ذخیره نشده است.</div>
          </section>

          <aside class="nutrition-summary" aria-live="polite">
            <div class="nutrition-summary__head"><div><small>جمع برنامهٔ در حال ویرایش</small><strong>{{ builder.title || 'برنامهٔ روزانه' }}</strong></div><span class="nutrition-summary__branch"><Store :size="14" />{{ branchTitle || 'شعبه انتخاب نشده' }}</span></div>
            <div class="nutrition-summary__stats"><span><small>کالری برنامه</small><strong>{{ formatNumber(builderTotals.totals.kcal) }} <small>kcal</small></strong></span><span><small>پروتئین برنامه</small><strong>{{ formatNumber(builderTotals.totals.protein_g) }} <small>g</small></strong></span><span><small>قیمت سفارش‌پذیر</small><strong>{{ planPriceLabel(builderTotals) }}</strong></span></div>
            <p v-if="!builderTotals.complete" class="nutrition-summary__warning"><CircleAlert :size="14" /> بعضی اقلام اطلاعات تغذیه‌ای کامل ندارند؛ عدد نمایش‌داده‌شده جمع اقلام معلوم است.</p>
            <div class="nutrition-summary__compare" v-if="targets.calorie_target_kcal"><span>هدف کالری روزانه</span><div><i :style="{ width: `${calorieProgress}%` }"></i></div><strong>{{ calorieProgress }}٪</strong></div>
            <div class="nutrition-summary__actions"><button class="nutrition-primary" type="button" :disabled="savingProfile || savingPlan || !profileExists || !profile.consent || !selectedBranch || !builder.items.length" @click="savePlan">{{ savingPlan ? 'در حال ذخیره…' : editingPlanName ? 'ذخیرهٔ تغییرات' : 'ذخیرهٔ برنامه' }}<Save :size="16" /></button><button v-if="editingPlanName" class="nutrition-text-button" type="button" @click="resetBuilder">برنامهٔ تازه</button></div>
            <p v-if="!profileExists" class="nutrition-note">برای ذخیرهٔ برنامه، ابتدا اطلاعات و رضایت را در گام اول ثبت کن.</p>
          </aside>
        </template>
      </template>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ArrowLeft, Bookmark, Check, CircleAlert, Coffee, HeartPulse, LoaderCircle, Moon, Pencil, Plus, Save, Search, Sparkles, Store, Trash2, UserRound, Utensils, X, Minus } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import { cartState, clearCart, saveOrderContext, upsertLine } from '@/stores/cartStore'
import { hasCustomerSession } from '@/utils/customerAuth'
import { isCustomerCompany } from '@/utils/orderBranches'
import { calculateNutritionTargets, calculatePlanTotals, NUTRITION_MEAL_SLOTS, NUTRITION_WEEKDAYS, localWeekdayIndex } from '@/utils/nutritionPlanning'
import { deleteMyMealPlan, deleteMyNutritionProfile, getBranches, getMyNutritionWorkspace, prepareMyMealPlanOrder, saveMyMealPlan, saveMyNutritionProfile, suggestMyMealPlans } from '@/utils/api'

const signedIn = ref(hasCustomerSession())
const loading = ref(false)
const pageError = ref('')
const profileExists = ref(false)
const profile = reactive({ age_years: '', formula_sex: '', height_cm: '', weight_kg: '', goal_weight_kg: '', activity_level: '', goal: '', calorie_target: '', protein_target_g: '', needs_specialist: false, specialist_reason: '', allergens: [], liked_items: [], disliked_items: [], liked_ingredients: [], disliked_ingredients: [], consent: false })
const profileMessage = ref('')
const profileError = ref('')
const savingProfile = ref(false)
const branches = ref([])
const selectedBranch = ref(cartState.orderContext.branch || '')
const catalog = ref([])
const plans = ref([])
const suggestions = ref([])
const suggestionMessage = ref('')
const suggesting = ref(false)
const builder = reactive({ title: 'برنامهٔ روزانه', weekdays: [], items: [] })
const editingPlanName = ref('')
const savingPlan = ref(false)
const planMessage = ref('')
const planError = ref('')
const pickerSlot = ref('')
const productSearch = ref('')
const orderingPlan = ref('')
const manualFood = reactive({ name: '', quantity: '', slot: 'میان‌وعده', kcal: '', protein_g: '', qty: 1 })
const weekdays = NUTRITION_WEEKDAYS
const mealSlots = NUTRITION_MEAL_SLOTS
const todayDate = ref('')
const todayWeekday = ref(weekdays[localWeekdayIndex()])
const targets = computed(() => calculateNutritionTargets(profile))
const catalogByCode = computed(() => Object.fromEntries(catalog.value.map((item) => [item.name, item])))
const builderTotals = computed(() => calculatePlanTotals(builder.items, catalogByCode.value))
const todayPlan = computed(() => plans.value.find((plan) => isTodayPlan(plan)) || null)
const todayPlanTotals = computed(() => todayPlan.value ? calculatePlanTotals(todayPlan.value.items || [], catalogByCode.value) : calculatePlanTotals())
const allergenOptions = computed(() => uniqueTags(catalog.value.flatMap((item) => item.allergens || [])))
const ingredientOptions = computed(() => uniqueTags(catalog.value.filter((item) => item.ingredients_reviewed).flatMap((item) => item.ingredient_tags || [])))
const safePickerProducts = computed(() => catalog.value.filter((item) => {
  if (!item.nutrition_verified || !item.allergen_reviewed || !item.ingredients_reviewed || item.out_of_stock || !Number(item.base_price)) return false
  if (pickerSlot.value && !(item.meal_slots || []).includes(pickerSlot.value)) return false
  if (profile.allergens.some((tag) => (item.allergens || []).some((allergen) => sameTag(tag, allergen)))) return false
  if (profile.disliked_items.includes(item.name)) return false
  if (profile.disliked_ingredients.some((tag) => (item.ingredient_tags || []).some((ingredient) => sameTag(tag, ingredient)))) return false
  const query = productSearch.value.trim().toLocaleLowerCase('fa-IR')
  return !query || String(item.title || '').toLocaleLowerCase('fa-IR').includes(query)
}))
const branchTitle = computed(() => branches.value.find((row) => (row.id || row.name) === selectedBranch.value)?.title || branches.value.find((row) => (row.id || row.name) === selectedBranch.value)?.name || selectedBranch.value)
const bmiLabel = computed(() => {
  if (Number(profile.age_years) > 0 && Number(profile.age_years) < 18) return 'نمایش BMI بزرگسالان برای زیر ۱۸ سال مناسب نیست'
  if (!Number(profile.age_years)) return 'برای نمایش BMI، سن بزرگسال را وارد کن'
  if (targets.value.bmi === null) return 'برای نمایش، قد و وزن را وارد کن'
  if (targets.value.bmi < 18.5) return 'پایین‌تر از بازهٔ مرجع'
  if (targets.value.bmi < 25) return 'در بازهٔ مرجع'
  if (targets.value.bmi < 30) return 'بالاتر از بازهٔ مرجع'
  return 'نیازمند بررسی تخصصی'
})
const calorieProgress = computed(() => targets.value.calorie_target_kcal ? Math.min(Math.round(builderTotals.value.totals.kcal / targets.value.calorie_target_kcal * 100), 100) : 0)

function sameTag(a, b) { return String(a || '').trim().toLocaleLowerCase('fa-IR') === String(b || '').trim().toLocaleLowerCase('fa-IR') }
function uniqueTags(values) { return [...new Set(values.map((value) => String(value || '').trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'fa')) }
function formatNumber(value) { return value === null || value === undefined || value === '' ? '—' : Math.round(Number(value)).toLocaleString('fa-IR') }
function formatPrice(value) { return `${Math.round(Number(value || 0)).toLocaleString('fa-IR')} تومان` }
function planPriceLabel(summary) { return !summary.restaurantItems ? 'بدون قلم وی‌درخت' : summary.priceComplete ? formatPrice(summary.totals.price) : 'قیمت پس از بررسی شعبه' }
function lineNutrition(row, key) {
  const product = row.source_type === 'ثبت دستی' ? null : productFor(row.item_code)
  if (row.source_type !== 'ثبت دستی' && !product?.nutrition_verified) return null
  const value = row.source_type === 'ثبت دستی' ? row.nutrition?.[key] : product?.nutrition?.[key]
  return value === null || value === undefined || value === '' ? null : Number(value) * Number(row.qty || 1)
}
function slotIcon(slot) { return slot === 'صبحانه' ? Coffee : slot === 'شام' ? Moon : Utensils }
function productFor(code) { return catalogByCode.value[code] }
function itemsForSlot(slot) { return builder.items.filter((row) => row.meal_slot === slot) }
function planTotals(plan) { return calculatePlanTotals(plan.items || [], catalogByCode.value) }
function isTodayPlan(plan) { return Boolean(plan.active && (plan.weekdays || []).includes(todayWeekday.value)) }

function applyProfile(source = {}) {
  for (const key of ['age_years', 'formula_sex', 'height_cm', 'weight_kg', 'goal_weight_kg', 'activity_level', 'goal', 'calorie_target', 'protein_target_g', 'specialist_reason']) profile[key] = source[key] ?? ''
  profile.needs_specialist = Boolean(Number(source.needs_specialist || 0))
  profile.allergens = [...(source.allergens || [])]
  profile.liked_items = [...(source.liked_items || [])]
  profile.disliked_items = [...(source.disliked_items || [])]
  profile.liked_ingredients = [...(source.liked_ingredients || [])]
  profile.disliked_ingredients = [...(source.disliked_ingredients || [])]
  profile.consent = Boolean(Number(source.consent || 0))
}

async function loadWorkspace() {
  if (!signedIn.value) return
  loading.value = true
  pageError.value = ''
  try {
    const branchPayload = await getBranches()
    branches.value = (branchPayload?.branches || []).filter(isCustomerCompany)
    if (!branches.value.some((row) => (row.id || row.name) === selectedBranch.value)) selectedBranch.value = branches.value.length === 1 ? branches.value[0].id || branches.value[0].name : ''
    const workspace = await getMyNutritionWorkspace(selectedBranch.value)
    todayDate.value = workspace?.today || ''
    todayWeekday.value = workspace?.today_weekday || todayWeekday.value
    applyProfile(workspace?.profile?.profile || {})
    profileExists.value = Boolean(workspace?.profile?.exists)
    plans.value = workspace?.plans || []
    catalog.value = workspace?.catalog || []
    if (selectedBranch.value && !workspace?.branch) await loadCatalog()
  } catch (error) { pageError.value = error?.message || 'اطلاعات برنامه دریافت نشد.' }
  finally { loading.value = false }
}

async function loadCatalog() {
  catalog.value = []
  suggestions.value = []
  if (!selectedBranch.value) return
  try {
    const workspace = await getMyNutritionWorkspace(selectedBranch.value)
    catalog.value = workspace?.catalog || []
    if (cartState.orderContext.branch !== selectedBranch.value) {
      const branch = branches.value.find((row) => (row.id || row.name) === selectedBranch.value)
      saveOrderContext({ branch: selectedBranch.value, branch_title: branch?.title || branch?.name || selectedBranch.value })
    }
  } catch (error) { pageError.value = error?.message || 'منوی شعبه دریافت نشد.' }
}

async function saveProfile() {
  if (!profile.consent || savingProfile.value) return
  savingProfile.value = true
  profileError.value = ''
  profileMessage.value = ''
  try {
    const payload = { ...profile, consent: 1, needs_specialist: profile.needs_specialist ? 1 : 0 }
    const result = await saveMyNutritionProfile(payload)
    applyProfile(result?.profile || payload)
    profileExists.value = true
    profileMessage.value = 'پروفایل تغذیه‌ای خصوصی شما ذخیره شد.'
  } catch (error) { profileError.value = error?.message || 'ذخیرهٔ پروفایل انجام نشد.' }
  finally { savingProfile.value = false }
}

async function deleteProfile() {
  if (!window.confirm('اطلاعات تغذیه‌ای و برنامه‌های ذخیره‌شده حذف شوند؟')) return
  savingProfile.value = true
  profileError.value = ''
  try {
    await deleteMyNutritionProfile()
    applyProfile({})
    profileExists.value = false
    plans.value = []
    resetBuilder()
    profileMessage.value = 'اطلاعات و برنامه‌های تغذیه‌ای حذف شدند.'
  } catch (error) { profileError.value = error?.message || 'حذف اطلاعات انجام نشد.' }
  finally { savingProfile.value = false }
}

async function loadSuggestions() {
  suggesting.value = true
  suggestions.value = []
  suggestionMessage.value = ''
  try {
    await saveProfile()
    if (profileError.value) throw new Error(profileError.value)
    if (!profileExists.value) throw new Error(profileError.value || 'ابتدا پروفایل را ذخیره کن.')
    const payload = await suggestMyMealPlans(selectedBranch.value)
    suggestions.value = payload?.suggestions || []
    suggestionMessage.value = payload?.reason || ''
  } catch (error) { suggestionMessage.value = error?.message || 'ساخت پیشنهاد انجام نشد.' }
  finally { suggesting.value = false }
}

function useSuggestion(suggestion) {
  builder.title = suggestion.title || 'برنامهٔ پیشنهادی'
  builder.items = (suggestion.items || []).map((row) => ({ ...row, customization: row.customization || {} }))
  planMessage.value = 'ترکیب پیشنهادی وارد برنامه شد؛ می‌توانی وعده‌ها را تغییر بدهی.'
}

function openPicker(slot) { pickerSlot.value = slot; productSearch.value = '' }
function addProduct(product) {
  const found = builder.items.find((row) => row.meal_slot === pickerSlot.value && row.source_type === 'وی‌درخت' && row.item_code === product.name)
  if (found) found.qty = Math.min(Number(found.qty || 1) + 1, 40)
  else builder.items.push({ meal_slot: pickerSlot.value, source_type: 'وی‌درخت', item_code: product.name, qty: 1, customization: {} })
  pickerSlot.value = ''
}
function addManualFood() {
  if (!manualFood.name.trim()) return
  builder.items.push({ meal_slot: manualFood.slot, source_type: 'ثبت دستی', manual_name: manualFood.name.trim(), manual_quantity: manualFood.quantity.trim(), qty: Math.max(1, Number(manualFood.qty || 1)), nutrition: { kcal: manualFood.kcal === '' ? null : Number(manualFood.kcal), protein_g: manualFood.protein_g === '' ? null : Number(manualFood.protein_g), carb_g: null, fat_g: null } })
  manualFood.name = ''; manualFood.quantity = ''; manualFood.kcal = ''; manualFood.protein_g = ''; manualFood.qty = 1
}
function changeQty(row, delta) { row.qty = Math.max(1, Math.min(40, Number(row.qty || 1) + delta)) }
function removeLine(row) { const index = builder.items.indexOf(row); if (index >= 0) builder.items.splice(index, 1) }
function editPlan(plan) {
  editingPlanName.value = plan.name
  builder.title = plan.title
  builder.weekdays = [...(plan.weekdays || [])]
  builder.items = JSON.parse(JSON.stringify(plan.items || []))
  if (plan.branch !== selectedBranch.value) {
    selectedBranch.value = plan.branch
    loadCatalog()
  }
  window.scrollTo({ top: document.querySelector('.nutrition-builder-top')?.getBoundingClientRect().top + window.scrollY - 90 || 0, behavior: 'smooth' })
}
function resetBuilder() { editingPlanName.value = ''; builder.title = 'برنامهٔ روزانه'; builder.weekdays = []; builder.items = []; planMessage.value = ''; planError.value = '' }
async function savePlan() {
  if (!selectedBranch.value || !builder.title.trim() || !builder.items.length || !profile.consent || savingProfile.value || savingPlan.value) return
  savingPlan.value = true; planError.value = ''; planMessage.value = ''
  try {
    await saveProfile()
    if (profileError.value) throw new Error(profileError.value)
    const payload = await saveMyMealPlan({ name: editingPlanName.value, title: builder.title.trim(), branch: selectedBranch.value, weekdays: builder.weekdays, items: builder.items })
    const plan = payload?.plan
    if (plan) {
      const index = plans.value.findIndex((row) => row.name === plan.name)
      if (index < 0) plans.value.unshift(plan)
      else plans.value[index] = plan
      editingPlanName.value = plan.name
    }
    planMessage.value = 'برنامه ذخیره شد. سفارش هر روز با بررسی و تأیید خودت انجام می‌شود.'
  } catch (error) { planError.value = error?.message || 'ذخیرهٔ برنامه انجام نشد.' }
  finally { savingPlan.value = false }
}
async function deletePlan(plan) {
  if (!window.confirm(`برنامهٔ «${plan.title}» حذف شود؟`)) return
  planError.value = ''
  try { await deleteMyMealPlan(plan.name); plans.value = plans.value.filter((row) => row.name !== plan.name); if (editingPlanName.value === plan.name) resetBuilder(); planMessage.value = 'برنامه حذف شد.' }
  catch (error) { planError.value = error?.message || 'حذف برنامه انجام نشد.' }
}
async function orderPlan(plan) {
  if (savingProfile.value || orderingPlan.value) return
  orderingPlan.value = plan.name; planError.value = ''
  try {
    if (!profile.consent) throw new Error('برای استفاده از حساسیت‌ها و برنامهٔ خصوصی، رضایت ذخیره‌سازی را تأیید کن یا اطلاعات را حذف کن.')
    const requestedBranch = selectedBranch.value || plan.branch
    if (requestedBranch !== plan.branch && !window.confirm(`شعبهٔ این برنامه «${plan.branch}» است. اقلام را برای شعبهٔ «${branchTitle.value || requestedBranch}» دوباره بررسی کنم؟ محصول جایگزین بدون انتخاب شما اضافه نمی‌شود.`)) return
    if (cartState.lines.length && !window.confirm('سبد فعلی جایگزین اقلام برنامهٔ امروز شود؟')) return
    await saveProfile()
    if (profileError.value) throw new Error(profileError.value)
    const payload = await prepareMyMealPlanOrder(plan.name, requestedBranch)
    if (payload?.warnings?.length) {
      planError.value = payload.warnings.map((row) => `${productFor(row.item_code)?.title || row.item_code}: ${row.reason}`).join(' ')
      return
    }
    if (!payload?.can_order || !payload.items?.length) throw new Error('در این برنامه محصول سفارش‌پذیری وجود ندارد.')
    clearCart()
    for (const item of payload.items) upsertLine({ item_slug: item.item_slug, item_title: item.item_title, base_price: item.base_price, qty: item.qty, unit_price_preview: item.base_price, line_total_preview: item.base_price * item.qty, customization: item.customization })
    const branchRow = branches.value.find((row) => (row.id || row.name) === payload.branch)
    saveOrderContext({ branch: payload.branch, branch_title: branchRow?.title || branchRow?.name || payload.branch })
    const savedPlan = plans.value.find((row) => row.name === plan.name)
    if (savedPlan) savedPlan.last_cart_prepared_date = payload.run_date || todayDate.value
    window.location.assign(cartState.orderContext.order_type ? '/cart' : '/order/type')
  } catch (error) { planError.value = error?.message || 'آماده‌سازی سفارش انجام نشد.' }
  finally { orderingPlan.value = '' }
}

watch(selectedBranch, () => { suggestions.value = [] })
onMounted(async () => {
  if (signedIn.value) await loadWorkspace()
})
</script>

<style scoped>
.nutrition-page { min-height: 100vh; padding-bottom: calc(12rem + env(safe-area-inset-bottom)); background: var(--ds-color-bg-page); color: var(--ds-color-text-primary); }
.nutrition-page :deep(.customer-page__hero) { background: radial-gradient(ellipse at 10% 0%, color-mix(in srgb, var(--ds-color-action-accent) 12%, transparent), transparent 42%), var(--ds-color-surface-raised); border-bottom: 1px solid var(--ds-color-border); }
.nutrition-header-link { min-height: 44px; display: inline-flex; align-items: center; color: var(--ds-color-action-primary); font-size: .82rem; font-weight: 850; text-decoration: none; }
.nutrition-layout { width: min(920px, calc(100% - 1.25rem)); margin: 1rem auto 2rem; display: grid; gap: .85rem; }
.nutrition-panel { min-width: 0; padding: clamp(1rem, 3vw, 1.4rem); border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-raised); box-shadow: var(--ds-shadow-sm); }
.nutrition-intro { display: flex; gap: .8rem; align-items: flex-start; background: color-mix(in srgb, var(--ds-color-action-accent) 6%, var(--ds-color-surface-raised)); }
.nutrition-intro__icon,.nutrition-step { flex: none; display: grid; place-items: center; width: 40px; height: 40px; border-radius: 13px; background: color-mix(in srgb, var(--ds-color-action-accent) 15%, var(--ds-color-surface)); color: var(--ds-color-action-accent); }
.nutrition-intro h2,.nutrition-section-head h2,.nutrition-empty h2 { margin: 0; font-size: 1rem; font-weight: 900; }
.nutrition-intro p,.nutrition-section-head p,.nutrition-empty p { margin: .3rem 0 0; color: var(--ds-color-text-secondary); font-size: .8rem; line-height: 1.8; }
.nutrition-section-head { display: flex; justify-content: space-between; align-items: flex-start; gap: .8rem; margin-bottom: 1rem; }
.nutrition-eyebrow { margin: 0 0 .2rem !important; color: var(--ds-color-action-accent) !important; font-size: .69rem !important; font-weight: 900; }
.nutrition-step { width: 34px; height: 34px; font-weight: 900; }
.nutrition-form-grid { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: .7rem; }
.nutrition-form-grid label,.nutrition-builder-top label,.nutrition-manual-grid label { display: grid; gap: .35rem; color: var(--ds-color-text-secondary); font-size: .73rem; font-weight: 800; }
.nutrition-form-grid__wide { grid-column: span 2; }
.nutrition-form-grid label small { color: var(--ds-color-text-muted); font-size: .65rem; }
.nutrition-input { width: 100%; min-width: 0; min-height: 44px; padding: .58rem .68rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-sm); background: var(--ds-color-surface); color: var(--ds-color-text-primary); font: inherit; font-size: .8rem; }
.nutrition-input:focus-visible,.nutrition-primary:focus-visible,.nutrition-secondary:focus-visible,.nutrition-icon-button:focus-visible { outline: 3px solid color-mix(in srgb, var(--ds-color-action-accent) 50%, transparent); outline-offset: 2px; }
.nutrition-input-unit { position: relative; }
.nutrition-input-unit input { padding-inline-end: 2.4rem; }
.nutrition-input-unit small { position: absolute; inset-inline-end: .7rem; top: 50%; transform: translateY(-50%); color: var(--ds-color-text-muted); font-size: .7rem; }
.nutrition-safety { margin: .9rem 0 0; padding: .8rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); }
.nutrition-safety legend,.nutrition-filter-grid legend { padding: 0 .25rem; color: var(--ds-color-text-primary); font-size: .77rem; font-weight: 900; }
.nutrition-safety label { display: flex; gap: .5rem; align-items: flex-start; color: var(--ds-color-text-secondary); font-size: .72rem; line-height: 1.8; }
.nutrition-safety input,.nutrition-chip input { accent-color: var(--ds-color-action-primary); }
.nutrition-safety p { margin: .25rem 1.3rem .55rem 0; color: var(--ds-color-text-muted); font-size: .68rem; line-height: 1.7; }
.nutrition-safety .nutrition-consent { padding-top: .65rem; border-top: 1px solid var(--ds-color-border); color: var(--ds-color-text-primary); font-weight: 800; }
.nutrition-metrics { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: .55rem; margin-top: .8rem; }
.nutrition-metrics article { display: grid; gap: .2rem; min-height: 82px; padding: .7rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); }
.nutrition-metrics article small,.nutrition-metrics article span { color: var(--ds-color-text-muted); font-size: .66rem; }
.nutrition-metrics article strong { font-size: .9rem; font-weight: 900; }
.nutrition-metrics__accent { border-color: color-mix(in srgb, var(--ds-color-action-accent) 45%, var(--ds-color-border)) !important; background: color-mix(in srgb, var(--ds-color-action-accent) 7%, var(--ds-color-surface)) !important; }
.nutrition-note,.nutrition-muted { margin: .55rem 0; color: var(--ds-color-text-muted); font-size: .7rem; line-height: 1.8; }
.nutrition-actions { display: flex; align-items: center; gap: .7rem; flex-wrap: wrap; margin-top: .8rem; }
.nutrition-primary,.nutrition-secondary,.nutrition-text-button,.nutrition-add-button,.nutrition-icon-button { display: inline-flex; align-items: center; justify-content: center; gap: .4rem; min-height: 44px; padding: .55rem .8rem; border-radius: var(--ds-radius-md); font: inherit; font-size: .77rem; font-weight: 900; cursor: pointer; text-decoration: none; }
.nutrition-primary { border: 1px solid var(--ds-color-action-accent); background: var(--ds-color-action-accent); color: var(--ds-color-action-accent-foreground); }
.nutrition-secondary,.nutrition-icon-button { border: 1px solid var(--ds-color-border); background: var(--ds-color-surface); color: var(--ds-color-text-primary); }
.nutrition-text-button { border: 0; background: transparent; color: var(--ds-color-status-danger); }
.nutrition-primary:disabled,.nutrition-secondary:disabled { opacity: .55; cursor: not-allowed; }
.nutrition-success,.nutrition-error { margin: .55rem 0 0; font-size: .75rem; line-height: 1.8; }
.nutrition-success { color: var(--ds-color-status-success); }.nutrition-error { color: var(--ds-color-status-danger); }
.nutrition-filter-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: .6rem; }
.nutrition-filter-grid fieldset { min-width: 0; margin: 0; padding: .65rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); }
.nutrition-chips { display: flex; gap: .4rem; flex-wrap: wrap; }
.nutrition-chip { position: relative; }.nutrition-chip input { position: absolute; opacity: 0; }.nutrition-chip span { display: inline-flex; min-height: 35px; align-items: center; padding: .3rem .55rem; border: 1px solid var(--ds-color-border); border-radius: 999px; background: var(--ds-color-surface); color: var(--ds-color-text-secondary); font-size: .68rem; cursor: pointer; }
.nutrition-chip.selected span { border-color: var(--ds-color-action-accent); background: color-mix(in srgb, var(--ds-color-action-accent) 10%, var(--ds-color-surface)); color: var(--ds-color-text-primary); font-weight: 850; }
.nutrition-branch { display: grid; grid-template-columns: 1fr 1.5fr; align-items: center; gap: .8rem; max-width: 560px; margin-top: .8rem; color: var(--ds-color-text-secondary); font-size: .75rem; font-weight: 800; }
.nutrition-branch > span { display: inline-flex; align-items: center; gap: .4rem; }
.nutrition-builder-top { display: grid; grid-template-columns: 1fr 1.3fr; align-items: end; gap: .8rem; }
.nutrition-day-picker { display: grid; gap: .35rem; color: var(--ds-color-text-secondary); font-size: .73rem; font-weight: 800; }.nutrition-day-picker > div { display: flex; gap: .35rem; }
.nutrition-day-picker label { position: relative; }.nutrition-day-picker input { position: absolute; opacity: 0; }.nutrition-day-picker span { display: grid; place-items: center; width: 36px; height: 36px; border: 1px solid var(--ds-color-border); border-radius: 50%; background: var(--ds-color-surface); cursor: pointer; }.nutrition-day-picker label.selected span { border-color: var(--ds-color-action-primary); background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); font-weight: 900; }
.nutrition-suggestion-row { display: flex; gap: .6rem; align-items: center; flex-wrap: wrap; margin: .8rem 0; }.nutrition-suggestion-row small { color: var(--ds-color-text-muted); font-size: .7rem; }
.nutrition-suggestions { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: .45rem; margin-bottom: .85rem; }.nutrition-suggestions button { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: .15rem .35rem; padding: .6rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); color: var(--ds-color-text-primary); text-align: start; cursor: pointer; }.nutrition-suggestions button strong { font-size: .72rem; }.nutrition-suggestions button small { color: var(--ds-color-text-muted); font-size: .63rem; }.nutrition-suggestions button svg { grid-column: 2; grid-row: 1 / 3; color: var(--ds-color-action-accent); }
.nutrition-slot-list { display: grid; gap: .55rem; }.nutrition-slot { overflow: hidden; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); }.nutrition-slot > header { display: flex; justify-content: space-between; align-items: center; gap: .5rem; padding: .65rem .75rem; border-bottom: 1px solid var(--ds-color-border); }.nutrition-slot > header > div { display: flex; align-items: center; gap: .45rem; }.nutrition-slot h3 { margin: 0; font-size: .8rem; }.nutrition-slot > header small { color: var(--ds-color-text-muted); font-size: .65rem; }.nutrition-slot__icon { display: grid; place-items: center; width: 30px; height: 30px; border-radius: 10px; background: color-mix(in srgb, var(--ds-color-action-primary) 10%, var(--ds-color-surface)); color: var(--ds-color-action-primary); }
.nutrition-add-button { min-height: 36px; padding: .35rem .6rem; border: 1px solid color-mix(in srgb, var(--ds-color-action-accent) 45%, var(--ds-color-border)); background: color-mix(in srgb, var(--ds-color-action-accent) 8%, var(--ds-color-surface)); color: var(--ds-color-text-primary); font-size: .68rem; }.nutrition-line-list { display: grid; }.nutrition-line { display: flex; align-items: center; justify-content: space-between; gap: .5rem; padding: .6rem .75rem; border-bottom: 1px solid var(--ds-color-border); }.nutrition-line:last-child { border-bottom: 0; }.nutrition-line__copy { display: grid; gap: .15rem; min-width: 0; }.nutrition-line__copy strong { overflow: hidden; color: var(--ds-color-text-primary); font-size: .75rem; text-overflow: ellipsis; white-space: nowrap; }.nutrition-line__copy small { color: var(--ds-color-text-muted); font-size: .64rem; }.nutrition-line__controls { display: flex; align-items: center; gap: .2rem; flex: none; }.nutrition-line__controls button { display: grid; place-items: center; width: 32px; height: 32px; border: 1px solid var(--ds-color-border); border-radius: 9px; background: var(--ds-color-surface-raised); color: var(--ds-color-text-secondary); cursor: pointer; }.nutrition-line__controls .remove { margin-inline-start: .25rem; color: var(--ds-color-status-danger); }.nutrition-line__controls span { min-width: 20px; text-align: center; font-size: .72rem; font-weight: 850; }.nutrition-slot-empty { margin: 0; padding: .7rem; color: var(--ds-color-text-muted); font-size: .7rem; }
.nutrition-manual-food { margin-top: .7rem; border: 1px dashed var(--ds-color-border); border-radius: var(--ds-radius-md); }.nutrition-manual-food summary { display: flex; align-items: center; gap: .4rem; min-height: 46px; padding: .5rem .7rem; color: var(--ds-color-action-primary); font-size: .75rem; font-weight: 850; cursor: pointer; list-style: none; }.nutrition-manual-food summary::-webkit-details-marker { display: none; }.nutrition-manual-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: .55rem; padding: .7rem; border-top: 1px solid var(--ds-color-border); }.nutrition-manual-grid .nutrition-secondary { align-self: end; }
.nutrition-plan-list { display: grid; gap: .5rem; }.nutrition-plan-list article { display: flex; justify-content: space-between; align-items: center; gap: .7rem; padding: .75rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); }.nutrition-plan-list article.today { border-color: color-mix(in srgb, var(--ds-color-action-accent) 55%, var(--ds-color-border)); }.nutrition-plan-list__main { display: grid; gap: .2rem; }.nutrition-plan-list__main strong { font-size: .8rem; }.nutrition-plan-list__main small { color: var(--ds-color-text-muted); font-size: .67rem; }.nutrition-plan-actions { display: flex; gap: .35rem; align-items: center; }.nutrition-primary--small,.nutrition-secondary--small { min-height: 36px; padding: .35rem .55rem; font-size: .67rem; }.nutrition-icon-button { width: 38px; height: 38px; padding: .35rem; color: var(--ds-color-text-secondary); }
.nutrition-summary { position: sticky; z-index: 20; bottom: calc(.5rem + env(safe-area-inset-bottom)); padding: .8rem; border: 1px solid color-mix(in srgb, var(--ds-color-action-primary) 35%, var(--ds-color-border)); border-radius: var(--ds-radius-lg); background: color-mix(in srgb, var(--ds-color-surface-raised) 94%, transparent); box-shadow: var(--ds-shadow-lg); backdrop-filter: blur(14px); }.nutrition-summary__head { display: flex; align-items: center; justify-content: space-between; gap: .5rem; }.nutrition-summary__head > div { display: grid; gap: .15rem; }.nutrition-summary__head small,.nutrition-summary__branch { color: var(--ds-color-text-muted); font-size: .64rem; }.nutrition-summary__head strong { font-size: .8rem; }.nutrition-summary__branch { display: inline-flex; align-items: center; gap: .25rem; }.nutrition-summary__stats { display: grid; grid-template-columns: repeat(3,1fr); gap: .4rem; margin: .6rem 0; }.nutrition-summary__stats span { display: grid; gap: .15rem; padding: .45rem; border-radius: 10px; background: var(--ds-color-surface); }.nutrition-summary__stats small { color: var(--ds-color-text-muted); font-size: .6rem; }.nutrition-summary__stats strong { font-size: .77rem; }.nutrition-summary__warning { display: flex; align-items: center; gap: .3rem; margin: .2rem 0; color: var(--ds-color-status-warning); font-size: .65rem; }.nutrition-summary__compare { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: .45rem; color: var(--ds-color-text-muted); font-size: .64rem; }.nutrition-summary__compare > div { height: 6px; overflow: hidden; border-radius: 99px; background: var(--ds-color-surface-muted); }.nutrition-summary__compare i { display: block; height: 100%; border-radius: inherit; background: var(--ds-color-action-accent); }.nutrition-summary__actions { display: flex; gap: .45rem; align-items: center; margin-top: .55rem; }.nutrition-summary__actions .nutrition-primary { flex: 1; min-height: 42px; }
.nutrition-inline-alert,.nutrition-empty-small { padding: .8rem; border: 1px dashed var(--ds-color-border); border-radius: var(--ds-radius-md); color: var(--ds-color-text-muted); font-size: .73rem; line-height: 1.7; }.nutrition-empty { min-height: 200px; display: grid; justify-items: center; align-content: center; gap: .5rem; text-align: center; }.nutrition-empty .nutrition-primary { margin-top: .5rem; }.nutrition-empty-small { text-align: center; }
.nutrition-picker-backdrop { position: fixed; z-index: 1000; inset: 0; display: grid; place-items: center; padding: 1rem; background: rgb(25 24 22 / 54%); }.nutrition-picker { display: grid; grid-template-rows: auto auto minmax(0,1fr); width: min(620px,100%); max-height: min(80vh,720px); padding: 1rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-raised); box-shadow: var(--ds-shadow-lg); }.nutrition-picker > header { display: flex; justify-content: space-between; align-items: flex-start; gap: .5rem; }.nutrition-picker h2 { margin: 0; font-size: .95rem; }.nutrition-search { display: flex; align-items: center; gap: .45rem; margin: .8rem 0; padding-inline: .65rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-sm); color: var(--ds-color-text-muted); }.nutrition-search input { min-height: 42px; width: 100%; border: 0; outline: 0; background: transparent; color: var(--ds-color-text-primary); font: inherit; font-size: .78rem; }.nutrition-picker-list { overflow: auto; display: grid; align-content: start; gap: .45rem; }.nutrition-picker-list article { display: flex; justify-content: space-between; align-items: center; gap: .5rem; padding: .6rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); }.nutrition-picker-list article > div { display: grid; gap: .15rem; }.nutrition-picker-list strong { font-size: .75rem; }.nutrition-picker-list small { color: var(--ds-color-text-muted); font-size: .65rem; }
.spin { animation: nutrition-spin 1s linear infinite; }@keyframes nutrition-spin { to { transform: rotate(360deg); } }
@media (max-width: 720px) { .nutrition-form-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }.nutrition-form-grid__wide { grid-column: span 2; }.nutrition-metrics { grid-template-columns: repeat(2,minmax(0,1fr)); }.nutrition-filter-grid { grid-template-columns: 1fr; }.nutrition-suggestions { grid-template-columns: 1fr; }.nutrition-plan-list article { align-items: flex-start; flex-direction: column; }.nutrition-plan-actions { width: 100%; flex-wrap: wrap; }.nutrition-plan-actions .nutrition-primary { flex: 1; }.nutrition-summary__stats strong { font-size: .7rem; }.nutrition-builder-top { grid-template-columns: 1fr; }.nutrition-manual-grid { grid-template-columns: repeat(2,minmax(0,1fr)); } }
@media (max-width: 420px) { .nutrition-layout { width: calc(100% - .75rem); }.nutrition-panel { padding: .8rem; }.nutrition-form-grid { gap: .5rem; }.nutrition-day-picker > div { justify-content: space-between; }.nutrition-day-picker span { width: 32px; height: 32px; }.nutrition-summary { padding: .65rem; }.nutrition-summary__stats { gap: .25rem; }.nutrition-summary__stats span { padding: .35rem; }.nutrition-summary__stats small { font-size: .55rem; }.nutrition-summary__stats strong { font-size: .65rem; }.nutrition-branch { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: reduce) { .spin { animation: none; } }
.nutrition-meal-select { max-width: 6.5rem; min-height: 32px; padding: .25rem; border: 1px solid var(--ds-color-border); border-radius: 8px; background: var(--ds-color-surface); color: var(--ds-color-text-secondary); font: inherit; font-size: .62rem; }
.nutrition-product-preferences { min-height: 110px; }
.nutrition-choice-list { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: .3rem; max-height: 190px; overflow: auto; padding: .15rem; }
.nutrition-choice { display: flex; align-items: flex-start; gap: .35rem; min-width: 0; padding: .35rem; border-radius: 9px; color: var(--ds-color-text-secondary); font-size: .65rem; line-height: 1.6; cursor: pointer; }
.nutrition-choice input { flex: none; margin-top: .2rem; accent-color: var(--ds-color-action-accent); }
.nutrition-choice span { overflow-wrap: anywhere; }
.nutrition-choice.selected { background: color-mix(in srgb, var(--ds-color-action-accent) 8%, var(--ds-color-surface)); color: var(--ds-color-text-primary); font-weight: 800; }
.nutrition-today { border-color: color-mix(in srgb, var(--ds-color-action-accent) 45%, var(--ds-color-border)); background: linear-gradient(135deg,color-mix(in srgb,var(--ds-color-action-accent) 5%,var(--ds-color-surface-raised)),var(--ds-color-surface-raised)); }
.nutrition-today__badge { display: inline-flex; align-items: center; gap: .25rem; padding: .35rem .55rem; border-radius: 999px; background: var(--ds-color-action-accent-soft); color: var(--ds-color-action-accent); font-size: .68rem; font-weight: 900; }
.nutrition-today__items { display: grid; gap: .35rem; }
.nutrition-today__items > div { display: flex; justify-content: space-between; align-items: center; gap: .5rem; padding: .55rem .65rem; border: 1px solid var(--ds-color-border); border-radius: 11px; background: var(--ds-color-surface); }
.nutrition-today__items > div > span { display: grid; gap: .12rem; min-width: 0; }
.nutrition-today__items strong { overflow: hidden; font-size: .74rem; text-overflow: ellipsis; white-space: nowrap; }
.nutrition-today__items small { color: var(--ds-color-text-muted); font-size: .63rem; }
.nutrition-today__items b { flex: none; color: var(--ds-color-text-secondary); font-size: .67rem; }
.nutrition-today__totals { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: .4rem; margin-top: .55rem; }
.nutrition-today__totals > span { display: grid; gap: .15rem; padding: .55rem; border-radius: 10px; background: var(--ds-color-surface); }
.nutrition-today__totals small { color: var(--ds-color-text-muted); font-size: .62rem; }
.nutrition-today__totals strong { font-size: .73rem; }
.nutrition-today__actions { display: flex; align-items: center; gap: .7rem; flex-wrap: wrap; margin-top: .65rem; }
.nutrition-today__actions .nutrition-primary { min-height: 42px; }
@media (max-width: 720px) { .nutrition-today__totals { grid-template-columns: 1fr; } }
</style>
