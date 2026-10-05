<script setup lang="ts">
import type { PlayerView, ResourcePack } from '../types'

const props = defineProps<{ player: PlayerView; me: boolean; submitted: boolean }>()

const RES: Array<{ key: keyof ResourcePack; label: string }> = [
  { key: 'hp', label: '生命值' },
  { key: 'money', label: '钱' },
  { key: 'knives', label: '刀' },
  { key: 'gunpowder', label: '火药' },
  { key: 'bombs', label: '炸弹' },
  { key: 'reflect_shields', label: '反弹盾' },
]
</script>

<template>
  <div class="panel" :class="{ me: props.me, dead: !props.player.alive }">
    <div class="head">
      <span class="who">
        {{ props.player.name }}
        <small>{{ props.player.player_id }}</small>
      </span>
      <span class="chips">
        <span v-if="!props.player.alive" class="chip dead">阵亡</span>
        <span v-if="props.submitted" class="chip ready">已出招</span>
      </span>
    </div>
    <div class="res">
      <div v-for="r in RES" :key="r.key" class="item" :class="r.key">
        <span class="label">{{ r.label }}</span>
        <span class="value">{{ props.player.resources[r.key] }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px 18px;
  opacity: 0.85;
}

.panel.me {
  opacity: 1;
  border-color: rgba(59, 130, 246, 0.55);
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2);
}

.panel.dead {
  filter: grayscale(0.7);
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.who {
  font-size: 17px;
  font-weight: 600;
}

.who small {
  margin-left: 8px;
  color: var(--muted);
  font-weight: 400;
  font-size: 12px;
}

.chips {
  display: flex;
  gap: 6px;
}

.chip {
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 10px;
  border: 1px solid var(--border);
  color: var(--muted);
}

.chip.ready {
  color: var(--green);
  border-color: rgba(34, 197, 94, 0.5);
}

.chip.dead {
  color: #fda4af;
  border-color: rgba(239, 68, 68, 0.5);
}

.res {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.item {
  background: var(--panel-2);
  border-radius: 10px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item.hp .value {
  color: #fda4af;
  font-weight: 700;
}

.item.money .value {
  color: var(--gold);
  font-weight: 700;
}

.item.knives .value,
.item.gunpowder .value,
.item.bombs .value {
  color: #fca5a5;
  font-weight: 700;
}

.item.reflect_shields .value {
  color: #93c5fd;
  font-weight: 700;
}

.label {
  font-size: 12px;
  color: var(--muted);
}

.value {
  font-size: 18px;
}
</style>
