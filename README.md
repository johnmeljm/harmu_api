# Harmu API — 回合制双人对决服务端

2 名玩家互相对抗的回合制游戏服务端：双方每回合各自提交**一个**动作，服务端同时结算并返回事件日志。生命值默认 1，受到伤害即死亡。

## 快速开始

```bash
uv run harmu-api --host 127.0.0.1 --port 8000
```

启动后可访问：

- **Web 前端（两人浏览器对战）**：http://127.0.0.1:8000/
- 交互式 API 文档（Swagger UI，可直接调试）：http://127.0.0.1:8000/docs
- Reoc 文档：http://127.0.0.1:8000/redoc
- OpenAPI 规范：http://127.0.0.1:8000/openapi.json

> 首次运行前需先构建前端：`cd web && npm install && npm run build`（FastAPI 检测到 `web/dist` 后自动托管）。

## 前端（web/，Vue 3 + Vite + TypeScript）

**生产模式（单进程，API 与页面同端口）：**

```bash
cd web && npm run build      # 类型检查 + 构建到 web/dist
uv run harmu-api --host 0.0.0.0 --port 8000
# 浏览器打开 http://<服务器IP>:8000 ，两个玩家各自创建/加入对局即可
```

**开发模式（热更新，需同时启动后端）：**

```bash
uv run harmu-api --port 8000           # 终端 1：后端
cd web && npm run dev                  # 终端 2：Vite 开发服务器（/matches、/health 自动代理到 8000）
# 浏览器打开 http://127.0.0.1:5173
```

> 若所在环境配置了 HTTP 代理，curl 访问本地端口需加 `--noproxy '*'` 或先 `export no_proxy=127.0.0.1`。

前端要点：

- 玩家身份与对局 ID 存于 `sessionStorage`，同一浏览器开两个标签页即可双人对战（互不干扰），刷新/断线后自动恢复对局；
- 回合等待通过轮询 `GET /matches/{id}`（1.5s）实现，`submitted` 字段用于展示"对手已出招"提示；
- 结算弹窗与对局记录直接展示服务端返回的中文 `events[].detail`；
- 组件结构：`App.vue`（入口）→ `views/HomeView.vue`（创建/加入）+ `views/GameView.vue`（对局主界面）→ `components/ResourcePanel.vue`（资源面板）、`components/RoundModal.vue`（结算弹窗）；游戏状态与 API 封装在 `src/composables/game.ts`、`src/api.ts`。

## 双人对战：两个玩家如何进入游戏

每个玩家在自己的终端运行一个交互式客户端（菜单选动作，自动轮询对手、展示结算日志）：

**终端 0（任一玩家或第三方，先启动服务器）：**

```bash
uv run harmu-api --host 127.0.0.1 --port 8000
```

**玩家 1（创建对局，执 `p1`）：**

```bash
uv run harmu-player --create
# → 对局已创建，ID：m1
# → 请把该 ID 发给对手，对方执行：uv run harmu-player --match m1
```

**玩家 2（加入对局，执 `p2`）：**

```bash
uv run harmu-player --match m1
```

之后双方每回合从 10 个动作的编号菜单中选择一个，先出招者显示"等待对手…"，双方交齐后两端都会打印本回合结算日志，直至一方死亡或平局。

说明：

- 两名玩家可在**同一台机器**的两个终端，也可在**不同机器**——后者在创建/加入命令中加 `--server http://<服务器IP>:8000`，且服务器需以 `--host 0.0.0.0` 启动。
- 断线/误退不会丢失对局（状态保存在服务器），重新执行加入命令即可续玩：`uv run harmu-player --match m1 --player p1`。
- 不用客户端也可直接调 API 对战：玩家 1 的所有请求都带 `"player_id": "p1"`，玩家 2 都带 `"player_id": "p2"`（详见下文接口说明）。

## 核心概念

- **对局（match）**：固定 2 名玩家，由 `match_id` 标识，内存存储。
- **回合**：每回合双方各提交一个动作（先提交者收到 `waiting_opponent`）；两人交齐后服务端**立即自动结算**，后提交者的响应中直接携带结算结果。
- **资源包**：`hp`（生命值，固定 1，不支持多生命值）、`money`（钱）、`knives`（刀）、`gunpowder`（火药）、`bombs`（炸弹）、`reflect_shields`（反弹盾）。
- **胜负**：一方生命值归零即死亡，对局结束；双方同时死亡判平局（`winner: "draw"`）。

## 动作代码表

`action` 字段的全部合法取值（每回合只能选 **一个**）：

| action 值 | 中文名 | 类别 | 前置条件 | 效果 |
|---|---|---|---|---|
| `earn_money` | 赚钱 | 生产 | 无 | 钱 +1 |
| `buy_knife` | 买刀 | 生产 | 钱 ≥ 1 | 钱 -1，刀 +1 |
| `buy_gunpowder` | 买火药 | 生产 | 钱 ≥ 2 | 钱 -2，火药 +1 |
| `craft_bomb` | 制作炸弹 | 生产 | 火药 ≥ 1 | 火药 -1，炸弹 +1 |
| `craft_reflect_shield` | 制作反弹盾 | 生产 | 无 | 反弹盾 +1 |
| `use_knife` | 使用刀 | 攻击 | 刀 ≥ 1 | 刀 -1；按结算表造成伤害（须带 `target_id`） |
| `use_double_knife` | 使用双刀 | 攻击 | 刀 ≥ 2 | 刀 -2；穿透普通盾（须带 `target_id`） |
| `use_bomb` | 使用炸弹 | 攻击 | 炸弹 ≥ 1 | 炸弹 -1；穿透普通盾（须带 `target_id`） |
| `use_normal_shield` | 使用普通盾 | 防御 | 无 | 挡下单刀；数量不限、无消耗 |
| `use_reflect_shield` | 使用反弹盾 | 防御 | 反弹盾 ≥ 1 | 反弹盾 -1（使用即消耗，无论对方是否攻击） |

## 攻击结算表

| 攻击 \ 目标本回合动作 | 无防御（生产/攻击） | 普通盾 | 反弹盾 |
|---|---|---|---|
| 使用刀 | 目标 HP -1 | **被挡下**（双方无伤，回合结束） | **反弹**：攻击者 HP -1 |
| 使用双刀 | 目标 HP -1 | **穿透**：目标 HP -1 | **反弹**：攻击者 HP -1 |
| 使用炸弹 | 目标 HP -1 | **穿透**：目标 HP -1 | **被挡下**（双方无伤） |

无论结果如何，攻击方武器消耗照常扣除。

## 接口说明

### GET /health

健康检查。响应：`{"status": "ok"}`

### POST /matches — 创建对局

请求体（全部可省略，省略时默认玩家 `p1`/`p2`、初始资源全 0、生命值 1）：

```json
{
  "players": [
    {"player_id": "alice", "name": "爱丽丝"},
    {"player_id": "bob", "name": "鲍勃"}
  ],
  "initial_resources": {"money": 2, "knives": 1}
}
```

- `players`：必须恰好 2 人，`player_id` 不可重复；`name` 缺省为 `玩家1`/`玩家2`。
- `initial_resources`：两名玩家的相同初始资源（便于测试）。不可包含 `hp`（暂不支持多生命值），不可为负。

响应（对局状态视图）：

```json
{
  "match_id": "m1",
  "round_number": 1,
  "status": "in_progress",
  "winner": null,
  "players": {
    "p1": {
      "player_id": "p1", "name": "玩家1", "alive": true,
      "resources": {"hp": 1, "money": 0, "knives": 0, "gunpowder": 0, "bombs": 0, "reflect_shields": 0}
    },
    "p2": { "...": "同上" }
  },
  "submitted": []
}
```

### GET /matches — 对局列表

响应：`{"matches": [对局状态视图, ...]}`

### GET /matches/{match_id} — 查询对局状态

响应为上述对局状态视图。字段说明：

- `round_number`：当前回合数（对局结束后停留在最后一回合）。
- `status`：`in_progress` / `ended`。
- `winner`：获胜玩家 ID、`"draw"`（平局）或 `null`（未结束）。
- `submitted`：本回合已提交动作的玩家 ID 列表（用于轮询对手是否交卷）。
- `players.*.alive`：是否存活。

### POST /matches/{match_id}/actions — 提交动作（核心接口）

请求体：

```json
{"player_id": "p1", "action": "use_knife", "target_id": "p2"}
```

- 攻击类动作**必须**带 `target_id`，且只能指向对方玩家；
- 非攻击类动作**不能**带 `target_id`；
- 同一玩家每回合只能提交一次；资源前置条件在提交时校验。

响应一（对方未提交，等待中）：

```json
{
  "status": "waiting_opponent",
  "match": { "...": "对局状态视图" }
}
```

响应二（双方交齐，本回合已结算）：

```json
{
  "status": "settled",
  "round": {
    "round_number": 3,
    "actions": {
      "p1": {"action": "use_knife", "target_id": "p2"},
      "p2": {"action": "use_reflect_shield", "target_id": null}
    },
    "events": [
      {"type": "defense",  "player": "p2", "action": "use_reflect_shield", "changes": {"reflect_shields": -1}, "detail": "p2 使用反弹盾：反弹盾数量-1"},
      {"type": "attack",   "player": "p1", "target": "p2", "action": "use_knife", "outcome": "reflected", "damage_to": "p1", "changes": {"knives": -1}, "detail": "p2 使用反弹盾反弹了 p1 的刀，p1 生命值-1，p2 生命值不变"},
      {"type": "death",    "player": "p1", "detail": "p1 受到伤害，生命值降为 0，死亡"},
      {"type": "match_end", "winner": "p2", "detail": "对局结束，p2 获胜"}
    ],
    "players": {"p1": {"alive": false, "resources": {"...": "..."}}, "p2": {"...": "..."}},
    "deaths": ["p1"],
    "match_status": "ended",
    "winner": "p2"
  },
  "match": { "...": "对局状态视图" }
}
```

`events` 事件类型（每条都带中文 `detail`，可直接用于客户端展示）：

| type | 含义 | 关键字段 |
|---|---|---|
| `production` | 生产结算 | `changes`（资源变化） |
| `defense` | 防御动作（含反弹盾消耗） | `changes` |
| `attack` | 攻击结算 | `outcome`（`hit`/`blocked`/`pierced`/`reflected`）、`damage_to`（受伤害方）、`changes`（武器消耗） |
| `death` | 死亡判定 | `player` |
| `match_end` | 对局结束 | `winner`（玩家 ID 或 `"draw"`） |

### GET /matches/{match_id}/history — 历史回合

响应：`{"match_id": "m1", "rounds": [回合结算结果, ...]}`，按回合顺序排列，结构同上表的 `round` 字段。

## 错误码

| HTTP 状态码 | 场景 | 响应体 |
|---|---|---|
| 400 | 非法动作：未知玩家/目标、攻击自己、攻击类缺 `target_id`、非攻击类带 `target_id`、非法初始资源 | `{"error": "中文描述"}` |
| 404 | 对局不存在 | `{"error": "对局不存在：m99"}` |
| 409 | 状态冲突：本回合重复提交、对局已结束仍提交 | `{"error": "玩家 p1 本回合已提交过动作"}` |
| 422 | 资源不足（前置条件不满足），或请求字段格式错误 | 前者为 `{"error": "动作「买刀」前置条件不满足：需要 钱>=1（当前 0）"}`；字段校验失败为 FastAPI 标准 `detail` 格式 |

## 完整对局示例（curl）

场景：p1 攒钱买刀进攻，p2 预制反弹盾反杀。以下省略响应中的 `match` 字段。

```bash
# 0. 创建对局
curl -s -X POST http://127.0.0.1:8000/matches \
  -H 'Content-Type: application/json' -d '{}'
# → {"match_id": "m1", "round_number": 1, "status": "in_progress", ...}

# 回合 1：p1 赚钱（先提交，等待对手）
curl -s -X POST http://127.0.0.1:8000/matches/m1/actions \
  -H 'Content-Type: application/json' \
  -d '{"player_id": "p1", "action": "earn_money"}'
# → {"status": "waiting_opponent", ...}

# 回合 1：p2 制作反弹盾（触发结算）
curl -s -X POST http://127.0.0.1:8000/matches/m1/actions \
  -H 'Content-Type: application/json' \
  -d '{"player_id": "p2", "action": "craft_reflect_shield"}'
# → {"status": "settled", "round": {"round_number": 1, "events": [两条 production], ...}}

# 回合 2：p1 买刀
curl -s -X POST http://127.0.0.1:8000/matches/m1/actions \
  -H 'Content-Type: application/json' \
  -d '{"player_id": "p1", "action": "buy_knife"}'

# 回合 2：p2 赚钱
curl -s -X POST http://127.0.0.1:8000/matches/m1/actions \
  -H 'Content-Type: application/json' \
  -d '{"player_id": "p2", "action": "earn_money"}'

# 回合 3：p1 用刀攻击 p2（攻击类必须带 target_id）
curl -s -X POST http://127.0.0.1:8000/matches/m1/actions \
  -H 'Content-Type: application/json' \
  -d '{"player_id": "p1", "action": "use_knife", "target_id": "p2"}'

# 回合 3：p2 举反弹盾 → 刀被反弹，p1 死亡，p2 获胜
curl -s -X POST http://127.0.0.1:8000/matches/m1/actions \
  -H 'Content-Type: application/json' \
  -d '{"player_id": "p2", "action": "use_reflect_shield"}'
# → {"status": "settled",
#    "round": {"events": [defense, attack(outcome=reflected, damage_to=p1), death(p1), match_end(winner=p2)], ...},
#    ...}

# 查看最终状态与完整历史
curl -s http://127.0.0.1:8000/matches/m1
curl -s http://127.0.0.1:8000/matches/m1/history
```

## 开发

```bash
uv run pytest   # 运行全部测试（65 个用例，覆盖所有结算分支）
```

模块结构：`models`（数据模型）→ `rules`（动作定义/校验）→ `settlement`（结算引擎）→ `match`（对局状态机）→ `service`（对局注册）→ `api`/`server`（HTTP 层）。
