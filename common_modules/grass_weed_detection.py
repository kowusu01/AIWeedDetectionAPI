#####################################################################
# This is the main for the service that is used to detect grass and
# weed in an image. It uses the Custom Vision API to detect the
# objects in the image.
#####################################################################
# 1. import libraries that are part of the standard python library
from datetime import datetime
from logging import Logger
from typing import List

# 2. import azure libraries and other third party libraries
import json

from azure.cognitiveservices.vision.customvision.prediction import (
    CustomVisionPredictionClient,
)
from azure.cognitiveservices.vision.customvision.training.models import (
    CustomVisionErrorException,
)
from msrest.authentication import ApiKeyCredentials

# 3. import my own libraries
from common_modules.common.models import (
    GrassPredictionData,
    GrassAnalysisResponse,
    MarkedDetectedArea,
)

from common_modules.common import constants
from common_modules.common.common_config import Config
from common_modules.common.common_utilities import create_grass_detection_summary
from common_modules.common.azure_storage_utilities import AzureBlobStorageHelper
from common_modules.image_processing.image_utilities import mark_image_with_rectangle


class GrassWeedDetector:
    def __init__(self, config: Config, logger: Logger) -> None:
        self.config = config
        self.logger = logger
        self.azure_storage_helper = AzureBlobStorageHelper(self.config, self.logger)

    def analyze(
        self,
        image: any,
        top_n: int,
        detection_type: constants.DetectionType = constants.DetectionType.WEED,
    ) -> GrassAnalysisResponse:

        self.logger.debug("GrassDectector.analyze() - analyzing image...")
        self.logger.debug(
            "GrassDectector.analyze() - setting up credential for Azure vision api..."
        )
        # Authenticate a client
        credentials = ApiKeyCredentials(
            in_headers={
                "Prediction-key": self.config.get(constants.CONFIG_PREDICTION_KEY)
            }
        )
        prediction_client = CustomVisionPredictionClient(
            endpoint=self.config.get(constants.CONFIG_PREDICTION_ENDPOINT),
            credentials=credentials,
        )
        self.logger.debug(
            "GrassDectector.analyze() - done setting up credential for Azure vision api."
        )
        self.logger.debug(
            "GrassDectector.analyze() - checking input type - image object or image url?..."
        )
        if isinstance(image, str):
            self.logger.debug("GrassDectector.analyze() - input type is image url.")
            image_data = (
                self.azure_storage_helper.read_test_data_image_with_url_anonymous(
                    filename=image
                )
            )

            if len(image_data) == 0:
                self.logger.debug(
                    "GrassDectector.analyze() - image could not be loaded from url."
                )
                raise ValueError(f"file not found: {image}.")
            self.logger.debug(
                "GrassDectector.analyze() - image has been loaded from url."
            )
        elif isinstance(image, bytes):
            self.logger.debug("GrassDectector.analyze() - input type is bytes.")
            image_data = image
        else:
            self.logger.debug("GrassDectector.analyze() - upsupported input type.")
            raise ValueError("GrassDectector.analyze() - image type not supported")

        self.logger.debug(
            "GrassDectector.analyze() - ready to call vision api for analysis."
        )
        try:
            results = prediction_client.detect_image(
                self.config.get(constants.CONFIG_PROJECT_ID),
                self.config.get(constants.CONFIG_DEPLOYED_NAME),
                image_data,
            )
            self.logger.debug(
                "GrassDectector.analyze() - analysis from vision api complete."
            )
        except CustomVisionErrorException as ex:
            self.logger.error(ex)

        self.logger.debug(
            "GrassDectector.analyze() - analysis complete. detected areas: {}".format(
                len(results.predictions)
            )
        )
        selected_predictions = self.process_analysis_results(results, top_n)
        predictions = mark_image_with_rectangle(
            image_data, selected_predictions, self.config, self.logger, detection_type
        )

        analysis_response = self.perform_post_detection_tasks(predictions)

        return analysis_response

    def process_analysis_results(
        self, results, top_n: int
    ) -> list[GrassPredictionData]:

        grass_predictions = {}
        weed_predictions = {}

        for prediction in results.predictions:
            # self.logger.debug(prediction)
            if prediction.tag_name == constants.DETECTED_TYPE_GRASS:
                grass_predictions[round(prediction.probability, 2)] = (
                    GrassPredictionData(
                        prediction.tag_name,
                        round(prediction.probability, 2),
                        prediction.bounding_box,
                    )
                )
            else:
                weed_predictions[round(prediction.probability, 2)] = (
                    GrassPredictionData(
                        prediction.tag_name,
                        round(prediction.probability, 2),
                        prediction.bounding_box,
                    )
                )

        self.logger.debug(
            f"GrassDectector.analyze() - grass areas: {len(grass_predictions)}, weed areas: {len(weed_predictions)}"
        )

        selected_predictions = []
        if len(grass_predictions) == 0 and len(weed_predictions) == 0:
            self.logger.debug(
                "GrassDectector.analyze() - no grass or weed detected. returning empty list."
            )
            return selected_predictions

        # attempt to select items for grass
        if len(grass_predictions) == 0:
            self.logger.debug("GrassDectector.analyze() - no grass detected.")
        elif len(grass_predictions) == 1:
            self.logger.debug(
                "GrassDectector.analyze() - one grass detected, it will be added to the selected predictions."
            )
            grass_keys = list(grass_predictions.keys())
            grass_keys.sort(reverse=True)
            selected_predictions.append(grass_predictions[grass_keys[0]])
        else:
            self.logger.debug("GrassDectector.analyze() - multiple grass detected.")
            if len(weed_predictions) == 0:
                self.logger.debug(
                    "GrassDectector.analyze() - no weed detected, so we pick two top grass predictions"
                )
                grass_keys = list(grass_predictions.keys())
                grass_keys.sort(reverse=True)
                selected_predictions.append(grass_predictions[grass_keys[0]])
                selected_predictions.append(grass_predictions[grass_keys[1]])
                return selected_predictions
            else:
                self.logger.debug(
                    "GrassDectector.analyze() - weed detected, so we pick the top 1 grass prediction"
                )
                grass_keys = list(grass_predictions.keys())
                grass_keys.sort(reverse=True)
                selected_predictions.append(grass_predictions[grass_keys[0]])
                # continue to weed selection

        self.logger.debug("selcted predictions: {len(selected_predictions)}")
        # attempt to select items for weed
        # we should max one item in the selected_predictions list
        if len(weed_predictions) == 1:
            weed_keys = list(weed_predictions.keys())
            selected_predictions.append(weed_predictions[weed_keys[0]])
        elif len(weed_predictions) > 1:
            weed_keys = list(weed_predictions.keys())
            weed_keys.sort(reverse=True)
            selected_predictions.append(weed_predictions[weed_keys[0]])
        else:
            self.logger.debug("GrassDectector.analyze() - no weed detected.")
            return selected_predictions

        self.logger.debug(
            f"GrassDectector.analyze() - selected predictions: {len(selected_predictions)}"
        )
        return selected_predictions

    def perform_post_detection_tasks(
        self, marked_areas: List[MarkedDetectedArea]
    ) -> GrassAnalysisResponse:
        """
        a copy of the image with the detected areas marked should be saved to the local file system
        1. upload it to azure blob storage
        2. create a detection summary
        3. save the detection summary to the local file system
        4. upload the detection summary to azure blob storage

        """

        self.logger.debug(
            "saving copy of the annotated/predicted image to azure storage..."
        )

        # 1.  save to azure blob storage
        azure_storage_helper = AzureBlobStorageHelper(self.config, self.logger)
        self.logger.debug("azure storage helper created.")
        azure_storage_helper.write_prediction_image_with_token(
            self.config.get(constants.CONFIG_DEFAULT_PREDICTION_IMAGE_FILE_NAME)
        )

        self.logger.debug(
            "done saving annotated/predicted image has been saved to azure storage."
        )

        self.logger.debug("creating final response object...")

        grass_confidence = 0.0
        weed_confidence = 0.0

        weed = [item for item in marked_areas if item.name == "Weed"]
        grass = [item for item in marked_areas if item.name == "Grass"]
        if len(weed) > 0:
            weed_confidence = weed[0].confidence_level
        if len(grass) > 0:
            grass_confidence = grass[0].confidence_level

        self.logger.debug(
            f"grass confidence: {grass_confidence}, weed confidence: {weed_confidence}"
        )

        self.logger.debug("creating a simple prediction summary information...")
        summary = create_grass_detection_summary(grass_confidence, weed_confidence)
        self.logger.debug(summary)

        self.logger.debug(
            self.config.get(constants.CONFIG_DEFAULT_PREDICTION_IMAGE_FILE_NAME)
        )
        self.logger.debug(
            self.config.get(constants.CONFIG_DEFAULT_PREDICTION_INFO_FILE_NAME)
        )

        result = GrassAnalysisResponse(
            predictions_image_url=self.config.get(
                constants.CONFIG_DEFAULT_PREDICTION_IMAGE_FILE_NAME
            ),
            predictions_info_url=self.config.get(
                constants.CONFIG_DEFAULT_PREDICTION_INFO_FILE_NAME
            ),
            timestamp=datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
            top_n=len(marked_areas),
            summary=summary,
            detected_details=marked_areas,
        )
        self.logger.debug(json.dumps(result.to_dict()))

        self.logger.debug(
            "saving prediction information (json) to local file system..."
        )
        with open(
            self.config.get(constants.CONFIG_DEFAULT_PREDICTION_INFO_FILE_NAME), "w"
        ) as f:
            json.dump(result.to_dict(), f)

        self.logger.debug("saving prediction information (json) to azure storage...")
        azure_storage_helper.read_prediction_details_json_with_token(
            self.config.get(constants.CONFIG_DEFAULT_PREDICTION_INFO_FILE_NAME)
        )
        self.logger.debug(
            "done saving prediction information (json) to local file system."
        )
        self.logger.debug("done creating final response object.")
        return result
