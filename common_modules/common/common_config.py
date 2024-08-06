import os

# from environment variables
from dotenv import load_dotenv

# from azure App Configuration (cloud appsetings)
from azure.appconfiguration.provider import load
from common_modules.common import constants


class Config:
    def __init__(self) -> None:
        self.config_source = None
        self.config = None
        self.app_version = None
        self.config_source_descr = None
        self.config_version = None
        self.setup()
        print(
            f"App version: {self.app_version}, config source: {self.config_source_descr}, - version: {self.config_version}"
        )

    def setup(self):
        # setup environment variables as a source by default
        load_dotenv()
        self.app_version = os.getenv(constants.CONFIG_APP_VERSION)
        self.config_version = os.getenv(constants.CONFIG_APP_CONFIG_VERSION)
        self.config_source_descr = os.getenv(constants.CONFIG_CONFIG_SOURCE)

        self.config_source = os.getenv(constants.CONFIG_CONFIG_SOURCE)
        print(f"config source: {self.config_source}")
        if self.config_source == constants.CONFIG_SOURCE_AZURE_APP_CONFIGURATION:
            print("setting up Azure App Configuration...")
            self.setup_config_source_app_configuration()

    def setup_config_source_app_configuration(self):
        print("loading Azure App Configuration...")
        self.config = load(
            connection_string=os.getenv(
                constants.CONFING_AZURE_APP_CONFIGURATION_CONNECTION_STRING
            )
        )

        # at this point config object sould be ready to use
        self.app_version = self.config.get(constants.CONFIG_APP_VERSION)
        self.config_version = self.config.get(constants.CONFIG_APP_CONFIG_VERSION)
        self.config_source_descr = self.config.get(constants.CONFIG_APP_SOURCE_DESCR)

    def get(self, key: str):
        if self.config_source == constants.CONFIG_SOURCE_AZURE_APP_CONFIGURATION:
            return self.config.get(key)
        else:
            return os.getenv(key)
