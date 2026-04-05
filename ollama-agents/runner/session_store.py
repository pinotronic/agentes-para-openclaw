from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_MAX_SESSION_CHARS = 24_000
DEFAULT_PRESERVE_TAIL_CHARS = 8_000


@dataclass
class AgentSession:
    version: int
    agent_id: str
    model: str
    workspace: str
    prompt: str
    transcript: str
    final_output: str
    tool_rounds: int
    created_at: float
    updated_at: float


def default_session_path(agent_id: str, workspace: Path | None) -> Path:
    base = workspace if workspace is not None else Path.cwd()
    return base / ".ollama-agent-sessions" / f"{agent_id}.json"


def load_session(path: Path) -> AgentSession:
    data = json.loads(path.read_text(encoding="utf-8"))
    return AgentSession(
        version=int(data.get("version", 1)),
        agent_id=str(data.get("agent_id", "")),
        model=str(data.get("model", "")),
        workspace=str(data.get("workspace", "")),
        prompt=str(data.get("prompt", "")),
        transcript=str(data.get("transcript", "")),
        final_output=str(data.get("final_output", "")),
        tool_rounds=int(data.get("tool_rounds", 0)),
        created_at=float(data.get("created_at", time.time())),
        updated_at=float(data.get("updated_at", time.time())),
    )


def save_session(path: Path, session: AgentSession) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(session), ensure_ascii=False, indent=2), encoding="utf-8")


def compact_transcript(
    transcript: str,
    *,
    max_chars: int = DEFAULT_MAX_SESSION_CHARS,
    preserve_tail_chars: int = DEFAULT_PRESERVE_TAIL_CHARS,
) -> str:
    if len(transcript) <= max_chars:
        return transcript

    preserve_tail_chars = min(max(preserve_tail_chars, 1), max_chars)
    split_index = len(transcript) - preserve_tail_chars
    markers = ("<ASSISTANT>", "<TOOL_RESULT>")
    longest_marker = max(len(marker) for marker in markers)
    next_starts = [
        index
        for marker in markers
        if (index := transcript.find(marker, max(0, split_index - longest_marker + 1))) != -1
        and index >= split_index
    ]
    previous_starts = [
        index
        for marker in markers
        if (index := transcript.rfind(marker, 0, min(len(transcript), split_index + longest_marker))) != -1
    ]
    tail_start = min(next_starts) if next_starts else max(previous_starts, default=split_index)

    head = transcript[:tail_start]
    tail = transcript[tail_start:]
    assistant_blocks = head.count("<ASSISTANT>")
    tool_results = head.count("<TOOL_RESULT>")

    compacted_header = (
        "<COMPACTED_HISTORY>\n"
        f"Earlier transcript compacted to keep session size bounded. Removed chars: {len(head)}\n"
        f"Assistant blocks compacted: {assistant_blocks}\n"
        f"Tool results compacted: {tool_results}\n"
        "Recent transcript is preserved below.\n"
        "</COMPACTED_HISTORY>\n\n"
    )
    return compacted_header + tail.lstrip()


def new_session(agent_id: str, model: str, workspace: Path | None, prompt: str) -> AgentSession:
    now = time.time()
    return AgentSession(
        version=1,
        agent_id=agent_id,
        model=model,
        workspace=str(workspace) if workspace is not None else "",
        prompt=prompt,
        transcript="",
        final_output="",
        tool_rounds=0,
        created_at=now,
        updated_at=now,
    )