<script setup lang="ts">
import { computed, onMounted } from 'vue'
import HomeView from './views/HomeView.vue'
import GameView from './views/GameView.vue'
import { game, resumeIfActive } from './composables/game'

onMounted(() => resumeIfActive())

const inGame = computed(() => !!game.matchId)
</script>

<template>
  <header class="topbar">
    <h1>Harmu 对决</h1>
    <span class="tagline">回合制双人对抗 · 每回合一招 · 生命值 1 · 受伤即死</span>
  </header>
  <main class="content">
    <HomeView v-if="!inGame" />
    <GameView v-else :key="`${game.matchId}:${game.myId}`" />
  </main>
</template>
