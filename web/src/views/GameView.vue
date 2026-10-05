<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { createMatch, dismissResult, game, leaveGame, refresh, submit } from '../composables/game'
import { ACTIONS, CATEGORY_LABEL, isAffordable } from '../actions'
import type { ActionDefUI, Category } from '../actions'
import ResourcePanel from '../components/ResourcePanel.vue'
import RoundModal from '../components/RoundModal.vue'

let timer: number | undefined
onMounted(() => {
  void refresh(true)
  timer = window.setInterval(() => void refresh(), 1500)
})
onUnmounted(() => window.clearInterval(timer))

const me = computed(() => game.view?.players[game.myId])
const opponentId = computed(() =>
  game.view ? (Object.keys(game.view.players).find((id) => id !== game.myId) ?? '') : '',
)
const opponent = computed(() => game.view?.players[opponentId.value])
const myResources = computed(() => me.value?.resources)
const iSubmitted = computed(() => game.view?.submitted.includes(game.myId) ?? false)
const oppSubmitted = computed(() => game.view?.submitted.includes(opponentId.value) ?? false)
const ended = computed(() => game.view?.status === 'ended')

const showInvite = computed(
  () =>
    game.myId === 'p1' &&
    game.view !== null &&
    game.view.round_number === 1 &&
    game.view.submitted.length === 0 &&
    game.shownRounds === 0,
)

const statusText = computed(() => {
  if (!game.view) return '连接中…'
  if (ended.value) {
    if (game.view.winner === 'draw') return '对局结束 · 平局'
    return game.view.winner === game.myId ? '对局结束 · 你获胜' : '对局结束 · 你落败'
  }
  if (iSubmitted.value && !oppSubmitted.value) return '已出招，等待对手…'
  if (!iSubmitted.value && oppSubmitted.value) return '对手已出招，轮到你出招'
  return '出招阶段'
})

const canAct = computed(() => game.view?.status === 'in_progress' && !iSubmitted.value && !game.submitting)

const grouped = computed(() => {
  const groups: Record<Category, ActionDefUI[]> = { production: [], attack: [], defense: [] }
  for (const a of ACTIONS) groups[a.category].push(a)
  return groups
})

function onAction(actionId: string): void {
  if (canAct.value) void submit(actionId)
}

async function onRestart(): Promise<void> {
  dismissResult()
  await createMatch(game.myName || '玩家1')
}

function copyId(): void {
  void navigator.clipboard?.writeText(game.matchId).catch(() => undefined)
}
</script>

<template>
  <section class="game">
    <div v-if="!game.view" class="loading">连接对局中…</div>
    <template v-else>
      <div class="statusbar">
        <span class="round">第 {{ game.view.round_number }} 回合</span>
        <span class="phase">{{ statusText }}</span>
        <span class="spacer" />
        <button class="matchid" title="点击复制对局 ID" @click="copyId">{{ game.matchId }}</button>
        <button class="btn ghost small" @click="leaveGame">退出</button>
      </div>

      <div v-if="showInvite" class="invite">
        等待对手加入：把对局 ID <b>{{ game.matchId }}</b> 发给对手，对方在首页「加入对局」中输入即可
      </div>

      <div v-if="game.error" class="error">{{ game.error }}</div>

      <div class="panels">
        <ResourcePanel v-if="me" :player="me" :me="true" :submitted="iSubmitted" />
        <ResourcePanel v-if="opponent" :player="opponent" :me="false" :submitted="oppSubmitted" />
      </div>

      <div class="board">
        <div v-for="(group, cat) in grouped" :key="cat" class="group" :class="`cat-${cat}`">
          <h3>{{ CATEGORY_LABEL[cat as Category] }}</h3>
          <div class="group-actions">
            <button
              v-for="a in group"
              :key="a.id"
              class="action"
              :disabled="!canAct || !isAffordable(a, myResources)"
              @click="onAction(a.id)"
            >
              <span class="name">{{ a.name }}</span>
              <span class="help">{{ a.help }}</span>
              <span v-if="!isAffordable(a, myResources)" class="lock">资源不足</span>
            </button>
          </div>
        </div>
      </div>

      <div class="log">
        <h3>对局记录</h3>
        <div v-for="r in [...game.rounds].reverse()" :key="r.round_number" class="log-round">
          <div class="log-title">第 {{ r.round_number }} 回合</div>
          <div v-for="(e, i) in r.events" :key="i" class="log-line" :class="`t-${e.type}`">
            {{ e.detail }}
          </div>
        </div>
        <div v-if="game.rounds.length === 0" class="log-empty">暂无记录，双方各出一招后开始结算</div>
      </div>

      <RoundModal
        v-if="game.pendingResult"
        :round="game.pendingResult"
        :my-id="game.myId"
        @close="dismissResult"
        @restart="onRestart"
        @leave="leaveGame"
      />
    </template>
  </section>
</template>

<style scoped>
.game {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 8px;
}

.loading {
  color: var(--muted);
  text-align: center;
  padding: 60px 0;
}

.statusbar {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px 16px;
}

.round {
  font-size: 17px;
  font-weight: 700;
}

.phase {
  color: var(--muted);
  font-size: 13px;
}

.spacer {
  flex: 1;
}

.matchid {
  background: var(--panel-2);
  border: 1px dashed var(--border);
  color: var(--muted);
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 13px;
  cursor: pointer;
}

.matchid:hover {
  color: var(--text);
  border-color: var(--blue);
}

.invite {
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
}

.invite b {
  color: #93c5fd;
  font-size: 16px;
  margin: 0 4px;
}

.panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.board {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.group h3 {
  margin: 0 0 8px;
  font-size: 13px;
  letter-spacing: 4px;
}

.cat-production h3 {
  color: var(--green);
}

.cat-attack h3 {
  color: var(--red);
}

.cat-defense h3 {
  color: var(--blue);
}

.group-actions {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 10px;
}

.action {
  position: relative;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text);
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: transform 0.08s ease, border-color 0.15s ease;
}

.action:hover:not(:disabled) {
  transform: translateY(-2px);
  border-color: currentColor;
}

.action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.cat-production .action:hover:not(:disabled) {
  border-color: var(--green);
}

.cat-attack .action:hover:not(:disabled) {
  border-color: var(--red);
}

.cat-defense .action:hover:not(:disabled) {
  border-color: var(--blue);
}

.action .name {
  font-size: 15px;
  font-weight: 600;
}

.action .help {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}

.action .lock {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 11px;
  color: var(--red);
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: 999px;
  padding: 1px 8px;
}

.log {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 18px;
}

.log h3 {
  margin: 0 0 10px;
  font-size: 13px;
  color: var(--muted);
  letter-spacing: 4px;
}

.log-round {
  margin-bottom: 12px;
}

.log-title {
  font-size: 13px;
  font-weight: 600;
  color: #93c5fd;
  margin-bottom: 4px;
}

.log-line {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.8;
  border-left: 2px solid var(--border);
  padding-left: 10px;
}

.log-line.t-death,
.log-line.t-match_end {
  color: var(--text);
  border-left-color: var(--gold);
}

.log-empty {
  color: var(--muted);
  font-size: 13px;
}

@media (max-width: 720px) {
  .panels {
    grid-template-columns: 1fr;
  }
}
</style>
