from enum import Enum

# e.g: 1.0.0
CONFIG_APP_VERSION = "ApiVersion"
CONFIG_API_BUILID_DATE = "ApiBuildDate"


CONFIG_CONFIG_SOURCE = "ConfigSource"
CONFIG_APP_CONFIG_VERSION = "AppConfigVersion"  # e.g: yymmdd.timestamp
CONFIG_APP_SOURCE_DESCR = "AppConfigDescr"

# possible values for the configuration source
# access the actual values from configuration or .env file
CONFIG_SOURCE_ENVIRONMENT_VARIABLES = "EnvironmentVariables"
CONFIG_SOURCE_AZURE_APP_CONFIGURATION = "AzureAppConfiguration"

# if using Azure App Configuration, this is the key to read the connection string from the environment variable
CONFING_AZURE_APP_CONFIGURATION_CONNECTION_STRING = "AzureConfigConnectionString"


DETECTED_TYPE_GRASS = "Grass"
DETECTED_TYPE_WEED = "Weed"

BOUNDING_BOX_COLOR_GRASS = "#FFDF00"
BOUNDING_BOX_COLOR_WEED = "#FF0000"

# some sample colors for drawing rectangles around detected objects
COLOR_RED_RED = "#FF0000"
COLOR_SCARLET_RED = "#FF2400"
COLOR_AMBER = "#FFBF00"
COLOR_CORAL_ORANGE = "#FF7F50"
COLOR_VERMILION_RED = "#D9381E"

COLOR_LIME = "#BFFF00"
COLOR_SPRING = "#A3C566"

COLOR_LIST = {}

# this is the default color for marking detected objects
COLOR_LIST[DETECTED_TYPE_GRASS] = COLOR_SPRING
COLOR_LIST[DETECTED_TYPE_WEED] = COLOR_VERMILION_RED

# keys for reading the color codes from the configuration
COLOR_CODE_GRASS = "ColorCodeGrass"
COLOR_CODE_WEED = "ColorCodeWeed"

# project information
CONFIG_PROJECT_NAME = "ProjectName"
CONFIG_PROJECT_ID = "ProjectId"
CONFIG_DEPLOYED_NAME = "DeployedName"

# azure vision api information
CONFIG_PREDICTION_ENDPOINT = "PredictionEndpoint"
CONFIG_PREDICTION_KEY = "PredictionKey"

# storage account information
CONFIG_TEST_DATA_STORAGE_ACCOUNT = "TestDataStorageAccount"

CONFIG_PREDICTIONS_STORAGE_ACCOUNT = "PredictionsStorageAccount"
CONFIG_PREDICTIONS_STORAGE_CONTAINER = "PredictionsStorageContainer"
CONFIG_PREDICTIONS_STORAGE_ACCOUNT_TOKEN = "WriteAccessToken"

CONFIG_DEFAULT_PREDICTION_IMAGE_FILE_NAME = "PredictionsImageFileName"
CONFIG_DEFAULT_PREDICTION_INFO_FILE_NAME = "PredictionsInfoFileName"


DetectionType = Enum("DetectionType", ["WEED", "GRASS", "BOTH"])

LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"

# - path to the log file - if you include a folder, make sure it exists.
# - if can be very tricky when deploying to cloud because
#   you may not have the luxury of creating a folder before the app is deployed!
# - so keep it simple, just specify the file name,
#   and the log file will be created in the same folder as the app.
CONFIG_LOG_PATH = "LogPath"

CONFIG_LOG_LEVEL = "LogLevel"
CONFIG_LOG_TO_FILE = "LogToFile"
