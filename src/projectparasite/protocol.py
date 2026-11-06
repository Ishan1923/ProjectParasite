"""Shared wire protocol for ProjectParasite.

Both the (server) and (client) import this file, so message
shapes can never drift apart.

Design notes
------------
* Every message has a literal discriminator field `t`.
* Key codes are OS-neutral names following the browser KeyboardEvent.code
  convention ("KeyA", "ArrowLeft", "ControlLeft", "Enter", ...). Each side
  keeps its own table translating to/from native keycodes.
* Mouse movement is relative (dx, dy). Scroll direction is defined as
  "positive dy = content moves down"; each receiver adapts to its own
  convention with a local config flag, not by changing messages.
* The ONLY place that knows about JSON is `encode` / `decode` at the bottom.
  To move to protobuf later, replace those two functions (and keep the
  model classes as the in-memory representation).
"""

from __future__ import annotations

import json
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

PROTOCOL_VERSION = 1


class ProtocolError(Exception):
    """Raised when incoming data is not a valid protocol message."""


class _Msg(BaseModel):
    # Reject unknown fields: this side injects keystrokes, be strict.
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- handshake

class Hello(_Msg):
    """Client -> server. First message after connecting."""
    t: Literal["hello"] = "hello"
    v: int = PROTOCOL_VERSION
    name: str = Field(min_length=1, max_length=64)
    token: str = Field(max_length=256)


class Accepted(_Msg):
    """Server -> client. Mac user approved the connection."""
    t: Literal["accepted"] = "accepted"
    v: int = PROTOCOL_VERSION


class Rejected(_Msg):
    """Server -> client. Denied (user said no, bad token, version mismatch)."""
    t: Literal["rejected"] = "rejected"
    reason: str = Field(default="", max_length=200)


# ------------------------------------------------------------------ control

class Mode(_Msg):
    """Server -> client. Remote control turned on or off."""
    t: Literal["mode"] = "mode"
    remote: bool


class ReleaseAll(_Msg):
    """Release every held key and mouse button (stuck-key protection)."""
    t: Literal["release_all"] = "release_all"


class Ping(_Msg):
    t: Literal["ping"] = "ping"
    ts: float


class Pong(_Msg):
    t: Literal["pong"] = "pong"
    ts: float


# -------------------------------------------------------------------- input

class Key(_Msg):
    """Key press/release. Modifiers are ordinary keys (ControlLeft, ...)."""
    t: Literal["key"] = "key"
    code: str = Field(min_length=1, max_length=32)
    down: bool


class MouseMove(_Msg):
    """Relative pointer movement, in pixels. Safe to coalesce."""
    t: Literal["mouse_move"] = "mouse_move"
    dx: int
    dy: int


class MouseBtn(_Msg):
    t: Literal["mouse_btn"] = "mouse_btn"
    btn: Literal["left", "right", "middle"]
    down: bool


class Scroll(_Msg):
    """Scroll amount. Positive dy = content moves down (protocol convention)."""
    t: Literal["scroll"] = "scroll"
    dx: int = 0
    dy: int = 0


Message = Annotated[
    Union[
        Hello, Accepted, Rejected,
        Mode, ReleaseAll, Ping, Pong,
        Key, MouseMove, MouseBtn, Scroll,
    ],
    Field(discriminator="t"),
]

_adapter: TypeAdapter = TypeAdapter(Message)


# -------------------------------------------------- encode/decode (wire format)

def encode(msg: _Msg) -> str:
    """Message -> wire text."""
    return msg.model_dump_json()


def decode(raw: str | bytes) -> _Msg:
    """Wire text -> validated message. Raises ProtocolError on bad input."""
    try:
        return _adapter.validate_json(raw)
    except ValidationError as e:
        raise ProtocolError(str(e)) from e