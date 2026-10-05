from __future__ import annotations

import json
import os
import re
from html import unescape
from time import monotonic
from threading import Lock
from typing import Literal
from collections.abc import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from pydantic import BaseModel, Field, ValidationError

from app.services.analysis_provider import (
    AnalysisProviderConfigurationError,
    StructuredOutputMalformedError,
    call_openai_responses,
)


class Equipment(BaseModel):
    id: str
    name: str
    exercises: list[str]
    search_query: str
    safety_note: str


CATALOG: tuple[Equipment, ...] = (
    Equipment(id="lat_pulldown", name="랫풀다운 머신", exercises=["랫풀다운"], search_query="랫풀다운 머신 사용법 자세", safety_note="시트를 고정하고 반동 없이 당겨요."),
    Equipment(id="leg_press", name="레그프레스 머신", exercises=["레그프레스"], search_query="레그프레스 머신 사용법 발 위치", safety_note="무릎을 완전히 잠그지 않고 발판을 밀어요."),
    Equipment(id="chest_press", name="체스트 프레스 머신", exercises=["체스트 프레스 머신"], search_query="체스트 프레스 머신 사용법 자세", safety_note="손잡이를 가슴 높이에 맞추고 어깨를 과하게 들지 않아요."),
    Equipment(id="seated_row", name="시티드 로우 머신", exercises=["시티드 로우", "케이블 로우", "체스트 서포티드 로우"], search_query="시티드 로우 머신 사용법 자세", safety_note="몸통을 크게 흔들지 말고 당겨요."),
    Equipment(id="cable_machine", name="케이블 머신", exercises=["케이블 하이 로우", "케이블 컬", "트라이셉스 프레스다운", "팔로프 프레스"], search_query="케이블 머신 높이 조절 사용법", safety_note="핀과 손잡이 체결을 먼저 확인해요."),
    Equipment(id="smith_machine", name="스미스 머신", exercises=["스쿼트", "벤치프레스"], search_query="스미스 머신 안전 걸쇠 사용법", safety_note="바의 잠금 방향과 안전 스토퍼를 먼저 확인해요."),
    Equipment(id="squat_rack", name="스쿼트 랙", exercises=["스쿼트", "벤치프레스"], search_query="스쿼트 랙 세이프티바 설정 사용법", safety_note="안전바 높이를 먼저 맞추고 무게를 올려요."),
    Equipment(id="dumbbell", name="덤벨", exercises=["덤벨 숄더프레스", "고블릿 스쿼트", "원암 덤벨 로우"], search_query="덤벨 운동 기본 자세 사용법", safety_note="처음에는 가벼운 무게로 움직임을 익혀요."),
    Equipment(id="treadmill", name="트레드밀", exercises=[], search_query="트레드밀 런닝머신 안전 사용법", safety_note="안전 클립과 정지 버튼 위치를 먼저 확인해요."),
    Equipment(id="leg_curl", name="레그 컬 머신", exercises=["레그 컬"], search_query="레그 컬 머신 사용법 자세", safety_note="관절 축과 기구 축을 맞추고 천천히 움직여요."),
    Equipment(id="leg_extension", name="레그 익스텐션 머신", exercises=["레그 익스텐션"], search_query="레그 익스텐션 머신 사용법", safety_note="좌석과 패드를 먼저 조절하고 가벼운 무게로 시작해요."),
    Equipment(id="hack_squat", name="핵 스쿼트 머신", exercises=["핵 스쿼트"], search_query="핵 스쿼트 머신 안전장치 사용법", safety_note="안전장치와 잠금 위치를 먼저 확인해요."),
    Equipment(id="pec_deck", name="펙덱 플라이 머신", exercises=["펙덱 플라이", "리버스 펙덱"], search_query="펙덱 플라이 머신 사용법", safety_note="좌석과 손잡이 위치를 조절하고 가벼운 무게로 시작해요."),
    Equipment(id="shoulder_press", name="숄더 프레스 머신", exercises=["숄더 프레스 머신"], search_query="숄더 프레스 머신 사용법", safety_note="기구 설명판에 맞춰 좌석을 조절하고 통증 없는 범위에서 움직여요."),
    Equipment(id="assisted_pullup", name="어시스트 풀업·딥스 머신", exercises=["어시스트 풀업", "어시스트 딥스"], search_query="어시스트 풀업 딥스 머신 사용법 보조 무게", safety_note="보조 무게의 방향과 발판의 움직임을 직원에게 먼저 확인해요."),
    Equipment(id="hip_abduction", name="힙 어브덕션 머신", exercises=["힙 어브덕션"], search_query="힙 어브덕션 머신 사용법", safety_note="좌석과 패드를 조절하고 가벼운 무게로 시작해요."),
    Equipment(id="stationary_bike", name="실내 사이클", exercises=[], search_query="실내 사이클 안장 높이 사용법", safety_note="안장과 페달을 조절하고 낮은 저항에서 시작해요."),
    Equipment(id="rowing_machine", name="로잉 머신", exercises=[], search_query="로잉 머신 기본 사용법", safety_note="발판과 스트랩을 확인하고 낮은 강도로 움직임을 익혀요."),
)
EQUIPMENT_BY_ID = {item.id: item for item in CATALOG}


class EquipmentIdentification(BaseModel):
    equipment_id: str | None
    confidence: Literal["high", "medium", "low", "none"]
    visible_evidence: list[str] = Field(max_length=3)
    needs_confirmation: Literal[True] = True
    cleanup_pending: bool = False


class VideoLink(BaseModel):
    video_id: str
    title: str
    channel_title: str
    url: str


class EquipmentGuide(BaseModel):
    equipment_id: str
    name: str
    exercises: list[str]
    safety_note: str
    search_url: str
    source: Literal["youtube_api", "search_link"]
    videos: list[VideoLink]


class EquipmentProviderDisabledError(RuntimeError):
    pass


class OpenAIEquipmentProvider:
    def __init__(self, *, api_key: str, model: str, responses_call: Callable[[dict[str, object], str], str] | None = None) -> None:
        self._api_key = api_key
        self._model = model
        self._responses_call = responses_call or (lambda payload, key: call_openai_responses(payload, key, timeout=22))

    def identify(self, image_reference: str) -> EquipmentIdentification:
        payload = {
            "model": self._model,
            "store": False,
            "max_output_tokens": 350,
            "input": [{"role": "user", "content": [
                {"type": "input_text", "text": (
                    "Identify the main gym equipment visible in this photo. Choose only one catalog ID or unknown. "
                    "Do not identify people, infer health, evaluate form, or guess a brand/model. "
                    "If the equipment is unclear, multiple machines overlap, or it is not in the catalog, choose unknown. "
                    "Visible evidence must be short Korean descriptions of machine parts only. "
                    f"Catalog: {', '.join(f'{item.id}={item.name}' for item in CATALOG)}."
                )},
                {"type": "input_image", "image_url": image_reference, "detail": "low"},
            ]}],
            "text": {"format": {"type": "json_schema", "name": "equipment_identification", "strict": True, "schema": {
                "type": "object", "additionalProperties": False,
                "required": ["equipment_id", "confidence", "visible_evidence"],
                "properties": {
                    "equipment_id": {"type": "string", "enum": [*EQUIPMENT_BY_ID, "unknown"]},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low", "none"]},
                    "visible_evidence": {"type": "array", "maxItems": 3, "items": {"type": "string"}},
                },
            }}},
        }
        raw = self._responses_call(payload, self._api_key)
        try:
            data = json.loads(raw)
            equipment_id = data["equipment_id"]
            confidence = data["confidence"]
            evidence = data["visible_evidence"]
            if equipment_id not in {*EQUIPMENT_BY_ID, "unknown"} or confidence not in {"high", "medium", "low", "none"}:
                raise ValueError("out_of_catalog")
            if not isinstance(evidence, list) or len(evidence) > 3 or any(not isinstance(value, str) or len(value) > 120 for value in evidence):
                raise ValueError("invalid_evidence")
            return EquipmentIdentification(
                equipment_id=None if equipment_id == "unknown" else equipment_id,
                confidence="none" if equipment_id == "unknown" else confidence,
                visible_evidence=evidence,
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise StructuredOutputMalformedError("equipment_output_malformed") from exc


def get_equipment_provider(environ: Mapping[str, str] | None = None) -> OpenAIEquipmentProvider:
    env = environ if environ is not None else os.environ
    provider = (env.get("EQUIPMENT_AI_PROVIDER") or "disabled").strip().lower()
    if provider == "disabled":
        raise EquipmentProviderDisabledError("equipment_ai_disabled")
    if provider != "openai":
        raise AnalysisProviderConfigurationError("equipment_provider_unknown")
    if env.get("EQUIPMENT_RETENTION_VERIFIED") != "true":
        raise AnalysisProviderConfigurationError("equipment_retention_not_verified")
    key = env.get("AI_PROVIDER_API_KEY")
    if not key:
        raise AnalysisProviderConfigurationError("openai_api_key_missing")
    model = env.get("AI_MODEL_VISION") or "gpt-5.4-mini"
    if model.startswith("sk-"):
        raise AnalysisProviderConfigurationError("openai_model_invalid")
    return OpenAIEquipmentProvider(api_key=key, model=model)


_VIDEO_CACHE: dict[str, tuple[float, list[VideoLink]]] = {}
_VIDEO_LOCKS = {equipment_id: Lock() for equipment_id in EQUIPMENT_BY_ID}
_VIDEO_COOLDOWN_UNTIL = 0.0


def get_equipment_guide(equipment_id: str, *, environ: Mapping[str, str] | None = None, opener=None) -> EquipmentGuide:
    with _VIDEO_LOCKS[equipment_id]:
        return _get_equipment_guide(equipment_id, environ=environ, opener=opener)


def _get_equipment_guide(equipment_id: str, *, environ: Mapping[str, str] | None = None, opener=None) -> EquipmentGuide:
    global _VIDEO_COOLDOWN_UNTIL
    item = EQUIPMENT_BY_ID[equipment_id]
    search_url = "https://www.youtube.com/results?" + urlencode({"search_query": item.search_query})
    env = environ if environ is not None else os.environ
    key = env.get("YOUTUBE_API_KEY")
    videos: list[VideoLink] = []
    cached = _VIDEO_CACHE.get(equipment_id) if opener is None else None
    if key and cached and monotonic() < cached[0]:
        videos = cached[1]
    elif key and (opener is not None or monotonic() >= _VIDEO_COOLDOWN_UNTIL):
        query = urlencode({
            "part": "snippet", "type": "video", "maxResults": 3, "q": item.search_query,
            "relevanceLanguage": "ko", "regionCode": "KR", "safeSearch": "strict", "key": key,
        })
        try:
            with (opener or urlopen)("https://www.googleapis.com/youtube/v3/search?" + query, timeout=6) as response:
                data = json.load(response)
            if not isinstance(data, dict) or not isinstance(data.get("items"), list):
                raise ValueError("youtube_response_invalid")
            for result in data["items"][:3]:
                if not isinstance(result, dict) or not isinstance(result.get("id"), dict) or not isinstance(result.get("snippet"), dict):
                    continue
                video_id = result.get("id", {}).get("videoId")
                snippet = result.get("snippet", {})
                if isinstance(video_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
                    videos.append(VideoLink(
                        video_id=video_id,
                        title=unescape(str(snippet.get("title", "")))[:160],
                        channel_title=unescape(str(snippet.get("channelTitle", "")))[:100],
                        url=f"https://www.youtube.com/watch?v={video_id}",
                    ))
        except HTTPError as exc:
            videos = []
            if opener is None and exc.code in {403, 429}:
                _VIDEO_COOLDOWN_UNTIL = monotonic() + 3600
        except (URLError, TimeoutError, OSError, ValueError, TypeError, KeyError, ValidationError):
            videos = []
        if opener is None:
            _VIDEO_CACHE[equipment_id] = (monotonic() + (3600 if videos else 300), videos)
    return EquipmentGuide(
        equipment_id=item.id, name=item.name, exercises=item.exercises,
        safety_note=item.safety_note, search_url=search_url,
        source="youtube_api" if videos else "search_link", videos=videos,
    )
