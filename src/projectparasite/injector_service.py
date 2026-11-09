import sys, signal
from . import protocol
from .injector import Injector
from .keymap import KEYMAP

def handle_line(line, inj: Injector) -> None:

    line = line.strip()
    if not line:
        return

    try:
        msg = protocol.decode(line)
    except protocol.ProtocolError as e:
        print(f"Protocol error: {e}", file = sys.stderr)
        return

    if isinstance(msg, protocol.Key):
        code = KEYMAP.get(msg.code)
        if code is None:
            print(f"Unknown key code: {msg.code}", file = sys.stderr)
            return
        if msg.down:
            inj.press_key(code)
        else:
            inj.release_key(code)

    elif isinstance(msg, protocol.MouseMove):
        inj.mouse_move(msg.dx, msg.dy)

    elif isinstance(msg, protocol.MouseBtn):
        inj.mouse_click(inj.BUTTONS.get(msg.btn), msg.down)

    elif isinstance(msg, protocol.ReleaseAll):
        inj.release_all_keys()

    else:
        print(f"Unknown message type: {msg}", file = sys.stderr)

    return

def main():
    signal.signal(signal.SIGTERM, lambda *_ : sys.exit(0))
    inj = Injector()
    try:
        for line in sys.stdin:
            handle_line(line, inj)
    finally:
        inj.close()

    return


if __name__ == "__main__":
    main()