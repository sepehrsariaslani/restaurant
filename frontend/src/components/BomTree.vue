<template>
  <div class="bom-tree" :class="`depth-${depth}`">
    <div
      v-for="node in nodes"
      :key="node.item_code"
      class="bom-node"
      :class="{
        'is-assembly': node.is_sub_assembly,
        'is-expanded': expandedNodes.has(node.item_code),
      }"
    >
      <!-- Node header -->
      <div class="bom-node__header" @click="toggleNode(node)">
        <svg
          v-if="node.is_sub_assembly"
          class="bom-node__chevron"
          :class="{ expanded: expandedNodes.has(node.item_code) }"
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

        <span class="bom-node__name">{{ node.item_name }}</span>
        <span class="bom-node__qty">{{ formatQty(node.qty) }} {{ node.uom }}</span>
        <span
          v-if="node.is_sub_assembly && node.children && node.children.length"
          class="bom-node__badge"
        >
          {{ node.children.length }} ماده
        </span>
      </div>

      <!-- Children (recursive) -->
      <Transition name="slide">
        <BomTree
          v-if="node.is_sub_assembly && expandedNodes.has(node.item_code)"
          :nodes="node.children"
          :depth="depth + 1"
          :default-expanded="defaultExpanded"
        />
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  depth: { type: Number, default: 0 },
  defaultExpanded: { type: Boolean, default: false },
})

const expandedNodes = ref(new Set())

function toggleNode(node) {
  if (!node.is_sub_assembly) return
  const code = node.item_code
  if (expandedNodes.value.has(code)) {
    expandedNodes.value.delete(code)
  } else {
    expandedNodes.value.add(code)
  }
  // Force reactivity
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
    function collectCodes(nodes) {
      for (const n of nodes) {
        if (n.is_sub_assembly) {
          codes.add(n.item_code)
          if (n.children) collectCodes(n.children)
        }
      }
    }
    collectCodes(props.nodes)
    expandedNodes.value = codes
  }
})
</script>

<style scoped>
.bom-tree {
  border: 1px solid var(--theme-border);
  border-radius: 12px;
  overflow: hidden;
}

.bom-node__header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.15s ease;
  border-bottom: 1px solid var(--theme-border);
}

.bom-node:last-child .bom-node__header {
  border-bottom: none;
}

.bom-node__header:hover {
  background: var(--surface-alt);
}

.bom-node__chevron {
  flex-shrink: 0;
  transition: transform 0.2s ease;
  transform: rotate(0deg);
}

.bom-node__chevron.expanded {
  transform: rotate(90deg);
}

.bom-node__leaf-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  flex-shrink: 0;
}

.bom-node__name {
  flex: 1;
  font-weight: 500;
  font-size: 0.9rem;
  color: var(--ink-800);
}

.bom-node__qty {
  font-variant-numeric: tabular-nums;
  font-size: 0.85rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.bom-node__badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
}

/* Depth indentation */
.bom-tree.depth-1 {
  padding-right: 1.5rem;
}
.bom-tree.depth-2 {
  padding-right: 1.5rem;
}
.bom-tree.depth-3 {
  padding-right: 1.5rem;
}

/* Slide animation */
.slide-enter-active {
  transition: all 0.2s ease-out;
}
.slide-leave-active {
  transition: all 0.15s ease-in;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  overflow: hidden;
}
.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 2000px;
}
</style>
