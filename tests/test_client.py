import signal
import unittest

from multiprocessing import Process
from time import sleep

import os

from detector_integration_api import DetectorIntegrationClient
from tests.utils import start_test_integration_server, get_csax9m_test_writer_parameters


class TestRestClient(unittest.TestCase):
    def setUp(self):
        self.host = "0.0.0.0"
        self.port = 10000

        self.dia_process = Process(target=start_test_integration_server, args=(self.host, self.port))
        self.dia_process.start()

        # Give it some time to start.
        sleep(1)

    def tearDown(self):
        os.kill(self.dia_process.pid, signal.SIGINT)

        # Wait for the server to die.
        sleep(1)

    def test_client_workflow(self):
        client = DetectorIntegrationClient()
        self.assertEqual(client.get_status()["status"], "IntegrationStatus.INITIALIZED")

        writer_config = get_csax9m_test_writer_parameters()
        writer_config.update({"output_file": "/tmp/test.h5",
                              "user_id": 0,
                              "group_id": 0})

        backend_config = {"bit_depth": 16,
                          "n_frames": 100}

        detector_config = {"period": 0.1,
                           "frames": 100,
                           "exptime": 0.01,
                           "dr": 16}

        bsread_config = {"output_file": "/tmp/test_meta.h5",
                         "user_id": 0,
                         "channels": []}

        response = client.set_config(writer_config, backend_config, detector_config, bsread_config)

        self.assertDictEqual(response["config"]["writer"], writer_config)
        self.assertDictEqual(response["config"]["backend"], backend_config)
        self.assertDictEqual(response["config"]["detector"], detector_config)
        self.assertDictEqual(response["config"]["bsread"], bsread_config)

        self.assertEqual(client.get_status()["status"], "IntegrationStatus.CONFIGURED")

        client.start()

        self.assertEqual(client.get_status()["status"], "IntegrationStatus.RUNNING")

        client.stop()

        self.assertEqual(client.get_status()["status"], "IntegrationStatus.INITIALIZED")

        client.debug_start()

        self.assertEqual(client.get_status()["status"], "IntegrationStatus.RUNNING")

        client.debug_stop()

        self.assertEqual(client.get_status()["status"], "IntegrationStatus.INITIALIZED")

        response = client.update_config(writer_config={"user_id": 1},
                                        backend_config={"n_frames": 50},
                                        detector_config={"frames": 50},
                                        bsread_config={"user_id": 1})

        writer_config["user_id"] = 1
        backend_config["n_frames"] = 50
        detector_config["frames"] = 50
        bsread_config["user_id"] = 1

        self.assertDictEqual(response["config"]["writer"], writer_config)
        self.assertDictEqual(response["config"]["backend"], backend_config)
        self.assertDictEqual(response["config"]["detector"], detector_config)
        self.assertDictEqual(response["config"]["bsread"], bsread_config)

        response = client.update_config(writer_config={"group_id": 1})

        writer_config["group_id"] = 1

        self.assertDictEqual(response["config"]["writer"], writer_config)
        self.assertDictEqual(response["config"]["backend"], backend_config)
        self.assertDictEqual(response["config"]["detector"], detector_config)
        self.assertDictEqual(response["config"]["bsread"], bsread_config)

        self.assertEqual(client.get_status()["status"], "IntegrationStatus.CONFIGURED")

        client.reset()

        self.assertEqual(client.get_status()["status"], "IntegrationStatus.INITIALIZED")

        response = client.set_last_config()

        self.assertDictEqual(response["config"]["writer"], writer_config)
        self.assertDictEqual(response["config"]["backend"], backend_config)
        self.assertDictEqual(response["config"]["detector"], detector_config)

        self.assertDictEqual(response["config"]["bsread"], bsread_config)

        self.assertEqual(client.get_status()["status"], "IntegrationStatus.CONFIGURED")

        self.assertEqual(client.get_detector_value("frames"), response["config"]["detector"]["frames"])

        client.reset()

        client.set_config_from_file(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 "csaxs_eiger_config.json"))

        self.assertEqual(client.get_status()["status"], "IntegrationStatus.CONFIGURED")

        self.assertTrue("server_info" in client.get_server_info())

    def test_update_config(self):
        client = DetectorIntegrationClient()

        config = client.get_config()
        self.assertEqual(config["config"]["backend"], {})
        self.assertEqual(config["config"]["writer"], {})
        self.assertEqual(config["config"]["detector"], {})
        self.assertEqual(config["config"]["bsread"], {})

        detector_config = {"frames": 10000, "dr": 16, "period": 0.001}
        backend_config = {"n_frames": 10000, "bit_depth": 16}
        writer_config = {"process_uid": 16371, "output_file": "something"}
        bsread_config = {"process_uid": 122, "output_file": "something"}

        client.update_config(detector_config=detector_config,
                             backend_config=backend_config,
                             writer_config=writer_config,
                             bsread_config=bsread_config)

        configuration = client.get_config()["config"]

        self.assertEqual(configuration["detector"], detector_config)
        self.assertEqual(configuration["writer"], writer_config)
        self.assertEqual(configuration["backend"], backend_config)
        self.assertEqual(configuration["bsread"], bsread_config)

        client.update_config(detector_config={"dr": 32})
        detector_config["dr"] = 32

        configuration = client.get_config()["config"]
        self.assertEqual(configuration["detector"], detector_config)
        self.assertEqual(configuration["writer"], writer_config)
        self.assertEqual(configuration["backend"], backend_config)
        self.assertEqual(configuration["bsread"], bsread_config)

    def test_set_detector_value(self):
        client = DetectorIntegrationClient()

        client

        value = 0.023
        client.set_detector_value("period", value)

        self.assertEqual(value, client.get_detector_value("period"))



