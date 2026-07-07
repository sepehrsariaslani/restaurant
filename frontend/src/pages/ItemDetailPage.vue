<template>
  <div class="detail-page" dir="rtl">
    <div class="state-shell" v-if="!item && (loading || error)">
      <div class="state-content">
        <!-- Loading skeleton -->
        <div class="detail-skeleton" v-if="loading">
          <div class="skeleton-hero shimmer"></div>
          <div class="skeleton-info">
            <div class="skeleton-line shimmer" style="width: 30%"></div>
            <div class="skeleton-line shimmer" style="width: 70%"></div>
            <div class="skeleton-line shimmer" style="width: 40%"></div>
            <div class="skeleton-line shimmer" style="width: 90%"></div>
            <div class="skeleton-line shimmer" style="width: 80%"></div>
            <div class="skeleton-line shimmer" style="width: 60%"></div>
          </div>
        </div>
        <!-- Error state with retry -->
        <div class="error-state" v-else-if="error">
          <svg class="error-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <p class="error-msg">{{ error }}</p>
          <button class="retry-btn" @click="loadItem" :disabled="loading">تلاش مجدد</button>
        </div>
      </div>
    </div>

    <div class="detail-wrap" v-if="item">
      <OrderContextStrip :currency="currency" />
      <!-- ════════════════════════════════════════════════════════════════
           MOBILE LAYOUT
           ════════════════════════════════════════════════════════════════ -->
      <!-- Hero gallery: full-bleed, no header above it -->
      <div class="hero-area mobile-only">
        <div class="gallery-track" :style="{ transform: `translateX(${galleryOffset}%)` }">
          <div v-for="(src, idx) in galleryImages" :key="idx" class="gallery-slide">
            <img
              :src="src"
              :alt="`${item.title} - ${idx + 1}`"
              class="gallery-img"
            />
          </div>
        </div>

        <template v-if="galleryImages.length > 1">
          <button class="gallery-arrow gallery-arrow--prev" @click="prevImage" aria-label="قبلی">›</button>
          <button class="gallery-arrow gallery-arrow--next" @click="nextImage" aria-label="بعدی">‹</button>
          <div class="gallery-dots">
            <span
              v-for="(_, idx) in galleryImages"
              :key="idx"
              class="gallery-dot"
              :class="{ active: galleryIndex === idx }"
              @click="galleryIndex = idx"
            ></span>
          </div>
        </template>

        <!-- Overlay nav buttons on the image -->
        <div class="hero-nav">
          <a href="/menu" class="nav-circle back-btn" aria-label="بازگشت">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
          </a>
          <div class="hero-nav-actions">
            <button
              class="nav-circle wishlist-circle"
              :class="{ loved: isWishlisted }"
              type="button"
              @click="toggleWishlist"
              aria-label="علاقه‌مندی"
            >{{ isWishlisted ? '♥' : '♡' }}</button>
            <button
              class="nav-circle"
              type="button"
              @click="shareProduct"
              aria-label="اشتراک‌گذاری"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile content card -->
      <div class="content-card mobile-only">
        <!-- Title row -->
        <div class="title-row">
          <div class="title-block">
            <p class="item-category">{{ item.category_title || item.category || 'منو' }}</p>
            <h1 class="item-title">{{ item.title }}</h1>
          </div>
          <div class="prep-badge" v-if="prepTimeText">
            <span class="prep-icon">⏱</span>
            <span class="prep-text">{{ prepTimeText }}</span>
          </div>
        </div>

        <!-- Rating -->
        <div class="rating-row" v-if="reviewCount > 0">
          <div class="stars-display">
            <span v-for="s in 5" :key="s" class="star" :class="{ filled: s <= Math.round(averageRating) }">★</span>
          </div>
          <span class="rating-num">{{ averageRating }}</span>
          <span class="rating-count">({{ reviewCount }} نظر)</span>
        </div>

        <!-- Base price -->
        <div class="price-block">
          <span class="base-price">{{ isComingSoon ? 'به‌زودی' : displayBasePriceText }}</span>
        </div>

        <!-- Description -->
        <p class="item-desc">{{ item.long_desc || item.short_desc || 'توضیح تکمیلی ثبت نشده است.' }}</p>

        <!-- Tabs -->
        <div class="detail-tabs">
          <button
            class="detail-tab"
            :class="{ active: activeTab === 'details' }"
            @click="activeTab = 'details'"
            type="button"
          >
            اطلاعات کلی
          </button>
          <button
            class="detail-tab"
            :class="{ active: activeTab === 'ingredients' }"
            @click="activeTab = 'ingredients'"
            type="button"
          >
            {{ ingredientTabLabel }}
          </button>
          <button
            v-if="isBuilderEnabled"
            class="detail-tab"
            :class="{ active: activeTab === 'builder' }"
            @click="activeTab = 'builder'"
            type="button"
          >
            سفارشی‌سازی
          </button>
          <button
            class="detail-tab"
            :class="{ active: activeTab === 'reviews' }"
            @click="activeTab = 'reviews'"
            type="button"
          >
            نظرات
            <span class="tab-badge" v-if="reviewCount > 0">{{ reviewCount }}</span>
          </button>
        </div>

        <!-- Tab: details -->
        <div class="tab-pane" v-show="activeTab === 'details'">
          <div class="nutri-row" v-if="nutritionCards.length">
            <div class="nutri-chip" v-for="card in nutritionCards" :key="card.key">
              <span class="nutri-chip__icon" :class="`tone-${card.tone}`">
                <component :is="card.icon" :size="18" stroke-width="2.1" />
              </span>
              <small>{{ card.label }}</small>
              <strong>{{ card.value }}</strong>
            </div>
          </div>

          <div class="tags-row" v-if="allergens.length">
            <span class="tag" v-for="a in allergens" :key="a">{{ a }}</span>
          </div>

          <p class="empty-tab" v-if="!nutritionCards.length && !allergens.length">
            اطلاعات تکمیلی برای این محصول ثبت نشده است.
          </p>
        </div>

        <!-- Tab: ingredients -->
        <div class="tab-pane" v-show="activeTab === 'ingredients'">
          <section v-if="hasIngredientCustomization">
            <IngredientQuantityEditor
              :ingredients="ingredients"
              :model-value="customization"
              :currency="currency"
              @update:model-value="setCustomization"
            />
          </section>
          <p class="empty-tab" v-else>برای این محصول ماده تشکیل‌دهنده‌ای قابل تنظیم تعریف نشده است.</p>
        </div>

        <div class="tab-pane" v-show="activeTab === 'builder' && isBuilderEnabled">
          <section class="builder-launch-card">
            <div class="builder-launch-copy">
              <span class="builder-kicker">محصول سفارشی</span>
              <h3>در حال آماده‌سازی سفارشی‌سازی…</h3>
              <p>
                برای این محصول ویزارد مرحله‌به‌مرحله به‌صورت خودکار باز می‌شود.
              </p>
            </div>
            <p v-if="builderLoading" class="empty-tab">در حال بارگذاری قالب سفارشی‌سازی…</p>
            <p v-else-if="builderError" class="error-msg">{{ builderError }}</p>
            <p v-else-if="!builderTemplate" class="empty-tab">برای این محصول هنوز قالب سفارشی‌سازی فعالی تعریف نشده است.</p>
          </section>
        </div>

        <!-- Tab: reviews -->
        <div class="tab-pane" v-show="activeTab === 'reviews'">
          <div class="reviews-header">
            <h3>نظرات مشتریان</h3>
            <span class="reviews-count" v-if="reviewCount > 0">{{ reviewCount }} نظر</span>
          </div>

          <div class="reviews-list" v-if="reviews.length">
            <div class="review-card" v-for="rv in reviews.slice(0, showAllReviews ? reviews.length : 3)" :key="rv.id">
              <div class="review-top">
                <div class="review-avatar">{{ rv.author.slice(0, 1) }}</div>
                <div class="review-meta">
                  <strong class="review-author">{{ rv.author || 'کاربر' }}</strong>
                  <div class="review-stars">
                    <span v-for="s in 5" :key="s" class="star sm" :class="{ filled: s <= rv.rating }">★</span>
                  </div>
                </div>
                <span class="review-date">{{ formatReviewDate(rv.date) }}</span>
              </div>
              <p class="review-comment" v-if="rv.comment">{{ rv.comment }}</p>
            </div>
            <button
              v-if="reviews.length > 3 && !showAllReviews"
              class="show-more-btn"
              type="button"
              @click="showAllReviews = true"
            >
              نمایش همه {{ reviews.length }} نظر
            </button>
          </div>

          <p class="no-reviews" v-else>هنوز نظری ثبت نشده. اولین نفر باشید!</p>

          <div class="add-review">
            <h4>ثبت نظر</h4>
            <div class="star-picker">
              <button
                v-for="s in 5"
                :key="s"
                type="button"
                class="star-btn"
                :class="{ filled: s <= newReview.rating }"
                @click="newReview.rating = s"
              >★</button>
            </div>
            <input
              class="review-input"
              v-model.trim="newReview.author"
              placeholder="نام شما (اختیاری)"
            />
            <textarea
              class="review-textarea"
              v-model.trim="newReview.comment"
              placeholder="نظر خود را بنویسید..."
              rows="3"
              maxlength="500"
            ></textarea>
            <div class="review-form-footer">
              <span class="char-counter" :class="{ near: newReview.comment.length > 450 }">{{ newReview.comment.length }}/۵۰۰</span>
              <button class="submit-review-btn" type="button" @click="submitReview" :disabled="reviewSubmitting">
                {{ reviewSubmitting ? 'در حال ثبت...' : 'ثبت نظر' }}
              </button>
            </div>
            <p class="review-error" v-if="reviewError">{{ reviewError }}</p>
            <p class="review-success" v-if="reviewSubmitted">✓ نظر شما ثبت شد. ممنون!</p>
          </div>
        </div>

        <!-- Common customization (always visible) -->
          <section class="detail-section" v-if="hasModifierCustomization">
            <div class="section-head">
              <h3>سایز، افزودنی و فرمول</h3>
            </div>
            <ModifierRecipeImpactSelector
              :groups="modifierGroups"
            :currency="currency"
            :model-value="customization.selected_modifiers"
            @update:model-value="setSelectedModifiers"
          />
          <p class="error-msg" v-if="selectionError">{{ selectionError }}</p>
        </section>

        <section class="detail-section">
          <LivePricingBreakdown :breakdown="linePreview.pricingBreakdown" :currency="currency" />
        </section>
      </div>

      <!-- ════════════════════════════════════════════════════════════════
           DESKTOP LAYOUT
           ════════════════════════════════════════════════════════════════ -->
      <div class="desktop-detail-layout desktop-only" v-if="item">
        <!-- Left: Image (sticky) -->
        <div class="desktop-image-col">
          <div class="desktop-main-image" @click="openLightbox" role="button" tabindex="0" aria-label="مشاهده تصویر در اندازه بزرگ" @keydown.enter="openLightbox">
            <img :src="galleryImages[galleryIndex]" :alt="item.title" />
            <div class="zoom-hint">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
            </div>
          </div>
          <div class="desktop-thumbnails" v-if="galleryImages.length > 0">
            <button
              v-for="(src, idx) in galleryImages"
              :key="idx"
              class="thumb-btn"
              :class="{ active: galleryIndex === idx }"
              @click="galleryIndex = idx"
            >
              <img :src="src" :alt="`${item.title} - ${idx + 1}`" />
            </button>
          </div>
        </div>

        <!-- Right: Info -->
        <div class="desktop-info-col">
          <div class="desktop-info-inner">
            <!-- Back link -->
            <a href="/menu" class="desktop-back-link" aria-label="بازگشت به منو">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
              بازگشت به منو
            </a>

            <!-- Top actions -->
            <div class="desktop-top-actions">
              <button class="desktop-action-btn" :class="{ loved: isWishlisted }" @click="toggleWishlist" aria-label="علاقه‌مندی">
                <span class="heart-icon">{{ isWishlisted ? '♥' : '♡' }}</span>
                <span class="action-label">{{ isWishlisted ? 'ذخیره شده' : 'علاقه‌مندی' }}</span>
              </button>
              <button class="desktop-action-btn" @click="shareProduct" aria-label="اشتراک‌گذاری">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
                <span class="action-label">اشتراک‌گذاری</span>
              </button>
            </div>

            <p class="item-category">{{ item.category_title || item.category || 'منو' }}</p>
            <h1 class="item-title">{{ item.title }}</h1>

            <!-- Rating -->
            <div class="rating-row" v-if="reviewCount > 0">
              <div class="stars-display">
                <span v-for="s in 5" :key="s" class="star" :class="{ filled: s <= Math.round(averageRating) }">★</span>
              </div>
              <span class="rating-num">{{ averageRating }}</span>
              <span class="rating-count">({{ reviewCount }} نظر)</span>
            </div>

            <!-- Price + prep time -->
            <div class="desktop-meta-row">
              <div class="desktop-price-row">
                <span class="desktop-price-label">قیمت:</span>
                <span class="desktop-price">{{ isComingSoon ? 'به‌زودی' : displayBasePriceText }}</span>
              </div>
              <div class="prep-badge" v-if="prepTimeText">
                <span class="prep-icon">⏱</span>
                <span class="prep-text">{{ prepTimeText }}</span>
              </div>
            </div>

            <!-- Description -->
            <p class="item-desc">{{ item.long_desc || item.short_desc || 'توضیح تکمیلی ثبت نشده است.' }}</p>

            <!-- Tabs -->
            <div class="detail-tabs desktop-tabs">
              <button
                class="detail-tab"
                :class="{ active: activeTab === 'details' }"
                @click="activeTab = 'details'"
                type="button"
              >اطلاعات کلی</button>
              <button
                class="detail-tab"
                :class="{ active: activeTab === 'ingredients' }"
                @click="activeTab = 'ingredients'"
                type="button"
              >{{ ingredientTabLabel }}</button>
              <button
                v-if="isBuilderEnabled"
                class="detail-tab"
                :class="{ active: activeTab === 'builder' }"
                @click="activeTab = 'builder'"
                type="button"
              >سفارشی‌سازی</button>
              <button
                class="detail-tab"
                :class="{ active: activeTab === 'reviews' }"
                @click="activeTab = 'reviews'"
                type="button"
              >
                نظرات
                <span class="tab-badge" v-if="reviewCount > 0">{{ reviewCount }}</span>
              </button>
            </div>

            <!-- Tab content -->
            <div class="tab-pane desktop-pane" v-show="activeTab === 'details'">
              <div class="nutri-row" v-if="nutritionCards.length">
                <div class="nutri-chip" v-for="card in nutritionCards" :key="card.key">
                  <span class="nutri-chip__icon" :class="`tone-${card.tone}`">
                    <component :is="card.icon" :size="18" stroke-width="2.1" />
                  </span>
                  <small>{{ card.label }}</small>
                  <strong>{{ card.value }}</strong>
                </div>
              </div>

              <div class="tags-row" v-if="allergens.length">
                <span class="tag" v-for="a in allergens" :key="a">{{ a }}</span>
              </div>

              <p class="empty-tab" v-if="!nutritionCards.length && !allergens.length">
                اطلاعات تکمیلی برای این محصول ثبت نشده است.
              </p>
            </div>

            <section class="tab-pane desktop-pane" v-show="activeTab === 'ingredients'">
              <IngredientQuantityEditor
                v-if="hasIngredientCustomization"
                :ingredients="ingredients"
                :model-value="customization"
                :currency="currency"
                @update:model-value="setCustomization"
              />
              <p class="empty-tab" v-else>برای این محصول ماده تشکیل‌دهنده‌ای قابل تنظیم تعریف نشده است.</p>
            </section>

            <section class="tab-pane desktop-pane" v-show="activeTab === 'builder' && isBuilderEnabled">
              <section class="builder-launch-card builder-launch-card--desktop">
                <div class="builder-launch-copy">
                  <span class="builder-kicker">محصول سفارشی</span>
                  <h3>در حال آماده‌سازی سفارشی‌سازی…</h3>
                  <p>
                    ویزارد کامل این محصول به‌صورت خودکار باز می‌شود تا سفارش را مرحله‌به‌مرحله بسازید.
                  </p>
                </div>
                <p v-if="builderLoading" class="empty-tab">در حال بارگذاری قالب سفارشی‌سازی…</p>
                <p v-else-if="builderError" class="error-msg">{{ builderError }}</p>
                <p v-else-if="!builderTemplate" class="empty-tab">برای این محصول هنوز قالب سفارشی‌سازی فعالی تعریف نشده است.</p>
              </section>
            </section>

            <section class="tab-pane desktop-pane" v-show="activeTab === 'reviews'">
              <div class="reviews-header">
                <h3>نظرات مشتریان</h3>
                <span class="reviews-count" v-if="reviewCount > 0">{{ reviewCount }} نظر</span>
              </div>

              <div class="reviews-list" v-if="reviews.length">
                <div class="review-card" v-for="rv in reviews.slice(0, showAllReviews ? reviews.length : 3)" :key="rv.id">
                  <div class="review-top">
                    <div class="review-avatar">{{ rv.author.slice(0, 1) }}</div>
                    <div class="review-meta">
                      <strong class="review-author">{{ rv.author || 'کاربر' }}</strong>
                      <div class="review-stars">
                        <span v-for="s in 5" :key="s" class="star sm" :class="{ filled: s <= rv.rating }">★</span>
                      </div>
                    </div>
                    <span class="review-date">{{ formatReviewDate(rv.date) }}</span>
                  </div>
                  <p class="review-comment" v-if="rv.comment">{{ rv.comment }}</p>
                </div>
                <button
                  v-if="reviews.length > 3 && !showAllReviews"
                  class="show-more-btn"
                  type="button"
                  @click="showAllReviews = true"
                >
                  نمایش همه {{ reviews.length }} نظر
                </button>
              </div>

              <p class="no-reviews" v-else>هنوز نظری ثبت نشده. اولین نفر باشید!</p>

              <div class="add-review">
                <h4>ثبت نظر</h4>
                <div class="star-picker">
                  <button
                    v-for="s in 5"
                    :key="s"
                    type="button"
                    class="star-btn"
                    :class="{ filled: s <= newReview.rating }"
                    @click="newReview.rating = s"
                  >★</button>
                </div>
                <input
                  class="review-input"
                  v-model.trim="newReview.author"
                  placeholder="نام شما (اختیاری)"
                />
                <textarea
                  class="review-textarea"
                  v-model.trim="newReview.comment"
                  placeholder="نظر خود را بنویسید..."
                  rows="3"
                  maxlength="500"
                ></textarea>
                <div class="review-form-footer">
                  <span class="char-counter" :class="{ near: newReview.comment.length > 450 }">{{ newReview.comment.length }}/۵۰۰</span>
                  <button class="submit-review-btn" type="button" @click="submitReview" :disabled="reviewSubmitting">
                    {{ reviewSubmitting ? 'در حال ثبت...' : 'ثبت نظر' }}
                  </button>
                </div>
                <p class="review-error" v-if="reviewError">{{ reviewError }}</p>
                <p class="review-success" v-if="reviewSubmitted">✓ نظر شما ثبت شد. ممنون!</p>
              </div>
            </section>

            <!-- Common customization (always visible) -->
            <section class="detail-section" v-if="hasModifierCustomization">
              <div class="section-head">
                <h3>سایز، افزودنی و فرمول</h3>
              </div>
              <ModifierRecipeImpactSelector
                :groups="modifierGroups"
                :currency="currency"
                :model-value="customization.selected_modifiers"
                @update:model-value="setSelectedModifiers"
              />
              <p class="error-msg" v-if="selectionError">{{ selectionError }}</p>
            </section>

            <section class="detail-section">
              <LivePricingBreakdown :breakdown="linePreview.pricingBreakdown" :currency="currency" />
            </section>

            <!-- Qty + Add to cart (inline) -->
            <div class="desktop-cart-row">
              <div class="qty-control" v-if="hasIngredientCustomization || hasModifierCustomization">
                <button class="qty-btn" type="button" @click="qty = Math.max(qty - 1, 1)">−</button>
                <span class="qty-num">{{ qty }}</span>
                <button class="qty-btn" type="button" @click="qty += 1">+</button>
              </div>
              <div class="desktop-price-display">
                <small>قیمت کل</small>
                <strong>{{ isComingSoon ? 'به‌زودی' : formatMoney(linePreview.lineTotal, currency) }}</strong>
              </div>
              <button class="add-to-cart-btn desktop-add-btn" type="button" :disabled="isComingSoon" @click="primaryAddAction">
                {{ isComingSoon ? 'به‌زودی' : isBuilderEnabled ? (item.restaurant_customize_button_label || 'شروع سفارشی‌سازی') : isEditing ? 'ذخیره تغییرات' : 'افزودن به سبد' }}
                <span class="cart-plus" v-if="!isComingSoon">+</span>
              </button>
            </div>

          </div>
        </div>
      </div>

      <!-- ─── Related Items ─── -->
      <section class="related-section" v-if="relatedItems.length">
        <h3 class="related-title">محصولات مرتبط</h3>
        <div class="related-scroll">
          <a
            v-for="ri in relatedItems"
            :key="ri.slug"
            :href="`/item/${ri.slug}`"
            class="related-card"
          >
            <div class="related-img-wrap">
              <img :src="ri.image || fallbackImage" :alt="ri.title" loading="lazy" />
            </div>
            <p class="related-name">{{ ri.title }}</p>
            <strong class="related-price">{{ formatMoney(ri.base_price, currency) }}</strong>
          </a>
        </div>
      </section>
    </div>

    <!-- ─── Mobile Sticky Add-to-Cart Bar (sits above the bottom nav) ─── -->
    <div class="sticky-bottom-bar mobile-only" v-if="item" dir="rtl">
      <div class="qty-control" v-if="hasIngredientCustomization || hasModifierCustomization">
        <button class="qty-btn" type="button" @click="qty = Math.max(qty - 1, 1)">−</button>
        <span class="qty-num">{{ qty }}</span>
        <button class="qty-btn" type="button" @click="qty += 1">+</button>
      </div>

      <div class="price-and-add">
        <div class="bottom-price">
          <small>قیمت کل</small>
          <strong>{{ isComingSoon ? 'به‌زودی' : formatMoney(linePreview.lineTotal, currency) }}</strong>
        </div>
        <button class="add-to-cart-btn" type="button" :disabled="isComingSoon" @click="primaryAddAction">
          {{ isComingSoon ? 'به‌زودی' : isBuilderEnabled ? (item.restaurant_customize_button_label || 'شروع سفارشی‌سازی') : isEditing ? 'ذخیره تغییرات' : 'افزودن به سبد' }}
          <span class="cart-plus" v-if="!isComingSoon">+</span>
        </button>
      </div>
    </div>

    <!-- Print card -->
    <section class="print-product-card">
      <header class="print-product-name">{{ item?.title || '-' }}</header>
      <main class="print-product-desc">{{ item?.long_desc || item?.short_desc || 'توضیحی ثبت نشده است.' }}</main>
      <footer class="print-product-price">{{ formatMoney(item?.base_price, currency) }}</footer>
    </section>

    <Teleport to="body">
      <ProductBuilderWizard
        v-if="builderOpen && builderTemplate && item"
        :product="{ ...item, item_name: item.title, item_code: item.name || item.item_code, image: resolveItemImage(item) }"
        :template="builderTemplate"
        :base-price="Number(item.base_price || 0)"
        :currency="currency"
        :loading-price="builderPriceLoading"
        :initial-selections="builderInitialSelections"
        :editing="isEditing"
        @close="builderOpen = false"
        @selection-change="handleBuilderSelectionChange"
        @add-to-cart="handleBuilderAddToCart"
      />
    </Teleport>

    <!-- ─── Image Lightbox ─── -->
    <Teleport to="body">
      <div class="lightbox-overlay" v-if="lightboxOpen" @click.self="closeLightbox" role="dialog" aria-modal="true" aria-label="نمایش تصویر در اندازه بزرگ">
        <button class="lightbox-close" @click="closeLightbox" aria-label="بستن">✕</button>
        <button class="lightbox-arrow lightbox-arrow--prev" @click="lightboxPrev" aria-label="تصویر قبلی">‹</button>
        <button class="lightbox-arrow lightbox-arrow--next" @click="lightboxNext" aria-label="تصویر بعدی">›</button>
        <div class="lightbox-image-wrap">
          <img :src="galleryImages[lightboxIndex]" :alt="item?.title" class="lightbox-img" />
        </div>
        <div class="lightbox-counter">{{ lightboxIndex + 1 }} / {{ galleryImages.length }}</div>
      </div>
    </Teleport>

    <!-- ─── Scroll to top ─── -->
    <button class="scroll-top-btn" :class="{ visible: showScrollTop }" @click="scrollToTop" aria-label="بازگشت به بالا">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 15l-6-6-6 6"/></svg>
    </button>

    <!-- ─── Share toast ─── -->
    <div class="share-toast" :class="{ visible: shareToastVisible }">لینک کپی شد</div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Teleport } from 'vue'
import { Flame, Dumbbell, Wheat, Droplets, Percent } from 'lucide-vue-next'
import IngredientQuantityEditor from '@/components/IngredientQuantityEditor.vue'
import ModifierRecipeImpactSelector from '@/components/ModifierRecipeImpactSelector.vue'
import LivePricingBreakdown from '@/components/LivePricingBreakdown.vue'
import ProductBuilderWizard from '@/components/ProductBuilderWizard.vue'
import OrderContextStrip from '@/components/OrderContextStrip.vue'
import { getItemDetail, getRelatedItems, getItemReviews as fetchItemReviews, submitReview as submitItemReview, getBuilderTemplate, computeBuilderPrice } from '@/utils/api'
import { formatMoney, normalizeMobile, parseQuery } from '@/utils/format'
import { createDefaultCustomization, estimateLine, sanitizeCustomization } from '@/utils/itemConfig'
import { getLineById, upsertLine } from '@/stores/cartStore'
import { getItemReviews as getLocalItemReviews, addItemReview, getAverageRating as getLocalAverageRating, getReviewCount as getLocalReviewCount } from '@/utils/reviewsStore'

const props = defineProps({
  boot: { type: Object, default: () => ({}) },
})

const fallbackImage = 'https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=1000&auto=format&fit=crop&q=60'

const loading = ref(false)
const error = ref('')
const item = ref(null)
const activeTab = ref('details')
const ingredients = ref([])
const modifierGroups = ref([])
const allergens = ref([])
const currency = ref(props.boot.currency || 'IRR')
const qty = ref(1)
const customization = ref({ ingredient_adjustments: [], selected_modifiers: [] })
const selectionError = ref('')
const builderLoading = ref(false)
const builderError = ref('')
const builderTemplate = ref(null)
const builderOpen = ref(false)
const builderPriceLoading = ref(false)
const builderPriceData = ref(null)
const builderAutoOpened = ref(false)

// ─── Lightbox ────────────────────────────────────────────────────────
const lightboxOpen = ref(false)
const lightboxIndex = ref(0)
function openLightbox() { lightboxIndex.value = galleryIndex.value; lightboxOpen.value = true }
function closeLightbox() { lightboxOpen.value = false }
function lightboxPrev() { lightboxIndex.value = (lightboxIndex.value - 1 + galleryImages.value.length) % galleryImages.value.length }
function lightboxNext() { lightboxIndex.value = (lightboxIndex.value + 1) % galleryImages.value.length }

// ─── Scroll to top ───────────────────────────────────────────────────
const showScrollTop = ref(false)
function handleScroll() { showScrollTop.value = window.scrollY > 400 }
function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }) }

// ─── Share ───────────────────────────────────────────────────────────
const shareToastVisible = ref(false)
async function shareProduct() {
  const url = window.location.href
  const title = item.value?.title || ''
  if (navigator.share) {
    try { await navigator.share({ title, url }) } catch (_) {}
  } else {
    try { await navigator.clipboard.writeText(url) } catch (_) {}
    shareToastVisible.value = true
    setTimeout(() => { shareToastVisible.value = false }, 2000)
  }
}

// ─── Related items ───────────────────────────────────────────────────
const relatedItems = ref([])
async function loadRelatedItems() {
  const slug = item.value?.slug || ''
  if (!slug) return
  try {
    const data = await getRelatedItems(slug, 6)
    relatedItems.value = Array.isArray(data) ? data : []
  } catch (_) { relatedItems.value = [] }
}

// ─── Review validation ───────────────────────────────────────────────
const reviewSubmitting = ref(false)
const reviewError = ref('')
const REVIEW_MAX_CHARS = 500
function validateReview() {
  if (!newReview.value.comment.trim()) { reviewError.value = 'لطفا نظر خود را بنویسید'; return false }
  if (newReview.value.comment.trim().length < 3) { reviewError.value = 'نظر باید حداقل ۳ کاراکتر باشد'; return false }
  if (newReview.value.comment.length > REVIEW_MAX_CHARS) { reviewError.value = `نظر نمی‌تواند بیشتر از ${REVIEW_MAX_CHARS} کاراکتر باشد`; return false }
  if (newReview.value.author.length > 50) { reviewError.value = 'نام نمی‌تواند بیشتر از ۵۰ کاراکتر باشد'; return false }
  reviewError.value = ''
  return true
}
const galleryIndex = ref(0)
const userUploadedImages = ref([])
const USER_IMAGES_KEY = 'restaurant_user_images_'

function loadUserImages(slug) {
  try {
    const stored = localStorage.getItem(USER_IMAGES_KEY + slug)
    userUploadedImages.value = stored ? JSON.parse(stored) : []
  } catch (_) { userUploadedImages.value = [] }
}

function saveUserImages(slug) {
  try {
    localStorage.setItem(USER_IMAGES_KEY + slug, JSON.stringify(userUploadedImages.value))
  } catch (_) {}
}

const galleryImages = computed(() => {
  const main = resolveItemImage(item.value)
  const extra = Array.isArray(item.value?.extra_images) ? item.value.extra_images : []
  const user = userUploadedImages.value || []
  const all = [main, ...extra, ...user].filter(Boolean)
  return all.length ? all : [fallbackImage]
})

const galleryOffset = computed(() => galleryIndex.value * -100)
function prevImage() { galleryIndex.value = (galleryIndex.value + 1) % galleryImages.value.length }
function nextImage() { galleryIndex.value = (galleryIndex.value - 1 + galleryImages.value.length) % galleryImages.value.length }

// Upload image
const fileInput = ref(null)
const uploadError = ref('')

function triggerUpload() {
  uploadError.value = ''
  fileInput.value?.click()
}

function handleFileChange(e) {
  const files = e.target?.files
  if (!files || !files.length) return
  const slug = item.value?.slug || ''
  if (!slug) return

  Array.from(files).forEach(file => {
    if (!file.type.startsWith('image/')) {
      uploadError.value = 'لطفا فقط فایل تصویری انتخاب کنید.'
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      uploadError.value = 'حجم فایل نباید بیشتر از 5 مگابایت باشد.'
      return
    }
    const reader = new FileReader()
    reader.onload = (ev) => {
      userUploadedImages.value = [...userUploadedImages.value, ev.target.result]
      saveUserImages(slug)
    }
    reader.readAsDataURL(file)
  })
  e.target.value = ''
}

function removeUserImage(idx) {
  const slug = item.value?.slug || ''
  if (!slug) return
  // idx is in galleryImages space; user images start after main + extra
  const main = resolveItemImage(item.value)
  const extra = Array.isArray(item.value?.extra_images) ? item.value.extra_images : []
  const userIdx = idx - (main ? 1 : 0) - extra.length
  if (userIdx >= 0 && userIdx < userUploadedImages.value.length) {
    userUploadedImages.value.splice(userIdx, 1)
    saveUserImages(slug)
    if (galleryIndex.value >= galleryImages.value.length) {
      galleryIndex.value = Math.max(0, galleryImages.value.length - 1)
    }
  }
}

function isUserImage(idx) {
  const main = resolveItemImage(item.value)
  const extra = Array.isArray(item.value?.extra_images) ? item.value.extra_images : []
  const userIdx = idx - (main ? 1 : 0) - extra.length
  return userIdx >= 0 && userIdx < userUploadedImages.value.length
}

// Touch swipe
let touchStartX = 0
function onTouchStart(e) { touchStartX = e.touches[0].clientX }
function onTouchEnd(e) {
  const dx = e.changedTouches[0].clientX - touchStartX
  if (Math.abs(dx) > 40) { dx > 0 ? nextImage() : prevImage() }
}

// Wishlist
const WISHLIST_KEY = 'restaurant_wishlist_v1'
function loadWishlist() {
  try { return JSON.parse(localStorage.getItem(WISHLIST_KEY) || '[]') } catch (_) { return [] }
}
const isWishlisted = ref(false)
function toggleWishlist() {
  const slug = item.value?.slug || ''
  if (!slug) return
  const list = loadWishlist()
  const idx = list.indexOf(slug)
  if (idx >= 0) { list.splice(idx, 1); isWishlisted.value = false }
  else { list.push(slug); isWishlisted.value = true }
  try { localStorage.setItem(WISHLIST_KEY, JSON.stringify(list)) } catch (_) {}
}

// Reviews
const reviews = ref([])
const showAllReviews = ref(false)
const averageRating = ref(0)
const reviewCount = ref(0)
const newReview = ref({ author: '', rating: 5, comment: '' })
const reviewSubmitted = ref(false)

function readCustomerAuth() {
  try {
    const auth = JSON.parse(localStorage.getItem('restaurant-customer-auth-v1') || '{}')
    return {
      mobile: auth.mobile || localStorage.getItem('customer_phone') || '',
      name: auth.customer_name || localStorage.getItem('customer_name') || '',
    }
  } catch {
    return { mobile: '', name: '' }
  }
}

function normalizeReviewRows(rows = []) {
  return (Array.isArray(rows) ? rows : []).map((row) => ({
    id: row.id || row.name || `review-${row.created_at || Date.now()}`,
    author: row.author || row.customer_name || 'مشتری',
    rating: Number(row.rating || 0),
    comment: row.comment || '',
    date: row.date || row.created_at || row.creation || '',
  }))
}

async function refreshReviews() {
  const slug = item.value?.slug || ''
  if (!slug) return
  try {
    const payload = await fetchItemReviews({ item_slug: slug, page_size: 50 })
    reviews.value = normalizeReviewRows(payload?.reviews || [])
    averageRating.value = Number(payload?.average_rating || 0)
    reviewCount.value = Number(payload?.count || reviews.value.length || 0)
  } catch (_) {
    reviews.value = getLocalItemReviews(slug)
    averageRating.value = getLocalAverageRating(slug)
    reviewCount.value = getLocalReviewCount(slug)
  }
}

async function submitReview() {
  if (!validateReview()) return
  const slug = item.value?.slug || ''
  if (!slug) return
  reviewSubmitting.value = true
  try {
    const auth = readCustomerAuth()
    const customerName = newReview.value.author.trim() || auth.name || 'مشتری'
    const mobile = normalizeMobile(auth.mobile || localStorage.getItem('customer_phone') || '')
    if (!mobile) {
      reviewError.value = 'برای ثبت نظر، ابتدا با شماره موبایل وارد شوید.'
      window.setTimeout(() => { window.location.href = `/customer/login?redirect=${encodeURIComponent(window.location.pathname)}` }, 900)
      return
    }
    await submitItemReview({
      customer_name: customerName,
      mobile,
      item_slug: slug,
      rating: newReview.value.rating,
      comment: newReview.value.comment,
    })
    await refreshReviews()
    newReview.value = { author: '', rating: 5, comment: '' }
    reviewSubmitted.value = true
    setTimeout(() => { reviewSubmitted.value = false }, 3000)
  } catch (err) {
    try {
      addItemReview(slug, { ...newReview.value })
      await refreshReviews()
      newReview.value = { author: '', rating: 5, comment: '' }
      reviewSubmitted.value = true
      setTimeout(() => { reviewSubmitted.value = false }, 3000)
    } catch (_) {
      reviewError.value = err?.message || 'ثبت نظر ناموفق بود. لطفا دوباره تلاش کنید.'
    }
  } finally {
    reviewSubmitting.value = false
  }
}

function formatReviewDate(dateStr = '') {
  try {
    const d = new Date(dateStr)
    if (isNaN(d)) return ''
    return d.toLocaleDateString('fa-IR', { year: 'numeric', month: 'long', day: 'numeric' })
  } catch (_) { return '' }
}

// ─── existing logic ───────────────────────────────────────────────
const query = parseQuery()
const editLineId = ref((props.boot.edit_line || query.edit || '').trim())
const isEditing = computed(() => Boolean(editLineId.value))
const editingLine = computed(() => (editLineId.value ? getLineById(editLineId.value) : null))
const builderInitialSelections = computed(() => {
  const customizationPayload = editingLine.value?.customization || {}
  const nested = customizationPayload.builder_selection || {}
  const rows = Array.isArray(nested.selections)
    ? nested.selections
    : Array.isArray(customizationPayload.builder_portion_rows)
      ? customizationPayload.builder_portion_rows
      : []
  return rows.map((row) => ({
    step_key: row.step_key,
    option_key: row.option_key,
    qty: Number(row.qty ?? row.portion_count ?? 0),
  })).filter((row) => row.step_key && row.option_key && row.qty > 0)
})
const isComingSoon = computed(() => Number(item.value?.coming_soon ?? item.value?.restaurant_coming_soon ?? 0) === 1)
const activeBranch = ref(
  String(props.boot.active_branch || props.boot?.table_context?.table?.branch || query.branch || '').trim(),
)

const linePreview = computed(() =>
  estimateLine({
    basePrice: Number(item.value?.base_price || 0),
    qty: qty.value,
    ingredients: ingredients.value,
    modifierGroups: modifierGroups.value,
    customization: customization.value,
  }),
)

const isBuilderEnabled = computed(() => {
  return Boolean(
    item.value &&
      Number(item.value.restaurant_is_customizable || 0) === 1 &&
      Number(item.value.restaurant_builder_active || 0) === 1,
  )
})

const builderSummary = computed(() => {
  const steps = builderTemplate.value?.steps || []
  const count = steps.reduce((sum, step) => sum + ((step.options || []).length), 0)
  return {
    steps: steps.length,
    options: count,
  }
})

const builderDisplayPrice = computed(() => {
  return Number(builderPriceData.value?.final_price || item.value?.base_price || 0)
})
const displayBasePriceText = computed(() => {
  const basePrice = formatMoney(item.value?.base_price || 0, currency.value)
  return isBuilderEnabled.value ? `از ${basePrice}` : basePrice
})

const hasIngredientCustomization = computed(() => Array.isArray(ingredients.value) && ingredients.value.length > 0)
const hasModifierCustomization = computed(() => Array.isArray(modifierGroups.value) && modifierGroups.value.length > 0)
const ingredientTabLabel = computed(() =>
  (ingredients.value || []).some((row) => Number(row?.is_replaceable || 0) === 1)
    ? 'مواد و جایگزین‌ها'
    : 'مواد تشکیل‌دهنده',
)

const nutritionKcal = computed(() => {
  const value = Number(item.value?.nutrition?.kcal ?? item.value?.nutrition_kcal ?? 0)
  return Number.isFinite(value) && value > 0 ? Math.round(value) : '--'
})

const nutritionProteinPercent = computed(() => {
  const value = Number(item.value?.nutrition?.protein_percent ?? item.value?.nutrition_protein_percent ?? 0)
  return Number.isFinite(value) && value > 0 ? Math.round(value) : '--'
})

const prepTimeText = computed(() => {
  const mins = Number(item.value?.prep_time_mins || 0)
  return Number.isFinite(mins) && mins > 0 ? `${mins} دقیقه` : ''
})

const macroCards = computed(() => {
  const nutrition = item.value?.nutrition || {}
  return [
    { key: 'protein_g', label: 'پروتئین', suffix: 'g' },
    { key: 'carb_g', label: 'کربوهیدرات', suffix: 'g' },
    { key: 'sugar_g', label: 'قند', suffix: 'g' },
    { key: 'fat_g', label: 'چربی', suffix: 'g' },
  ]
    .map((macro) => {
      const value = Number(nutrition[macro.key] ?? item.value?.[`nutrition_${macro.key}`] ?? 0)
      if (!Number.isFinite(value) || value <= 0) return null
      return { key: macro.key, label: macro.label, value: `${Math.round(value)} ${macro.suffix}` }
    })
    .filter(Boolean)
})

const nutritionCards = computed(() => {
  const cards = []
  if (nutritionKcal.value !== '--') {
    cards.push({
      key: 'kcal',
      label: 'کالری',
      value: `${nutritionKcal.value} kcal`,
      icon: Flame,
      tone: 'warm',
    })
  }
  if (nutritionProteinPercent.value !== '--') {
    cards.push({
      key: 'protein_percent',
      label: 'درصد پروتئین',
      value: `${nutritionProteinPercent.value}%`,
      icon: Percent,
      tone: 'cool',
    })
  }
  const iconByKey = {
    protein_g: Dumbbell,
    carb_g: Wheat,
    sugar_g: Percent,
    fat_g: Droplets,
  }
  const toneByKey = {
    protein_g: 'cool',
    carb_g: 'soft',
    sugar_g: 'soft',
    fat_g: 'warm',
  }
  for (const macro of macroCards.value) {
    cards.push({
      ...macro,
      icon: iconByKey[macro.key] || Dumbbell,
      tone: toneByKey[macro.key] || 'soft',
    })
  }
  return cards
})

function resolveSlug() {
  const fromBoot = String(props.boot.item_slug || '').trim()
  if (fromBoot) return fromBoot
  const path = window.location.pathname.replace(/^\/|\/+$/g, '')
  const parts = path.split('/')
  if (parts.length >= 3 && parts[parts.length - 2] === 'item') return parts[parts.length - 1]
  return ''
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function normalizeModifierGroups(rawGroups = []) {
  return (rawGroups || []).map((group) => {
    const groupName = String(group?.group_name || group?.name || group?.title || '').trim()
    if (!groupName) return null
    const options = (group.options || []).map((option) => {
      const optionName = String(option?.name || option?.option_name || option?.option_key || '').trim()
      if (!optionName) return null
      const baseQty = Math.max(toNumber(option.base_qty ?? option.option_qty, 1), 0.0001)
      const minQty = Math.max(toNumber(option.min_qty, 0), 0)
      const maxQty = Math.max(toNumber(option.max_qty, Math.max(baseQty, baseQty * 4)), minQty, baseQty)
      const qtyStep = Math.max(toNumber(option.qty_step, baseQty), 0.0001)
      return {
        ...option,
        name: optionName,
        label: String(option?.label || option?.option_name || optionName).trim() || optionName,
        min_qty: minQty,
        max_qty: maxQty,
        qty_step: qtyStep,
        option_qty: baseQty,
        base_qty: baseQty,
        stock_uom: String(option?.stock_uom || '').trim(),
        option_uom: String(option?.option_uom || option?.stock_uom || '').trim(),
        unit_rate: toNumber(option.unit_rate, 0),
        base_price: toNumber(option.base_price ?? option.price_delta, 0),
        conversion_factor: Math.max(toNumber(option.conversion_factor, 1), 0),
        price_delta: toNumber(option.price_delta, 0),
        is_selectable: Number(option?.is_selectable ?? 1),
        disabled: Number(option?.disabled ?? 0),
        price_status: String(option?.price_status || 'ok').trim() || 'ok',
        unavailable_reason: String(option?.unavailable_reason || '').trim(),
      }
    }).filter(Boolean)
    return { ...group, group_name: groupName, title: String(group.title || groupName).trim(), selection_mode: String(group.selection_mode || 'single').trim() || 'single', min_select: Math.max(toNumber(group.min_select, 0), 0), max_select: Math.max(toNumber(group.max_select, 1), 1), is_variant_attribute_selector: Number(group.is_variant_attribute_selector || 0), options }
  }).filter(Boolean)
}

function normalizeSelectedModifiers(selectedRows = [], groups = []) {
  const groupMap = new Map(groups.map((group) => [group.group_name, group]))
  const deduped = new Map()
  for (const row of selectedRows || []) {
    const groupName = String(row?.group || row?.group_name || '').trim()
    const optionName = String(row?.option || row?.option_name || '').trim()
    if (!groupName || !optionName) continue
    const group = groupMap.get(groupName)
    if (!group) continue
    const option = (group.options || []).find((entry) => entry.name === optionName)
    if (!option || Number(option.is_selectable ?? 1) !== 1) continue
    const baseQty = Math.max(toNumber(option.base_qty ?? option.option_qty, 1), 0.0001)
    const minQty = Math.max(toNumber(option.min_qty, 0), 0)
    const maxQty = Math.max(toNumber(option.max_qty, Math.max(baseQty, baseQty * 4)), minQty, baseQty)
    const step = Math.max(toNumber(option.qty_step, baseQty), 0.0001)
    let qty2 = toNumber(row.qty, baseQty)
    if (qty2 <= 0) qty2 = baseQty
    const snapped = minQty + Math.round((qty2 - minQty) / step) * step
    const clamped = Math.min(Math.max(snapped, minQty), maxQty)
    deduped.set(`${groupName}::${optionName}`, { group: groupName, option: optionName, qty: Number(clamped.toFixed(4)) })
  }
  return Array.from(deduped.values())
}

function setCustomization(next) {
  const sanitized = sanitizeCustomization({ ...customization.value, ...next, selected_modifiers: customization.value.selected_modifiers }, ingredients.value)
  customization.value = { ...sanitized, selected_modifiers: normalizeSelectedModifiers(sanitized.selected_modifiers, modifierGroups.value) }
}

function withVariantContext(customizationPayload = {}) {
  const fixed = item.value?.variant_fixed_attributes
  if (fixed && typeof fixed === 'object' && Object.keys(fixed).length) return { ...customizationPayload, variant_fixed_attributes: { ...fixed } }
  return customizationPayload
}

function setSelectedModifiers(next) {
  const sanitized = sanitizeCustomization({ ...customization.value, selected_modifiers: next, selected_alternatives: customization.value.selected_alternatives }, ingredients.value)
  customization.value = { ...withVariantContext(sanitized), selected_modifiers: normalizeSelectedModifiers(sanitized.selected_modifiers, modifierGroups.value) }
}

function validateSelections() {
  const selectedRows = normalizeSelectedModifiers(customization.value.selected_modifiers || [], modifierGroups.value)
  customization.value = { ...customization.value, selected_modifiers: selectedRows }
  for (const group of modifierGroups.value) {
    const count = selectedRows.filter((row) => row.group === group.group_name).length
    if (count < Number(group.min_select || 0)) { selectionError.value = `برای گروه "${group.title}" حداقل ${group.min_select} انتخاب لازم است.`; return false }
    if (count > Number(group.max_select || 1)) { selectionError.value = `برای گروه "${group.title}" حداکثر ${group.max_select} انتخاب مجاز است.`; return false }
  }
  selectionError.value = ''
  return true
}

function hydrateForEdit(currentSlug) {
  if (!editLineId.value) return
  const line = getLineById(editLineId.value)
  if (!line || line.item_slug !== currentSlug) { editLineId.value = ''; return }
  qty.value = Math.max(Number(line.qty || 1), 1)
  const sanitized = sanitizeCustomization(line.customization || {}, ingredients.value)
  customization.value = { ...withVariantContext(sanitized), selected_modifiers: normalizeSelectedModifiers(sanitized.selected_modifiers, modifierGroups.value) }
}

async function loadBuilderTemplate() {
  if (!item.value?.name && !item.value?.item_code) {
    builderTemplate.value = null
    return
  }
  if (!isBuilderEnabled.value) {
    builderTemplate.value = null
    builderError.value = ''
    return
  }

  builderLoading.value = true
  builderError.value = ''
  builderPriceData.value = null
  try {
    const response = await getBuilderTemplate(item.value.name || item.value.item_code)
    builderTemplate.value = response?.data?.template || response?.template || response || null
  } catch (err) {
    builderTemplate.value = null
    builderError.value = err?.message || 'دریافت قالب سفارشی‌سازی ناموفق بود.'
  } finally {
    builderLoading.value = false
  }
}

async function handleBuilderSelectionChange(selections) {
  if (!item.value?.name && !item.value?.item_code) return
  if (!Array.isArray(selections) || !selections.length) {
    builderPriceData.value = null
    return
  }

  builderPriceLoading.value = true
  try {
    const response = await computeBuilderPrice(item.value.name || item.value.item_code, selections)
    builderPriceData.value = response?.data || response || null
  } catch (_) {
    builderPriceData.value = null
  } finally {
    builderPriceLoading.value = false
  }
}

async function primaryAddAction() {
  if (isBuilderEnabled.value) {
    if (!builderTemplate.value && !builderLoading.value) {
      await loadBuilderTemplate()
    }
    if (builderTemplate.value) {
      builderOpen.value = true
      return
    }
    activeTab.value = 'builder'
    return
  }
  addToCart()
}

function handleBuilderAddToCart(payload) {
  if (!item.value) return

  const finalPrice = Number(
    payload?.builder_pricing_breakdown?.final_price ??
    builderPriceData.value?.final_price ??
    payload?.final_price ??
    item.value.base_price ??
    0,
  )
  const optionsTotal = Number(
    payload?.builder_pricing_breakdown?.options_total ??
    payload?.options_total ??
    builderPriceData.value?.options_total ??
    0,
  )
  const builderSelections = Array.isArray(payload?.selections) ? payload.selections : []
  const builderSummaryText = String(
    payload?.builder_summary ||
    builderSelections
      .map((row) => {
        const count = Number(row?.portion_count ?? row?.qty ?? 0)
        return `${row.option_label}${count > 1 ? ` × ${count}` : ''}`
      })
      .join('، '),
  ).trim()
  const builderPricingBreakdown = payload?.builder_pricing_breakdown || {
    base_price: Number(item.value.base_price || 0),
    options_total: optionsTotal,
    final_price: finalPrice,
    builder_portion_rows: builderSelections,
  }

  upsertLine({
    id: editLineId.value || undefined,
    item_slug: item.value.slug,
    item_title: item.value.title,
    item_image: resolveItemImage(item.value),
    base_price: Number(item.value.base_price || 0),
    qty: 1,
    unit_price_preview: finalPrice,
    line_total_preview: finalPrice,
    customization: {
      ingredient_adjustments: [],
      selected_modifiers: [],
      builder_selection: {
        template: payload?.template || builderTemplate.value?.name || '',
        selections: builderSelections,
        options_total: optionsTotal,
        final_price: finalPrice,
        summary: builderSummaryText,
      },
      builder_summary: builderSummaryText,
      builder_pricing_breakdown: builderPricingBreakdown,
      builder_portion_rows: Array.isArray(payload?.builder_portion_rows) ? payload.builder_portion_rows : builderSelections,
      builder_template: payload?.template || builderTemplate.value?.name || '',
    },
    ingredient_catalog: [],
    modifier_groups_catalog: [],
  })

  builderOpen.value = false
  window.location.href = '/cart'
}

async function loadItem() {
  const slug = resolveSlug()
  if (!slug) { error.value = 'آدرس محصول معتبر نیست.'; return }
  loading.value = true
  error.value = ''
  try {
    const data = await getItemDetail(slug, activeBranch.value)
    item.value = data.item
    ingredients.value = data.ingredients || []
    modifierGroups.value = normalizeModifierGroups(data.modifier_groups || [])
    allergens.value = data.allergens || []
    currency.value = 'TOMAN'
    const defaults = createDefaultCustomization(ingredients.value, modifierGroups.value)
    const defaultsWithVariant = withVariantContext(defaults)
    customization.value = { ...defaultsWithVariant, selected_modifiers: normalizeSelectedModifiers(defaultsWithVariant.selected_modifiers, modifierGroups.value) }
    hydrateForEdit(slug)
    isWishlisted.value = loadWishlist().includes(slug)
    loadUserImages(slug)
    await refreshReviews()
    loadRelatedItems()
    await loadBuilderTemplate()
    if (isBuilderEnabled.value && builderTemplate.value && !builderAutoOpened.value) {
      activeTab.value = 'builder'
      builderAutoOpened.value = true
      builderOpen.value = !editLineId.value || builderInitialSelections.value.length > 0
    }
  } catch (err) {
    error.value = err.message || 'دریافت جزئیات آیتم ناموفق بود.'
  } finally {
    loading.value = false
  }
}

function addToCart() {
  if (!item.value || isComingSoon.value || !validateSelections()) return
  const cleanCustomization = sanitizeCustomization(customization.value, ingredients.value)
  upsertLine({
    id: editLineId.value || undefined,
    item_slug: item.value.slug,
    item_title: item.value.title,
    item_image: resolveItemImage(item.value),
    base_price: Number(item.value.base_price || 0),
    qty: linePreview.value.qty,
    unit_price_preview: linePreview.value.unitPrice,
    line_total_preview: linePreview.value.lineTotal,
    customization: cleanCustomization,
    ingredient_catalog: ingredients.value,
    modifier_groups_catalog: modifierGroups.value,
  })
  window.location.href = '/cart'
}

function resolveItemImage(source = null) {
  const extraImages = Array.isArray(source?.extra_images) ? source.extra_images : []
  const directExtraImage = source?.extra_images?.[0]
  const firstExtra = extraImages.find((entry) => {
    if (typeof entry === 'string') return String(entry).trim()
    return String(entry?.image || entry?.url || entry?.file_url || '').trim()
  })
  const normalizedDirectExtra = typeof directExtraImage === 'string'
    ? String(directExtraImage).trim()
    : String(directExtraImage?.image || directExtraImage?.url || directExtraImage?.file_url || '').trim()
  const normalizedExtra = typeof firstExtra === 'string'
    ? String(firstExtra).trim()
    : String(firstExtra?.image || firstExtra?.url || firstExtra?.file_url || '').trim()
  const img = String(
    source?.image ||
    source?.item_image ||
    source?.website_image ||
    source?.hero_image ||
    source?.media?.main_image ||
    source?.thumbnail ||
    normalizedDirectExtra ||
    normalizedExtra ||
    '',
  ).trim()
  return img || fallbackImage
}

function handlePrintShortcut(event) {
  const key = String(event?.key || '').toLowerCase()
  if ((event?.ctrlKey || event?.metaKey) && key === 'p') { event.preventDefault(); window.print() }
}

function handleLightboxKeydown(e) {
  if (!lightboxOpen.value) return
  if (e.key === 'Escape') closeLightbox()
  if (e.key === 'ArrowLeft') lightboxNext()
  if (e.key === 'ArrowRight') lightboxPrev()
}

onMounted(() => {
  loadItem()
  window.addEventListener('keydown', handlePrintShortcut)
  window.addEventListener('keydown', handleLightboxKeydown)
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('keydown', handlePrintShortcut)
  window.removeEventListener('keydown', handleLightboxKeydown)
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.detail-page {
  min-height: 100svh;
  background: var(--theme-background, #f6f1ea);
  direction: rtl;
  padding-bottom: calc(env(safe-area-inset-bottom) + 6.75rem);
}

.state-shell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60svh;
}

.state-content { text-align: center; padding: 2rem; }

/* ─── Responsive visibility ─── */
.mobile-only { display: block; }
.desktop-only { display: none; }

@media (min-width: 768px) {
  .mobile-only { display: none !important; }
  .desktop-only { display: block; }
}

/* ════════════════════════════════════════════════════════════════
   GALLERY (Mobile)
   ════════════════════════════════════════════════════════════════ */
.hero-area {
  position: relative;
  width: 100%;
  overflow: hidden;
  background:
    radial-gradient(circle at top, rgb(255 255 255 / 0.92), transparent 42%),
    linear-gradient(180deg, rgb(var(--palette-eggshell-rgb) / 0.98), rgb(var(--palette-eggshell-rgb) / 0.86));
}

.gallery-track {
  display: flex;
  transition: transform 0.35s cubic-bezier(.4,0,.2,1);
  height: min(390px, 82vw);
}

.gallery-slide {
  position: relative;
  min-width: 100%;
  height: 100%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.1rem 1rem 0.9rem;
  box-sizing: border-box;
}

.gallery-img {
  width: auto;
  max-width: min(100%, 27rem);
  max-height: 100%;
  object-fit: contain;
  object-position: center center;
  display: block;
  flex-shrink: 0;
}

@media (max-width: 767px) {
  .gallery-img { object-fit: contain; }
}

@media (max-width: 480px) {
  .gallery-track { height: min(360px, 84vw); }
  .gallery-slide { padding-inline: 0.8rem; }
  .gallery-img { max-width: min(100%, 22rem); }
}

.gallery-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(8px);
  border: none;
  cursor: pointer;
  font-size: 1.3rem;
  color: var(--text-primary, #3f2a1d);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 2;
}
.gallery-arrow--prev { left: 0.75rem; }
.gallery-arrow--next { right: 0.75rem; }

.gallery-dots {
  position: absolute;
  bottom: 0.75rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 0.35rem;
  z-index: 2;
}

.gallery-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.55);
  cursor: pointer;
  transition: background 0.2s, width 0.2s;
}
.gallery-dot.active { background: #fff; width: 20px; border-radius: 4px; }

/* Overlay nav buttons on the hero image */
.hero-nav {
  position: absolute;
  top: calc(env(safe-area-inset-top) + 0.85rem);
  left: 0.85rem;
  right: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 3;
  gap: 0.5rem;
}

.hero-nav-actions {
  display: flex;
  gap: 0.5rem;
}

.nav-circle {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(8px);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary, #3f2a1d);
  font-size: 1.2rem;
  cursor: pointer;
  text-decoration: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: background 0.2s, transform 0.2s;
}
.nav-circle:hover { background: rgba(255,255,255,0.95); }
.back-btn { font-size: 1.5rem; font-weight: 700; }

.wishlist-circle.loved {
  color: #e74c3c;
  background: rgba(255,255,255,0.95);
}

/* ════════════════════════════════════════════════════════════════
   CONTENT CARD (Mobile)
   ════════════════════════════════════════════════════════════════ */
.detail-wrap {
  max-width: 640px;
  margin: 0 auto;
}

.content-card {
  background: var(--glass-bg, #fdf8f1);
  border-radius: 30px 30px 0 0;
  margin-top: -26px;
  position: relative;
  padding: 1.5rem 1.2rem 1.5rem;
  display: grid;
  gap: 1rem;
  box-shadow: 0 -10px 36px rgba(0,0,0,0.07);
  z-index: 2;
}

.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}
.title-block { flex: 1; min-width: 0; }
.item-category {
  margin: 0 0 0.3rem;
  font-size: 0.78rem;
  color: var(--accent-gold, #c98d42);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.item-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-primary, #3f2a1d);
  line-height: 1.3;
}

.prep-badge {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  background: var(--accent-green40, rgba(111,74,49,0.1));
  border-radius: 999px;
  padding: 0.42rem 0.78rem;
  margin-top: 0.2rem;
}
.prep-icon { font-size: 0.9rem; }
.prep-text { font-size: 0.8rem; color: var(--text-secondary, #654a38); font-weight: 600; white-space: nowrap; }

/* Rating row */
.rating-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.stars-display { display: flex; gap: 0.1rem; }
.star { color: #ddd; font-size: 1rem; }
.star.filled { color: #f5a623; }
.star.sm { font-size: 0.75rem; }
.rating-num { font-size: 0.9rem; font-weight: 700; color: var(--text-primary, #3f2a1d); }
.rating-count { font-size: 0.78rem; color: var(--text-muted, #846b58); }

/* Price */
.price-block {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}
.base-price {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--accent-green, #6f4a31);
  font-variant-numeric: tabular-nums;
}

.item-desc {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-muted, #846b58);
  line-height: 1.7;
}

/* ════════════════════════════════════════════════════════════════
   TABS
   ════════════════════════════════════════════════════════════════ */
.detail-tabs {
  display: flex;
  gap: 0.4rem;
  padding: 0.3rem;
  background: var(--theme-surface-alt, #f1e7db);
  border-radius: 16px;
  position: sticky;
  top: 0.5rem;
  z-index: 8;
}

.detail-tab {
  flex: 1;
  padding: 0.6rem 0.4rem;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--text-muted, #846b58);
  font-family: inherit;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  white-space: nowrap;
}

.detail-tab.active {
  background: var(--accent-green, #6f4a31);
  color: #fff;
  box-shadow: 0 4px 12px rgb(var(--palette-deep-sapphire-rgb) / 0.25);
}

.detail-tab:not(.active):hover {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  color: var(--text-primary, #3f2a1d);
}

.tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  border-radius: 999px;
  background: var(--accent-gold, #c98d42);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0 0.35rem;
}

.detail-tab.active .tab-badge {
  background: rgba(255,255,255,0.3);
}

/* Tab panes */
.tab-pane {
  display: grid;
  gap: 0.9rem;
  min-height: 120px;
}

.empty-tab {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted, #846b58);
  text-align: center;
  padding: 1.5rem 0.5rem;
}

/* Tags / allergens */
.tags-row { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.tag {
  background: var(--accent-gold20, rgba(201,141,66,0.14));
  color: var(--text-secondary, #654a38);
  border-radius: 999px;
  padding: 0.28rem 0.7rem;
  font-size: 0.76rem;
  font-weight: 600;
}

/* Nutrition chips */
.nutri-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.nutri-chip {
  flex: 1;
  min-width: 108px;
  border-radius: 18px;
  padding: 0.72rem 0.78rem;
  background: linear-gradient(180deg, rgb(var(--palette-eggshell-rgb) / 0.98), rgb(var(--palette-eggshell-rgb) / 0.9));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  box-shadow: 0 10px 22px rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  display: flex;
  flex-direction: column;
  gap: 0.22rem;
  text-align: center;
  align-items: center;
}
.nutri-chip__icon {
  width: 2.15rem;
  height: 2.15rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.1rem;
  background: rgb(var(--palette-mint-rgb, 126 211 165) / 0.16);
  color: var(--accent-green, #6f4a31);
}
.nutri-chip small {
  font-size: 0.7rem;
  color: var(--text-muted, #846b58);
  font-weight: 700;
}
.nutri-chip strong {
  font-size: 0.9rem;
  color: var(--text-primary, #3f2a1d);
  font-variant-numeric: tabular-nums;
  line-height: 1.35;
}

/* Sections (common customization) */
.detail-section {
  border-top: 1px solid var(--glass-border, #e5ddd4);
  padding-top: 0.9rem;
  display: grid;
  gap: 0.65rem;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.section-head h3 { margin: 0; font-size: 1rem; color: var(--text-primary, #3f2a1d); }

.error-msg { color: #c0392b; font-size: 0.83rem; margin: 0; }
.muted { color: var(--text-muted, #846b58); font-size: 0.82rem; }

.builder-launch-card {
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border-radius: 22px;
  background:
    radial-gradient(circle at top right, rgb(var(--palette-gold-rgb) / 0.14), transparent 38%),
    linear-gradient(180deg, rgb(var(--palette-eggshell-rgb) / 0.96), rgb(var(--palette-eggshell-rgb) / 0.88));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  box-shadow: 0 18px 42px rgb(var(--palette-deep-sapphire-rgb) / 0.08);
}

.builder-launch-card--desktop {
  padding: 1.25rem;
}

.builder-launch-copy {
  display: grid;
  gap: 0.45rem;
}

.builder-kicker {
  display: inline-flex;
  width: fit-content;
  padding: 0.32rem 0.72rem;
  border-radius: 999px;
  background: rgb(var(--palette-gold-rgb) / 0.14);
  color: var(--accent-gold, #c98d42);
  font-size: 0.75rem;
  font-weight: 800;
}

.builder-launch-copy h3 {
  margin: 0;
  font-size: 1.05rem;
  color: var(--text-primary, #3f2a1d);
}

.builder-launch-copy p {
  margin: 0;
  color: var(--text-secondary, #654a38);
  line-height: 1.8;
  font-size: 0.88rem;
}

.builder-launch-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.builder-stat {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 0.45rem 0.8rem;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  color: var(--text-primary, #3f2a1d);
  font-size: 0.8rem;
  font-weight: 700;
}

.builder-start-btn {
  min-height: 48px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--accent-green, #6f4a31), rgb(var(--palette-gold-rgb) / 0.92));
  color: #fff;
  font-family: inherit;
  font-size: 0.92rem;
  font-weight: 800;
  cursor: pointer;
  transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
  box-shadow: 0 14px 28px rgb(var(--palette-deep-sapphire-rgb) / 0.16);
}

.builder-start-btn:hover {
  transform: translateY(-1px);
}

.builder-start-btn:active {
  transform: scale(0.985);
}

/* ════════════════════════════════════════════════════════════════
   REVIEWS
   ════════════════════════════════════════════════════════════════ */
.reviews-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.reviews-header h3 { margin: 0; font-size: 1rem; color: var(--text-primary, #3f2a1d); }
.reviews-count {
  font-size: 0.75rem;
  background: var(--accent-green40, rgba(111,74,49,0.12));
  color: var(--text-secondary, #654a38);
  border-radius: 999px;
  padding: 0.18rem 0.6rem;
  font-weight: 600;
}

.reviews-list { display: grid; gap: 0.65rem; }

.review-card {
  background: var(--theme-surface-alt, #f1e7db);
  border-radius: 16px;
  padding: 0.9rem;
  display: grid;
  gap: 0.5rem;
}
.review-top {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.review-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  font-weight: 700;
  flex-shrink: 0;
}
.review-meta { flex: 1; display: grid; gap: 0.1rem; min-width: 0; }
.review-author { font-size: 0.85rem; color: var(--text-primary, #3f2a1d); }
.review-stars { display: flex; gap: 0.05rem; }
.review-date { font-size: 0.72rem; color: var(--text-muted, #846b58); white-space: nowrap; }
.review-comment { margin: 0; font-size: 0.84rem; color: var(--text-secondary, #654a38); line-height: 1.55; }

.show-more-btn {
  background: none;
  border: 1px solid var(--glass-border, #e5ddd4);
  border-radius: 999px;
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  color: var(--accent-green, #6f4a31);
  cursor: pointer;
  font-weight: 600;
  margin-top: 0.25rem;
  justify-self: center;
}

.no-reviews { margin: 0; font-size: 0.84rem; color: var(--text-muted, #846b58); text-align: center; padding: 0.5rem; }

.add-review {
  background: var(--glass-bg, #fdf8f1);
  border: 1px solid var(--glass-border, #e5ddd4);
  border-radius: 16px;
  padding: 1rem;
  display: grid;
  gap: 0.6rem;
}
.add-review h4 { margin: 0; font-size: 0.9rem; color: var(--text-primary, #3f2a1d); }

.star-picker { display: flex; gap: 0.25rem; flex-direction: row-reverse; justify-content: flex-end; }
.star-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #ddd;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color 0.15s;
}
.star-btn.filled { color: #f5a623; }

.review-input,
.review-textarea {
  border: 1px solid var(--glass-border, #e5ddd4);
  border-radius: 12px;
  padding: 0.65rem 0.8rem;
  font-family: inherit;
  font-size: 0.85rem;
  background: #fff;
  color: var(--text-primary, #3f2a1d);
  width: 100%;
  box-sizing: border-box;
  outline: none;
  direction: rtl;
}
.review-textarea { resize: vertical; min-height: 72px; }

.submit-review-btn {
  background: var(--accent-green, #6f4a31);
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 0.65rem 1.5rem;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  justify-self: flex-start;
}

.review-success {
  margin: 0;
  font-size: 0.82rem;
  color: #27ae60;
  font-weight: 600;
}

.review-form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.char-counter {
  font-size: 0.72rem;
  color: var(--text-muted, #846b58);
}
.char-counter.near {
  color: var(--warning, #d97706);
}
.review-error {
  margin: 0;
  font-size: 0.82rem;
  color: var(--danger, #dc2626);
  font-weight: 600;
}

/* ════════════════════════════════════════════════════════════════
   STICKY ADD-TO-CART BAR (Mobile)
   ════════════════════════════════════════════════════════════════ */
.sticky-bottom-bar {
  position: fixed;
  bottom: calc(env(safe-area-inset-bottom) + 0.75rem);
  left: 0.5rem;
  right: 0.5rem;
  background: #fff;
  border: 1px solid var(--glass-border, #e5ddd4);
  box-shadow: 0 10px 30px rgba(0,0,0,0.12);
  padding: 0.6rem 0.7rem;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  z-index: 116;
  border-radius: 22px;
  max-width: 600px;
  margin: 0 auto;
}

.qty-control {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--theme-surface-alt, #f1e7db);
  border-radius: 999px;
  padding: 0.3rem 0.5rem;
  flex-shrink: 0;
}
.qty-num {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary, #3f2a1d);
  min-width: 1.4rem;
  text-align: center;
}
.qty-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  line-height: 1;
}

.price-and-add {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  min-width: 0;
}
.bottom-price {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.bottom-price small { font-size: 0.68rem; color: var(--text-muted, #846b58); }
.bottom-price strong { font-size: 1.05rem; color: var(--text-primary, #3f2a1d); font-weight: 800; }

.add-to-cart-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 0.75rem 1.3rem;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 0 6px 18px rgba(111,74,49,0.28);
}
.cart-plus {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255,255,255,0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 900;
}

/* Print */
.print-product-card { display: none; }
@media print {
  .sticky-bottom-bar, .hero-nav, .gallery-arrow, .gallery-dots,
  .scroll-top-btn, .lightbox-overlay, .share-toast { display: none !important; }
  .print-product-card { display: block; padding: 1rem; }
  .print-product-name { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.5rem; }
  .print-product-desc { font-size: 0.9rem; color: #555; margin-bottom: 0.5rem; }
  .print-product-price { font-size: 1rem; font-weight: 600; }
}

/* ─── Loading skeleton ─── */
.detail-skeleton {
  width: 100%;
  max-width: 640px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}
.skeleton-hero {
  width: 100%;
  height: 300px;
  border-radius: 24px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  background-size: 200% 100%;
}
.skeleton-info {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.skeleton-line {
  height: 1rem;
  border-radius: 6px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  background-size: 200% 100%;
  animation: shimmerAnim 1.5s infinite;
}
@keyframes shimmerAnim {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ─── Error state ─── */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  text-align: center;
}
.error-icon {
  color: var(--danger, #dc2626);
}
.retry-btn {
  border-radius: 999px;
  border: 1px solid var(--accent-green, #6f4a31);
  background: var(--accent-green, #6f4a31);
  color: #fff;
  padding: 0.6rem 1.5rem;
  font-family: inherit;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.18s ease;
}
.retry-btn:hover { opacity: 0.85; }
.retry-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ════════════════════════════════════════════════════════════════
   RELATED ITEMS
   ════════════════════════════════════════════════════════════════ */
.related-section {
  margin-top: 1.5rem;
  border-top: 1px solid var(--glass-border, #e5ddd4);
  padding-top: 1rem;
}
.related-title {
  margin: 0 0 0.75rem;
  font-size: 1rem;
  color: var(--text-primary, #3f2a1d);
  font-weight: 700;
}
.related-scroll {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  scroll-snap-type: x mandatory;
  padding-bottom: 0.5rem;
}
.related-scroll::-webkit-scrollbar { display: none; }
.related-card {
  flex-shrink: 0;
  width: 140px;
  text-decoration: none;
  color: inherit;
  scroll-snap-align: start;
}
.related-img-wrap {
  width: 140px;
  height: 100px;
  border-radius: 14px;
  overflow: hidden;
  background: var(--theme-surface-alt, #f1e7db);
}
.related-img-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.related-name {
  margin: 0.4rem 0 0.15rem;
  font-size: 0.8rem;
  color: var(--text-primary, #3f2a1d);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.related-price {
  font-size: 0.78rem;
  color: var(--accent-green, #6f4a31);
  font-variant-numeric: tabular-nums;
}

/* ════════════════════════════════════════════════════════════════
   DESKTOP LAYOUT
   ════════════════════════════════════════════════════════════════ */
@media (min-width: 768px) {
  .detail-page {
    padding-bottom: 3rem;
  }

  .detail-wrap {
    max-width: 100%;
  }

  .desktop-detail-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 2.5rem;
    width: 100%;
    max-width: min(1240px, 96vw);
    margin: 2rem auto;
    padding: 0 2rem;
    align-items: start;
  }

  .desktop-image-col {
    position: sticky;
    top: 2rem;
  }

  .desktop-main-image {
    width: 100%;
    height: 480px;
    border-radius: 28px;
    overflow: hidden;
    background: var(--theme-surface-alt, #f1e7db);
    box-shadow: 0 12px 36px rgba(0,0,0,0.1);
    cursor: pointer;
    position: relative;
  }

  .desktop-main-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
    display: block;
  }

  .desktop-thumbnails {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.75rem;
    overflow-x: auto;
    padding-bottom: 0.25rem;
  }

  .thumb-btn {
    width: 80px;
    height: 80px;
    border-radius: 14px;
    overflow: hidden;
    border: 2px solid transparent;
    background: var(--theme-surface-alt, #f1e7db);
    cursor: pointer;
    padding: 0;
    flex-shrink: 0;
    transition: border-color 0.2s;
  }

  .thumb-btn.active {
    border-color: var(--accent-green, #6f4a31);
  }

  .thumb-btn img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .desktop-info-col {
    display: flex;
    flex-direction: column;
  }

  .desktop-info-inner {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .desktop-info-inner .item-category {
    margin: 0;
    font-size: 0.85rem;
    color: var(--accent-gold, #c98d42);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .desktop-info-inner .item-title {
    margin: 0;
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary, #3f2a1d);
    line-height: 1.2;
  }

  .desktop-meta-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .desktop-price-row {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }

  .desktop-price-label {
    font-size: 0.9rem;
    color: var(--text-muted, #846b58);
  }

  .desktop-price {
    font-size: 1.7rem;
    font-weight: 800;
    color: var(--accent-green, #6f4a31);
    font-variant-numeric: tabular-nums;
  }

  .desktop-info-inner .item-desc {
    margin: 0;
    font-size: 0.97rem;
    color: var(--text-muted, #846b58);
    line-height: 1.8;
  }

  .desktop-pane {
    background: var(--glass-bg, #fdf8f1);
    border: 1px solid var(--glass-border, #e5ddd4);
    border-radius: 18px;
    padding: 1rem;
  }

  .desktop-tabs {
    position: static;
    background: var(--theme-surface-alt, #f1e7db);
  }

  /* Desktop back link */
  .desktop-back-link {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.82rem;
    color: var(--text-muted, #846b58);
    text-decoration: none;
    font-weight: 600;
    transition: color 0.18s ease;
    width: fit-content;
  }
  .desktop-back-link:hover { color: var(--accent-green, #6f4a31); }

  /* Desktop top actions */
  .desktop-top-actions {
    display: flex;
    gap: 0.5rem;
  }
  .desktop-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    border-radius: 14px;
    border: 1.5px solid var(--glass-border, #e5ddd4);
    background: none;
    padding: 0.55rem 0.9rem;
    cursor: pointer;
    font-family: inherit;
    font-size: 0.82rem;
    color: var(--text-secondary, #654a38);
    font-weight: 600;
    transition: border-color 0.2s, background 0.2s;
  }
  .desktop-action-btn.loved {
    border-color: #e74c3c;
    background: rgba(231, 76, 60, 0.06);
    color: #e74c3c;
  }
  .desktop-action-btn .heart-icon {
    font-size: 1.05rem;
    line-height: 1;
  }
  .desktop-action-btn:not(.loved) .heart-icon { color: var(--text-muted, #846b58); }
  .desktop-action-btn.loved .heart-icon { color: #e74c3c; }
  .desktop-action-btn:hover {
    border-color: var(--accent-green, #6f4a31);
    background: var(--accent-green20, rgba(111,74,49,0.06));
  }

  /* Zoom hint on desktop image */
  .zoom-hint {
    position: absolute;
    bottom: 0.75rem;
    right: 0.75rem;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-primary, #3f2a1d);
    opacity: 0;
    transition: opacity 0.2s;
    pointer-events: none;
  }
  .desktop-main-image:hover .zoom-hint { opacity: 1; }

  /* Desktop cart row */
  .desktop-cart-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 0;
    border-top: 1px solid var(--glass-border, #e5ddd4);
    margin-top: 0.5rem;
  }

  .desktop-price-display {
    display: flex;
    flex-direction: column;
    margin-right: auto;
  }

  .desktop-price-display small {
    font-size: 0.72rem;
    color: var(--text-muted, #846b58);
  }

  .desktop-price-display strong {
    font-size: 1.3rem;
    color: var(--text-primary, #3f2a1d);
    font-weight: 800;
    font-variant-numeric: tabular-nums;
  }

  .desktop-add-btn {
    padding: 0.85rem 2rem;
    font-size: 1rem;
  }

  /* Desktop related items grid */
  .related-scroll {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    overflow-x: visible;
  }
  .related-card {
    width: 100%;
  }
  .related-img-wrap {
    width: 100%;
    height: 140px;
  }
}

/* ════════════════════════════════════════════════════════════════
   LIGHTBOX
   ════════════════════════════════════════════════════════════════ */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0,0,0,0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.lightbox-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
  border: none;
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  z-index: 10;
}
.lightbox-close:hover { background: rgba(255,255,255,0.25); }

.lightbox-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
  border: none;
  color: #fff;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  z-index: 10;
}
.lightbox-arrow:hover { background: rgba(255,255,255,0.25); }
.lightbox-arrow--prev { left: 1rem; }
.lightbox-arrow--next { right: 1rem; }

.lightbox-image-wrap {
  max-width: 90vw;
  max-height: 85vh;
}
.lightbox-img {
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 8px;
  display: block;
}

.lightbox-counter {
  position: absolute;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255,255,255,0.7);
  font-size: 0.85rem;
  font-weight: 600;
}

/* ════════════════════════════════════════════════════════════════
   SCROLL TO TOP
   ════════════════════════════════════════════════════════════════ */
.scroll-top-btn {
  position: fixed;
  bottom: calc(env(safe-area-inset-bottom) + 7rem);
  left: 1.2rem;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  border: 0;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 8px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.35);
  opacity: 0;
  transform: translateY(12px) scale(0.85);
  transition: opacity 0.3s ease, transform 0.3s ease;
  z-index: 9999;
  pointer-events: none;
}
.scroll-top-btn.visible {
  opacity: 1;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}
.scroll-top-btn:hover {
  transform: translateY(-2px) scale(1.08);
  box-shadow: 0 12px 28px rgb(var(--palette-deep-sapphire-rgb) / 0.45);
}
@media (min-width: 768px) {
  .scroll-top-btn { bottom: 2rem; }
}

/* ════════════════════════════════════════════════════════════════
   SHARE TOAST
   ════════════════════════════════════════════════════════════════ */
.share-toast {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%) translateY(20px);
  background: var(--text-primary, #3f2a1d);
  color: #fff;
  padding: 0.6rem 1.2rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
  opacity: 0;
  transition: opacity 0.3s ease, transform 0.3s ease;
  z-index: 9999;
  pointer-events: none;
  white-space: nowrap;
}
.share-toast.visible {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
</style>
