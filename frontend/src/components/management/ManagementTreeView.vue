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
        <div class="tree-copy">
          <strong>{{ node.label || '-' }}</strong>
          <small v-if="node.caption">{{ node.caption }}</small>
        </div>
      </div>

      <span v-if="node.badge" class="tree-badge">{{ node.badge }}</span>
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
  gap: 0.4rem;
}

.tree-row {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.16);
  border-radius: 12px;
  padding: 0.45rem 0.55rem;
  display: flex;
  align-items: center;
  gap: 0.38rem;
  flex-wrap: wrap;
  background: rgb(var(--palette-eggshell-rgb) / 0.56);
  position: relative;
}

.tree-row.nested {
  background:
    linear-gradient(90deg, rgb(var(--palette-deep-sapphire-rgb) / 0.03), transparent 38%),
    rgb(var(--palette-eggshell-rgb) / 0.56);
}

.tree-row.nested::before {
  content: '';
  position: absolute;
  inset-inline-start: calc(var(--tree-depth-indent) - 0.48rem);
  top: 0.36rem;
  bottom: 0.36rem;
  width: 2px;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.34);
  pointer-events: none;
}

.tree-row.clickable {
  cursor: pointer;
}

.tree-row.clickable:hover {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.38);
  box-shadow: 0 8px 18px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.tree-main {
  min-width: 0;
  flex: 1;
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
}

.tree-toggle {
  width: 1.05rem;
  height: 1.05rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.26);
  border-radius: 8px;
  background: #fff;
  color: var(--text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  line-height: 1;
  cursor: pointer;
}

.tree-toggle--ghost {
  border: none;
  background: transparent;
  pointer-events: none;
}

.tree-copy {
  min-width: 0;
  display: grid;
  gap: 0.08rem;
}

.tree-copy strong {
  font-size: 0.8rem;
  line-height: 1.45;
  color: var(--ink-900);
}

.tree-copy small {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.tree-badge {
  border-radius: 999px;
  padding: 0.12rem 0.48rem;
  font-size: 0.68rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.24);
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.88);
  background: #fff;
}

.tree-status {
  border-radius: 999px;
  padding: 0.14rem 0.5rem;
  font-size: 0.68rem;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
}

.tree-status.tone-success {
  background: rgb(var(--palette-june-bud-rgb) / 0.35);
  color: var(--accent-green);
}

.tree-status.tone-warning {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.2);
  color: var(--accent-gold);
}
</style>
