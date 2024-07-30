#####################################################################
# This is the main for the service that is used to detect grass and
# weed in an image. It uses the Custom Vision API to detect the
# objects in the image.
#####################################################################

import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import traceback

# import my own libraries
from common_modules.common import constants
from common_modules.common.common_logging import LogHelper
from common_modules.grass_weed_detection import GrassWeedDetector
from common_modules.common.common_config import Config
from common_modules.common.azure_storage_utilities import AzureBlobStorageHelper

# maximum number of predictions to return
MAX_PREDICTIONS = 2


def setup_config() -> Config:
    config = Config()
    return config


# global objects
app = FastAPI()
config = setup_config()
logger = LogHelper(config, logger_name=__name__)
azure_storage = AzureBlobStorageHelper(config, logger)
detector = GrassWeedDetector(config, logger)
logger.info("app started...")
logger.debug(
    f"version: {config.get(constants.CONFIG_APP_VERSION)} - ConfigSource: {config.get('ConfigSource')}"
)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Default endpoint for the service. Returns a welcome message.

    Returns:

         - string: welcome message
    """
    return {
        "greetings": "Hello, and welcome to Azure AI Vision and Python! (v1.0.2 rev.0729:1453)"
    }


@app.get("/prediction/details/{filename}")
def read_root(filename: str):
    """Reads the prediction details from the server.
       Prediction details are json files containing predictions (Grass/Weed)
       and the confidence levels. The name of the file is returned by the
       call to the analyze endpoint.

    Args:

        - filename (str): name of the file containing the prediction details
        as returned by the analyze endpoint. E.g. sample.json

    HTTPException:

        - HTTPException with status code 400 if the file is not found.

    Returns:

        - json: json string containing the prediction details.
    """

    # all images are stored in azure blob storage
    # given a file name, read the image from azure blob storage
    try:
        json_data = azure_storage.read_prediction_details_json(filename)
        json_string = json.dumps(json_data)
        return JSONResponse(json_string)
    except Exception as e:
        logger.error(f"unable to read prediction details: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=400,
            detail="unable to read prediction details, see logs for details.",
        )


@app.get("/prediction/image/{filename}")
def read_root(filename: str):
    """Reads the analyzed and annotated image after the image analysis is completed.
        In the analyzed image, there are marked areas of detected grass and/or weed if the model is able to detect any.

    Args:

        - filename (str): name of the file containing the prediction details
        as returned by the analyze endpoint. E.g. sample.jpg

    HTTPException:

        - HTTPException with status code 400 if the file is not found.

    Returns:
        - Image: image file
    """

    try:
        # all images are stored in azure blob storage
        #  given a file name, read the image from azure blob storage
        image_file = azure_storage.read_prediction_image(filename)
        return Response(image_file, media_type="image/jpeg")
    except Exception as e:
        logger.error(f"unable to read prediction image: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=400,
            detail="unable to read prediction image, see logs for details.",
        )


# /analyze/filename/test-9-mixed.JPG
@app.post(
    "/analyze/filename/{file}",
)
async def analyze_with_filename(file):
    """Analyze the selected test image stored on the server and return the prediction details.

    Args:

        - filename (string: name of the test image to analyze.

    Raises:

        - HTTPException: HTTPException with status code 400 if the file is not found.

    Returns:

            - JSONResponse: JSON response containing the prediction details.
    """
    logger.debug("/analyze/filename invoked")
    if not file:
        raise HTTPException(status_code=400, detail="No filename provided")

    logger.debug(f"api - filename provided for analysis : {file}")

    # analyze the image and save prediction to result to azure blob storage
    logger.debug("api - analyzing image...")
    return analyze_image(file)


@app.post(
    "/analyze/file",
)
async def analyze(file: UploadFile = File(...)):
    """Analyze the uploaded image and return the prediction details.

    Args:

        - file (UploadFile): File to analyze

    Raises:

        - HTTPException: HTTPException with status code 400 if the file cannot be analyzed.

    Returns:

            - JSONResponse: JSON response containing the prediction details.
    """
    logger.debug("api - /analyze/file endpoint invoked.")
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    logger.debug(f"api - filename provided for analysis: {file.filename}")

    # read the image as bytes
    image = None
    try:
        image = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="unable to analyze image, see logs for details."
        )

    # call the detector to analyze the image and save predictions to azure blob storage
    logger.debug("api - analyzing image...")
    return analyze_image(image)


def analyze_image(image: any):
    try:
        response = detector.analyze(image, MAX_PREDICTIONS)
        logger.debug("api - analyzing image complete.")

        response_json = json.dumps(response.to_dict())
        # return the prediction details without the image, needs to do a fetch to get the image
        return JSONResponse(response_json)
    except Exception as e:
        logger.error(f"unable to analyze image: {e}")
        logger.error(traceback.format_exc())

        raise HTTPException(
            status_code=400, detail="unable to analyze image, see logs for details."
        )
