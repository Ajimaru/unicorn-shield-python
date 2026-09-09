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
| `GET /eye/left?status=on\|off` | Left eye (D1) |
| `GET /eye/right?status=on\|off` | Right eye (D2) |
| `GET /eyes?status=on\|off` | Both eyes at once |
| `GET /pixel/<0-8>?r=&g=&b=` | Set one mane pixel and show it |
| `GET /all?r=&g=&b=` | Set all 9 mane pixels and show them |
| `GET /off` | Clear the mane |
| `GET /brightness?value=0.0-1.0` | Set mane brightness |
| `GET /nose` | Read the light sensor (charge time in seconds) |
| `GET /ear` | Read the button state (`true` / `false`) |

`r`, `g` and `b` are integers from 0 to 255.

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

If the eyes work but the mane is dark, **measure resistance between DIN and DOUT
on each pixel** before suspecting the driver. This is faster and more conclusive
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
