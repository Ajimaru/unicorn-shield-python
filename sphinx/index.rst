.. role:: python(code)
   :language: python

.. toctree::
   :titlesonly:
   :maxdepth: 0

Welcome
-------

This documentation covers the methods available in the Coding Unicorn Shield
Python library (:python:`unicornshield`).

The Coding Unicorn Shield is a Raspberry Pi add-on with **9 individually
controllable RGB LEDs** (the mane), **two single-colour eye LEDs**, a **push
button**, and a capacitive **nose** sensor.

* Library source - https://github.com/coding-world/unicorn-shield-python
* Example projects - https://github.com/coding-world/coding-unicorn-shield-projects
* More resources (German) - https://codingworld.io

.. note::

   The mane LEDs (WS2812) are driven via PWM/DMA and therefore require root
   privileges. Run your scripts with ``sudo``.

.. warning::

   The RGB LEDs can be very bright and blinking patterns may trigger
   photosensitive seizures. Keep the brightness low (0.2 is recommended) and do
   not stare directly into the LEDs. See ``EXTREMELY_IMPORTANT_WARNINGS.txt``.

Getting Started
---------------

.. code-block:: python

   import unicornshield as unicorn
   import time

   unicorn.brightness(0.2)      # keep it dim!
   unicorn.setAll(255, 0, 255)  # all 9 mane LEDs magenta
   unicorn.show()
   time.sleep(1)
   unicorn.off()

Mane LEDs
=========

The mane consists of 9 RGB LEDs, addressed by index ``0`` to ``8``. Changes to
the buffer are only visible after calling :python:`show()`.

Brightness
----------

.. autofunction:: unicornshield.brightness

Get Brightness
--------------

.. autofunction:: unicornshield.getBrightness

Set Pixel
---------

.. autofunction:: unicornshield.setPixel

Get Pixel
---------

.. autofunction:: unicornshield.getPixel

Set All
-------

.. autofunction:: unicornshield.setAll

Show
----

.. autofunction:: unicornshield.show

Clear
-----

.. autofunction:: unicornshield.clear

Turn Off
--------

.. autofunction:: unicornshield.off

Eyes
====

Two single-colour LEDs, controlled independently.

.. autofunction:: unicornshield.leftEyeOn

.. autofunction:: unicornshield.leftEyeOff

.. autofunction:: unicornshield.rightEyeOn

.. autofunction:: unicornshield.rightEyeOff

Button
======

.. autofunction:: unicornshield.buttonPressed

Nose
====

A capacitive touch sensor. :python:`nose()` returns the charge time in seconds;
a higher value means the nose is being touched.

.. autofunction:: unicornshield.nose
