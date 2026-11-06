"""Run with:  uv run python test_protocol.py   (or: uv run pytest)"""

import json

from protocol import (
    Accepted, Hello, Key, Message, Mode, MouseBtn, MouseMove, Ping, Pong,
    ProtocolError, Rejected, ReleaseAll, Scroll, decode, encode,
)

SAMPLES = [
    Hello(name="popos", token="secret"),
    Accepted(),
    Rejected(reason="denied by user"),
    Mode(remote=True),
    ReleaseAll(),
    Ping(ts=1730900000.5),
    Pong(ts=1730900000.5),
    Key(code="KeyA", down=True),
    Key(code="ControlLeft", down=False),
    MouseMove(dx=5, dy=-3),
    MouseBtn(btn="left", down=True),
    Scroll(dy=-1),
]


def test_round_trip():
    for msg in SAMPLES:
        assert decode(encode(msg)) == msg


def test_wire_shape():
    assert json.loads(encode(Key(code="KeyA", down=True))) == {
        "t": "key", "code": "KeyA", "down": True,
    }
    assert json.loads(encode(MouseMove(dx=5, dy=-3))) == {
        "t": "mouse_move", "dx": 5, "dy": -3,
    }


def _rejects(raw):
    try:
        decode(raw)
    except ProtocolError:
        return True
    return False


def test_rejects_bad_input():
    assert _rejects("not json")
    assert _rejects('{"t":"nope"}')                         # unknown type
    assert _rejects('{"code":"KeyA","down":true}')          # missing t
    assert _rejects('{"t":"key","code":"KeyA"}')            # missing field
    assert _rejects('{"t":"key","code":"KeyA","down":true,"x":1}')  # extra field
    assert _rejects('{"t":"mouse_btn","btn":"side","down":true}')   # bad enum
    assert _rejects('{"t":"key","code":"","down":true}')    # empty code
    assert _rejects('{"t":"mouse_move","dx":"a","dy":1}')   # wrong type


def test_decodes_bytes():
    assert decode(b'{"t":"release_all"}') == ReleaseAll()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    print("all passed")