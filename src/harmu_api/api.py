"""HTTP API 层（FastAPI）。"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .models import ActionType, GameError, ResourcePack
from .service import MatchService

WEB_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"


class PlayerIn(BaseModel):
    player_id: str | None = None
    name: str | None = None


class CreateMatchRequest(BaseModel):
    players: list[PlayerIn] = Field(
        default_factory=lambda: [PlayerIn(), PlayerIn()]
    )
    initial_resources: dict[str, int] | None = None


class SubmitActionRequest(BaseModel):
    player_id: str
    action: ActionType
    target_id: str | None = None


def _initial_resources(values: dict[str, int] | None) -> ResourcePack:
    if not values:
        return ResourcePack()
    valid = set(ResourcePack.__dataclass_fields__)
    unknown = set(values) - valid
    if unknown:
        raise GameError(f"未知资源字段：{', '.join(sorted(unknown))}")
    if "hp" in values:
        raise GameError("生命值固定为 1，暂不支持多生命值")
    if any(v < 0 for v in values.values()):
        raise GameError("初始资源不能为负数")
    return ResourcePack(**values)


def create_app(service: MatchService | None = None) -> FastAPI:
    app = FastAPI(
        title="Harmu API",
        version="0.1.0",
        description="回合制双人对决：服务端回合结算规则。",
    )
    svc = service or MatchService()

    @app.exception_handler(GameError)
    async def game_error_handler(request, exc: GameError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": str(exc)})

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/matches")
    def create_match(req: CreateMatchRequest) -> dict:
        specs = [
            (p.player_id or f"p{i + 1}", p.name or f"玩家{i + 1}")
            for i, p in enumerate(req.players)
        ]
        match = svc.create_match(specs, _initial_resources(req.initial_resources))
        return match.view()

    @app.get("/matches")
    def list_matches() -> dict:
        return {"matches": svc.list_matches()}

    @app.get("/matches/{match_id}")
    def get_match(match_id: str) -> dict:
        return svc.get_match_view(match_id)

    @app.post("/matches/{match_id}/actions")
    def submit_action(match_id: str, req: SubmitActionRequest) -> dict:
        return svc.submit_action(match_id, req.player_id, req.action, req.target_id)

    @app.get("/matches/{match_id}/history")
    def match_history(match_id: str) -> dict:
        return {"match_id": match_id, "rounds": svc.match_history(match_id)}

    if WEB_DIST.is_dir():
        app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")

    return app


app = create_app()
