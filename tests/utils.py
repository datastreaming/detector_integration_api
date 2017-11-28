import json
from importlib import import_module

import bottle
import os

from detector_integration_api import config
from detector_integration_api.rest_api.rest_server import register_rest_interface, register_debug_rest_interface


class MockBackendClient(object):
    def __init__(self):
        self.status = "INITIALIZED"
        self.backend_url = "backend_url"
        self.config = None

    def get_status(self):
        return self.status

    def set_config(self, configuration):
        self.status = "CONFIGURED"
        self.config = configuration

    def open(self):
        self.status = "OPEN"

    def close(self):
        self.status = "CLOSE"

    def reset(self):
        self.status = "INITIALIZED"


class MockDetectorClient(object):
    def __init__(self):
        self.status = "idle"
        self.config = {}

    def get_status(self):
        return self.status

    def set_config(self, configuration):
        self.config = configuration

    def start(self):
        self.status = "running"

    def stop(self):
        self.status = "idle"

    def get_value(self, name):
        return self.config[name]

    def set_value(self, name, value, no_verification=False):
        self.config[name] = value
        return value


class MockMflowNodesClient(object):
    def __init__(self):
        self.is_running = False
        self._api_address = "writer_url"
        self.config = None

    def get_status(self):
        return {"is_running": self.is_running}

    def set_parameters(self, configuration):
        self.config = configuration

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    def reset(self):
        self.is_running = False


def get_test_integration_manager(manager_module=config.DEFAULT_MANAGER_MODULE):
    backend_client = MockBackendClient()
    detector_client = MockDetectorClient()
    writer_client = MockMflowNodesClient()
    bsread_client = MockMflowNodesClient()
    manager_module = import_module(manager_module)

    manager = manager_module.IntegrationManager(backend_client, writer_client, detector_client, bsread_client)

    return manager


def start_test_integration_server(host, port, manager_module=config.DEFAULT_MANAGER_MODULE):
    backend_client = MockBackendClient()
    writer_client = MockMflowNodesClient()
    detector_client = MockDetectorClient()
    bsread_client = MockMflowNodesClient()

    manager_module = import_module(manager_module)

    integration_manager = manager_module.IntegrationManager(writer_client=writer_client,
                                                            backend_client=backend_client,
                                                            detector_client=detector_client,
                                                            bsread_client=bsread_client)
    app = bottle.Bottle()
    register_rest_interface(app=app, integration_manager=integration_manager)
    register_debug_rest_interface(app=app, integration_manager=integration_manager)

    bottle.run(app=app, host=host, port=port)


def get_csax9m_test_writer_parameters():
    """
    This are all the parameters you need to pass to the writer in order to write in the csax format.
    """
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "csaxs_eiger_config.json")

    with open(filename) as input_file:
        configuration = json.load(input_file)

    return configuration["writer"]
