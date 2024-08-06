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
    AnnotatedImageData,
    GrassPredictionData,
    GrassAnalysisDetails,
    MarkedDetectedArea,
)

from common_modules.common import constants
from common_modules.common.common_config import Config
from common_modules.common.common_utilities import (
    create_grass_detection_summary,
    generate_random_filename,
)
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
    ) -> AnnotatedImageData:  # GrassAnalysisResponse:

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
            ai_vision_response = prediction_client.detect_image(
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
                len(ai_vision_response.predictions)
            )
        )

        selected_predictions = self.get_top_n_predictions(
            ai_vision_response.predictions, top_n
        )

        annotated_image_data = mark_image_with_rectangle(
            image_data, selected_predictions, self.config, self.logger, detection_type
        )

        analysis_details = self.perform_post_detection_tasks(
            annotated_image_data.marked_areas
        )

        return analysis_details

    def get_top_n_predictions(
        self, ai_vision_predictions, top_n: int
    ) -> list[GrassPredictionData]:

        # put each category of predictions in its own list
        grass_predictions = self.filter_predictions_by_label(
            ai_vision_predictions, constants.DETECTED_TYPE_GRASS
        )
        weed_predictions = self.filter_predictions_by_label(
            ai_vision_predictions, constants.DETECTED_TYPE_WEED
        )

        # now sport the predictions by confidence level
        grass_predictions.sort(key=lambda x: x.probability, reverse=True)
        weed_predictions.sort(key=lambda x: x.probability, reverse=True)

        # now select the top n predictions
        selected_top_grass_predictions = []

        top_n = top_n if top_n > 0 else 1
        if top_n > len(grass_predictions):
            top_n = len(grass_predictions)
        selected_top_grass_predictions = grass_predictions[:top_n]

        if top_n > len(weed_predictions):
            top_n = len(weed_predictions)
        selected_top_weed_predictions = weed_predictions[:top_n]

        # now combine the selected predictions
        selected_predictions = selected_top_grass_predictions
        selected_predictions.extend(selected_top_weed_predictions)

        # convert the selected predictions to GrassPredictionData objects
        selected_predictions = [
            GrassPredictionData(
                prediction.tag_name, prediction.probability, prediction.bounding_box
            )
            for prediction in selected_predictions
        ]

        print(f"selected_predictions count: {len(selected_predictions)}")

        return selected_predictions

    def filter_predictions_by_label(self, predictions: any, label: str) -> any:
        return [
            prediction
            for prediction in predictions
            if prediction.tag_name.lower() == label.lower()
        ]

    def perform_post_detection_tasks(
        self, marked_areas: List[MarkedDetectedArea]
    ) -> GrassAnalysisDetails:
        """
        This method performs the following tasks:
        1. create a detection summary
        2. upload the detection summary to azure blob storage

        """

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

        analysis_details = GrassAnalysisDetails(
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
        prediction_details = json.dumps(analysis_details.to_dict())
        # write the prediction details to file for later use
        with open(
            self.config.get(constants.CONFIG_DEFAULT_PREDICTION_INFO_FILE_NAME), "w"
        ) as f:
            f.write(prediction_details)

        self.logger.debug(prediction_details)

        self.logger.debug("saving prediction information (json) to azure storage...")

        # use method from comoom to generate rendom file name for the prediction information
        # random_file_name = generate_random_filename("json")

        self.azure_storage_helper.write_prediction_details(
            self.config.get(constants.CONFIG_DEFAULT_PREDICTION_INFO_FILE_NAME)
        )

        self.azure_storage_helper.write_prediction_image(
            self.config.get(constants.CONFIG_DEFAULT_PREDICTION_IMAGE_FILE_NAME)
        )

        self.logger.debug("done saving prediction information (json) to azure storage.")

        return analysis_details
