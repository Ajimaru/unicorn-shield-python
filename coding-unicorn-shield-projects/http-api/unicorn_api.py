from flask import Flask, request
from flask_cors import CORS
import json
import threading
import unicornshield as unicorn

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


def _eyes(left, right):
    if left is not None:
        unicorn.leftEyeOn() if left else unicorn.leftEyeOff()
    if right is not None:
        unicorn.rightEyeOn() if right else unicorn.rightEyeOff()


# --- routes ------------------------------------------------------------------
@app.route("/")
def hello():
    return ok(msg="Unicorn Shield HTTP API. See /help")


@app.route("/help")
def helproute():
    return json.dumps({
        "status": True,
        "endpoints": {
            "GET /eye/left?status=on|off": "left eye (D1)",
            "GET /eye/right?status=on|off": "right eye (D2)",
            "GET /eyes?status=on|off": "both eyes",
            "GET /pixel/<0-8>?r=&g=&b=": "set one mane pixel + show",
            "GET /all?r=&g=&b=": "set all 9 mane pixels + show",
            "GET /off": "clear mane (all pixels off)",
            "GET /brightness?value=0.0-1.0": "set mane brightness",
            "GET /nose": "read light sensor (charge time seconds)",
            "GET /ear": "read button state (true/false)",
        }
    })


@app.route("/eye/left")
def leftEye():
    status = request.args.get('status')
    if status not in ("on", "off"):
        return err("status must be >on< or >off<")
    hw(_eyes, status == "on", None)
    return ok()


@app.route("/eye/right")
def rightEye():
    status = request.args.get('status')
    if status not in ("on", "off"):
        return err("status must be >on< or >off<")
    hw(_eyes, None, status == "on")
    return ok()


@app.route("/eyes")
def eyes():
    status = request.args.get('status')
    if status not in ("on", "off"):
        return err("status must be >on< or >off<")
    on = status == "on"
    hw(_eyes, on, on)
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


@app.route("/off")
def off():
    hw(_clear)
    return ok()


@app.route("/brightness")
def brightness():
    value = request.args.get('value')
    if value is None:
        return err("send >value< (0.0-1.0) via GET parameter")
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
    return ok(data=hw(unicorn.nose))


@app.route("/ear")
def ear():
    return ok(data=hw(unicorn.buttonPressed))


if __name__ == "__main__":
    # threaded=True: accept concurrent HTTP requests (dashboard polls + clicks).
    # All actual hardware access is funneled to one worker thread (see hw()),
    # so DMA show() always runs on the same thread and never hangs.
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
