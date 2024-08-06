####################################################################
# This file contains the utility functions that are used to process
# the images. Currently, it is used for mark the detected objects
# with rectangles
####################################################################

# IMPORT LIBRARIES
# 1. import libraries that are part of the standard python library
import io
from logging import Logger
from typing import List

# 2. import libraries that require inbstallation
from PIL import Image, ImageDraw

# from the matplotlib library
from matplotlib import pyplot as plt

# 3. import my own libraries
from common_modules.common.models import (
    AnnotatedImageData,
    GrassPredictionData,
    MarkedDetectedArea,
)
from common_modules.common.common_config import Config
from common_modules.common import constants


def mark_image_with_rectangle(
    image_data: bytes,
    image_properties: list[GrassPredictionData],
    config: Config,
    logger: Logger,
    markWhat: constants.DetectionType = constants.DetectionType.WEED,
) -> AnnotatedImageData:
    """
    Marks the image with rectangles around detected objects.
    It called after an image has been processed by the model
    and the detected objects are returned.

    parameters:
    - image_data: bytes - the image im PIL format
    - image_properties: list[GrassPredictionData] - the detected objects
    """

    logger.debug("marking detected areas of the image with rectangles...")

    # open the image from the url to mark the detected areas
    byte_stream = io.BytesIO(image_data)

    # Open the image file
    image = Image.open(byte_stream)

    # get basic image properties
    # the image dimensions are given as a tuple (width, height)
    image_width = image.size[0]
    image_height = image.size[1]

    # prepare the plotting for the inmemory editing to take place
    fig = plt.figure(figsize=(image.width / 100, image.height / 100))
    plt.axis("off")
    draw = ImageDraw.Draw(image)

    color = constants.BOUNDING_BOX_COLOR_GRASS

    marked_areas = []

    count = 0
    # Draw object bounding box
    for detected_object in image_properties:
        rect = detected_object.bounding_box

        ########################################################################
        #
        # calculating coordinates, width and heights
        # The bounding box coordinates are given as :
        # - rect.left: the x coordinate of the leftmost point of the bounding box
        # - width and height of the box
        #
        ########################################################################
        # bounding box coordinates are given as a percentage of the original image
        # for instance,
        # - the rightmost x point of the image will be 1.0
        #   - e.g. rightmost point of 5000 pixel wide image, x will be 1.0 * 5000 = 5000
        # - midpoint wil be 0.5
        #   - e.g. midpoint of 5000 pixel wide image, x will be 0.5 * 5000 = 2500
        #
        bounding_box = (
            (rect.left * image_width, rect.top * image_height),
            (
                rect.left * image_width + rect.width * image_width,
                rect.top * image_height + rect.height * image_height,
            ),
        )

        color: str = None
        if detected_object.name == constants.DETECTED_TYPE_GRASS:
            color = config.get(constants.COLOR_CODE_GRASS)
        elif detected_object.name == constants.DETECTED_TYPE_WEED:
            color = config.get(constants.COLOR_CODE_WEED)

        # if color is not found in the configuration, use the default color
        if color == "" or color == None:
            color = constants.COLOR_LIST[detected_object.name]

        draw.rectangle(bounding_box, outline=color, width=7)

        marked_area = MarkedDetectedArea(
            name=detected_object.name,
            confidence_level=detected_object.confidence_level,
            marked_color=color,
            bounding_box=bounding_box,
        )
        marked_areas.append(marked_area)
        count += 1

    # save the image with the marked areas
    # Save annotated image
    plt.imshow(image)
    plt.tight_layout(pad=0)
    fig.savefig(config.get(constants.CONFIG_DEFAULT_PREDICTION_IMAGE_FILE_NAME))

    annotated_image_data = AnnotatedImageData(image=image, marked_areas=marked_areas)

    logger.debug("--------- image processing complete. ------------")
    return annotated_image_data
