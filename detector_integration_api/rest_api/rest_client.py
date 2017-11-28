import json
from time import time, sleep

import requests

from detector_integration_api import config
from detector_integration_api.rest_api.rest_server import routes


def validate_response(server_response):
    if server_response["state"] != "ok":
        raise Exception("An exception happened on the server:\n" +
                        server_response.get("status", "Unknown error occurred."))

    return server_response

# TODO: Add functionality to get all the clients separatelly.


class DetectorIntegrationClient(object):
    def __init__(self, api_address=None):
        if not api_address:
            api_address = "http://%s:%s" % (config.DEFAULT_SERVER_INTERFACE, config.DEFAULT_SERVER_PORT)

        self.api_address = api_address.rstrip("/")

    def start(self):
        request_url = self.api_address + routes["start"]

        response = requests.post(request_url).json()

        return validate_response(response)

    def stop(self):
        request_url = self.api_address + routes["stop"]

        response = requests.post(request_url).json()

        return validate_response(response)

    def get_status(self):
        request_url = self.api_address + routes["get_status"]

        response = requests.get(request_url).json()

        return validate_response(response)

    def get_status_details(self):
        request_url = self.api_address + routes["get_status_details"]

        response = requests.get(request_url).json()

        return validate_response(response)

    def get_config(self):
        request_url = self.api_address + routes["get_config"]

        response = requests.get(request_url).json()

        return validate_response(response)

    def wait_for_status(self, target_status, timeout=None, polling_interval=0.2):

        if not isinstance(target_status, (list, tuple)):
            target_status = [target_status]

        start_time = time()
        while True:
            last_status = self.get_status()["status"]

            if last_status in target_status:
                return

            if timeout and time() - start_time > timeout:
                raise ValueError("Timeout exceeded. Could not reach target status '%s'. Last received status: '%s'." %
                                 (target_status, last_status))

            sleep(polling_interval)

    def get_clients_enabled(self):
        request_url = self.api_address + routes["clients_enabled"]

        response = requests.get(request_url).json()

        return validate_response(response)

    def set_clients_enabled(self, bsread=True, writer=True, backend=True, detector=True):
        request_url = self.api_address + routes["clients_enabled"]

        configuration = {"writer": writer,
                         "backend": backend,
                         "detector": detector,
                         "bsread": bsread}

        response = requests.post(request_url, json=configuration).json()

        return validate_response(response)

    def set_config(self, writer_config, backend_config, detector_config, bsread_config=None):
        request_url = self.api_address + routes["set_config"]

        configuration = {"writer": writer_config,
                         "backend": backend_config,
                         "detector": detector_config,
                         "bsread": bsread_config or {}}

        response = requests.put(request_url, json=configuration).json()

        return validate_response(response)

    def set_config_from_file(self, filename):
        with open(filename) as input_file:
            configuration = json.load(input_file)

        self.set_config(configuration.get("writer"),
                        configuration.get("backend"),
                        configuration.get("detector"),
                        configuration.get("bsread"))

    def set_last_config(self):
        request_url = self.api_address + routes["set_last_config"]

        response = requests.post(request_url).json()

        return validate_response(response)

    def update_config(self, writer_config=None, backend_config=None, detector_config=None, bsread_config=None):
        request_url = self.api_address + routes["update_config"]

        configuration = {"writer": writer_config,
                         "backend": backend_config,
                         "detector": detector_config,
                         "bsread": bsread_config}

        response = requests.post(request_url, json=configuration).json()

        return validate_response(response)

    def get_detector_value(self, name):
        request_url = self.api_address + routes["get_detector_value"] + "/" + name

        response = requests.get(request_url).json()

        return validate_response(response)["value"]

    def set_detector_value(self, parameter_name, parameter_value):
        request_url = self.api_address + routes["set_detector_value"]

        request_json = {"name": parameter_name,
                        "value": parameter_value}

        response = requests.post(request_url, json=request_json).json()

        return validate_response(response)["value"]

    def reset(self):
        request_url = self.api_address + routes["reset"]

        response = requests.post(request_url).json()

        return validate_response(response)

    def get_server_info(self):
        request_url = self.api_address + routes["get_server_info"]

        response = requests.get(request_url).json()

        return validate_response(response)

    def debug_start(self, configuration=None):
        request_url = self.api_address + "/debug" + routes["start"]

        response = requests.post(request_url, json=configuration).json()

        return validate_response(response)

    def debug_stop(self):
        request_url = self.api_address + "/debug" + routes["stop"]

        response = requests.post(request_url).json()

        return validate_response(response)

    def get_metrics(self):
        request_url = self.api_address + routes["get_metrics"]
        response = requests.get(request_url)
        
        return validate_response(response.json())

    def get_backend(self, action, configuration={}):
        request_url = self.api_address + routes["backend_client"] + "/" + action

        response = requests.get(request_url).json() 
        return validate_response(response)

    def put_backend(self, action, configuration={}):
        request_url = self.api_address + routes["backend_client"] + "/" + action

        response = requests.put(request_url, json=configuration).json() 
        return validate_response(response)
