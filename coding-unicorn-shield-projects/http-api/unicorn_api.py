from flask import Flask, request
from flask_cors import CORS
import json
import logging
import threading
import unicornshield as unicorn

# Silence the werkzeug per-request access log. Node-RED polls /nose and /ear
# continuously, which wrote ~10k lines/day into /var/log/daemon.log via rsyslog
# for requests nobody reads back. WARNING keeps errors and tracebacks visible.
logging.getLogger("werkzeug").setLevel(logging.WARNING)

try:
    import queue
except ImportError:  # py2 fallback
    import Queue as queue


app = Flask(__name__)
CORS(app)

# --- Hardware worker thread --------------------------------------------------
# The WS2812 mane is driven by rpi_ws281x via PWM/DMA. ws2811_render() (show())
# only works reliably when always called from the SAME thread. Flask with
# threaded=True runs each request in its own worker thread, so calling show()
# directly from a handler hangs the DMA. Instead, every hardware operation is
# submitted to a single dedicated worker thread through this queue; handlers
# block on a per-job Event until the worker finishes.
_jobs = queue.Queue()


def _hw_worker():
    while True:
        fn, args, done, box = _jobs.get()
        try:
            box["result"] = fn(*args)
        except Exception as e:  # noqa
            box["error"] = e
        finally:
            done.set()


_worker = threading.Thread(target=_hw_worker)
_worker.daemon = True
_worker.start()


def hw(fn, *args):
    """Run fn(*args) on the dedicated hardware thread and return its result."""
    done = threading.Event()
    box = {}
    _jobs.put((fn, args, done, box))
    done.wait()
    if "error" in box:
        raise box["error"]
    return box.get("result")


# --- helpers -----------------------------------------------------------------
def ok(**extra):
    d = {"status": True}
    d.update(extra)
    return json.dumps(d)


def err(msg):
    return json.dumps({"status": False, "msg": msg})


# hardware primitives (each runs on the worker thread via hw())
def _set_all(r, g, b):
    unicorn.setAll(r, g, b)
    unicorn.show()


def _set_pixel(i, r, g, b):
    unicorn.setPixel(i, r, g, b)
    unicorn.show()


def _clear():
    unicorn.clear()


# --- zones ---------------------------------------------------------------------
# Named groups of mane pixels, so callers can address a body part instead of
# memorising indices. Pixel numbers here are 0-based, matching /pixel/<0-8>;
# the silkscreen labels P1..P9 on the board are 1-based, so P1 is index 0.
ZONES = {
    "paw-rear-right":  [0],   # P1
    "paw-front-right": [1],   # P2
    "paw-front-left":  [2],   # P3
    "paw-rear-left":   [3],   # P4
    "tail":            [4, 5, 6],   # P5-P7
    "mane":            [7, 8],      # P8-P9
}

# Convenience groups built from the ones above.
ZONES["paws"] = (ZONES["paw-rear-right"] + ZONES["paw-front-right"]
                 + ZONES["paw-front-left"] + ZONES["paw-rear-left"])
ZONES["paws-right"] = ZONES["paw-rear-right"] + ZONES["paw-front-right"]
ZONES["paws-left"] = ZONES["paw-front-left"] + ZONES["paw-rear-left"]
ZONES["paws-front"] = ZONES["paw-front-right"] + ZONES["paw-front-left"]
ZONES["paws-rear"] = ZONES["paw-rear-right"] + ZONES["paw-rear-left"]
ZONES["all"] = sorted(set(sum(ZONES.values(), [])))


def _set_zone(pixels, r, g, b):
    for i in pixels:
        unicorn.setPixel(i, r, g, b)
    unicorn.show()


def _eyes(left, right):
    """left/right: None (leave alone), True/False (on/off), or a 0.0-1.0
    float (brightness). Booleans stay for /pixel-style on/off callers; the
    float path is what the value= parameter below uses."""
    if left is not None:
        if isinstance(left, bool):
            unicorn.leftEyeOn() if left else unicorn.leftEyeOff()
        else:
            unicorn.leftEyeBrightness(left)
    if right is not None:
        if isinstance(right, bool):
            unicorn.rightEyeOn() if right else unicorn.rightEyeOff()
        else:
            unicorn.rightEyeBrightness(right)


def _eye_value():
    """Parse the optional value= GET parameter (eye brightness, 0.0-1.0).
    Returns None if absent, the float if present and valid, or raises
    ValueError with a message if present but out of range/unparseable."""
    raw = request.args.get('value')
    if raw is None:
        return None
    try:
        v = float(raw)
    except ValueError:
        raise ValueError("value must be a float 0.0-1.0")
    if v < 0.0 or v > 1.0:
        raise ValueError("value must be between 0.0 and 1.0")
    return v


# --- routes ------------------------------------------------------------------
@app.route("/")
def hello():
    return ok(msg="Unicorn Shield HTTP API. See /help")


@app.route("/help")
def helproute():
    return json.dumps({
        "status": True,
        "endpoints": {
            "GET /eye/left?status=on|off&value=0.0-1.0": "left eye (D1); value sets brightness, status=off overrides value",
            "GET /eye/right?status=on|off&value=0.0-1.0": "right eye (D2); same rules as /eye/left",
            "GET /eyes?status=on|off&value=0.0-1.0": "both eyes; same rules as /eye/left",
            "GET /pixel/<0-8>?r=&g=&b=": "set one mane pixel + show",
            "GET /all?r=&g=&b=": "set all 9 mane pixels + show",
            "GET /zone/<name>?r=&g=&b=": "set one named body zone (see /zones)",
            "GET /zones": "list zone names and their pixel indices",
            "GET /off": "clear mane (all pixels off)",
            "GET /brightness?value=0.0-1.0": "set mane brightness",
            "GET /brightness": "read current mane brightness (0.0-1.0)",
            "GET /nose": ("read light sensor (charge time seconds); "
                          "adds timeout=true when too dark to measure"),
            "GET /ear": "read button state (true/false)",
        }
    })


def _eye_arg():
    """Combine status= and value= into one arg for _eyes(): True/False for
    plain on/off, a float for a specific brightness, or raises ValueError.
    status=off wins over value (an explicit off should not be second-guessed
    by a stale brightness value left over from an earlier call)."""
    status = request.args.get('status')
    if status is not None and status not in ("on", "off"):
        raise ValueError("status must be >on< or >off<")
    value = _eye_value()
    if status == "off":
        return False
    if value is not None:
        return value
    if status == "on":
        return True
    raise ValueError("send >status< (on/off) and/or >value< (0.0-1.0)")


@app.route("/eye/left")
def leftEye():
    try:
        arg = _eye_arg()
    except ValueError as e:
        return err(str(e))
    hw(_eyes, arg, None)
    return ok()


@app.route("/eye/right")
def rightEye():
    try:
        arg = _eye_arg()
    except ValueError as e:
        return err(str(e))
    hw(_eyes, None, arg)
    return ok()


@app.route("/eyes")
def eyes():
    try:
        arg = _eye_arg()
    except ValueError as e:
        return err(str(e))
    hw(_eyes, arg, arg)
    return ok()


def _rgb():
    """Parse and validate r,g,b GET params. Returns (r,g,b) or raises ValueError."""
    r = request.args.get('r')
    g = request.args.get('g')
    b = request.args.get('b')
    if r is None or g is None or b is None:
        raise ValueError("You need to send r, g and b via GET parameter")
    try:
        r, g, b = int(r), int(g), int(b)
    except ValueError:
        raise ValueError("r, g and b must be integer")
    for name, v in (("r", r), ("g", g), ("b", b)):
        if v < 0 or v > 255:
            raise ValueError("%s must be between 0 and 255" % name)
    return r, g, b


@app.route("/pixel/<id>")
def pixel(id):
    try:
        id = int(id)
    except ValueError:
        return err("ID must be an integer")
    if id < 0 or id > 8:
        return err("ID not valid (0-8 are valid)")
    try:
        r, g, b = _rgb()
    except ValueError as e:
        return err(str(e))
    hw(_set_pixel, id, r, g, b)
    return ok()


@app.route("/all")
def all_pixels():
    try:
        r, g, b = _rgb()
    except ValueError as e:
        return err(str(e))
    hw(_set_all, r, g, b)
    return ok()


@app.route("/zone/<name>")
def zone(name):
    pixels = ZONES.get(name)
    if pixels is None:
        return err("unknown zone >%s< (see /zones)" % name)
    try:
        r, g, b = _rgb()
    except ValueError as e:
        return err(str(e))
    hw(_set_zone, pixels, r, g, b)
    return ok()


@app.route("/zones")
def zones():
    return json.dumps({"status": True, "zones": ZONES})


@app.route("/off")
def off():
    hw(_clear)
    return ok()


@app.route("/brightness")
def brightness():
    value = request.args.get('value')
    # Without a value this reads instead of writes. Brightness is global and
    # persists between calls, so a caller that did not set it is at the mercy of
    # whoever set it last - being able to read it back makes that debuggable.
    if value is None:
        return ok(data=hw(unicorn.getBrightness))
    try:
        value = float(value)
    except ValueError:
        return err("value must be a float 0.0-1.0")
    if value < 0.0 or value > 1.0:
        return err("value must be between 0.0 and 1.0")
    hw(unicorn.brightness, value)
    return ok()


@app.route("/nose")
def nose():
    # A reading that hits the library's cap is not a real measurement, only a
    # floor value meaning "at least this dark". Flag it so clients can skip the
    # sample instead of treating the cap as a genuine brightness level.
    value = hw(unicorn.nose)
    timeout = getattr(unicorn, "NOSE_TIMEOUT", None)
    if timeout is not None and value >= timeout:
        return ok(data=value, timeout=True)
    return ok(data=value)


@app.route("/ear")
def ear():
    return ok(data=hw(unicorn.buttonPressed))


if __name__ == "__main__":
    # threaded=True: accept concurrent HTTP requests (dashboard polls + clicks).
    # All actual hardware access is funneled to one worker thread (see hw()),
    # so DMA show() always runs on the same thread and never hangs.
    # Bind to loopback only. The sole consumer is the Node-RED flow on this
    # same host (verified: 395/395 requests over 24h came from 127.0.0.1), and
    # there is no firewall on this box, so listening on 0.0.0.0 exposed the
    # unauthenticated hardware API - and the permissive CORS(app) above - to
    # the whole LAN for no benefit.
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)
