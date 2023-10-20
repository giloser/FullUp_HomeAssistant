"""GitHub sensor platform."""
import logging
import re
from datetime import timedelta
from typing import Any, Callable, Dict, Optional
from urllib import parse

from .fullup import FullUp 
from datetime import datetime
import voluptuous as vol
from aiohttp import ClientError

from time import strftime, localtime

import json

from homeassistant import config_entries, core
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity,SensorDeviceClass,SensorEntityDescription,SensorStateClass,PLATFORM_SCHEMA

from homeassistant.const import (
    ATTR_NAME,
    CONF_ACCESS_TOKEN,
    CONF_USERNAME,
    CONF_PASSWORD,
    PERCENTAGE,
    VOLUME,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_WATT_HOUR, POWER_WATT, Platform, PERCENTAGE,VOLUME_LITERS
)
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
from homeassistant.util import Throttle

from .const import (
    BASE_API_URL,
    CONF_TANKID,CONF_TANK,ATTR_TANK,TANKS_ENDPOINT,ATTR_LAST_CONNECTION_DATE,DOMAIN,ATTR_BATTERY_LEVEL,ATTR_TANK_TOTAL_VOLUME,ATTR_LAST_MINIMUM_LEVEL,COORDINATOR,NAME
)


_LOGGER = logging.getLogger(__name__)
# Time between updating data from GitHub
SCAN_INTERVAL = timedelta(minutes=60)
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=60)

TANK_SCHEMA = vol.Schema(
    {vol.Required(CONF_TANKID): cv.string}
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_TANKID): vol.All(cv.ensure_list, [TANK_SCHEMA]),
    }
)

async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    dataconf = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = dataconf[COORDINATOR]
    config = coordinator.data
    _LOGGER.warning(f"async_setup_entry  || config={config}")
    _LOGGER.warning(f"async_setup_entry  || config_entry.entry_id={config_entry.entry_id}")
    session = async_create_clientsession(hass)
    string = '{"username":"","password":"","token":""}'
    #data["username"]=config[CONF_USERNAME]
    #data["password"]=config[CONF_PASSWORD]
    #data["token"]=config[CONF_ACCESS_TOKEN]
    data = json.loads(string)

    data['username']=config[CONF_USERNAME]
    data["password"]=config[CONF_PASSWORD]
    if CONF_ACCESS_TOKEN in config:
        data["token"]=config[CONF_ACCESS_TOKEN]

    coordinator = dataconf[COORDINATOR]
    name = dataconf[NAME]
    vAuth = FullUp(session,data)
    #github = GitHubAPI(session, "requester", oauth_token=config[CONF_ACCESS_TOKEN])
    #sensors = [FullUpTankSensor(vAuth, tank) for tank in config[CONF_TANK]]
    sensors = []
    
    for tank in config[CONF_TANK]:
        name = tank["name"]
        _LOGGER.warning(f"async_setup_entry => tank={tank}")
        id=tank["id"]
        tank["id_sensor"] = f"{id}"
        sensors.append(FullUpTankSensor(vAuth, tank,coordinator))
        tank["name"] = f"{name}_volume"
        tank["id_sensor"] = f"{id}_volume"
        sensors.append(FullUpTankVolumeEntity(vAuth, tank,coordinator,ATTR_LAST_MINIMUM_LEVEL))
        tank["name"] = f"{name}_total_volume"
        tank["id_sensor"] = f"{id}_total_volume"
        sensors.append(FullUpTankVolumeEntity(vAuth, tank,coordinator,ATTR_TANK_TOTAL_VOLUME))
        tank["name"] = f"{name}_battery_level"
        tank["id_sensor"] = f"{id}_battery_level"
        sensors.append(FullUpTankBatteryEntity(vAuth, tank,coordinator))
        tank["name"] = f"{name}_content"
        tank["id_sensor"] = f"{id}_content"
        sensors.append(FullUpTankContentEntity(vAuth, tank,coordinator))
    async_add_entities(sensors, update_before_add=True)

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    session = async_create_clientsession(hass)
    string = '{"username":"","password":"","token":""}'
    data = json.loads(string)

    data['username']=config[CONF_USERNAME]
    data["password"]=config[CONF_PASSWORD]
    if CONF_ACCESS_TOKEN in config:
        data["token"]=config[CONF_ACCESS_TOKEN]

    coordinator = data[COORDINATOR]
    name = data[NAME]
    vAuth = FullUp(session,data)
    #github = GitHubAPI(session, "requester", oauth_token=config[CONF_ACCESS_TOKEN])
    #sensors = [FullUpTankSensor(vAuth, tank) for tank in config[CONF_TANK]]
    sensors = []
    
    for tank in config[CONF_TANK]:
        name = tank["name"]
        _LOGGER.warning(f"async_setup_platform => tank={tank}")
        id=tank["id"]
        tank["id_sensor"] = f"{id}"
        sensors.append(FullUpTankSensor(vAuth, tank,coordinator))
        tank["name"] = f"{name}_volume"
        tank["id_sensor"] = f"{id}_volume"
        sensors.append(FullUpTankVolumeEntity(vAuth, tank,coordinator,ATTR_LAST_MINIMUM_LEVEL))
        tank["name"] = f"{name}_total_volume"
        tank["id_sensor"] = f"{id}_total_volume"
        sensors.append(FullUpTankVolumeEntity(vAuth, tank,coordinator,ATTR_TANK_TOTAL_VOLUME))
        tank["name"] = f"{name}_battery_level"
        tank["id_sensor"] = f"{id}_battery_level"
        sensors.append(FullUpTankBatteryEntity(vAuth, tank,coordinator))
        tank["name"] = f"{name}_content"
        tank["id_sensor"] = f"{id}_content"
        sensors.append(FullUpTankContentEntity(vAuth, tank,coordinator))
        tank["name"] = name 
    async_add_entities(sensors, update_before_add=True)


class FullUpTankSensor(CoordinatorEntity, SensorEntity):
    """Representation of a FullUp Tank sensor."""

    def __init__(self,auth: FullUp, tank: Dict[str, str], coordinator, ):
        super().__init__(coordinator)
        self.auth = auth
        _LOGGER.warning(f"FullUpTankSensor => tank={tank}")
        self.tankid = tank.get("id", tank)
        self.tankuniqueid = tank.get("id_sensor",tank)
        self.tank = tank
        self.attrs: Dict[str, Any] = {ATTR_TANK: self.tank}
        self._name = tank.get("name", self.tank)
        self._state = None
        self._available = True
        units = {VOLUME: "volume", PERCENTAGE: "percent",ELECTRIC_POTENTIAL_VOLT: "voltage"}
        self.data = {}

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.tankuniqueid

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        return self.attrs
    
    @callback
    async def _async_handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.warning(f"handle_coordinator_update")

        tank_data = self.coordinator.data
        
        if(self.coordinator.data != None):
            tank_data = self.coordinator.data
        else:
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            tank_res =  await self.auth.getitem(tank_url)
            tank_data = tank_res['result']


        last_connection = tank_data[ATTR_LAST_CONNECTION_DATE]
        datetime_object = datetime.fromisoformat(last_connection)#, '2023-08-25T18:13:35.859Z')
        now  = datetime.now()
        iso_date = datetime_object = datetime.fromisoformat(now.isoformat())
        duration = iso_date - datetime_object
        duration_in_s = duration.total_seconds()  
        _LOGGER.warning(f"duration_in_s={duration_in_s}")
        if(duration_in_s < 3600 * 3):
            self._state = "On"
        else:
            self._state = "Off"
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if(self.coordinator.data != None):
            tank_data = self.coordinator.data
        else:
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            tank_res =  self.auth.getitem(tank_url)
            tank_data = tank_res['result']

        _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankSensor Getting account details Getting account details.. tank_data={tank_data}")

        if(tank_data != None):
            if (tank_data.get(ATTR_BATTERY_LEVEL) is not None):
                last_connection = tank_data[ATTR_LAST_CONNECTION_DATE]
                datetime_object = datetime.fromisoformat(last_connection)#, '2023-08-25T18:13:35.859Z')
                now  = datetime.now()
                iso_date = datetime_object = datetime.fromisoformat(now.isoformat())
                duration = iso_date - datetime_object
                duration_in_s = duration.total_seconds()  
                _LOGGER.warning(f"duration_in_s={duration_in_s}")
                if(duration_in_s < 3600 * 3):
                    self._state = "On"
                else:
                    self._state = "Off"
            else:
                _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankSensor No info")
        _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankSensor No info tank_data is None")
        self.async_write_ha_state()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        try:
            _LOGGER.warning(f"async_update sensor.py")
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            if(self.coordinator.data != None):
                tank_data = self.coordinator.data
            else:
                tank_data = None

            if tank_data == None or tank_data.get(ATTR_LAST_CONNECTION_DATE) is None:
                tank_res = await self.auth.getitem(tank_url)
                tank_data = tank_res['result']

            self.attrs = tank_data
            _LOGGER.warning(f"async_update sensor.py Getting account details... tank_data={tank_data}")

            try:
                totalvolume = self.attrs[ATTR_TANK_TOTAL_VOLUME]
                volume = self.attrs[ATTR_LAST_MINIMUM_LEVEL]
                voltage = self.attrs[ATTR_BATTERY_LEVEL]
                percent =  ((100* ((self.attrs[ATTR_BATTERY_LEVEL]) -2.2)/(3-2.2)) ) 
                last_connection = tank_data[ATTR_LAST_CONNECTION_DATE]
                datetime_object = datetime.fromisoformat(last_connection)#, '2023-08-25T18:13:35.859Z')
                now  = datetime.now()
                iso_date = datetime_object = datetime.fromisoformat(now.isoformat())
                duration = iso_date - datetime_object
                duration_in_s = duration.total_seconds()  
                _LOGGER.warning(f"duration_in_s={duration_in_s}")
                if(duration_in_s < 3600 * 3):
                    self._state = "On"
                else:
                    self._state = "Off"

                self._data = {VOLUME: volume, PERCENTAGE: percent,ELECTRIC_POTENTIAL_VOLT: voltage}
            except Exception as error:
                _LOGGER.exception(f"Error retrieving data from FullUp. => {error}")
                self._state = "Off"
                self._data = {VOLUME: 0, PERCENTAGE: 0,ELECTRIC_POTENTIAL_VOLT: 0}
            
            
            self._available = True
        except Exception as error:
            self._available = False
            _LOGGER.exception(f"Error retrieving data from FullUp. => {error}")


class FullUpTankBatteryEntity(FullUpTankSensor):
    """Fullup battery entity."""

    def __init__(self,auth: FullUp, tank: Dict[str, str], coordinator, ):
        super().__init__(
            auth=auth,
            tank=tank,
            coordinator=coordinator
        )
        self._state = None
        self._available = True

        _LOGGER.warning(f"async_update sensor.py FullUpTankBatteryEntity Getting account details... tank={tank}")
        _LOGGER.warning(f"async_update sensor.py FullUpTankBatteryEntity Getting account details... self.coordinator.data={self.coordinator.data}")
        if(self.coordinator.data != None):
            if (self.coordinator.data.get(ATTR_BATTERY_LEVEL) is not None):
                self._state = self.coordinator.data.get[ATTR_BATTERY_LEVEL]

    @callback
    async def _async_handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        
        if(self.coordinator.data != None):
            tank_data = self.coordinator.data
        else:
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            tank_res =  await self.auth.getitem(tank_url)
            tank_data = tank_res['result']
        _LOGGER.warning(f"_async_handle_coordinator_update sensor.py FullUpTankBatteryEntity Getting account details Getting account details.. tank_data={tank_data}")

        if (tank_data.get(ATTR_BATTERY_LEVEL) is not None):
            _LOGGER.warning(f"_async_handle_coordinator_update sensor.py FullUpTankBatteryEntity {tank_data.get(ATTR_BATTERY_LEVEL)}")
            self._state = tank_data.get(ATTR_BATTERY_LEVEL)
        else:
            _LOGGER.warning(f"_async_handle_coordinator_update sensor.py FullUpTankBatteryEntity No Battery info")
        
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if(self.coordinator.data != None):
            tank_data = self.coordinator.data
        else:
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            tank_res =  self.auth.getitem(tank_url)
            tank_data = tank_res['result']

        _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankVolumeEntity Getting account details Getting account details.. tank_data={tank_data}")

        if(tank_data != None):
            if (tank_data.get(ATTR_BATTERY_LEVEL) is not None):
                _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankBatteryEntity {tank_data.get(ATTR_BATTERY_LEVEL)}")
                self._state = tank_data.get(ATTR_BATTERY_LEVEL)
            else:
                _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankBatteryEntity No Battery info")
        else:
            _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankBatteryEntity No Battery info tank_data is None")
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self._name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if (
            self.coordinator.data.get(ATTR_BATTERY_LEVEL) is not None
        ):
        
            return ((100* ((self.coordinator.data.get[ATTR_BATTERY_LEVEL]) -2.2)/(3-2.2))) 

        return None

    @property
    def icon(self) -> str:
             return "mdi:battery"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "%"
        
    @property
    def device_class(self):
        return SensorDeviceClass.BATTERY

    @property
    def state(self) -> Optional[str]:
        #return self._state
        if self._state != None:
            return ((100* ((self._state) -2.2)/(3-2.2))) 
        else:
            return 0

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if(self.coordinator.data != None):
            if (
                self.coordinator.data.get(ATTR_BATTERY_LEVEL) is not None
            ):
                battery = self.coordinator.data.get(ATTR_BATTERY_LEVEL)
                last_reported = self.coordinator.data.get(ATTR_LAST_CONNECTION_DATE)
                #last_reported = strftime(
                #    "%Y-%m-%d %H:%M:%S", localtime(self.coordinator.data.get(ATTR_LAST_CONNECTION_DATE))
                #)
                return {
                    "last_reported": last_reported,
                    "voltage": battery
                }

        return None
    
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        try:
            _LOGGER.warning(f"async_update sensor.py FullUpTankBatteryEntity ")
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            if(self.coordinator.data != None):
                tank_data = self.coordinator.data
            else:
                tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
                tank_res =  await self.auth.getitem(tank_url)
                tank_data = tank_res['result']

            if tank_data == None or tank_data.get(ATTR_LAST_CONNECTION_DATE) is None:
                tank_res = await self.auth.getitem(tank_url)
                tank_data = tank_res['result']
            
            self.attrs = tank_data
            _LOGGER.warning(f"async_update sensor.py async_update sensor.py FullUpTankBatteryEntity Getting account details Getting account details.. tank_data={tank_data}")

            if (tank_data.get(ATTR_BATTERY_LEVEL) is not None):
                self._state = tank_data.get(ATTR_BATTERY_LEVEL)
            else:
                 _LOGGER.warning(f"async_update sensor.py async_update sensor.py FullUpTankBatteryEntity No Battery info")
        except Exception as error:
            self._available = False
            _LOGGER.exception(f"Error retrieving data from FullUp. => {error}")
    
class FullUpTankVolumeEntity(FullUpTankSensor):
    """FullUp volume entity."""

    def __init__(self,auth: FullUp, tank: Dict[str, str], coordinator, data_value ):
        super().__init__(
            auth=auth,
            tank=tank,
            coordinator=coordinator
        )
        self._state = None
        self._data_value = data_value
        self._available = True
        if(self.coordinator.data != None):
            if (
                self.coordinator.data.get(data_value) is not None
            ):
            
                self._state = self.coordinator.data.get(data_value) 

    @callback
    async def _async_handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if(self.coordinator.data != None):
            tank_data = self.coordinator.data
        else:
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            tank_res =  await self.auth.getitem(tank_url)
            tank_data = tank_res['result']

        _LOGGER.warning(f"async handle_coordinator_update FullUpTankVolumeEntity Getting account details Getting account details.. tank_data={tank_data}")
        if (tank_data.get(self.data_value) is not None):
            _LOGGER.warning(f"_async_handle_coordinator_update sensor.py FullUpTankVolumeEntity {tank_data.get(self.data_value)}")
            self._state = tank_data.get(self.data_value)
        else:
            _LOGGER.warning(f"_async_handle_coordinator_update sensor.py FullUpTankVolumeEntity No Volume info")
        
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if(self.coordinator.data != None):
            tank_data = self.coordinator.data
        else:
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            tank_res =  self.auth.getitem(tank_url)
            tank_data = tank_res['result']

        _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankVolumeEntity Getting account details Getting account details.. tank_data={tank_data}")

        if(tank_data != None):
            if (tank_data.get(self.data_value) is not None):
                 _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankVolumeEntity {tank_data.get(self.data_value)}")
                 self._state = tank_data.get(self.data_value)
            else:
                _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankContentEntity No Content info")
        self.async_write_ha_state()

    @property
    def icon(self) -> str:
        return "mdi:storage-tank"

    @property
    def data_value (self) -> str:
        return self._data_value

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self._name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if(self.coordinator.data != None):
            if (
                self.coordinator.data.get(self.data_value) is not None
            ):
            
                return self.coordinator.data.get(self.data_value) 

        return None
    
   
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        try:
            _LOGGER.warning(f"async_update sensor.py FullUpTankVolumeEntity ")
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            if(self.coordinator.data != None):
                tank_data = self.coordinator.data
            else:
                tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
                tank_res =  await self.auth.getitem(tank_url)
                tank_data = tank_res['result']

            if tank_data == None or tank_data.get(ATTR_LAST_CONNECTION_DATE) is None:
                tank_res = await self.auth.getitem(tank_url)
                tank_data = tank_res['result']
            self.attrs = tank_data
            _LOGGER.warning(f"async_update sensor.py async_update sensor.py FullUpTankVolumeEntity Getting account details Getting account details.. tank_data={tank_data}")
            self._available = True
            if (tank_data.get(self.data_value) is not None):
                _LOGGER.warning(f"async_update sensor.py async_update sensor.py FullUpTankVolumeEntity {tank_data.get(self.data_value)}")
                self._state = tank_data.get(self.data_value)
            else:
                 _LOGGER.warning(f"async_update sensor.py async_update sensor.py FullUpTankVolumeEntity No Volume info")
        except Exception as error:
            self._available = False
            _LOGGER.exception(f"Error retrieving data from FullUp. => {error}")

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "L"
        
    @property
    def device_class(self):
        return SensorDeviceClass.VOLUME_STORAGE

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if(self.coordinator.data != None):
            if (
                self.coordinator.data.get(self.data_value) is not None
            ):
                totalvol = self.coordinator.data.get(self.data_value)
                last_reported = self.coordinator.data.get(ATTR_LAST_CONNECTION_DATE)
                #)
                return {
                    "last_reported": last_reported,
                    "total_volume": totalvol
                }

        return None



class FullUpTankContentEntity(FullUpTankSensor):
    """FullUp volume in percent entity."""

    def __init__(self,auth: FullUp, tank: Dict[str, str], coordinator, ):
        super().__init__(
            auth=auth,
            tank=tank,
            coordinator=coordinator
        )

    @callback
    async def _async_handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if(self.coordinator.data != None):
            tank_data = self.coordinator.data
        else:
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            tank_res =  await self.auth.getitem(tank_url)
            tank_data = tank_res['result']

        _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankContentEntity Getting account details Getting account details.. tank_data={tank_data}")

        if(tank_data != None):
            if (tank_data.get(ATTR_LAST_MINIMUM_LEVEL) is not None and tank_data.get(ATTR_TANK_TOTAL_VOLUME) is not None):
                self._state = (tank_data.get(ATTR_LAST_MINIMUM_LEVEL) / tank_data.get(ATTR_TANK_TOTAL_VOLUME)) * 100
                self._totalvol = tank_data.get(ATTR_TANK_TOTAL_VOLUME)
                self._lastminvol = tank_data.get(ATTR_LAST_MINIMUM_LEVEL)
                self._lastcondate = tank_data.get(ATTR_LAST_CONNECTION_DATE)
            else:
                _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankContentEntity No Content info")
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if(self.coordinator.data != None):
            tank_data = self.coordinator.data
        else:
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            tank_res =  self.auth.getitem(tank_url)
            tank_data = tank_res['result']

        _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankContentEntity Getting account details Getting account details.. tank_data={tank_data}")

        if(tank_data != None):
            if (tank_data.get(ATTR_LAST_MINIMUM_LEVEL) is not None and tank_data.get(ATTR_TANK_TOTAL_VOLUME) is not None):
                self._state = (tank_data.get(ATTR_LAST_MINIMUM_LEVEL) / tank_data.get(ATTR_TANK_TOTAL_VOLUME)) * 100
                self._totalvol = tank_data.get(ATTR_TANK_TOTAL_VOLUME)
                self._lastminvol = tank_data.get(ATTR_LAST_MINIMUM_LEVEL)
                self._lastcondate = tank_data.get(ATTR_LAST_CONNECTION_DATE)
            else:
                _LOGGER.warning(f"_handle_coordinator_update sensor.py FullUpTankContentEntity No Content info")
        self.async_write_ha_state()

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "%"
    

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self._name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if(self.coordinator.data != None):
            if (
                self.coordinator.data.get(ATTR_LAST_MINIMUM_LEVEL) is not None and self.coordinator.data.get(ATTR_TANK_TOTAL_VOLUME) is not None
            ):
            
                return  (self.coordinator.data.get(ATTR_LAST_MINIMUM_LEVEL) / self.coordinator.data.get(ATTR_TANK_TOTAL_VOLUME)) * 100

        return None
    
    @property
    def totalvol(self):
        return self._totalvol
    
    @property
    def lastminvol(self):
        return self._lastminvol
    
    @property
    def lastcondate(self):
        return self._lastcondate

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        try:
            _LOGGER.warning(f"async_update sensor.py FullUpTankContentEntity ")
            tank_url = f"{TANKS_ENDPOINT}{self.tankid}"
            if(self.coordinator.data != None):
                tank_data = self.coordinator.data
            else:
                tank_data = None

            if tank_data == None or tank_data.get(ATTR_LAST_CONNECTION_DATE) is None:
                tank_res = await self.auth.getitem(tank_url)
                tank_data = tank_res['result']
            self.attrs = tank_data
            _LOGGER.warning(f"async_update sensor.py async_update sensor.py FullUpTankContentEntity Getting account details Getting account details.. tank_data={tank_data}")
            if(tank_data != None):
                if (tank_data.get(ATTR_LAST_MINIMUM_LEVEL) is not None and tank_data.get(ATTR_TANK_TOTAL_VOLUME) is not None):
                    self._state = (tank_data.get(ATTR_LAST_MINIMUM_LEVEL) / tank_data.get(ATTR_TANK_TOTAL_VOLUME)) * 100
                    self._totalvol = tank_data.get(ATTR_TANK_TOTAL_VOLUME)
                    self._lastminvol = tank_data.get(ATTR_LAST_MINIMUM_LEVEL)
                    self._lastcondate = tank_data.get(ATTR_LAST_CONNECTION_DATE)
                else:
                    _LOGGER.warning(f"async_update sensor.py async_update sensor.py FullUpTankContentEntity No Content info")
        except Exception as error:
            self._available = False
            _LOGGER.exception(f"Error retrieving data from FullUp. => {error}")

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""

        return {
            "last_reported": self._lastcondate,
            "total_volume": self._totalvol,
            "last_minimum_level": self._lastminvol
        }

        return None