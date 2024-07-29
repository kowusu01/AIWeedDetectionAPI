import os

# from environment variables
from dotenv import load_dotenv

# from azure App Configuration (cloud appsetings)
from azure.appconfiguration.provider import load
from common_modules.common import constants


class Config:
    def __init__(self) -> None:
        self.config_source = None
        self.setup()

    def setup(self):
        # setup environment variables as a source by default
        load_dotenv()
        self.config_source = os.getenv(constants.CONFIG_CONFIG_SOURCE)

        if self.config_source == constants.CONFIG_SOURCE_AZURE_APP_CONFIGURATION:
            self.setup_config_source_app_configuration()

    def setup_config_source_app_configuration(self):
        self.config = load(
            connection_string=os.getenv(
                constants.CONFING_AZURE_APP_CONFIGURATION_CONNECTION_STRING
            )
        )

    def get(self, key: str):
        if self.config_source == constants.CONFIG_SOURCE_AZURE_APP_CONFIGURATION:
            return self.config.get(key)
        else:
            return os.getenv(key)
