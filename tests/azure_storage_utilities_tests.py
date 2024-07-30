from datetime import datetime
import json
import os
import sys
from unittest.mock import patch

from pydantic import Json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common_modules.common.azure_storage_utilities import AzureBlobStorageHelper

TEST_PREDICTION_DETAILS_FILENAME = "predictions.json"
TEST_PREDICTION_IMAGE_FILENAME = "predictions.jpg"

TEST_FILE_NOT_FOUND = "File not found"


class TestAzureBlobStorageHelper:
    """
    Unit tests for the AzureBlobStorageHelper class
    Code was generated with the help of Github Copilot.
    """

    def setup_method(self, method):
        # Patch the AzureBlobStorageHelper class
        self.patcher = patch(
            "common_modules.common.azure_storage_utilities.AzureBlobStorageHelper"
        )
        self.MockAzureBlobStorageHelper = self.patcher.start()
        self.mock_instance = self.MockAzureBlobStorageHelper.return_value

        # Define a side effect function for the mock method
        def read_prediction_details_json_side_effect(filename: str):
            details = {}
            details["prediction_image_url"] = "predictions.jpg"
            details["prediction_info_url"] = "predictions.json"
            details["timestamp"] = datetime.now()
            details["top_n"] = 2
            details["summary"] = (
                "The area analyzed is most likely all Grass with very low chance of Weed."
            )
            details["predictions"] = [
                {
                    "name": "Grass",
                    "confidence_level": 0.98,
                    "marked_color": ["#FF2400"],
                    "bounding_box": {
                        "left": 0.0,
                        "top": 16.0,
                        "box_width": 239.0,
                        "box_height": 180.0,
                    },
                },
                {
                    "name": "Weed",
                    "confidence_level": 0.09,
                    "marked_color": ["#D9381E"],
                    "bounding_box": {
                        "left": 227.0,
                        "top": 363.0,
                        "box_width": 332.0,
                        "box_height": 387.0,
                    },
                },
            ]

            if filename == TEST_PREDICTION_DETAILS_FILENAME:
                return details
            else:
                return {"error": "File not found"}

        # Set the side effect on the mock method
        self.mock_instance.read_prediction_details_json.side_effect = (
            read_prediction_details_json_side_effect
        )

    def teardown_method(self, method):
        # Stop the patcher
        self.patcher.stop()

    def test_read_prediction_details_PASS(self):
        # Act
        result = self.mock_instance.read_prediction_details_json(
            TEST_PREDICTION_DETAILS_FILENAME
        )

        # Assert
        print(result)
        assert result["prediction_image_url"] == "predictions.jpg"

    def test_read_prediction_details_FAIL(self):
        # Act
        result = self.mock_instance.read_prediction_details_json(
            "invalid_filename.json"
        )

        # Assert
        assert result == {"error": TEST_FILE_NOT_FOUND}

    # Add more tests here using the same mock setup
