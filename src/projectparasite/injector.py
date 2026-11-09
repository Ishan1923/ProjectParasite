from evdev import UInput, ecodes as e
import time

class Injector:
    def __init__(self):
        self.held_keys = {}  # keep track of held keys to release them later
        self.held_btns = {}
        self.kbd = UInput(name="parasite-keyboard")   # default = all keys
        self.mouse = UInput(
            {e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
             e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL, e.REL_HWHEEL]},
            name="parasite-mouse",
        )
        self.BUTTONS = {
            "left": e.BTN_LEFT,
            "right": e.BTN_RIGHT,
            "middle": e.BTN_MIDDLE,
        }
        time.sleep(0.5)  # wait for the devices to be ready
        self.release_all_keys()

    def press_key(self, code):
        self.kbd.write(e.EV_KEY, code, 1)
        self.kbd.syn()
        self.held_keys[code] = True

    def release_key(self, code):
        self.kbd.write(e.EV_KEY, code, 0)
        self.kbd.syn()
        self.held_keys.pop(code, None)

    def release_all_keys(self):
        lst_held_keys = reversed(list(self.held_keys))
        lst_held_btns = reversed(list(self.held_btns))
        for key in lst_held_keys:
            self.release_key(key)
        for btn in lst_held_btns:
            self.mouse_click(btn, False)

    def mouse_move(self, dx, dy):
        self.mouse.write(e.EV_REL, e.REL_X, dx)
        self.mouse.write(e.EV_REL, e.REL_Y, dy)
        self.mouse.syn()

    def mouse_click(self, btn_code, down):
        self.mouse.write(e.EV_KEY, btn_code, 1 if down else 0)
        self.mouse.syn()
        if down:
            self.held_btns[btn_code] = True
        else:
            self.held_btns.pop(btn_code, None)


    def close(self): # call in finally block to ensure proper cleanup
        try:
            self.release_all_keys()
        finally:
            self.kbd.close()
            self.mouse.close()