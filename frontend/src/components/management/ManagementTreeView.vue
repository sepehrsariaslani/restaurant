<template>
  <div v-if="flatNodes.length" class="tree-view">
    <article
      v-for="node in flatNodes"
      :key="node.key"
      class="tree-row"
      :class="{ clickable: isNodeClickable(node), nested: node.depth > 0 }"
      :style="resolveRowStyle(node)"
      :tabindex="isNodeClickable(node) ? 0 : undefined"
      @click="handleNodeClick($event, node)"
      @keydown.enter.prevent="handleNodeKeydown(node)"
      @keydown.space.prevent="handleNodeKeydown(node)"
    >
      <div class="tree-main">
        <button
          v-if="node.hasChildren"
          type="button"
          class="tree-toggle"
          :aria-label="node.isExpanded ? 'بستن شاخه' : 'باز کردن شاخه'"
          @click.stop="toggleNode(node)"
        >
          {{ node.isExpanded ? '▾' : '▸' }}
        </button>
        <span v-else class="tree-toggle tree-toggle--ghost" aria-hidden="true"></span>
        <span v-if="$slots.icon" class="tree-icon">
          <slot name="icon" :node="node" />
        </span>
        <div class="tree-copy">
          <strong>{{ node.label || '-' }}</strong>
          <small v-if="node.caption">{{ node.caption }}</small>
        </div>
      </div>

      <span v-if="node.badge" :class="['tree-badge', node.badge === 'دسته' ? 'tree-badge--category' : 'tree-badge--product']">{{ node.badge }}</span>
      <span v-if="node.status?.label" :class="['tree-status', node.status?.tone ? `tone-${node.status.tone}` : '']">
        {{ node.status.label }}
      </span>

      <slot name="actions" :node="node" />
    </article>
  </div>

  <p v-else class="muted">{{ emptyText }}</p>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  nodes: {
    type: Array,
    default: () => [],
  },
  nodeClickable: {
    type: [Boolean, Function],
    default: false,
  },
  defaultExpandAll: {
    type: Boolean,
    default: true,
  },
  emptyText: {
    type: String,
    default: 'داده‌ای برای نمایش وجود ندارد.',
  },
})

const emit = defineEmits(['node-click'])
const expandedKeys = ref(new Set())

function collectBranchKeys(nodes = [], depth = 0, parentKey = 'node') {
  const keys = []
  const rows = Array.isArray(nodes) ? nodes : []
  for (let index = 0; index < rows.length; index += 1) {
    const source = rows[index] || {}
    const key = String(source.key || `${parentKey}-${depth}-${index}`)
    const children = Array.isArray(source.children) ? source.children : []
    if (children.length) {
      keys.push(key)
      keys.push(...collectBranchKeys(children, depth + 1, key))
    }
  }
  return keys
}

function flattenNodes(nodes = [], depth = 0, parentKey = 'node', expandedSet = new Set()) {
  const output = []
  for (let index = 0; index < (Array.isArray(nodes) ? nodes : []).length; index += 1) {
    const source = nodes[index] || {}
    const key = String(source.key || `${parentKey}-${depth}-${index}`)
    const children = Array.isArray(source.children) ? source.children : []
    const hasChildren = children.length > 0
    const isExpanded = hasChildren ? expandedSet.has(key) : false

    output.push({
      ...source,
      key,
      depth,
      hasChildren,
      isExpanded,
      children,
    })

    if (hasChildren && isExpanded) {
      output.push(...flattenNodes(children, depth + 1, key, expandedSet))
    }
  }
  return output
}

const flatNodes = computed(() => flattenNodes(props.nodes || [], 0, 'node', expandedKeys.value))

function isNodeClickable(node) {
  if (typeof props.nodeClickable === 'function') {
    return Boolean(props.nodeClickable(node))
  }
  return Boolean(props.nodeClickable)
}

function handleNodeClick(event, node) {
  const target = event?.target
  if (target?.closest?.('a, button, input, select, textarea, label, [role="button"], [data-no-node-click="1"]')) {
    return
  }
  if (!isNodeClickable(node)) {
    return
  }
  emit('node-click', node)
}

function handleNodeKeydown(node) {
  if (!isNodeClickable(node)) {
    return
  }
  emit('node-click', node)
}

function toggleNode(node) {
  const key = String(node?.key || '').trim()
  if (!key || !node?.hasChildren) {
    return
  }
  const next = new Set(expandedKeys.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
  }
  expandedKeys.value = next
}

function resolveRowStyle(node) {
  const depth = Number(node?.depth || 0)
  const depthIndent = Math.max(0, depth) * 1.35
  return {
    '--tree-depth-indent': `${depthIndent}rem`,
    paddingInlineStart: `calc(0.6rem + ${depthIndent}rem)`,
  }
}

watch(
  () => props.nodes,
  (nodes) => {
    const branchKeys = collectBranchKeys(nodes || [], 0, 'node')
    const validKeys = new Set(branchKeys)
    const next = new Set()

    for (const key of expandedKeys.value) {
      if (validKeys.has(key)) {
        next.add(key)
      }
    }

    for (const key of branchKeys) {
      if (!expandedKeys.value.has(key) && props.defaultExpandAll) {
        next.add(key)
      }
    }

    expandedKeys.value = next
  },
  { immediate: true, deep: true },
)
</script>

<style scoped>
.tree-view {
  display: grid;
  gap: 0.3rem;
}

.tree-row {
  border: 1px solid var(--mg-border-light);
  border-radius: 10px;
  padding: 0.4rem 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.38rem;
  flex-wrap: wrap;
  background: var(--mg-bg-surface);
  position: relative;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.tree-row.nested {
  background: color-mix(in srgb, var(--mg-bg-soft) 30%, var(--mg-bg-surface));
}

.tree-row.nested::before {
  content: '';
  position: absolute;
  inset-inline-start: calc(var(--tree-depth-indent) - 0.48rem);
  top: 0.3rem;
  bottom: 0.3rem;
  width: 2px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--mg-primary) 30%, var(--mg-border-light));
  pointer-events: none;
}

.tree-row.clickable {
  cursor: pointer;
}

.tree-row.clickable:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
  background: color-mix(in srgb, var(--mg-primary) 5%, var(--mg-bg-surface));
  box-shadow: 0 6px 16px rgb(var(--mg-primary-rgb) / 0.1);
}

.tree-main {
  min-width: 0;
  flex: 1;
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
}

.tree-toggle {
  width: 1.1rem;
  height: 1.1rem;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 35%, var(--mg-border-light));
  border-radius: 7px;
  background: var(--mg-bg-page);
  color: var(--mg-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.68rem;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.12s ease;
}

.tree-toggle:hover {
  background: color-mix(in srgb, var(--mg-primary) 12%, var(--mg-bg-surface));
  border-color: var(--mg-primary);
}

.tree-toggle--ghost {
  border: none;
  background: transparent;
  pointer-events: none;
}

.tree-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--mg-primary);
  flex-shrink: 0;
}

.tree-copy {
  min-width: 0;
  display: grid;
  gap: 0.08rem;
}

.tree-copy strong {
  font-size: 0.8rem;
  line-height: 1.45;
  color: var(--mg-text-main);
}

.tree-copy small {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
}

.tree-badge {
  border-radius: 999px;
  padding: 0.1rem 0.45rem;
  font-size: 0.64rem;
  border: 1px solid color-mix(in srgb, var(--mg-olive) 30%, var(--mg-border-light));
  color: var(--mg-olive);
  background: color-mix(in srgb, var(--mg-olive-soft) 40%, var(--mg-bg-surface));
  flex-shrink: 0;
}

.tree-badge--category {
  color: var(--mg-success);
  border-color: color-mix(in srgb, var(--mg-success) 30%, var(--mg-border-light));
  background: var(--mg-success-bg);
}

.tree-badge--product {
  color: var(--mg-primary);
  border-color: color-mix(in srgb, var(--mg-primary) 30%, var(--mg-border-light));
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface));
}

.tree-status {
  border-radius: 999px;
  padding: 0.12rem 0.45rem;
  font-size: 0.64rem;
  flex-shrink: 0;
}

.tree-status.tone-success {
  background: var(--mg-success-bg);
  color: var(--mg-success);
  border: 1px solid color-mix(in srgb, var(--mg-success) 25%, transparent);
}

.tree-status.tone-warning {
  background: rgb(254 243 199 / 0.95);
  color: #92400e;
  border: 1px solid rgb(146 64 14 / 0.2);
}

@media (max-width: 520px) {
  .tree-row {
    padding: 0.35rem 0.45rem;
  }

  .tree-copy strong {
    font-size: 0.74rem;
  }

  .tree-badge,
  .tree-status {
    font-size: 0.58rem;
    padding: 0.08rem 0.35rem;
  }
}
</style>