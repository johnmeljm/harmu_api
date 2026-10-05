<script setup lang="ts">
import { ref } from 'vue'
import { api, ApiError } from '../api'
import { createMatch, joinMatch } from '../composables/game'

const myName = ref('')
const joinId = ref('')
const joinAs = ref<'p2' | 'p1'>('p2')
const busy = ref(false)
const error = ref('')

async function onCreate(): Promise<void> {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    await createMatch(myName.value)
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '创建失败，请检查服务端是否已启动'
  } finally {
    busy.value = false
  }
}

function onJoin(): void {
  if (busy.value || !joinId.value.trim()) return
  busy.value = true
  error.value = ''
  api
    .getMatch(joinId.value.trim())
    .then((view) => {
      if (view.status === 'ended') {
        error.value = `对局 ${view.match_id} 已结束（${view.winner === 'draw' ? '平局' : `${view.winner} 获胜`}）`
        return
      }
      joinMatch(joinId.value, joinAs.value)
    })
    .catch((err: unknown) => {
      error.value = err instanceof ApiError ? err.message : '加入失败，请稍后重试'
    })
    .finally(() => {
      busy.value = false
    })
}
</script>

<template>
  <section class="home">
    <div class="card create">
      <h2>创建对局</h2>
      <p class="hint">你将执 <b>p1</b>，创建后把对局 ID 发给对手即可开始</p>
      <input v-model="myName" placeholder="你的名字（可选）" maxlength="12" />
      <button class="btn primary" :disabled="busy" @click="onCreate">创建对局</button>
    </div>

    <div class="divider">或</div>

    <div class="card join">
      <h2>加入对局</h2>
      <p class="hint">输入对手发来的对局 ID</p>
      <input v-model="joinId" placeholder="对局 ID，如 m1" />
      <div class="identity">
        <label><input v-model="joinAs" type="radio" value="p2" /> 我是对手（p2）</label>
        <label><input v-model="joinAs" type="radio" value="p1" /> 创建者重连（p1）</label>
      </div>
      <button class="btn" :disabled="busy || !joinId.trim()" @click="onJoin">加入对局</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="rules">
      <h3>规则速览</h3>
      <ul>
        <li>每回合双方各出 <b>一个</b> 动作，同时结算</li>
        <li>普通盾免费可挡单刀；双刀 / 炸弹可穿透普通盾</li>
        <li>反弹盾反弹刀与双刀（攻击者反受伤害），并挡下炸弹</li>
        <li>生命值 1，受到伤害即死亡；双方同时死亡为平局</li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.home {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 20px;
  align-items: start;
  margin-top: 24px;
}

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card h2 {
  margin: 0;
  font-size: 18px;
}

.hint {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.divider {
  align-self: center;
  color: var(--muted);
  padding-top: 60px;
}

input[type='text'],
input:not([type]) {
  background: var(--panel-2);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 15px;
  outline: none;
}

input:focus {
  border-color: var(--blue);
}

.identity {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--muted);
}

.rules {
  grid-column: 1 / -1;
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed var(--border);
  border-radius: 12px;
  padding: 14px 20px;
}

.rules h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--muted);
}

.rules ul {
  margin: 0;
  padding-left: 18px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.9;
}

.error {
  grid-column: 1 / -1;
  margin: 0;
}

@media (max-width: 720px) {
  .home {
    grid-template-columns: 1fr;
  }

  .divider {
    padding-top: 0;
    text-align: center;
  }
}
</style>
