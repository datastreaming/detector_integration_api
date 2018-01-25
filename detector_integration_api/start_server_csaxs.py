import argparse

from importlib import import_module
import logging

import bottle
from mflow_nodes import NodeClient

from detector_integration_api import config
from detector_integration_api.client.backend_rest_client import BackendClient
from detector_integration_api.client.cpp_writer_client import CppWriterClient
from detector_integration_api.client.detector_cli_client import DetectorClient
from detector_integration_api.manager import csaxs_manager
from detector_integration_api.rest_api.rest_server import register_rest_interface, register_debug_rest_interface

_logger = logging.getLogger(__name__)


def start_integration_server(host, port, backend_url, writer_url):
    _logger.info("Starting integration REST API with:\nBackend url: %s\nWriter url: %s",
                 backend_url, writer_url)

    backend_client = BackendClient(backend_url)
    writer_client = CppWriterClient(writer_url)
    detector_client = DetectorClient()

    integration_manager = csaxs_manager.IntegrationManager(writer_client=writer_client,
                                                           backend_client=backend_client,
                                                           detector_client=detector_client)

    app = bottle.Bottle()
    register_rest_interface(app=app, integration_manager=integration_manager)

    try:
        bottle.run(app=app, host=host, port=port)
    finally:
        pass


def main():
    parser = argparse.ArgumentParser(description='Rest API for beamline software')
    parser.add_argument('-i', '--interface', default=config.DEFAULT_SERVER_INTERFACE,
                        help="Hostname interface to bind to")
    parser.add_argument('-p', '--port', default=config.DEFAULT_SERVER_PORT, help="Server port")
    parser.add_argument("--log_level", default=config.DEFAULT_LOGGING_LEVEL,
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")
    parser.add_argument("-b", "--backend_url", default=config.DEFAULT_BACKEND_URL,
                        help="Backend REST API url.")
    parser.add_argument("-w", "--writer_url", default=config.DEFAULT_WRITER_URL,
                        help="Writer REST API url.")

    arguments = parser.parse_args()

    # Setup the logging level.
    logging.basicConfig(level=arguments.log_level, format='[%(levelname)s] %(message)s')

    start_integration_server(arguments.interface, arguments.port,
                             arguments.backend_url,
                             arguments.writer_url, arguments.writer_instance_name,
                             arguments.bsread_url, arguments.bsread_instance_name,
                             arguments.manager_module,
                             arguments.disable_bsread)


if __name__ == "__main__":
    main()
