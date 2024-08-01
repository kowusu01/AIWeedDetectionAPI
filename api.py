#####################################################################
# This is the main for the service that is used to detect grass and
# weed in an image. It uses the Custom Vision API to detect the
# objects in the image.
#####################################################################

import json
from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from fastapi.openapi.utils import get_openapi
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


api_description = """
Weed/Grass Detection API helps you to determine the presence of grass and weed in an image.

## What you can do with this API:

* **Analyze an image.**  
Use the api interaction with AI model to detected weed or grass in an image. You can upload an image or pick one of our preselected test images.


* **Read prediction details.**  
You can also query the detection details from the model, i.e. detected labels, confidence levels,etc.


* **Read an annotated image.**  
After an image is analyzed by the AI model, you can read back the annotated image with detected areas of grass or weed.


"""

api_version = "1.0.0"

# global objects
app = FastAPI(
    title="Weed/Grass Detection API",
    description=api_description,
    version=api_version,
    contact={"name": "Kwaku Owusu-Tieku", "email": "dev1.zkot2@gmail.com"},
)

default_router = APIRouter()
prediction_router = APIRouter()

config = setup_config()
logger = LogHelper(config, logger_name=__name__)
azure_storage = AzureBlobStorageHelper(config, logger)
detector = GrassWeedDetector(config, logger)
logger.info("api started...")
logger.info(
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


@default_router.get(
    "/",
    description="Get welcome message, it shows at least the app is running.",
    summary="Get welcome message.",
)
def read_root() -> JSONResponse:
    """Default endpoint for the service. Returns a welcome message.

    Returns:

         - string: welcome message
    """
    version = f"v{api_version}"

    # revision is date of last update.time of day
    revision = "0730.2009"

    message = "Hello, and welcome to Azure AI Vision, Python, and FastApi! -  ({} rev {})".format(
        version, revision
    )
    print(message)
    return JSONResponse(
        {"greetings": message},
        media_type="application/json",
    )


class PredictionEndpoint:

    @staticmethod
    @prediction_router.get(
        "/details/{filename}",
        description="Read the prediction details.",
        summary="Read the prediction details.",
    )
    def read_prediction_details(filename: str) -> JSONResponse:
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
        print(f"api called for prediction details: {filename}")
        # all images are stored in azure blob storage
        # given a file name, read the image from azure blob storage
        try:
            json_data = azure_storage.read_prediction_details(filename)
            json_string = json.loads(json_data)
            print(f"prediction details: {json_string}")
            print(json_string)
            return JSONResponse(json_string, media_type="application/json")
        except Exception as e:
            logger.error(f"unable to read prediction details: {e}")
            logger.error(traceback.format_exc())
            print(f"unable to read prediction details {e}")
            raise HTTPException(
                status_code=400,
                detail="unable to read prediction details, see logs for details.",
            )

    @staticmethod
    @prediction_router.get(
        "/image/{filename}",
        description="Read the analyzed/annotated image.",
        summary="Read the analyzed/annotated image.",
    )
    def read_prediction_image(filename: str) -> Response:
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
        print(f"api called for prediction image: {filename}")
        try:
            # all images are stored in azure blob storage
            #  given a file name, read the image from azure blob storage
            image_file = azure_storage.read_prediction_image(filename)
            print(f"prediction image has successfully been read: {filename}")
            return Response(image_file, media_type="image/jpeg")
        except Exception as e:
            logger.error(f"unable to read prediction image: {e}")
            logger.error(traceback.format_exc())
            print(f"unable to read prediction image: {e}")
            raise HTTPException(
                status_code=400,
                detail="unable to read prediction image, see logs for details.",
            )

    @staticmethod
    @prediction_router.post(
        "/analyze/filename/{file}",
        description="Analyze the selected test image stored on our server.",
        summary="Analyze the selected test image stored on our server.",
    )
    async def analyze_with_filename(file) -> JSONResponse:
        """Analyze the selected test image stored on the server and return the prediction details.

        Args:

            - filename (string: name of the test image to analyze.

        Raises:

            - HTTPException: HTTPException with status code 400 if the file is not found.

        Returns:

                - JSONResponse: JSON response containing the prediction details.
        """
        logger.debug("/analyze/filename invoked")
        print(f"api - /analyze/filename endpoint invoked with file: {file}")
        if not file:
            raise HTTPException(status_code=400, detail="No filename provided")

        logger.debug(f"api - filename provided for analysis : {file}")

        # analyze the image and save prediction to result to azure blob storage
        logger.debug("api - analyzing image...")
        print("api - analyzing image...")
        return PredictionEndpoint.analyze_image(file)

    @staticmethod
    @prediction_router.post(
        "/analyze/file",
        description="Analyze an uploaded image.",
        summary="Analyze an uploaded image.",
    )
    async def analyze(file: UploadFile = File(...)) -> JSONResponse:
        """Analyze an uploaded image and return the prediction details.

        Args:

            - file (UploadFile): File to analyze

        Raises:

            - HTTPException: HTTPException with status code 400 if the file cannot be analyzed.

        Returns:

                - JSONResponse: JSON response containing the prediction details.
        """
        logger.debug("api - /analyze/file endpoint invoked.")
        print("api - /analyze/file endpoint invoked.")
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
        print("api - analyzing image...")
        return PredictionEndpoint.analyze_image(image)

    @staticmethod
    def analyze_image(image: any):

        print("api - inside generic method analyze image...")
        try:
            response = detector.analyze(image, MAX_PREDICTIONS)
            logger.debug("api - analyzing image complete.")
            print("api - analyzing image complete.")

            # response_json = json.dumps(response.to_dict())
            # return the prediction details without the image, needs to do a fetch to get the image
            return JSONResponse(response.to_dict(), media_type="application/json")
        except Exception as e:
            logger.error(f"unable to analyze image: {e}")
            logger.error(traceback.format_exc())
            print(f"unable to analyze image: {e}")

            raise HTTPException(
                status_code=400, detail="unable to analyze image, see logs for details."
            )


app.include_router(default_router, tags=["Default endpoint"])
app.include_router(
    prediction_router, prefix="/prediction", tags=["Prediction endpoint"]
)
