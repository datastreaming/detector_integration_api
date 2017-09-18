from detector_integration_api.manager import IntegrationStatus


class Validator(object):
    writer_cfg_params = ["output_file"]
    backend_cfg_params = ["bit_depth", "period", "n_frames"]

    @staticmethod
    def validate_writer_config(configuration):
        if Validator.writer_cfg_params not in configuration:
            raise ValueError("Writer configuration missing mandatory parameters: %s", Validator.writer_cfg_params)

        if configuration["output_file"][-3:] != ".h5":
            configuration["output_file"] += ".h5"

    @staticmethod
    def validate_backend_config(configuration):
        if Validator.backend_cfg_params not in configuration:
            raise ValueError("Backend configuration missing mandatory parameters: %s", Validator.backend_cfg_params)

    @staticmethod
    def validate_detector_config(configuration):
        pass

    @staticmethod
    def interpret_status(writer, backend, detector):

        if not writer and not detector:
            if backend == "INITIALIZED":
                return IntegrationStatus.INITIALIZED

            elif backend == "CONFIGURED":
                IntegrationStatus.CONFIGURED

        elif writer and detector and backend == "OPEN":
            return IntegrationStatus.RUNNING

        return IntegrationStatus.ERROR
