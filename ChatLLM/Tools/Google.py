import os
import typing as t
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from langchain_google_community import GoogleSearchAPIWrapper

import googlemaps

from .ExternalIo import logger


class GoogleToolBase(BaseTool):

    def __init__(self,
                 google_api_key: str = "",
                 google_cse_id: str = "",
                 **kwargs):
        super().__init__(**kwargs)
        self._google_api_key: str = google_api_key
        self._google_cse_id: str = google_cse_id


class PerformGoogleSearchTool(GoogleToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        query: str = Field(
            description="Things to search on google"
        )

    name: str = "Google_Search"
    description: str = "Used to perform google search to get recent and relevent information. Can be used to lookup anything. If there is somethgin you are not 100% sure, use this to look it up."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, query: str, **kwargs) -> str:
        if not self._google_api_key or not self._google_cse_id:
            logger.debug("No google api key defined, returning not avalable")
            return 'Cannot Perform Google Search'
        search = GoogleSearchAPIWrapper(
            google_api_key=self._google_api_key,
            google_cse_id=self._google_cse_id
        )
        logger.debug(f"Searching {query}")
        resault = search.run(query)
        logger.debug(f"Got {resault}")
        return resault


class ReverseGeocodeConvertionTool(GoogleToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        longitude: float = Field(
            description="longitude of the place to be address searched"
        )
        latitude: float = Field(
            description="latitude of the place to be address searched"
        )

    name: str = "Reverse_Geocode_Search"
    description: str = "Used to get the address or location from longitude, latitude. This tool return string formated addresses that corospond to the longitude, latitude provided."
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, latitude: float, longitude: float, **kwargs) -> str:
        if not self._google_api_key:
            logger.debug("No google api key defined, returning not avalable")
            return "Cannot Perform Reverse Geocode Search"
        logger.debug(f"Finding {longitude}, {latitude}")
        maps = googlemaps.Client(key=self._google_api_key)
        resault = maps.reverse_geocode((latitude, longitude))  # type: ignore
        addresses = list(map(lambda a: a['formatted_address'], resault))
        logger.debug(f"Got addresses {addresses}")
        return "\n".join(addresses)


class GetGeocodeFromPlaces(GoogleToolBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class ToolArgs(BaseModel):
        place: str = Field(
            description='Places or location. Best to be address.'
        )

    name: str = "Geocode_Search_From_Address"
    description: str = "Used to get latitude, longitude of the place if exists"
    args_schema: t.Type[BaseModel] = ToolArgs

    def _run(self, place: str, **kwargs) -> t.Tuple[int, int] | str:
        if not self._google_api_key:
            logger.debug("No google api key defined, returning not avalable")
            return "Cannot Perform Reverse Geocode Search"
        maps = googlemaps.Client(key=self._google_api_key)
        geocode_result = maps.geocode(place)  # type: ignore
        location = None
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
        if location:
            geolocation = location["lat"], location["lng"]
            logger.debug("got location " + str(geolocation))
            return geolocation
        return "No location found"
