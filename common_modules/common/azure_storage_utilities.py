from logging import Logger
import requests
from azure.storage.blob import BlobClient
from common_modules.common import constants
from common_modules.common.common_config import Config as Config


class AzureBlobStorageHelper:
    """
    This class It is meant to simplify the usage of common Azure Blob Storage tasks.
    Am sure there are many ways to interact with Azure Blob Storage, but
    this is one way that addressed my issue.

      Concern:
      - given an azure storage account, and blob storage container,
          how do I upload a files to the container?

      Solution:
      1. create azure storage account
      2. create a container in the storage account
      3. note the following:
          - container url:
          https://<your_storage_account_name>.blob.core.windows.net/<continername>/
          - container name: <containername>
      4. create a shared access signature (SAS) token for the storage account
          for the container.
      - IMPORTANT: create the container with the right access level just for
          that container, and not for the whole storage account.
      5. note the sas token

       Usage:
    - I intentionally forced a Config class as a parameter to the constructor
      to encourage the configuration to be centralized in one place.
    - The Config class is a simple class that holds the configuration for the
    - the application

    """

    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger

    def write_blob_with_token(
        self, storage_account, container, filename: str, token: str
    ):
        """
        Write a file to an azure blob storage account using a shared access token.
        This methods can write both images and json files.
        """
        blob_client = BlobClient(
            account_url=storage_account,
            container_name=container,
            blob_name=filename,
            credential=token,
        )
        blob_data = None
        with open(filename, "rb") as f:
            blob_data = f.read()

        return blob_client.upload_blob(blob_data, overwrite=True)

    def write_prediction_details(self, filename: str):
        """
        For my specific use case, it writes a file to a specific storage account.
        In this case, it writes to the predictions container.
        """
        return self.write_blob_with_token(
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_ACCOUNT),
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_CONTAINER),
            filename,
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_ACCOUNT_TOKEN),
        )

    def write_prediction_image(self, filename: str):
        """
        For my specific use case, it writes a file to a specific storage account.
        In this case, it writes to the predictions container.
        """
        return self.write_blob_with_token(
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_ACCOUNT),
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_CONTAINER),
            filename,
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_ACCOUNT_TOKEN),
        )

    def read_image_with_url_anonymous(
        self, storage_account_url: str, filename: str
    ) -> bytes:
        """
        This is the base method to read an image from an azure blob storage account.
        It is meant to be used when the blob storage account is public.
        """
        image_url = "{}{}".format(storage_account_url, filename)
        self.logger.debug(f"image path:{image_url}")
        image_data = requests.get(image_url, stream=True).content
        # self.logger.debug(f"image data:{image_data}")
        return image_data

    def read_test_data_image_with_url_anonymous(self, filename: str) -> bytes:
        """
        For my specific use case, it reads an image from the default storage account.
        In this case, it reads from the test data container.
        """
        return self.read_image_with_url_anonymous(
            self.config.get(constants.CONFIG_TEST_DATA_STORAGE_ACCOUNT), filename
        )

    def read_image_with_token(
        self, storage_account_url: str, container: str, filename: str, token: str
    ) -> bytes:
        blob_client = BlobClient(
            account_url=storage_account_url,
            container_name=container,
            blob_name=filename,
            credential=token,
        )
        image_blob = blob_client.download_blob().readall()
        return image_blob

    def read_prediction_image(self, filename: str) -> bytes:
        self.logger.debug(
            f"reading prediction image for {filename}, {self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_CONTAINER)}"
        )
        return self.read_image_with_token(
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_ACCOUNT),
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_CONTAINER),
            filename,
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_ACCOUNT_TOKEN),
        )

    def read_text_json_with_token(
        self, storage_account_url: str, container: str, filename: str, token: str
    ) -> str:
        self.logger.debug(
            f"storage_account_url:{storage_account_url}, container:{container}, filename:{filename}"
        )
        blob_client = BlobClient(
            account_url=storage_account_url,
            container_name=container,
            blob_name=filename,
            credential=token,
        )
        json_blob = blob_client.download_blob().content_as_text()
        self.logger.debug(f"text data:{json_blob}")
        return json_blob

    def read_prediction_details(self, filename: str) -> str:
        self.logger.debug(
            f"reading prediction details for {filename}, {self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_CONTAINER)}"
        )
        return self.read_text_json_with_token(
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_ACCOUNT),
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_CONTAINER),
            filename,
            self.config.get(constants.CONFIG_PREDICTIONS_STORAGE_ACCOUNT_TOKEN),
        )
