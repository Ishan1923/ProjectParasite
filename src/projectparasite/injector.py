from evdev import UInput, ecodes as e
import time

kbd = UInput(name="parasite-keyboard")   # default = all keys
mouse = UInput(
    {e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
     e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL, e.REL_HWHEEL]},
    name="parasite-mouse",
)

time.sleep(0.1)  # wait for the devices to be ready


held_keys = {}

def press_(code):
    kbd.write(e.EV_KEY, code, 1)
    kbd.syn()
    held_keys[code] = True

def release_(code):
    kbd.write(e.EV_KEY, code, 0)
    kbd.syn()
    held_keys.pop(code, None)

def release_all():
    lst_held_keys = reversed(list(held_keys))
    for key in lst_held_keys:
        release_(key)

def close(): # call in finally block to ensure proper cleanup
    try:
        release_all()
    finally:
        kbd.close()
        mouse.close()