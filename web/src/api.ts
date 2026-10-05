import type { HistoryResponse, MatchView, RoundResult } from './types'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!resp.ok) {
    let message = `请求失败（HTTP ${resp.status}）`
    try {
      const body: unknown = await resp.json()
      if (body && typeof body === 'object' && 'error' in body) {
        message = String((body as { error: unknown }).error)
      }
    } catch {
      /* 忽略非 JSON 错误体 */
    }
    throw new ApiError(message, resp.status)
  }
  return (await resp.json()) as T
}

export const api = {
  createMatch(name: string): Promise<MatchView> {
    return request<MatchView>('/matches', {
      method: 'POST',
      body: JSON.stringify({
        players: [
          { player_id: 'p1', name },
          { player_id: 'p2' },
        ],
      }),
    })
  },

  getMatch(matchId: string): Promise<MatchView> {
    return request<MatchView>(`/matches/${matchId}`)
  },

  history(matchId: string): Promise<HistoryResponse> {
    return request<HistoryResponse>(`/matches/${matchId}/history`)
  },

  submit(
    matchId: string,
    playerId: string,
    action: string,
    targetId: string | null,
  ): Promise<{ status: string; match: MatchView; round?: RoundResult }> {
    return request(`/matches/${matchId}/actions`, {
      method: 'POST',
      body: JSON.stringify({ player_id: playerId, action, target_id: targetId }),
    })
  },
}
