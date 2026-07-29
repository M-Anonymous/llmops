"""Agent 运行时 LLM 参数解析。"""

from __future__ import annotations

from typing import Any

PRESET_CREATIVE = "creative"
PRESET_BALANCED = "balanced"
PRESET_PRECISE = "precise"
PRESET_CUSTOM = "custom"

RUNTIME_PRESETS: dict[str, dict[str, float]] = {
    PRESET_CREATIVE: {"temperature": 1.0, "top_p": 0.95},
    PRESET_BALANCED: {"temperature": 0.7, "top_p": 1.0},
    PRESET_PRECISE: {"temperature": 0.2, "top_p": 0.9},
}

DEFAULT_RUNTIME_CONFIG: dict[str, Any] = {"preset": PRESET_BALANCED}


def resolve_runtime_config(config: dict[str, Any] | None) -> dict[str, Any]:
    """将 Agent.runtime_config 解析为 ChatOpenAI 可用的参数字典。"""
    raw = dict(config or DEFAULT_RUNTIME_CONFIG)
    preset = raw.get("preset") or PRESET_BALANCED

    if preset == PRESET_CUSTOM:
        params = dict(RUNTIME_PRESETS[PRESET_BALANCED])
        if raw.get("temperature") is not None:
            params["temperature"] = float(raw["temperature"])
        if raw.get("top_p") is not None:
            params["top_p"] = float(raw["top_p"])
        if raw.get("max_tokens") is not None:
            params["max_tokens"] = int(raw["max_tokens"])
        return params

    if preset in RUNTIME_PRESETS:
        return dict(RUNTIME_PRESETS[preset])

    return dict(RUNTIME_PRESETS[PRESET_BALANCED])
