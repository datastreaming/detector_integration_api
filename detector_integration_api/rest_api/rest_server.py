import json
from logging import getLogger

from bottle import request, response

_logger = getLogger(__name__)
_audit_logger = getLogger("audit_trail")

routes = {
    "start": "/api/v1/start",
    "stop": "/api/v1/stop",
    "reset": "/api/v1/reset",

    "get_status": "/api/v1/status",
    "get_status_details": "/api/v1/status_details",

    "get_config": "/api/v1/config",
    "set_config": "/api/v1/config",
    "update_config": "/api/v1/config",
    "set_last_config": "/api/v1/configure",

    "get_detector_value": "/api/v1/detector/value",
    "set_detector_value": "/api/v1/detector/value",

    "get_server_info": "/api/v1/info",

    "get_metrics": "/api/v1/metrics",

    "backend_client": "/api/v1/backend",
}


def register_debug_rest_interface(app, integration_manager):
    @app.post("/debug" + routes["start"])
    def debug_start():
        # Stop the current acquisition if running.
        debug_stop()

        debug_config = request.json or {}

        debug_writer_config = debug_config.get("writer", {})
        if debug_writer_config:
            integration_manager.writer_client.set_parameters(debug_writer_config)

        # We always need to call the config parameter on the backend.
        debug_backend_config = debug_config.get("backend", {})
        integration_manager.backend_client.set_config(debug_backend_config)

        debug_detector_config = debug_config.get("detector", {})
        if debug_detector_config:
            integration_manager.detector_client.set_config(debug_detector_config)

        integration_manager.writer_client.start()
        integration_manager.backend_client.open()
        integration_manager.detector_client.start()

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string()}

    @app.post("/debug" + routes["stop"])
    def debug_stop():
        integration_manager.stop_acquisition()

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string()}


def register_rest_interface(app, integration_manager):
    @app.post(routes["start"])
    def start():
        integration_manager.start_acquisition()

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string()}

    @app.post(routes["stop"])
    def stop():
        integration_manager.stop_acquisition()

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string()}

    @app.get(routes["get_status"])
    def get_status():
        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string()}

    @app.get(routes["get_status_details"])
    def get_status_details():

        writer_status, backend_status, detector_status = integration_manager.get_status_details()

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string(),
                "details": {"writer": writer_status,
                            "backend": backend_status,
                            "detector": detector_status}}

    @app.post(routes["set_last_config"])
    def set_last_config():
        current_config = integration_manager.get_acquisition_config()

        integration_manager.set_acquisition_config(current_config["writer"],
                                                   current_config["backend"],
                                                   current_config["detector"])

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string(),
                "config": integration_manager.get_acquisition_config()}

    @app.get(routes["get_config"])
    def get_config():
        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string(),
                "config": integration_manager.get_acquisition_config()}

    @app.put(routes["set_config"])
    def set_config():
        new_config = request.json

        if {"writer", "backend", "detector"} != set(new_config):
            raise ValueError("Specify config JSON with 3 root elements: 'writer', 'backend', 'detector'.")

        integration_manager.set_acquisition_config(new_config["writer"], new_config["backend"], new_config["detector"])

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string(),
                "config": integration_manager.get_acquisition_config()}

    @app.post(routes["update_config"])
    def update_config():
        config_updates = request.json

        current_config = integration_manager.get_acquisition_config()

        def update_config_section(section_name):
            if section_name in config_updates and config_updates.get(section_name):
                current_config[section_name].update(config_updates[section_name])

        update_config_section("writer")
        update_config_section("backend")
        update_config_section("detector")

        integration_manager.set_acquisition_config(current_config["writer"],
                                                   current_config["backend"],
                                                   current_config["detector"])

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string(),
                "config": integration_manager.get_acquisition_config()}

    @app.get(routes["get_detector_value"] + "/<name>")
    def get_detector_value(name):
        value = integration_manager.detector_client.get_value(name)

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string(),
                "value": value}

    @app.post(routes["set_detector_value"])
    def set_detector_value():
        parameter_request = request.json

        if not parameter_request:
            raise ValueError("Set detector value JSON request cannot be empty.")

        if "name" not in parameter_request or 'value' not in parameter_request:
            raise ValueError("'name' and 'value' must be set in JSON request.")

        parameter_name = parameter_request["name"]
        parameter_value = parameter_request["value"]

        value = integration_manager.detector_client.set_value(parameter_name, parameter_value, no_verification=True)

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string(),
                "value": value}

    @app.post(routes["reset"])
    def reset():
        integration_manager.reset()

        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string()}

    @app.get(routes["get_server_info"])
    def get_server_info():
        return {"state": "ok",
                "status": integration_manager.get_acquisition_status_string(),
                "server_info": integration_manager.get_server_info()}

    @app.get(routes["get_metrics"] + "/<metrics_name>")
    def get_metrics(metrics_name):
        return {"state": "ok",
                "metrics": integration_manager.get_metrics(metric_name)}

    @app.get(routes["backend_client"] + "/<action>")
    def get_backend_client(action):
        value = integration_manager.backend_client.__getattribute__(action)()
        return {"state": "ok", "value": value}

    @app.put(routes["backend_client"] + "/<action>")
    def put_backend_client(action):
        if action != "config":
            raise ValueError("Action %s not supported. Currently supported actions: config" % action)
        new_config = request.json
        integration_manager.validator.validate_backend_config(new_config)
        integration_manager.backend_client.set_config(new_config)
        integration_manager._last_set_backend_config = new_config

        return {"state": "ok",
                "status": integration_manager.backend_client.get_status(),
                "config": integration_manager.backend_client._last_set_backend_config}

    @app.error(500)
    def error_handler_500(error):
        response.content_type = 'application/json'
        response.status = 200

        error_text = str(error.exception)

        _logger.error(error_text)
        _audit_logger.error(error_text)

        return json.dumps({"state": "error",
                           "status": error_text})
