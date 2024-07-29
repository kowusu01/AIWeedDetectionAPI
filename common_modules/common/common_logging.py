import logging
import sys

from common_modules.common import constants
from common_modules.common.common_config import Config

DEFAULT_LOG_FORMAT = "%(levelname)s:    %(asctime)s - %(name)s - %(message)s"


class LogHelper:
    def __init__(
        self,
        config: Config,
        logger_name: str = None,
        log_format: str = DEFAULT_LOG_FORMAT,
    ):
        self.config = config

        # the main logger object
        if logger_name:
            name = __name__

        self.logger = logging.getLogger(logger_name)
        logging.basicConfig(format=log_format)
        self.logger.setLevel(
            self.get_log_level(self.config.get(constants.CONFIG_LOG_LEVEL))
        )
        self.configure_logging()
        print(f"LogHelper - logger configured, level: {self.logger.level}")

    def configure_logging(self) -> None:
        # Create a handler for stdout.
        console_handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(console_handler)
        console_handler.setLevel(
            self.get_log_level(self.config.get(constants.CONFIG_LOG_LEVEL))
        )

        # check if logging to file is enabled
        if self.config.get(constants.CONFIG_LOG_TO_FILE) == "True":
            file_handler = logging.FileHandler(
                self.config.get(constants.CONFIG_LOG_PATH)
            )
            file_handler.setLevel(
                self.get_log_level(self.config.get(constants.CONFIG_LOG_LEVEL))
            )
            file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
            self.logger.addHandler(file_handler)

    def get_log_level(self, log_level: str) -> any:
        level = None
        if log_level == constants.LOG_LEVEL_DEBUG:
            level = logging.DEBUG
        elif log_level == constants.LOG_LEVEL_INFO:
            level = logging.INFO
        elif log_level == constants.LOG_LEVEL_WARNING:
            level = logging.WARNING
        elif log_level == constants.LOG_LEVEL_ERROR:
            level = logging.ERROR
        else:
            level = logging.CRITICAL
        return level

    def log(self, msg, level=logging.DEBUG):
        self.logger.log(level, msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.log(msg, logging.INFO)

    def warning(self, msg):
        self.log(msg, logging.WARNING)

    def error(self, msg):
        self.log(msg, logging.ERROR)

    def critical(self, msg):
        self.log(msg, logging.CRITICAL)
