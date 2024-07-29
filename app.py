#####################################################################
## This is the main entry point for the commandline version
#####################################################################
import sys
from common_modules.common.common_logging import LogHelper
from common_modules.grass_weed_detection import GrassWeedDetector
from common_modules.common.common_config import ConfigHelper


def main():
    config = ConfigHelper()
    logger = LogHelper(config).configure_logging()
    logger.debug("app started...")

    detector = GrassWeedDetector(config, logger)

    # argv holds the command line args.
    #   e.g. python app.py
    #         - argv[0] will hold app.py
    #
    #      python app.py test.png
    #         - argv[0] will hold app.py,  argv[1] holds test.png

    processed_image = detector.analyze(sys.argv[1], 3)


if __name__ == "__main__":
    main()
