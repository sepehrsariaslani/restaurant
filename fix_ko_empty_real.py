with open('frontend/src/components/KitchenOrder.vue', 'r') as f:
    content = f.read()

replacement = """<div class="ko-items">
        <div v-if="(order.items || []).length === 0" class="ko-empty-items">
          بدون آیتم مشخص
        </div>
        <div v-for="(it, i) in (order.items || []).slice(0, 6)" :key="i" class="ko-item">"""

content = content.replace(
    '''<div class="ko-items">
        <div v-for="(it, i) in (order.items || []).slice(0, 6)" :key="i" class="ko-item">''',
    replacement
)

css = """
.ko-empty-items {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-style: italic;
  text-align: center;
  padding: 0.5rem;
}
"""

if ".ko-empty-items" not in content:
    content = content.replace('/* Header */', css + '\n/* Header */')

with open('frontend/src/components/KitchenOrder.vue', 'w') as f:
    f.write(content)
