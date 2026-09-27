<template>
  <section v-if="posts.length" class="blog-highlights" dir="rtl" aria-labelledby="blog-highlights-title">
    <div class="blog-highlights__head"><div><span>از آشپزخانهٔ ما</span><h2 id="blog-highlights-title">خواندنی‌های تازه</h2></div><a href="/blog">همهٔ مقاله‌ها <ArrowLeft :size="17" /></a></div>
    <div class="blog-highlights__grid"><a v-for="post in posts.slice(0, 3)" :key="post.name" class="blog-highlight" :href="`/blog/${encodeURIComponent(post.route)}`"><img v-if="post.cover_image" :src="post.cover_image" :alt="post.title" loading="lazy"><div class="blog-highlight__body"><small>{{ post.category || 'مجله' }} · {{ post.read_time }} دقیقه مطالعه</small><h3>{{ post.title }}</h3><p>{{ post.excerpt }}</p><b>ادامهٔ مطلب <ArrowLeft :size="15" /></b></div></a></div>
  </section>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import { getPublicBlogPosts } from '@/utils/api'
const posts = ref([])
onMounted(async () => { try { const result = await getPublicBlogPosts({ limit: 3 }); posts.value = result?.posts || [] } catch { posts.value = [] } })
</script>
<style scoped>
.blog-highlights{max-width:1200px;margin:clamp(2rem,6vw,5rem) auto;padding:0 1rem;color:var(--ds-color-text-primary)}.blog-highlights__head{display:flex;align-items:end;justify-content:space-between;gap:1rem;margin-bottom:1.1rem}.blog-highlights__head span,.blog-highlight small{color:var(--ds-color-action-accent);font-size:.78rem;font-weight:800}.blog-highlights h2{margin:.25rem 0 0;font-size:clamp(1.35rem,3vw,2rem)}.blog-highlights__head>a,.blog-highlight b{display:flex;align-items:center;gap:.4rem;color:var(--ds-color-action-primary);font-weight:800;text-decoration:none}.blog-highlights__grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}.blog-highlight{overflow:hidden;border:1px solid var(--ds-color-border);border-radius:var(--ds-radius-lg);background:var(--ds-color-surface-raised);color:inherit;text-decoration:none;box-shadow:var(--ds-shadow-sm)}.blog-highlight img{width:100%;height:190px;object-fit:cover;background:var(--ds-color-surface-muted)}.blog-highlight__body{padding:1rem}.blog-highlight h3{font-size:1.05rem;margin:.45rem 0;line-height:1.6}.blog-highlight p{color:var(--ds-color-text-secondary);font-size:.87rem;line-height:1.8;margin:0 0 .8rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.blog-highlight b{font-size:.82rem}@media(max-width:720px){.blog-highlights__grid{grid-template-columns:1fr}.blog-highlight{display:grid;grid-template-columns:110px 1fr}.blog-highlight img{height:100%;min-height:150px}.blog-highlight__body{padding:.8rem}}
</style>
