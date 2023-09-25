# coding: utf-8
# vim:sw=4:ts=4:et:
"""Python FullUp Auth Class."""
#from uuid import uuid4 as uuid
import logging
import json
from .const import BASE_API_URL, TIMEOUT,NEW_TOKEN
import aiohttp
import asyncio

_LOGGER = logging.getLogger(__name__)

class FullUp:
    """A Python Auth class for FullUp"""

    def __init__(self,session, data, token_updater=None):
        """
        :type data: Optional[Dict[str, str]]
        :type token_updater: Optional[Callable[[str], None]]
        """
        self.token_updater = token_updater
        self.token=None
        self.session = session
        _LOGGER.warning(f"data=> {data}")
        self.username = data["username"]
        self.password = data["password"]
        try:
            if 'token' in data:
                self.token = data['token']
            else:
                _LOGGER.warning("no token yet")
                #self.token = self.fetch_token()
                self.token = asyncio.run(self.fetch_token())
            
        except Exception as error:  
            _LOGGER.exception("An exception occurred:", error)
        self.language = "en"
        

    async def fetch_token(self):
        """Initial token fetch with username/password & 2FA
        :type username: str
        :type password: str
        :type otp_code: str
        """

        payload = {'email': self.username, 'password': self.password, 'language': self.language, 'Content-Type': 'application/json'}
                    
        async with self.session.post(
            f"{BASE_API_URL}{NEW_TOKEN}",
            data=payload
        ) as loggedPage:
            if loggedPage.status == 200:
                x = await loggedPage.content.read()
                j= x.decode("utf-8")
                jl = json.loads(j)
                _LOGGER.warning(f"fetch_token data=> {j}")
                self.token = jl["result"]
            else:
                _LOGGER.error(f"Error on fetch_token {loggedPage.status}")
                self.token = None
                raise Exception(f"Error on fetch_token {loggedPage.status}")
            
        if self.token_updater is not None:
            self.token_updater(self.token)

        return self.token

    async def refresh_tokens(self):
        """Refreshes the auth tokens"""
        token = await self.fetch_token(self.username,self.password)

        if self.token_updater is not None:
            self.token_updater(token)

        return token


    async def getitem(self,url):
        payload = {'email': self.username, 'password': self.password, 'language': self.language, 'Content-Type': 'application/json'}

        try:
            _LOGGER.warning(f"Getting item  self.token={self.token}")
            if self.token is None or self.token == "" :
                self.token = await self.fetch_token()

            _LOGGER.warning(f"Getting account details... self.token={self.token}")
            payload = {'Authorization': '{} {}'.format(self.token['type'],self.token['token']), 'Content-Type': 'application/json'}
            _LOGGER.warning(f"Getting account details... payload={payload}")
            _LOGGER.warning(f"Getting account details... url={BASE_API_URL}{url}")
            async with self.session.get(
                "{}{}".format(BASE_API_URL,url), 
                headers=payload
            ) as res:
                if res.status == 200 and res.content_type == "application/json":
                    try:
                        x = await res.content.read()
                        j= x.decode("utf-8")
                        jl = json.loads(j)
                        return jl    
                    except Exception as err:
                        _LOGGER.exception(err)
                    return None
                _LOGGER.warning(f"Something seems to be off... res={res}")
                #raise Exception("Could not retrieve account information from API")
            return None
        except aiohttp.ClientError as err:
            _LOGGER.exception(err)
            return None
