import os
import inspect

from ..ExternalIo import fetch, write_json_file, read_json_file


class OpenriceApi(object):

    SEARCH_BASE_API_URL: str = "https://www.openrice.com/api/v2/search?uiCity=hongkong&regionId=0&pageToken=CONST_DUMMY_TOKEN"
    DISTRICT_LANDMARKS_DATA_URL: str = "https://www.openrice.com/api/v2/metadata/region/all?uiLang=zh&uiCity=hongkong"
    PRICE_RANGE_DATA_URL: str = "https://www.openrice.com/api/v2/metadata/country/all"

    lang_dict_options: dict = ["en", "tc", "sc"]

    base_data_path = "./openrice_data/"

    _district_data: list = []
    _langmarks_data: list = []
    _price_range_data: list = []

    def verbose_print(self, msg: str) -> None:
        if not self.verbose:
            return
        print(f'\033[43;30m[{inspect.stack()[1][3]}] ' + msg + '\x1b[0m')

    def __init__(self,
                 store_data: bool = True,
                 force_fetch: bool = False,
                 base_data_path="./data/",
                 verbose: bool = False,
                 **kwargs
                 ) -> None:
        self.store_data = store_data
        self.force_fetch = force_fetch
        self.base_data_path = base_data_path
        self.raw_price_range_data_path = base_data_path + "openrice_priceRange_raw.json"
        self.price_range_data_path = base_data_path + "openrice_priceRange.json"
        self.raw_district_data_path = base_data_path + "openrice_district_raw.json"
        self.district_data_path = base_data_path + "openrice_district.json"
        self.landmarks_data_path = base_data_path + "openrice_landmarks.json"
        self.verbose = verbose

        self.verbose_print("Initializing Openrice Data Api")
        self.verbose_print("Store data: {}".format(self.store_data))
        self.verbose_print("Force fetch: {}".format(self.force_fetch))
        self.fetch_price_range_data()
        self.fetch_district_and_landmark_data()

    def fetch_district_and_landmark_data(self):
        # Use cached data
        if self.store_data and not self.force_fetch:
            self.verbose_print(
                f"Try Fetching data from {self.base_data_path}"
            )
            self._district_data = read_json_file(self.district_data_path)
            self._langmarks_data = read_json_file(self.landmarks_data_path)
            if self._district_data and self._langmarks_data:
                self.verbose_print(
                    f"Content Loaded from {self.base_data_path}"
                )
                return

        # Get raw data
        raw_district_landmarks_data = None
        if self.force_fetch or not os.path.exists(self.raw_district_data_path):
            self.verbose_print(
                "Existing raw data not found in {} or Force Fetch Enabled. Fetching data from API."
                .format(self.raw_district_data_path)
            )
            raw_district_landmarks_data = fetch(
                self.DISTRICT_LANDMARKS_DATA_URL
            )
        else:
            self.verbose_print(
                "Raw data path {} exists, try loading data."
                .format(self.raw_district_data_path)
            )
            raw_district_landmarks_data = read_json_file(
                self.raw_district_data_path
            )
            if not raw_district_landmarks_data:
                self.verbose_print(
                    "Empty raw data in {}, fetching from api."
                    .format(self.raw_district_data_path)
                )
                raw_district_landmarks_data = fetch(
                    self.DISTRICT_LANDMARKS_DATA_URL
                )

        # Parse data
        self.verbose_print("Parsing District data")
        self._district_data = [{
            "districtId": data["districtId"],
            "nameLangDict": {key: data['nameLangDict'][key] for key in self.lang_dict_options},
        } for data in raw_district_landmarks_data["districts"]]

        self.verbose_print("Parsing Lamdmark data")
        self._langmarks_data = [{
            "landmarkId": data["landmarkId"],
            "districtId": data["districtId"],
            "nameLangDict": {key: data['nameLangDict'][key] for key in self.lang_dict_options},
        } for data in raw_district_landmarks_data["landmarks"]]

        # Store data
        if self.store_data:
            self.verbose_print("Storage enabled, writing data to file.")
            write_json_file(raw_district_landmarks_data,
                            self.raw_district_data_path)
            write_json_file(self._district_data, self.district_data_path)
            write_json_file(self._langmarks_data, self.landmarks_data_path)

        return self.districts

    def fetch_price_range_data(self):
        # Use cached data
        if self.store_data and not self.force_fetch:
            self.verbose_print(
                f"Try Fetching data from {self.price_range_data_path}"
            )
            self._price_range_data = read_json_file(self.price_range_data_path)
            if self._price_range_data:
                self.verbose_print(
                    f"Content Loaded from {self.price_range_data_path}"
                )
                return self._price_range_data

        # Get raw data
        raw_price_range_data = None
        if self.force_fetch or not os.path.exists(self.raw_price_range_data_path):
            self.verbose_print(
                "Existing raw data not found in {} or Force Fetch Enabled. Fetching data from API."
                .format(self.raw_price_range_data_path)
            )
            raw_price_range_data = fetch(self.PRICE_RANGE_DATA_URL)
        else:
            self.verbose_print(
                "Raw data path {} exists, try loading data."
                .format(self.raw_price_range_data_path)
            )
            raw_price_range_data = read_json_file(
                self.raw_price_range_data_path
            )
            if not raw_price_range_data:
                self.verbose_print(
                    "Empty raw data in {}, fetching from api."
                    .format(self.raw_price_range_data_path)
                )
                raw_price_range_data = fetch(self.PRICE_RANGE_DATA_URL)

        # Parse data
        self.verbose_print("Parsing PriceRange data")
        self._price_range_data = [{
            "rangeId": data["priceRangeId"],
            "nameId": f"from-{data['rangeStart']}-to-{data['rangeEnd']}",
            "nameLangDict": {key: data['nameLangDict'][key] for key in self.lang_dict_options},
        } for data in raw_price_range_data["regions"]['0']['priceRanges']]

        # Store data
        if self.store_data:
            self.verbose_print("Storage enabled, writing data to file.")
            write_json_file(raw_price_range_data,
                            self.raw_price_range_data_path)
            write_json_file(self._price_range_data, self.price_range_data_path)

        return self._price_range_data

    @property
    def districts(self) -> list:
        if not self._district_data:
            self.fetch_district_and_landmark_data()
        return self._district_data

    @property
    def landmarks(self) -> list:
        if not self._langmarks_data:
            self.fetch_district_and_landmark_data()
        return self._langmarks_data

    @property
    def price_ranges(self) -> list:
        if not self._price_range_data:
            self.fetch_price_range_data()
        return self._price_range_data

    @staticmethod
    def convert_loc_to_google_map_url(self, lat: float, lng: float) -> str:
        # https://www.google.com/maps/place/22.2814411,114.1564406
        return f"https://www.google.com/maps/place/{lat},{lng}"

    def get_price_range_text_from_id(self, price_range_id: int, lang: str = "en") -> str | None:
        self.verbose_print(f"Getting price range id: {price_range_id}")
        for price_range in self.price_ranges:
            if price_range["rangeId"] == price_range_id:
                return price_range["nameLangDict"][lang]
        return None

    def get_district_text_from_id(self, district_id: int, lang: str = "en") -> str | None:
        self.verbose_print(f"Getting district id: {district_id}")
        for district in self.districts:
            if district["districtId"] == district_id:
                return district["nameLangDict"][lang]
        return None

    def get_district_id_from_text(self, district_text: int, lang: str = "en") -> str | None:
        self.verbose_print(
            f"Getting district from district text: {district_text}"
        )
        for district in self.districts:
            if district_text in district["nameLangDict"][lang]:
                return district["districtId"]
        return None

    def get_landmark_text_from_id(self, landmark_id: int, lang: str = "en") -> str | None:
        self.verbose_print(
            f"Getting landmark from id: {landmark_id}"
        )
        for landmark in self.landmarks:
            if landmark_id in landmark["landmarkId"]:
                return landmark["nameLangDict"][lang]
        return None

    def get_langmark_id_from_text(self, landmark_text: int, lang: str = "en") -> str | None:
        self.verbose_print(
            f"Getting landmark from text: {landmark_id}"
        )
        for landmark in self.landmarks:
            if landmark_text in landmark["nameLangDict"][lang]:
                return landmark["landmarkId"]
        return None

    def search(
        self,
        keywords=None,
        district_id=None,
        landmark_id=None,
        lang="en",
        start=0,
        count=3,
    ) -> list:

        district_ids = [district["districtId"] for district in self.districts]
        landmark_ids = [landmark["landmarkId"] for landmark in self.landmarks]

        search_param = ""

        # Check params
        if landmark_id and not district_id:
            if landmark_id in landmark_ids:
                self.verbose_print(
                    f"Invalid landmark id({landmark_id}), Check if in district")
                search_param += f"&landmarkId={landmark_id}"
            elif landmark_id in district_ids:
                self.verbose_print(
                    f"Landmark({landmark_id}) is in district, appending as district")
                search_param += f"&districtId={landmark_id}"

        if not landmark_id and district_id:
            if district_id in district_ids:
                self.verbose_print(
                    f"Invalid district id({district_id}), Check if in landmark")
                search_param += f"&districtId={district_id}"
            elif district_id in landmark_ids:
                self.verbose_print(
                    f"District({district_id}) is in landmark, appending as landmark")
                search_param += f"&landmarkId={district_id}"

        if landmark_id and district_id:
            if district_id in district_ids:
                search_param += f"&districtId={district_id}"
            if landmark_id in landmark_ids:
                search_param += f"&landmarkId={landmark_id}"

        search_param += f"&startAt={start}" if start else "&startAt=0"
        search_param += f"&rows={count}" if count else "&rows=3"
        # search_param += f"&districtId={district_id}" if district_id else ""
        # search_param += f"&landmarkId={landmark_id}" if landmark_id else ""
        search_param += f"&keyword={keywords}" if keywords else ""
        search_param += f"&uiLang={lang}"

        resault = fetch(self.SEARCH_BASE_API_URL + search_param)
        if resault.get('success') == False:
            self.verbose_print('Error: from API\n', resault)
            return []

        return [{
            "name": raw_data["name"],
            "faviconUrl": raw_data["doorPhoto"]["url"],
            "address": raw_data["address"],
            "loction": {
                "latitude": raw_data["mapLatitude"],
                "longitude": raw_data["mapLongitude"],
            },
            "priceRange": {
                "text": self.get_price_range_text_from_id(raw_data["priceRangeId"], lang),
                "id": raw_data["priceRangeId"],
            },
            "district": {
                "text": self.get_district_text_from_id(raw_data["district"]["districtId"], lang),
                "id": raw_data["district"]["districtId"],
            },
            "contectInfo": {
                "openRiceShortUrl": raw_data["shortenUrl"],
                "phones": raw_data["phones"],
            },
        } for raw_data in resault["paginationResult"]["results"]]

    @staticmethod
    def prettify(restaurant: dict) -> str:
        url = restaurant['contectInfo']['openRiceShortUrl']
        resault = f"Name: {restaurant['name'] or 'N/A'}\n"
        resault += f"Address: {restaurant['address'] or 'N/A'}\n"
        resault += f"Price Range: {restaurant['priceRange']['text']}\n"
        resault += f"District: {restaurant['district']['text']}\n"
        resault += f"Phone: {', '.join(restaurant['contectInfo']['phones'])}\n"
        resault += f"latitude: {restaurant['loction']['latitude']}\n"
        resault += f"longitude: {restaurant['loction']['longitude']}\n"
        resault += f"OpenRice Short Url: {url}\n"
        resault += f"Cover Image Url: {restaurant['faviconUrl']}"
        return resault


if __name__ == "__main__":
    openriceApi = OpenriceApi()
    district_id = openriceApi.get_district_id_from_text("Central", "en")
    landmark_id = openriceApi.get_langmark_id_from_text("IFC", "en")
    resaults = openriceApi.search(
        # keywords="麵包",
        start=0,
        count=3,
        # landmark_id=landmark_id,
        # district_id=district_id,
        landmark_id=3020,
        lang="en",  # used to specify the language of the resaults
    )
    for resault in resaults:
        print('-'*100)
        print(openriceApi.prettify(resault))
        print('-'*100)

    # print(openriceApi.landmarks)
    # Check id uniqueness
    # landmark_ids = [landmark["landmarkId"]
    #                 for landmark in openriceApi.landmarks]
    # district_ids = [district["districtId"]
    #                 for district in openriceApi.districts]
    # for i in district_ids:
    #     if i in landmark_ids:
    #         print(i)
    #         print("Landmark and district ids are not unique")
    #         break
