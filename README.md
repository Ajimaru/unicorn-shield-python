# Coding Unicorn Shield — Python Library

Python library and example projects for the Coding Unicorn Shield: a 9-pixel
WS2812 "mane", two eye LEDs, a light sensor in the nose and a button in the ear.

> Please note: this library is still beta.

This is a fork of [coding-world/unicorn-shield-python](https://github.com/coding-world/unicorn-shield-python),
ported to Python 3 (see [#1](https://github.com/Ajimaru/unicorn-shield-python/pull/1)).

## Requirements

* A Raspberry Pi with a Coding Unicorn Shield attached
* **Python 3.7 or newer** (Python 2 is no longer supported)
* Root privileges — the WS2812 mane is driven via PWM/DMA and needs `/dev/mem`

The library is developed against Python 3.7 (`python_requires = '>=3.7'`), which
is what Raspberry Pi OS *buster* ships. It also runs on newer Python versions.

## Install

```bash
sudo apt-get install python3-dev python3-setuptools
sudo pip3 install gpiozero

git clone https://github.com/Ajimaru/unicorn-shield-python
cd unicorn-shield-python

cd rpi-ws281x
sudo python3 setup.py install
cd ..

cd UnicornShield
sudo python3 setup.py install
cd ..
```

## Usage

```python
import unicornshield as unicorn

unicorn.brightness(0.2)      # 0.0 - 1.0; keep it low, the mane is bright
unicorn.setPixel(0, 255, 0, 0)
unicorn.show()               # nothing lights up until you call show()

unicorn.leftEyeOn()
unicorn.rightEyeOff()

print(unicorn.nose())          # light sensor: capacitor charge time in seconds
print(unicorn.buttonPressed()) # ear button: True / False

unicorn.clear()
```

`setPixel()` and `setAll()` only write to a buffer — call `show()` to push the
data to the hardware.

**Threading note:** `show()` drives the WS2812 chain over DMA and must always be
called from the *same* thread. Multi-threaded programs should funnel every
hardware call through one dedicated worker thread; see
[`coding-unicorn-shield-projects/http-api/unicorn_api.py`](coding-unicorn-shield-projects/http-api/unicorn_api.py)
for a working example.

Please read [EXTREMELY_IMPORTANT_WARNINGS.txt](EXTREMELY_IMPORTANT_WARNINGS.txt)
before wiring anything up.

## Projects

Example projects live in
[`coding-unicorn-shield-projects/`](coding-unicorn-shield-projects/):

| Project | Description |
| --- | --- |
| [`http-api`](coding-unicorn-shield-projects/http-api/) | Flask HTTP API for the shield, plus Node-RED dashboard flows |
| [`activity-shield`](coding-unicorn-shield-projects/activity-shield/) | Status/activity indicator |
| [`email-notification`](coding-unicorn-shield-projects/email-notification/) | Light up on new mail |
| [`hashtag-watcher`](coding-unicorn-shield-projects/hashtag-watcher/) | React to social-media hashtags |
| [`people-in-space`](coding-unicorn-shield-projects/people-in-space/) | Show how many people are currently in space |
| [`photobooth`](coding-unicorn-shield-projects/photobooth/) | Photobooth lighting |
| [`demo+documentation`](coding-unicorn-shield-projects/demo+documentation/) | Demos and docs |
| [`getting-started-documentation`](coding-unicorn-shield-projects/getting-started-documentation/) | Getting started guide |
| [`3D_Print_parts`](coding-unicorn-shield-projects/3D_Print_parts/) | Printable parts |

## Dependencies and Dependabot

`coding-unicorn-shield-projects/http-api/requirements.txt` is pinned to the
newest releases that still support **Python 3.7**, because that is what the
target hardware runs. Newer majors (Flask 3.x, Flask-Cors 5.0.1+) declare
`requires_python >=3.9` and cannot be installed there at all.

These pins are a compatibility constraint, not staleness — so Dependabot is
configured **not** to watch pip in this repo (see
[`.github/dependabot.yml`](.github/dependabot.yml)). Security advisories still
reach the repository through Dependabot security alerts, which that file does
not affect.

## Based on UnicornHat and rpi_ws281x

`UnicornShield` is based upon a modified, Pi 2/3 compatible version of the
RPi ws281x library by Jeremy Garff and an adaption of Pimoroni's UnicornHat.
The library was modified by Richard Hirst.

* UnicornHat library: <https://github.com/pimoroni/unicorn-hat>
* Modified version: <https://github.com/richardghirst/rpi_ws281x>
* Original: <https://github.com/jgarff/rpi_ws281x>

### RaspberryPi-NeoPixel-WS2812

Note: `unicornhat` is no longer based upon this library, but this information is
included for posterity.

`unicornhat` was previously based upon a modified version of the ws2812 C driver
from: <https://github.com/626Pilot/RaspberryPi-NeoPixel-WS2812>

## Credits

This project builds on rpi_ws281x (Jeremy Garff, Tony DiCola, Richard Hirst),
Pimoroni's UnicornHat, and the original Coding Unicorn Shield library by
Samuel Brinkmann / Coding World. See [AUTHORS.md](AUTHORS.md) for full credits.

## License

This repository combines differently licensed components (MIT, BSD 2-Clause and
GPL) — the root [LICENSE](LICENSE) does not cover all of it. See the
[licensing note in AUTHORS.md](AUTHORS.md#licensing-note) for which licence
applies where.
