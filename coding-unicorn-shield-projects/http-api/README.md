# Unicorn Shield HTTP API

A small Flask application that exposes the Coding Unicorn Shield over HTTP:
the 9-pixel mane, both eye LEDs, the nose light sensor and the ear button.

## Install

First install the Coding Unicorn Shield library — see the
[repository README](../../README.md).

```bash
sudo pip3 install -r requirements.txt
```

The pins in `requirements.txt` are capped at the last releases that still
support Python 3.7, which is what the target hardware runs. See
[Dependencies and Dependabot](../../README.md#dependencies-and-dependabot).

## Start the server

```bash
sudo python3 unicorn_api.py
```

Root is required: the WS2812 mane is driven over PWM/DMA and needs `/dev/mem`.

By default the server binds **`127.0.0.1:5000`**, so it is reachable only from
the same machine. That is deliberate — the API has **no authentication** and
controls hardware directly, so it is meant to sit behind a local frontend (for
example the included Node-RED flows). Only change the bind address if you
understand the consequences, and put a firewall in front of it.

### Two entry points

* **`unicorn_api.py`** — the current server. Use this one.
* **`server.py`** — the older, simpler version. Fewer endpoints, no threading
  safety, and it starts with `debug=True` on `0.0.0.0`. Kept for reference;
  not recommended for real use.

`unicorn_api.py` funnels every hardware call through a single dedicated worker
thread. `show()` drives the LEDs over DMA and hangs if called from changing
threads, which is what happens when Flask serves requests concurrently.

## Endpoints

Default base URL: `http://127.0.0.1:5000`

| Endpoint | Description |
| --- | --- |
| `GET /` | Service banner |
| `GET /help` | Machine-readable list of all endpoints |
| `GET /eye/left?status=on\|off&value=0.0-1.0` | Left eye (D1); on/off or a specific brightness |
| `GET /eye/right?status=on\|off&value=0.0-1.0` | Right eye (D2); same rules |
| `GET /eyes?status=on\|off&value=0.0-1.0` | Both eyes at once; same rules |
| `GET /pixel/<0-8>?r=&g=&b=` | Set one mane pixel and show it |
| `GET /all?r=&g=&b=` | Set all 9 mane pixels and show them |
| `GET /zone/<name>?r=&g=&b=` | Set one named body zone and show it |
| `GET /zones` | List zone names and their pixel indices |
| `GET /off` | Clear the mane |
| `GET /brightness?value=0.0-1.0` | Set mane brightness |
| `GET /brightness` | Read the current mane brightness |
| `GET /nose` | Read the light sensor (charge time in seconds) |
| `GET /ear` | Read the button state (`true` / `false`) |

`r`, `g` and `b` are integers from 0 to 255.

### Eye brightness

The eyes accept a `value` parameter (0.0–1.0) as well as `status`. `status=off`
always wins over `value` — an explicit off is not second-guessed by a stale
brightness left over from an earlier call. `value` alone (no `status`) just
sets the brightness.

```bash
curl "http://127.0.0.1:5000/eyes?value=0.35"          # dim both eyes
curl "http://127.0.0.1:5000/eye/left?value=1.0"        # left eye full on
curl "http://127.0.0.1:5000/eyes?status=off&value=0.9" # off wins, value ignored
```

Unlike the mane, eye dimming is software PWM (`gpiozero.PWMLED`, no hardware
timer on this board), running in its own thread per eye. Measured on a Pi 1 B+
with both eyes dimmed and the mane rendering continuously: an extra ~25-30% CPU
for the API process, no errors or dropped mane frames across hundreds of
renders. On a busier host that headroom may not be there — watch CPU if you use
this alongside other heavy work.

**Brightness is global and persists between calls.** It is a property of the
strip, not of a request, so whatever the last caller set stays in effect — a
night-time dimmer, a test script, a Node-RED flow. Setting a colour without
setting brightness means inheriting theirs, and at a low value the pixels are
written correctly, the API answers `{"status": true}`, and you still see
nothing.

If your colour must be visible regardless of what ran before, set the
brightness in the same sequence:

```bash
curl "http://127.0.0.1:5000/brightness?value=0.5"
curl "http://127.0.0.1:5000/all?r=255&g=128&b=0"
```

`GET /brightness` without a value reads the current setting back, which is the
quickest way to check this when something stays dark. Note that dimming affects
every zone at once — there is no per-zone brightness.

### Zones

Rather than addressing pixels by number, `/zone/<name>` targets a part of the
unicorn. Pixel indices are 0-based to match `/pixel/<0-8>`; the silkscreen
labels P1–P9 on the board are 1-based, so **P1 is index 0**.

| Zone | Pixels | Board |
| --- | --- | --- |
| `paw-rear-right` | 0 | P1 |
| `paw-front-right` | 1 | P2 |
| `paw-front-left` | 2 | P3 |
| `paw-rear-left` | 3 | P4 |
| `tail` | 4, 5, 6 | P5–P7 |
| `mane` | 7, 8 | P8–P9 |

Convenience groups: `paws` (all four), `paws-left`, `paws-right`, `paws-front`,
`paws-rear`, and `all`.

```bash
curl "http://127.0.0.1:5000/zone/tail?r=0&g=0&b=255"
curl "http://127.0.0.1:5000/zone/paws-front?r=255&g=255&b=255"
```

`GET /zones` returns the mapping, so a client can discover the names instead of
hard-coding them. The zone layout lives in `ZONES` at the top of
`unicorn_api.py` — adjust it there if the board is wired differently.

## Example

Turn the third pixel red:

```bash
curl "http://127.0.0.1:5000/pixel/2?r=255&g=0&b=0"
```

```json
{"status": true}
```

## Responses

Every response is a JSON object:

* `status` — always present, `true` or `false`
* `msg` — an error message, present when `status` is `false`
* `data` — the sensor value, returned by `/nose` and `/ear`

## Node-RED flows

This directory ships two Node-RED flows that drive the API:

* [`node-red-flow.json`](node-red-flow.json)
* [`node-red-dashboard-flow.json`](node-red-dashboard-flow.json)

Import them via the Node-RED editor (menu → Import). They call the API on
`127.0.0.1:5000` from the server side, so they keep working with the
loopback-only bind.

Poll intervals are a real cost on small hardware. On a Pi 1 the sensor
endpoints were originally polled once per second each, which alone accounted
for roughly a fifth of the CPU; 10 s for the light sensor and 2 s for the button
are plenty for a dashboard.

## Mock / test version

To run the server without a shield attached, replace

```python
import unicornshield as unicorn
```

with

```python
from src.unicornMock import unicornmock as unicorn
```

The server then responds with default values, so you can develop against the
API without the hardware.

## Troubleshooting: the mane stays dark

WS2812 LEDs are write-only — there is no return channel from the strip. So every
endpoint answers `{"status": true}` whether or not anything actually lights up,
and so do `ws2811_init()` and `ws2811_render()` underneath. A successful response
says the data was sent, not that a pixel lit.

**Check the brightness first** — it is the cheap explanation. Brightness is
global and survives between calls, so a low value left behind by something else
makes correctly-written colours invisible:

```bash
curl "http://127.0.0.1:5000/brightness"     # e.g. {"status": true, "data": 0.02}
```

Two more things that are not faults: the mane needs `snd_bcm2835` blacklisted,
because onboard audio claims the same PWM block (see the note below), and a
covered nose sensor returns a capped reading rather than a real one.

If brightness is sane and the eyes work but the mane is still dark, **measure
resistance between DIN and DOUT on each pixel** before suspecting the driver. This is faster and more conclusive
than an oscilloscope:

| Reading | Meaning |
| --- | --- |
| 100–250 Ω | Healthy — that is the controller's input stage |
| 0 Ω | **Dead: the chip is shorted through** |

Also check DIN against VDD; it must read open, which rules out a supply short.

Because WS2812 pixels are chained, one dead controller stops the whole strip:
it never passes data to the next pixel, so *all* of them stay dark. Compare the
suspect pixel against its neighbours — a single 0 Ω among 100–250 Ω readings is
the failure.

Two things that do **not** work as a repair:

* Bridging DIN to DOUT on the dead pixel. The wire sits in parallel with the
  existing internal short, so the dead chip still drags the line down. The pixel
  has to be desoldered.
* Holding a jumper by hand to test the idea. A frame takes about 280 µs and the
  render loop repeats every few milliseconds, so a hand contact just corrupts the
  stream mid-frame.

If you remove a pixel without replacing it, set `LED_COUNT` in `unicornshield.py`
to the new length; the remaining pixels shift down by one position.

A dead pixel may glow — often green — while you probe it. The meter's test
current writes a stray value into the colour register, and WS2812 transmits GRB
(green first). That is a sign the LEDs themselves are fine and only the
controller's data path failed.

## Onboard audio conflicts with the mane

On the Raspberry Pi the same PWM block drives both the 3.5 mm headphone jack and
the WS2812 data line on GPIO18, so the two cannot run at once. With onboard
audio enabled the mane stays dark, and every LED update puts an audible click
into the audio output.

The mane therefore needs onboard audio disabled:

```text
# /boot/config.txt
dtparam=audio=off
```

```text
# /etc/modprobe.d/blacklist-snd-bcm2835.conf
blacklist snd_bcm2835
```

To keep sound as well, use an output that does not touch the PWM block — a USB
audio adapter with a headphone jack, or Bluetooth. Note that a USB dongle may be
capture-only; check that `aplay -l` lists it, not just `arecord -l`.
