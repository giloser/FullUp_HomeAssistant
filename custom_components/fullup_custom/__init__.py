import logging
from datetime import timedelta
from homeassistant import config_entries, core
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import (
    CONF_NAME,CONF_USERNAME,
    PERCENTAGE,
    VOLUME,
    ELECTRIC_POTENTIAL_VOLT,CONF_ACCESS_TOKEN, CONF_PASSWORD
)
import json
from .fullup import FullUp
from .const import (
    BASE_API_URL,
    CONF_TANKID,CONF_TANK,ATTR_TANK,TANKS_ENDPOINT,ATTR_LAST_CONNECTION_DATE,DOMAIN,ATTR_BATTERY_LEVEL,ATTR_TANK_TOTAL_VOLUME,ATTR_LAST_MINIMUM_LEVEL,COORDINATOR,NAME,PLATFORMS
)

SCAN_INTERVAL = timedelta(minutes=60)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.warning(f"async_setup_entry => entry.data={entry.data}")
    
    config = entry.data
    name = DOMAIN #config[CONF_NAME]
    serial = entry.data[CONF_USERNAME]
    async def async_update_data():
        try:
            _LOGGER.warning(f"async_update_data")
            for tank in config[CONF_TANK]:
                name = tank["name"]
                tank_id = tank["id"]
                tank_url = f"{TANKS_ENDPOINT}{tank_id}"
                string = '{"username":"","password":"","token":""}'
                data = json.loads(string)
                data['username']=config[CONF_USERNAME]
                data["password"]=config[CONF_PASSWORD]
                if CONF_ACCESS_TOKEN in config:
                    data["token"]=config[CONF_ACCESS_TOKEN]
                session = async_get_clientsession(hass)
                vAuth = FullUp(session,data)

                tank_res = await vAuth.getitem(tank_url)
                tank_data = tank_res['result']
                
                _LOGGER.warning(f"async_update_data Getting account details... tank_data={tank_data}")

                #totalvolume = tank_data[ATTR_TANK_TOTAL_VOLUME]
                #volume = tank_data[ATTR_LAST_MINIMUM_LEVEL]
                #voltage = tank_data[ATTR_BATTERY_LEVEL]
                #percent =  ((100* ((tank_data[ATTR_BATTERY_LEVEL]|float) -2.2)/(3-2.2)) | int ) 
                data = tank_data

                return data
        except Exception as error:
            _LOGGER.exception(f"Error retrieving data from FullUp. => {error}")

        return



    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"fullup {name}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL
        
    )
    coordinator.data = config

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        NAME: name,
        "DATA":entry.data,
    } #entry.data

    hass.config_entries.async_update_entry(entry, unique_id=serial)

    # Forward the setup to the sensor platform.
    #hass.async_create_task(
        #hass.config_entries.async_forward_entry_setup(entry, "sensor")
        #hass.config_entries.async_forward_entry_setup(entry, PLATFORMS)
    #hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    #)
    return True


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the GitHub Custom component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True

 
    
