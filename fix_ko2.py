with open('frontend/src/components/KitchenOrder.vue', 'r') as f:
    content = f.read()

content = content.replace(
    '<div v-for="(it, i) in (order.items || [])" :key="i" class="ko-item">',
    '<div v-for="(it, i) in (order.items || []).slice(0, 6)" :key="i" class="ko-item">'
)

more_html = """
        </div>
        <div v-if="(order.items || []).length > 6" class="ko-more">
          + {{ toFaDigits((order.items || []).length - 6) }} آیتم دیگر
        </div>
      </div>
"""

content = content.replace(
    '        </div>\n      </div>\n    </div>',
    more_html + '\n    </div>'
)

css_more = """
.ko-more {
  text-align: center;
  font-size: 0.8rem;
  color: var(--mg-secondary);
  font-weight: 800;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--mg-border-light);
  margin-top: 0.2rem;
}
"""

content = content.replace('/* Footer */', css_more + '\n/* Footer */')

with open('frontend/src/components/KitchenOrder.vue', 'w') as f:
    f.write(content)
