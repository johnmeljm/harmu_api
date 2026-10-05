export interface ResourcePack {
  hp: number
  money: number
  knives: number
  gunpowder: number
  bombs: number
  reflect_shields: number
}

export interface PlayerView {
  player_id: string
  name: string
  alive: boolean
  resources: ResourcePack
}

export interface MatchView {
  match_id: string
  round_number: number
  status: 'in_progress' | 'ended'
  winner: string | null
  players: Record<string, PlayerView>
  submitted: string[]
}

export interface RoundEvent {
  type: 'production' | 'defense' | 'attack' | 'death' | 'match_end'
  player?: string
  target?: string
  action?: string
  outcome?: 'hit' | 'blocked' | 'pierced' | 'reflected'
  damage_to?: string | null
  changes?: Record<string, number>
  detail: string
}

export interface RoundResult {
  round_number: number
  actions: Record<string, { action: string; target_id: string | null }>
  events: RoundEvent[]
  players: Record<string, { alive: boolean; resources: ResourcePack }>
  deaths: string[]
  match_status: 'in_progress' | 'ended'
  winner: string | null
}

export interface HistoryResponse {
  match_id: string
  rounds: RoundResult[]
}
