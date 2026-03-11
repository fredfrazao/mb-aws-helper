"""Static configuration for AWS Helper."""

GRANTED_SSO_START_URL = "https://mb001.awsapps.com/start"
GRANTED_SSO_REGION = "eu-central-1"
DEFAULT_REGION = "eu-central-1"

ENV_MAP = {
    "prod": "PROD",
    "sandbox": "DEV",
    "dev": "DEV",
    "int": "INT",
    "integration": "INT",
}

PROFILE_PATTERNS = {
    "artifactory": "setart_SWFCS---SETART---Artifactory-{suffix}/1238-SwfDev",
    "gitlab": "setart_SWFCS---SETART---Gitlab-{suffix}/1238-SwfDev",
}

VALID_SERVICES = tuple(PROFILE_PATTERNS.keys())
VALID_SORT_ORDERS = ("asc", "desc")
RUNNING_STATES = {"Pending", "InProgress", "Delayed"}
DISCOVERY_CACHE_TTL_SECONDS = 30
