import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries, core
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import DOMAIN,CONF_TANKID,CONF_TANK,CONF_TANKNAME
from .fullup import FullUp

_LOGGER = logging.getLogger(__name__)



AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string
    }
)
TANK_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TANKID): cv.string,
        vol.Required(CONF_TANKNAME): cv.string,
        vol.Optional("add_another"): cv.boolean,
    }
)

async def validate_auth(data: Optional[Dict[str, Any]] , hass: core.HomeAssistant) -> None:
    """Validates a FullUp access info.

    Raises a ValueError if the auth token is invalid.
    """
    session = async_get_clientsession(hass)
    vAuth = FullUp(session,data)

    #gh = GitHubAPI(session, "requester", oauth_token=access_token)
    try:
        await vAuth.fetch_token()
    except Exception:
        raise ValueError


class FullUpCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """FullUp Custom config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(user_input, self.hass)
            except ValueError:
                errors["base"] = "auth"
            if not errors:
                # Input is valid, set data.
                self.data = user_input
                self.data[CONF_TANK] = []
                # Return the form of the next step.
                return await self.async_step_tank()

        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        )

    async def async_step_tank(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add a tank to watch."""
        errors: Dict[str, str] = {}
        if user_input is not None:

            if not errors:
                # Input is valid, set data.
                self.data[CONF_TANK].append(
                    {
                        "id": user_input[CONF_TANKID],
                        "name":user_input[CONF_TANKNAME],
                    }
                )
                # If user ticked the box show this form again so they can add an
                # additional tank.
                if user_input.get("add_another", False):
                    return await self.async_step_tank()

                # User is done adding repos, create the config entry.
                return self.async_create_entry(title="FullUp Custom", data=self.data)

        return self.async_show_form(
            step_id="tank", data_schema=TANK_SCHEMA, errors=errors
        )