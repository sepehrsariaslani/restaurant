with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'r') as f:
    content = f.read()

# Add empty states for each column
content = content.replace(
    '''<div class="kds-col-body">
            <KitchenOrder 
              v-for="o in colNew" :key="o.name" 
              :order="o" type="new" 
              @action="acceptOrder(o)" 
            />
          </div>''',
    '''<div class="kds-col-body">
            <div v-if="!colNew.length" class="lane-empty">سفارش جدیدی نیست</div>
            <KitchenOrder 
              v-for="o in colNew" :key="o.name" 
              :order="o" type="new" 
              @action="acceptOrder(o)" 
            />
          </div>'''
)

content = content.replace(
    '''<div class="kds-col-body">
            <KitchenOrder 
              v-for="o in colPrep" :key="o.name" 
              :order="o" type="prep" 
              @action="markReady(o)" 
            />
          </div>''',
    '''<div class="kds-col-body">
            <div v-if="!colPrep.length" class="lane-empty">آیتمی در حال تولید نیست</div>
            <KitchenOrder 
              v-for="o in colPrep" :key="o.name" 
              :order="o" type="prep" 
              @action="markReady(o)" 
            />
          </div>'''
)

content = content.replace(
    '''<div class="kds-col-body">
            <KitchenOrder 
              v-for="o in colReady" :key="o.name" 
              :order="o" type="ready" 
              @action="closeOrder(o)" 
            />
          </div>''',
    '''<div class="kds-col-body">
            <div v-if="!colReady.length" class="lane-empty">سفارشی آماده‌ی تحویل نیست</div>
            <KitchenOrder 
              v-for="o in colReady" :key="o.name" 
              :order="o" type="ready" 
              @action="closeOrder(o)" 
            />
          </div>'''
)

content = content.replace(
    '''<div class="kds-col-body">
            <KitchenOrder 
              v-for="o in colClosed" :key="o.name" 
              :order="o" type="closed" 
            />
          </div>''',
    '''<div class="kds-col-body">
            <div v-if="!colClosed.length" class="lane-empty">سفارشی در تاریخچه نیست</div>
            <KitchenOrder 
              v-for="o in colClosed" :key="o.name" 
              :order="o" type="closed" 
            />
          </div>'''
)

css = """
.lane-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--mg-text-muted);
  border: 1px dashed var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  background: var(--mg-bg-page);
  text-align: center;
  margin: 0.5rem;
  opacity: 0.8;
}
"""

content = content.replace('/* Responsive adjustments */', css + '\n/* Responsive adjustments */')

with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'w') as f:
    f.write(content)
