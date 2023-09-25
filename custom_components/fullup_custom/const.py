from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import ENERGY_WATT_HOUR, POWER_WATT, Platform, PERCENTAGE,VOLUME_LITERS

PLATFORMS = [Platform.SENSOR]

DOMAIN = "fullup_custom"

BASE_API_URL = "https://api.fullup.be"
NEW_TOKEN = "/auth/generate"
TANKS_ENDPOINT = "/tanks_public/"

# timeout for HTTP requests
TIMEOUT = 10
CONF_TANK ="tanks"
CONF_TANKID = "id"
CONF_TANKNAME ="name"

ATTR_TANK = "tank"
ATTR_STREET = "address_street"
ATTR_NUMBER = "address_number"
ATTR_POSTCODE = "address_postcode"
ATTR_COUNTRY = "address_country"
ATTR_OWNER_EMAIL = "owner_email"
ATTR_DEVICE_FULL_SERIAL = "device_full_serial"
ATTR_TANK_ID = "tank_id"
ATTR_TANK_NAME = "tank_name"
ATTR_TANK_USAGE = "tank_usage"
ATTR_TANK_DIAMETER = "tank_diameter"
ATTR_TANK_HEIGHT = "tank_height"
ATTR_TANK_LENGTH = "tank_length"
ATTR_TANK_CHIMNEY = "tank_chimney"
ATTR_TANK_SHAPE = "tank_shape"
ATTR_TANK_TOTAL_VOLUME = "tank_total_volume"
ATTR_TANK_NOTIFICATION_LEVEL = 'tank_notification_level'
ATTR_LAST_FILL = 'last_fill'
ATTR_LAST_FILL_DATE = 'last_fill_date'
ATTR_LAST_DRAIN = 'last_drain'
ATTR_LAST_DRAIN_DATE = 'last_drain_date'
ATTR_DAYS_LEFT_WASTING_OIL = 'days_left_wasting_oil'
ATTR_LAST_MEASURE_DATE = 'last_measure_date'
ATTR_CURRENT_VOLUME = 'current_volume'
ATTR_CURRENT_TEMPERATURE = 'current_temperature'
ATTR_BATTERY_LEVEL = 'battery_level'
ATTR_LAST_CONNECTION_DATE = 'last_connection_date'
ATTR_LAST_MINIMUM_LEVEL = 'last_minimum_level'

COORDINATOR = "coordinator"
NAME = "name"