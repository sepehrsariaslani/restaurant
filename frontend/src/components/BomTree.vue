<template>
  <div class="bom-tree" :class="`depth-${depth}`">
    <div
      v-for="(node, index) in normalizedNodes"
      :key="`${node.item_code || node.item_name}-${depth}-${index}`"
      class="bom-node"
      :class="{
        'is-assembly': node.is_sub_assembly,
        'is-expanded': expandedNodes.has(getNodeKey(node, index)),
      }"
    >
      <button
        class="bom-node__header"
        :class="{ 'is-leaf': !node.is_sub_assembly }"
        type="button"
        @click="toggleNode(node, index)"
      >
        <span class="bom-node__header-main">
          <span class="bom-node__thumb" :class="{ empty: !node.image }">
            <img v-if="node.image" :src="node.image" :alt="node.item_name || node.item_code" loading="lazy" />
          </span>
          <svg
            v-if="node.is_sub_assembly"
            class="bom-node__chevron"
            :class="{ expanded: expandedNodes.has(getNodeKey(node, index)) }"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
          <span v-else class="bom-node__leaf-dot"></span>

          <span class="bom-node__text">
            <span class="bom-node__name">{{ node.item_name || node.item_code }}</span>
            <span v-if="node.item_code && node.item_code !== node.item_name" class="bom-node__code">{{ node.item_code }}</span>
            <span v-if="node.is_sub_assembly && node.bom_batch_qty" class="bom-node__recipe-meta">
              خروجی اصلی: {{ formatQty(node.bom_batch_qty) }} {{ node.bom_batch_uom || node.uom || 'واحد' }}
              <span class="dot-sep">•</span>
              نیاز این محصول: {{ formatQty(node.bom_required_qty || node.qty) }} {{ node.uom || node.bom_batch_uom || 'واحد' }}
            </span>
          </span>
        </span>

        <span class="bom-node__meta">
          <span
            v-if="node.is_sub_assembly && node.children && node.children.length"
            class="bom-node__badge"
          >
            {{ node.children.length }} آیتم
          </span>
          <span class="bom-node__qty">{{ formatQty(node.qty) }} {{ node.uom || 'واحد' }}</span>
        </span>
      </button>

      <Transition name="slide">
        <div
          v-if="(node.is_sub_assembly || hasChildren(node)) && expandedNodes.has(getNodeKey(node, index))"
          class="bom-node__children"
        >
          <BomTree
            :nodes="node.children || []"
            :depth="depth + 1"
            :default-expanded="defaultExpanded"
          />
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  depth: { type: Number, default: 0 },
  defaultExpanded: { type: Boolean, default: false },
})

const expandedNodes = ref(new Set())
const depthKey = computed(() => props.depth)
const normalizedNodes = computed(() => normalizeNodes(props.nodes || []))

function hasChildren(node) {
  return Array.isArray(node?.children) && node.children.length > 0
}

function normalizeNode(node = {}) {
  const children = Array.isArray(node?.children) ? normalizeNodes(node.children) : []
  return {
    ...node,
    item_name: node?.item_name || node?.title || node?.item_code || 'آیتم بدون نام',
    item_code: node?.item_code || '',
    image: node?.image || node?.item_image || node?.website_image || '',
    uom: node?.uom || node?.stock_uom || '',
    qty: node?.qty ?? node?.stock_qty ?? 0,
    children,
    bom_batch_qty: node?.bom_batch_qty,
    bom_batch_uom: node?.bom_batch_uom,
    bom_declared_qty: node?.bom_declared_qty,
    bom_required_qty: node?.bom_required_qty,
    bom_scale: node?.bom_scale,
    bom_output_source: node?.bom_output_source,
    is_sub_assembly: Boolean(node?.is_sub_assembly || children.length),
  }
}

function normalizeNodes(nodes = []) {
  if (!Array.isArray(nodes)) return []
  return nodes.map((node) => normalizeNode(node))
}

function getNodeKey(node, index = 0) {
  return `${depthKey.value}:${node.item_code || node.item_name || 'node'}:${index}`
}

function toggleNode(node, index = 0) {
  if (!node.is_sub_assembly && !hasChildren(node)) return
  const code = getNodeKey(node, index)
  if (expandedNodes.value.has(code)) {
    expandedNodes.value.delete(code)
  } else {
    expandedNodes.value.add(code)
  }
  expandedNodes.value = new Set(expandedNodes.value)
}

function formatQty(value) {
  const num = Number(value)
  if (!Number.isFinite(num)) return value || '0'
  return Number.isInteger(num) ? num.toString() : num.toFixed(2)
}

onMounted(() => {
  if (props.defaultExpanded) {
    const codes = new Set()
    for (const [index, n] of normalizedNodes.value.entries()) {
      if (n.is_sub_assembly || hasChildren(n)) {
        codes.add(getNodeKey(n, index))
      }
    }
    expandedNodes.value = codes
  }
})
</script>

<style scoped>
.bom-tree {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.bom-node {
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.16);
  border-radius: 20px;
  background: linear-gradient(180deg, rgb(255 255 255 / 0.9), rgb(var(--palette-eggshell-rgb) / 0.96));
  box-shadow: 0 10px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  overflow: hidden;
}

.bom-node__header {
  width: 100%;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.95rem 1rem;
  cursor: pointer;
  text-align: right;
  font-family: inherit;
  transition: background 0.18s ease, transform 0.18s ease;
}

.bom-node__header:hover {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.05);
}

.bom-node__header.is-leaf {
  cursor: default;
}

.bom-node__header-main {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  flex: 1;
}

.bom-node__thumb {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  flex-shrink: 0;
  overflow: hidden;
  background: linear-gradient(180deg, rgb(var(--palette-deep-saffron-rgb) / 0.1), rgb(var(--palette-deep-sapphire-rgb) / 0.05));
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.16);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.bom-node__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.bom-node__thumb.empty::after {
  content: '';
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.75);
  box-shadow: 0 0 0 5px rgb(var(--palette-deep-saffron-rgb) / 0.12);
}

.bom-node__text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.bom-node__chevron {
  flex-shrink: 0;
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.85);
  transition: transform 0.22s ease;
  transform: rotate(0deg);
}

.bom-node__chevron.expanded {
  transform: rotate(90deg);
}

.bom-node__leaf-dot {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 999px;
  background: linear-gradient(135deg, rgb(var(--palette-deep-saffron-rgb) / 0.95), rgb(var(--palette-deep-sapphire-rgb) / 0.8));
  box-shadow: 0 0 0 4px rgb(var(--palette-deep-saffron-rgb) / 0.1);
  flex-shrink: 0;
}

.bom-node__name {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--ink-800);
  line-height: 1.5;
}

.bom-node__code {
  font-size: 0.72rem;
  color: var(--text-muted);
  direction: ltr;
  text-align: right;
}

.bom-node__recipe-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  color: var(--text-muted);
  font-size: 0.72rem;
  line-height: 1.6;
}

.dot-sep {
  opacity: 0.55;
}

.bom-node__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.35rem;
  flex-shrink: 0;
}

.bom-node__qty {
  font-variant-numeric: tabular-nums;
  font-size: 0.82rem;
  color: var(--ink-700);
  white-space: nowrap;
  padding: 0.32rem 0.7rem;
  border-radius: 999px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.12);
}

.bom-node__badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.22rem 0.6rem;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
}

.bom-node__children {
  padding: 0 0.75rem 0.75rem;
}

.bom-tree.depth-1,
.bom-tree.depth-2,
.bom-tree.depth-3,
.bom-tree.depth-4 {
  padding-right: 0.85rem;
  border-right: 2px solid rgb(var(--palette-deep-saffron-rgb) / 0.22);
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.22s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-4px);
  overflow: hidden;
}

.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 2000px;
}

@media (max-width: 640px) {
  .bom-node__header {
    padding: 0.9rem;
    gap: 0.6rem;
  }

  .bom-node__meta {
    gap: 0.3rem;
  }

  .bom-node__qty,
  .bom-node__badge {
    font-size: 0.68rem;
  }
}
</style>
