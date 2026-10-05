import { reactive } from 'vue'
import { api, ApiError } from '../api'
import { findAction } from '../actions'
import type { MatchView, RoundResult } from '../types'

const MATCH_KEY = 'harmu:matchId'
const PLAYER_KEY = 'harmu:myId'

interface GameState {
  matchId: string
  myId: string
  myName: string
  view: MatchView | null
  rounds: RoundResult[]
  shownRounds: number
  pendingResult: RoundResult | null
  submitting: boolean
  error: string
}

export const game = reactive<GameState>({
  matchId: '',
  myId: '',
  myName: '',
  view: null,
  rounds: [],
  shownRounds: 0,
  pendingResult: null,
  submitting: false,
  error: '',
})

function enter(matchId: string, myId: string, myName: string): void {
  sessionStorage.setItem(MATCH_KEY, matchId)
  sessionStorage.setItem(PLAYER_KEY, myId)
  game.matchId = matchId
  game.myId = myId
  game.myName = myName
  game.view = null
  game.rounds = []
  game.shownRounds = 0
  game.pendingResult = null
  game.submitting = false
  game.error = ''
}

export async function createMatch(name: string): Promise<void> {
  const myName = name.trim() || '玩家1'
  const view = await api.createMatch(myName)
  enter(view.match_id, 'p1', myName)
}

export function joinMatch(matchId: string, myId: string): void {
  const id = matchId.trim()
  if (!id) return
  enter(id, myId, myId === 'p1' ? '玩家1' : '玩家2')
}

export function resumeIfActive(): void {
  const matchId = sessionStorage.getItem(MATCH_KEY)
  const myId = sessionStorage.getItem(PLAYER_KEY)
  if (matchId && myId) {
    joinMatch(matchId, myId)
  }
}

export async function refresh(initial = false): Promise<void> {
  if (!game.matchId) return
  try {
    const view = await api.getMatch(game.matchId)
    game.view = view
    const settled = view.status === 'ended' ? view.round_number : view.round_number - 1
    if (settled > game.shownRounds) {
      const history = await api.history(game.matchId)
      const fresh = history.rounds.filter((r) => r.round_number > game.shownRounds)
      game.rounds.push(...fresh)
      game.shownRounds = settled
      if (!initial && fresh.length > 0) {
        game.pendingResult = fresh[fresh.length - 1]
      }
    }
    game.error = ''
  } catch (err) {
    game.error = err instanceof ApiError ? err.message : '网络异常，稍后自动重试'
  }
}

export async function submit(actionId: string): Promise<void> {
  if (!game.view || game.submitting) return
  const def = findAction(actionId)
  if (!def) return
  const opponentId = Object.keys(game.view.players).find((id) => id !== game.myId) ?? ''
  game.submitting = true
  try {
    const resp = await api.submit(
      game.matchId,
      game.myId,
      actionId,
      def.category === 'attack' ? opponentId : null,
    )
    game.view = resp.match
    game.error = ''
    await refresh()
  } catch (err) {
    game.error = err instanceof ApiError ? err.message : '提交失败，请重试'
  } finally {
    game.submitting = false
  }
}

export function dismissResult(): void {
  game.pendingResult = null
}

export function leaveGame(): void {
  sessionStorage.removeItem(MATCH_KEY)
  sessionStorage.removeItem(PLAYER_KEY)
  game.matchId = ''
  game.myId = ''
  game.myName = ''
  game.view = null
  game.rounds = []
  game.shownRounds = 0
  game.pendingResult = null
  game.submitting = false
  game.error = ''
}
