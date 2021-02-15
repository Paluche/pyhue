#!/usr/bin/env python3

"""
Script to initialize a connection with a Philips Hue bridge accessible from the
local network.
"""
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from threading import Thread
from queue import Queue
from time import sleep
from zeroconf import ServiceBrowser, Zeroconf, ServiceListener
from pyhue import HueBridge, LightAlert


class SetupThread(Thread):
    """SetupThread."""

    def __init__(self, service_browsing_listener):
        """__init__.

        :param service_browsing_listener:
        """
        self.service_browsing_listener = service_browsing_listener
        super().__init__()

    def run(self):
        """run."""
        while service_info := next(self.service_browsing_listener):
            # Handle newly discovered Hue Bridge
            if len(service_info.addresses) != 1:
                raise NotImplementedError(
                    'Several addresses for a single service'
                )

            address = service_info.addresses[0]

            if len(address) != 4:
                raise NotImplementedError(
                    'Only IPv4 address suppoer are implemented'
                )

            address = '.'.join(str(int(x)) for x in address)

            print(f'Hue bridge found at IP address {address}')

            answer = input('Would you like to create an API token? [Y/n]')

            if answer not in ['', 'y', 'yes']:
                print(f'Bridge {address} not setup')
                continue

            application_name = input(
                'Enter application name (20 characters max):\n'
                '                   <\r'
            )

            device_name = input(
                'Enter device name (19 characters max):\n'
                '                  <\r'
            )

            config_path = input(
                'Enter where to write configuration file. Default would be '
                f'{HueBridge.DEFAULT_CONF_PATH}\n'
            ) or HueBridge.DEFAULT_CONF_PATH

            HueBridge.configure_api(
                address,
                application_name,
                device_name,
                config_path=config_path
            )

            print(
                'Checking access by making all the lights blinks for 3 seconds'
            )

            hue_bridge = HueBridge(config_path=config_path)

            for light_id in hue_bridge.lights.keys():
                hue_bridge.set_light_state(light_id, alert=LightAlert.LSELECT)

            sleep(3)

            for light_id in hue_bridge.lights.keys():
                hue_bridge.set_light_state(light_id, alert=LightAlert.NONE)

            print('Setup done')


class ServiceBrowsingListener(ServiceListener):
    """ServiceBrowsingListener."""

    def __init__(self):
        """__init__."""
        self.queue = Queue()

    def add_service(self, zc: 'Zeroconf', type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        self.queue.put_nowait(info)

    def remove_service(self, zc: 'Zeroconf', type_: str, name: str) -> None:
        # No-op
        pass

    def update_service(self, zc: 'Zeroconf', type_: str, name: str) -> None:
        # No-op
        pass

    def __next__(self):
        return self.queue.get()

    def cancel(self):
        """cancel."""
        self.queue.put_nowait(None)


def main(prog, args):
    """main.

    :param prog:  Program name
    :type prog: str
    :param args:  Arguments provided by the user.
    :type args: list

    :return: 0 in case of success, 1 in case of error, 2 in case of error
             related to the provided arguments.
    """
    parser = ArgumentParser(prog=prog,
                            formatter_class=RawDescriptionHelpFormatter,
                            description=__doc__)

    # Parse the arguments.
    parser.parse_args(args)

    zeroconf = Zeroconf()
    listener = ServiceBrowsingListener()

    print('Browsing for Hue bridge on local network')
    print('Press Ctrl-C to stop the browsing')

    browser = ServiceBrowser(zeroconf, "_hue._tcp.local.", listener)
    setup_thread = SetupThread(listener)
    setup_thread.start()

    try:
        while True:
            sleep(60)
    except KeyboardInterrupt:
        pass

    # Cancel browsing
    browser.cancel()
    # Have None pushed into the queue of discovered services in order to have
    # the setup thread to auto finish once it has handled all the discovered
    # service.
    listener.cancel()

    # Wait for setup thread to stop handling all the discovered services.
    setup_thread.join()

    return 0


# Main entry point.
if __name__ == "__main__":
    sys.exit(main(sys.argv[0], sys.argv[1:]))
