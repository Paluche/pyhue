# PyHue

Light module to interact with a Philips Hue bridge and the lights which are
connected to it.

## Installation

Run at the root of this repository.

``` bash
$ python3 -m pip install .
```

## Setup

Use the script `hue_bridge_init.py` to obtain an username for a Hue Bridge
which will allow you to interact with it.

```
> hue_bridge_init.py
```

## Example

Here is showing a little example. Try it out in a interactive python session.

``` bash
$ python3 -i
>>> from pyhue import HueBridge, LightEffect
>>> hue_bridge = HueBridge()
>>> hue_bridge.lights
{1: 'Light', 2: 'Light', 3: 'Light'}
>>> hue_bridge.set_light_state(1, on=True, effect=LightEffect.COLOR_LOOP)
# Light 1 should start switching color.
>>> hue_bridge.set_light_state(1, effect=LightEffect.NONE)
# Turn it off
>>> hue_bridge.set_light_state(1, on=False)
```

## Enable debug log

Pyhue uses the module `logging` to print out its logs.

Note: Global logging level must be iset to at least level `logging.DEBUG`
__before__ setting the pyhue logging level, in order to see the debug logs.

``` python
import logging

# Set global logging level
logging.basicConfig(level=logging.DEBUG)
# Set pyhue module logging level
logging.getLogger('pyhue').setLevel(logging.DEBUG)
```
