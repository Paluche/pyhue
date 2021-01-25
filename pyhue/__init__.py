"""
Module to interact with a Philips Hue Bridge.
"""

import os
from json import JSONEncoder, dumps, loads
from enum import Enum
import logging
import requests

log = logging.getLogger('pyhue')


class HueError(Exception):
    """HueError."""


class LightAlert(Enum):
    """LightAlert. The different values you can set for the 'alert' feature of
    a Hue light.
    - NONE: The light is not performing an alert effect.
    - SELECT: The light is performing one breathe cycle.
    - LSELECT: The light is performing breathe cycles for 15 seconds or until
               an "alert": "none" command is received.Note that this contains
               the last alert sent to the light and not its current state.
               i.e. After the breathe cycle has finished the bridge does not
               reset the alert to “none“.
    """

    NONE = 'none'
    SELECT = 'select'
    LSELECT = 'lselect'


class LightEffect(Enum):
    """LightEffect. The different values you can set for the 'effect' feature
    of a Hue light.

    - NONE:
    - COLOR_LOOP: The cycle through all hues using the current brightness and
                  saturation settings.
    """

    NONE = 'none'
    COLOR_LOOP = 'colorloop'


class MyJsonEncoder(JSONEncoder):
    """ MyJsonEncoder. Custom JSONEncoder to have a builtin support of
    LightAlert and LightEffect classes into JSON.
    """
    def default(self, o):
        """default.

        :param o:
        """
        if isinstance(o, (LightAlert, LightEffect)):
            return o.value
        return super().default(o)


class HueBridge():
    """HueBridge."""

    DEFAULT_CONF_PATH = os.path.expanduser(
        os.path.join('~', '.config', 'hue_bridge_config.json')
    )

    @staticmethod
    def __check_kwarg(kwargs, kwargs_key, expected_type, limits=None):
        """check_argument.

        :param self:
        :param data_key:
        :param kwargs:
        :param kwargs_key:
        :param expected_type:
        :param limits:
        """
        value = kwargs.get(kwargs_key)

        if value is None:
            return

        if not isinstance(value, expected_type):
            raise TypeError(
                f'{kwargs_key} must be a {expected_type.__name__}'
            )

        if limits is not None:
            minimum, maximum = limits
            if value < minimum or maximum < value:
                raise ValueError(
                    f'Value for {kwargs_key} must be between {minimum} and '
                    f'{maximum}'
                )

    @staticmethod
    def __parse_response(response):
        """__parse_response.

        :param response:
        """
        if not response.ok:
            raise HueError('Error sending the request')

        response = response.json()

        if isinstance(response, list):
            for dict_ in response:
                for key, value in dict_.items():
                    if key == 'error':
                        raise HueError(dumps(value, indent=4))

                    if key == 'success':
                        return value

        elif isinstance(response, dict):
            return response

        raise HueError('Unexpected response content')

    # pylint: disable=too-many-arguments
    @classmethod
    def __do_request(cls, request_type, method, host, path, data):
        """__do_request.

        :param request_type:
        :param method:
        :param host:
        :param path:
        :param data:
        """
        url = f'http://{host}/{path}'

        data = dumps(data, cls=MyJsonEncoder)

        log.debug('%s request to %s with data:', request_type, url)
        log.debug('%s', data)

        response = method(url, data=data)

        log.debug('Response:')
        log.debug(dumps(response.json(), indent=4, sort_keys=True))

        return cls.__parse_response(response)

    # pylint: disable=too-many-arguments
    @classmethod
    def configure_api(cls,
                      host,
                      application_name,
                      device_name,
                      config_path=DEFAULT_CONF_PATH,
                      generate_client_key=False):
        """configure_api.

        :param host:
        :param application_name:
        :param device_name:
        :param config_path:
        :param generate_client_key:
        """
        if not isinstance(application_name, str):
            raise TypeError('Unexpected type for application_name')

        if not isinstance(device_name, str):
            raise TypeError('Unexpected type for device_name')

        if len(application_name) > 20:
            raise ValueError(
                'Application name too long (limited to 20 characters'
            )

        if len(device_name) > 19:
            raise ValueError(
                'Device name too long (limited to 19 characters'
            )

        input('Press the link button on the bridge then press enter within '
              '30 seconds')

        data = {
            'devicetype': f'{application_name}#{device_name}',
        }

        if generate_client_key:
            data['generateclientkey'] = generate_client_key

        config = cls.__do_request('POST', requests.post, host, 'api', data)

        config['host'] = host

        try:
            os.mkdir(os.path.dirname(config_path))
        except FileExistsError:
            pass

        with open(config_path, 'w') as config_file:
            config_file.write(dumps(config, indent=4))

    def put(self, path, **data):
        """put.

        :param path:
        :param data:
        """
        return self.__do_request('PUT',
                                 requests.put,
                                 self.__host,
                                 f'api/{self.__username}/{path}',
                                 data)

    def post(self, path, **data):
        """post. Do an authenticated POST request to the Hue bridge.

        :param path:  Path of the API to access.
        :type path: str
        :param **kwargs:  Data to be send along.
        """
        return self.__do_request('POST',
                                 requests.post,
                                 self.__host,
                                 f'api/{self.__username}/{path}',
                                 data)

    def get(self, path, **data):
        """get. Do an authenticated GET request to the Hue bridge.

        :param path:  Path of the API to access.
        :type path: str
        :param data:  Data to be send along.
        :type data: dict
        """
        return self.__do_request('GET',
                                 requests.get,
                                 self.__host,
                                 f'api/{self.__username}/{path}',
                                 data)

    def delete(self, path, data):
        """delete. Do an authenticated DELETE request to the Hue bridge.

        :param path:  Path of the API to access.
        :type path: str
        :param data:  Data to be send along.
        :type data: dict
        """
        return self.__do_request('DELETE',
                                 requests.delete,
                                 self.__host,
                                 f'api/{self.__username}/{path}',
                                 data)

    def __init__(self, config_path=DEFAULT_CONF_PATH):
        """__init__. HueBridge class initializer.

        :param config_path:  Path to the Hue bridge configuration file to load,
                             defaults to HueBridge.DEFAULT_CONF_PATH.
        :type config_path: str
        """
        with open(config_path) as config_file:
            config = loads(config_file.read())

        self.__host = config['host']
        self.__username = config['username']

        lights = self.get_full_state().get('lights')

        if lights is not None:
            self.lights = {
                int(key): value.get('name')
                for key, value in lights.items()
            }

    def __str__(self):
        """__str__. Get a human readable string describing this class.

        :return: String descbribing this class.
        :rtype: str
        """
        return f'Hue bridge at {self.__host} with lights:\n' + \
               '\n'.join(f'    - {key}: {value}'
                         for key, value in self.lights.items())

    def __repr__(self):
        """__repr__. Get a string representation of this class.
        :return: String representation of this class.
        :rtype: str
        """
        return f'{self.__class__.__name__}<{self.__host}>'

    def get_full_state(self):
        """get_full_state. Get a exhaustive current state of the Hue bridge.

        :return: JSSON as dict describing the full state of the Hue bridge.
        :rtype: dict
        """

        return self.get('')

    def get_configuration(self):
        """get_configuration."""
        return self.get('config')

    def set_configuration(self, **config):
        """set_configuration.

        :param config:
        """
        self.put('config', **config)

    #
    # Lights API
    #

    def get_light(self, light_id=None):
        """get_light.

        :param light_id:
        """
        return self.get('lights{}'.format(f'/{light_id}' if light_id else ''))

    def get_new_lights(self):
        """get_new_lights."""
        return self.get('lights/new')

    def rename_light(self, light_id, name):
        """rename_light.

        :param light_id:
        :param name:
        """
        self.put(f'lights/{light_id}', name=name)

    def set_light_state(self, light_id, **kwargs):
        """set_light_state.

        :param light_id:  ID of the light which state to change.
        :param on: On/Off state of the light. True turn it ON, False turns it
                   off. Defaults to not changing the on/off state of the light.
        :type on: bool
        :param bri: The brightness value to set the light to. Brightness is a
                    scale from 1 (the minimum the light is capable of) to 254
                    (the maximum). Note: a brightness of 1 is not off. Defaults
                    to not changing the brightness value of the light.
        :type bri: int
        :param bri_inc: Increments or decrements the value of the brightness.
                        Is ignored if the bri keyword argument is specified.
                        Any ongoing brightness transition is stopped. Setting a
                        value of 0 also stops any ongoing transition. Defaults
                        to no changing the brightness of the light.
        :param hue: The hue value to set light to. The hue value is a wrapping
                    value between 0 and 65535. Both 0 and 65535 are red, 25500
                    is green and 46920 is blue. Defaults to not changing the
                    color of the light.
        :type hue: int
        :param hue_inc: Increments or decrements the value of the hue. Is
                        ignored if the hue keyword argument is specified. Any
                        ongoing color transition is stopped. Setting a value of
                        0 also stops any ongoing transition. Note if the
                        resulting values are < 0 or > 65535 the result is
                        wrapped. For example a hue_inc value of 1 on a hue
                        value of 65535 results in a hue of 0. A hue_inc value
                        of -2 on a hue value of 0 results in a hue of 65534.
                        Defaults to not changing the color of the light.
        :type hue_inc: int
        :param sat: Saturation of the light. 254 is the most saturated
                    (colored) and 0 is the least saturated (white). Defaults to
                    not changing the saturation of the light.
        :type sat: int
        :param sat_inc: Increments or decrements the value of the saturation.
                        Is ignored if the sat keyword argument is specified.
                        Any ongoing saturation transition is stopped. Setting a
                        value of 0 also stops any ongoing transition.
        :type sat_inc: int
        :param xy_cie: The x and y coordinates of a color in CIE color space as
                       tuple of two elements. The first element is the x
                       coordinate and the second element is the y coordinate.
                       Both x and y must be between 0 and 1. If the specified
                       coordinates are not in the CIE color space, the closest
                       color to the coordinates will be chosen. Defaults to not
                       changing the color of the light. Defaults to not
                       changing the color of the light.
        :type xy_cie: tuple (float, float)
        :param xy_cie_inc: Increments or decrements the value of the xy_cie. Is
                           ignored if the xy_cie keyword argument is specified.
                           Any ongoing color transition is stopped. Setting a
                           value of 0 also stops any ongoing transition. Will
                           stop at it’s gamut boundaries. Minimum value
                           (-0.5, 0.5), maximum value (0.5, 0.5).
        :type xy_cie_inc: tuple (float, float)
        :param ct: The Mired color temperature of the light. 2012 connected
                   lights are capable of 153 (6500K) to 500 (2000K). Defaults
                   to not changing the Mired color temperature of the light.
        :type ct: int
        :param ct_inc: Increments or decrements the value of the Mired color
                       temperature. Is ignored if the ct keyword argument is
                       provided. Any ongoing color transition is stopped.
                       Setting a value of 0 also stops any ongoing transition.
                       Defaults to not changing the Mired color temperature of
                       the light.
        :param alert: The alert effect, is a temporary change to the bulb’s
                      state.
        :type alert: LightAlert
        :param effect: The dynamic effect of the light.
        :type effect: LightEffect
        :param transitiontime: The duration of the transition from the light’s
                               current state to the new state. This is given as
                               a multiple of 100ms and defaults to 4 (400ms).
                               For example, setting transition_time to 10 will
                               make the transition last 1 second.
        """
        keyword_arguments = {
            'on': [bool],
            'bri': [int, (1, 254)],
            'bri_inc': [int, (-254, 254)],
            'hue': [int, (0, 65535)],
            'hue_inc': [int, (-65534, 65534)],
            'sat': [int, (0, 65535)],
            'sat_inc': [int, (-65534, 65534)],
            'xy': [tuple, ((0, 0), (1.0, 1.0))],
            'xy_inc': [tuple, ((-0.5, -0.5), (0.5, 0.5))],
            'ct': [int, (153, 500)],
            'ct_inc': [int, (-364, 635)],
            'alert': [LightAlert],
            'effect': [LightEffect],
            'transitiontime': [int, (0, 65535)],
        }

        for key in kwargs:
            if key not in keyword_arguments:
                raise ValueError(f'Unknown {key} keyword argument')
            self.__check_kwarg(kwargs, key, *keyword_arguments[key])

        self.put(f'lights/{light_id}/state', **kwargs)
