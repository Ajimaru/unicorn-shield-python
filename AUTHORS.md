# Authors and Credits

This repository builds on several upstream projects. Credit for the hard parts —
the WS2812 timing, the DMA driver, the original board library — belongs to the
people below.

## Upstream projects

**rpi_ws281x** — the C driver and Python bindings that actually talk to the
WS2812 LEDs over PWM/DMA. Vendored in [`rpi-ws281x/`](rpi-ws281x/).

* Jeremy Garff `<jer@jers.net>` — original author
  <https://github.com/jgarff/rpi_ws281x>
* Tony DiCola `<tony@tonydicola.com>` — Python bindings and NeoPixel wrapper
* Richard Hirst — Raspberry Pi 2/3 compatible fork
  <https://github.com/richardghirst/rpi_ws281x>

Licensed BSD 2-Clause, see [`rpi-ws281x/lib/LICENSE`](rpi-ws281x/lib/LICENSE).

**UnicornHat** — Pimoroni's library for the original Unicorn HAT, which the
`UnicornShield` API is adapted from.

* Philip Howard, Pimoroni Ltd. — <https://github.com/pimoroni/unicorn-hat>

Licensed MIT, Copyright (c) 2017 Pimoroni Ltd., see [`LICENSE`](LICENSE).

**RaspberryPi-NeoPixel-WS2812** — 626Pilot's ws2812 C driver, which UnicornHat
was based on historically. No longer used, credited for posterity.

* <https://github.com/626Pilot/RaspberryPi-NeoPixel-WS2812>

## Coding Unicorn Shield

The shield library and the example projects in
[`coding-unicorn-shield-projects/`](coding-unicorn-shield-projects/).

* Samuel Brinkmann `<samuel@codingworld.io>` — author of `unicornshield`
  and the example projects
* Coding World UG (haftungsbeschränkt) | Jugend Programmiert — <http://cw42.io/unicorn>
* Sören Poschmann — contributor

Original repository: <https://github.com/coding-world/unicorn-shield-python>

Project code is MIT, Copyright (c) 2017 Coding World UG (haftungsbeschränkt) |
Jugend Programmiert, see
[`coding-unicorn-shield-projects/LICENSE`](coding-unicorn-shield-projects/LICENSE).

## This fork

<https://github.com/Ajimaru/unicorn-shield-python>

* Ajimaru — Python 3 port, maintenance, added projects

## Licensing note

This repository combines differently licensed components. `LICENSE` at the root
is not the whole story — check the licence file next to the code you intend to
reuse:

| Path | Licence |
| --- | --- |
| [`LICENSE`](LICENSE) | MIT — Pimoroni Ltd. |
| [`rpi-ws281x/lib/LICENSE`](rpi-ws281x/lib/LICENSE) | BSD 2-Clause — jgarff |
| [`UnicornShield/LICENSE.txt`](UnicornShield/LICENSE.txt) | GPL |
| [`coding-unicorn-shield-projects/LICENSE`](coding-unicorn-shield-projects/LICENSE) | MIT — Coding World UG |
| [`test/LICENSE.txt`](test/LICENSE.txt) | GPL |

If someone is missing here, that is an oversight rather than an intent — please
open an issue.
