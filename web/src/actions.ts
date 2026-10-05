import type { ResourcePack } from './types'

export type Category = 'production' | 'attack' | 'defense'

export interface ActionDefUI {
  id: string
  name: string
  category: Category
  help: string
  requirement: Partial<Record<keyof ResourcePack, number>>
}

export const ACTIONS: ActionDefUI[] = [
  { id: 'earn_money', name: '赚钱', category: 'production', help: '钱 +1', requirement: {} },
  { id: 'buy_knife', name: '买刀', category: 'production', help: '钱 -1 → 刀 +1', requirement: { money: 1 } },
  { id: 'buy_gunpowder', name: '买火药', category: 'production', help: '钱 -2 → 火药 +1', requirement: { money: 2 } },
  { id: 'craft_bomb', name: '制作炸弹', category: 'production', help: '火药 -1 → 炸弹 +1', requirement: { gunpowder: 1 } },
  { id: 'craft_reflect_shield', name: '制作反弹盾', category: 'production', help: '反弹盾 +1', requirement: {} },
  {
    id: 'use_knife',
    name: '使用刀',
    category: 'attack',
    help: '刀 -1 攻击对手；可被普通盾挡下、被反弹盾反弹',
    requirement: { knives: 1 },
  },
  {
    id: 'use_double_knife',
    name: '使用双刀',
    category: 'attack',
    help: '刀 -2 攻击对手；穿透普通盾，可被反弹盾反弹',
    requirement: { knives: 2 },
  },
  {
    id: 'use_bomb',
    name: '使用炸弹',
    category: 'attack',
    help: '炸弹 -1 攻击对手；穿透普通盾，被反弹盾挡下',
    requirement: { bombs: 1 },
  },
  {
    id: 'use_normal_shield',
    name: '使用普通盾',
    category: 'defense',
    help: '无消耗；挡下单刀（对双刀 / 炸弹无效）',
    requirement: {},
  },
  {
    id: 'use_reflect_shield',
    name: '使用反弹盾',
    category: 'defense',
    help: '反弹盾 -1；反弹刀 / 双刀，挡下炸弹（使用即消耗）',
    requirement: { reflect_shields: 1 },
  },
]

export const CATEGORY_LABEL: Record<Category, string> = {
  production: '生产',
  attack: '攻击',
  defense: '防御',
}

export function findAction(id: string): ActionDefUI | undefined {
  return ACTIONS.find((a) => a.id === id)
}

export function isAffordable(action: ActionDefUI, resources: ResourcePack | undefined): boolean {
  if (!resources) return false
  return Object.entries(action.requirement).every(
    ([key, need]) => resources[key as keyof ResourcePack] >= (need as number),
  )
}
