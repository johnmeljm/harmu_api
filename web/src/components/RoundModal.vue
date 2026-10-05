<script setup lang="ts">
import { computed } from 'vue'
import type { RoundResult } from '../types'

const props = defineProps<{ round: RoundResult; myId: string }>()

defineEmits<{ close: []; restart: []; leave: [] }>()

const finalText = computed(() => {
  if (props.round.winner === 'draw') return '双方同时死亡，平局'
  return props.round.winner === props.myId ? '你赢了！' : '你输了'
})

const finalClass = computed(() => {
  if (props.round.winner === 'draw') return 'draw'
  return props.round.winner === props.myId ? 'win' : 'lose'
})
</script>

<template>
  <div class="mask" @click.self="$emit('close')">
    <div class="modal">
      <h2>第 {{ round.round_number }} 回合结算</h2>
      <div class="events">
        <div v-for="(e, i) in round.events" :key="i" class="ev" :class="`ev-${e.type}`">
          {{ e.detail }}
        </div>
      </div>
      <div v-if="round.match_status === 'ended'" class="final" :class="finalClass">
        {{ finalText }}
      </div>
      <div class="actions">
        <template v-if="round.match_status === 'ended'">
          <button class="btn primary" @click="$emit('restart')">再来一局</button>
          <button class="btn" @click="$emit('leave')">返回首页</button>
        </template>
        <button v-else class="btn primary" @click="$emit('close')">继续</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 17, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
  padding: 20px;
}

.modal {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  width: min(480px, 100%);
  padding: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

h2 {
  margin: 0 0 14px;
  font-size: 18px;
}

.events {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 18px;
}

.ev {
  background: var(--panel-2);
  border-radius: 8px;
  padding: 9px 12px;
  font-size: 14px;
  border-left: 3px solid var(--border);
}

.ev-attack {
  border-left-color: var(--red);
}

.ev-defense {
  border-left-color: var(--blue);
}

.ev-production {
  border-left-color: var(--green);
}

.ev-death,
.ev-match_end {
  border-left-color: var(--gold);
  font-weight: 600;
}

.final {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 16px;
}

.final.win {
  color: var(--green);
  background: rgba(34, 197, 94, 0.1);
}

.final.lose {
  color: #fda4af;
  background: rgba(239, 68, 68, 0.1);
}

.final.draw {
  color: var(--gold);
  background: rgba(245, 158, 11, 0.1);
}

.actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}
</style>
