"""交互式终端客户端：两名玩家各自运行一个实例进行对战。

玩家1（创建者）:
    uv run harmu-player --create
玩家2（加入者）:
    uv run harmu-player --match <对局ID>
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .models import ActionType, RESOURCE_NAMES
from .rules import ACTION_DEFS, ACTION_NAMES


class ClientError(Exception):
    """客户端与服务器交互错误。"""


MENU_ACTIONS: list[ActionType] = [
    ActionType.EARN_MONEY,
    ActionType.BUY_KNIFE,
    ActionType.BUY_GUNPOWDER,
    ActionType.CRAFT_BOMB,
    ActionType.CRAFT_REFLECT_SHIELD,
    ActionType.USE_KNIFE,
    ActionType.USE_DOUBLE_KNIFE,
    ActionType.USE_BOMB,
    ActionType.USE_NORMAL_SHIELD,
    ActionType.USE_REFLECT_SHIELD,
]

ACTION_HELP: dict[ActionType, str] = {
    ActionType.EARN_MONEY: "钱+1",
    ActionType.BUY_KNIFE: "钱-1，刀+1",
    ActionType.BUY_GUNPOWDER: "钱-2，火药+1",
    ActionType.CRAFT_BOMB: "火药-1，炸弹+1",
    ActionType.CRAFT_REFLECT_SHIELD: "反弹盾+1",
    ActionType.USE_KNIFE: "刀-1 攻击对手；可被普通盾挡下、被反弹盾反弹",
    ActionType.USE_DOUBLE_KNIFE: "刀-2 攻击对手；穿透普通盾，可被反弹盾反弹",
    ActionType.USE_BOMB: "炸弹-1 攻击对手；穿透普通盾，被反弹盾挡下",
    ActionType.USE_NORMAL_SHIELD: "无消耗；挡下单刀（对双刀/炸弹无效）",
    ActionType.USE_REFLECT_SHIELD: "反弹盾-1；反弹刀/双刀，挡下炸弹（使用即消耗）",
}


def _opener(base_url: str) -> urllib.request.OpenerDirector:
    host = urllib.parse.urlsplit(base_url).hostname or ""
    if host in ("localhost", "127.0.0.1", "::1"):
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener()


def _request(base_url: str, method: str, path: str, body: dict | None = None) -> dict:
    url = f"{base_url.rstrip('/')}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with _opener(base_url).open(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            message = json.loads(raw).get("error", raw)
        except json.JSONDecodeError:
            message = raw
        raise ClientError(f"服务器拒绝（HTTP {exc.code}）：{message}") from None
    except urllib.error.URLError as exc:
        raise ClientError(
            f"无法连接服务器 {base_url}，请确认已启动：uv run harmu-api（{exc.reason}）"
        ) from None


def _fmt_resources(res: dict) -> str:
    return "  ".join(f"{RESOURCE_NAMES[k]}:{res[k]}" for k in res)


def _opponent_id(view: dict, my_id: str) -> str:
    return next(pid for pid in view["players"] if pid != my_id)


def _print_state(view: dict, my_id: str) -> None:
    me = view["players"][my_id]
    opp_id = _opponent_id(view, my_id)
    opp = view["players"][opp_id]
    print()
    print(f"══════ 第 {view['round_number']} 回合 ══════")
    print(f"我（{my_id}·{me['name']}）：{_fmt_resources(me['resources'])}")
    print(f"对手（{opp_id}·{opp['name']}）：{_fmt_resources(opp['resources'])}")
    if opp_id in view["submitted"]:
        print("⚠ 对手本回合已出招")


def _affordable(resources: dict, action: ActionType) -> bool:
    return all(resources[res] >= need for res, need in ACTION_DEFS[action].requirement.items())


def _choose_action(view: dict, my_id: str) -> ActionType:
    resources = view["players"][my_id]["resources"]
    print("── 可选动作 ──")
    for i, action in enumerate(MENU_ACTIONS, 1):
        mark = "" if _affordable(resources, action) else "（资源不足）"
        print(f"{i:>2}. {ACTION_NAMES[action]}：{ACTION_HELP[action]}{mark}")
    while True:
        raw = input("输入编号选择动作: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(MENU_ACTIONS):
            return MENU_ACTIONS[int(raw) - 1]
        print(f"输入无效，请输入 1-{len(MENU_ACTIONS)} 的编号")


def _submit(base_url: str, match_id: str, my_id: str, action: ActionType, opponent: str) -> dict:
    target_id = opponent if ACTION_DEFS[action].needs_target else None
    return _request(
        base_url,
        "POST",
        f"/matches/{match_id}/actions",
        {"player_id": my_id, "action": action.value, "target_id": target_id},
    )


def _wait_settled(base_url: str, match_id: str, my_round: int) -> dict:
    print("已出招，等待对手…")
    while True:
        time.sleep(1)
        view = _request(base_url, "GET", f"/matches/{match_id}")
        if view["round_number"] > my_round or view["status"] == "ended":
            rounds = _request(base_url, "GET", f"/matches/{match_id}/history")["rounds"]
            return rounds[-1]


def _print_round(result: dict) -> None:
    print()
    print(f"──── 第 {result['round_number']} 回合结算 ────")
    for event in result["events"]:
        print(f"  {event['detail']}")
    if result["match_status"] == "ended":
        if result["winner"] == "draw":
            print("★ 双方同时死亡，平局！")
        else:
            print(f"★ 对局结束，{result['winner']} 获胜！")
    else:
        print("（双方存活，进入下一回合）")


def play(base_url: str, match_id: str, my_id: str) -> None:
    while True:
        view = _request(base_url, "GET", f"/matches/{match_id}")
        if view["status"] == "ended":
            winner = view["winner"]
            print()
            print("★ 对局已结束：" + ("平局" if winner == "draw" else f"{winner} 获胜"))
            return
        my_round = view["round_number"]
        _print_state(view, my_id)
        opponent = _opponent_id(view, my_id)

        if my_id in view["submitted"]:
            result = _wait_settled(base_url, match_id, my_round)
            _print_round(result)
            continue

        while True:
            action = _choose_action(view, my_id)
            try:
                resp = _submit(base_url, match_id, my_id, action, opponent)
                break
            except ClientError as exc:
                print(f"✗ {exc}")
                view = _request(base_url, "GET", f"/matches/{match_id}")

        if resp["status"] == "settled":
            _print_round(resp["round"])
        else:
            result = _wait_settled(base_url, match_id, my_round)
            _print_round(result)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Harmu 回合制对决客户端")
    parser.add_argument("--server", default="http://127.0.0.1:8000", help="服务器地址")
    parser.add_argument("--create", action="store_true", help="创建新对局（我方为 p1）")
    parser.add_argument("--match", help="要加入的对局 ID")
    parser.add_argument("--player", help="我的玩家 ID（默认：创建者 p1 / 加入者 p2）")
    args = parser.parse_args(argv)

    try:
        if args.create:
            view = _request(args.server, "POST", "/matches", {})
            match_id = view["match_id"]
            my_id = args.player or "p1"
            print(f"对局已创建，ID：{match_id}")
            print(f"请把该 ID 发给对手，对方执行：uv run harmu-player --match {match_id}")
            play(args.server, match_id, my_id)
        elif args.match:
            my_id = args.player or "p2"
            print(f"加入对局 {args.match}，你执 {my_id}")
            play(args.server, args.match, my_id)
        else:
            parser.error("请用 --create 创建对局，或用 --match <对局ID> 加入对局")
    except (KeyboardInterrupt, EOFError):
        print("\n已退出对局（对局状态保留在服务器上，可用 --match 重新进入）")


if __name__ == "__main__":
    main()
