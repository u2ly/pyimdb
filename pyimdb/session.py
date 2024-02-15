from typing import Optional

import base64
import hashlib
import json
import langcodes
import requests
import uuid


class Session(requests.Session):
    def __init__(
        self,
        language: str = "en-US",
        region: Optional[str] = None,
        version: str = "8.9.8.108980200"
    ) -> None:
        super().__init__()

        if not language:
            raise ValueError("Language must be provided")

        if not langcodes.tag_is_valid(language):
            raise ValueError("Language must match IETF language tag format")

        language = langcodes.Language.get(language)

        if not region and language.region:
            region = language.region
            language = langcodes.Language.get(f"{language.language}-{region}")

        if not region:
            raise ValueError(
                "Region must be provided. Either make the language more specific or provide a region"
            )

        self.language = language
        self.region = region

        self.headers.update(
            {
                "Accept-Encoding": "gzip",
                "user-agent": self._construct_user_agent(version),
                "x-amzn-sessionId": self._get_session_id(),
                "x-imdb-client-name": "imdb-app-android",
                "x-imdb-client-version": version,
                "x-imdb-consent-info": self._dict_to_b64({"purposes": [], "vendors": []}),
                "x-imdb-user-country": region.upper(),
                "x-imdb-user-language": str(language),
                "x-imdb-weblab-search-algorithm": "C",
            }
        )

    def get(self, url, **kwargs):
        if "graphql.imdb.com" in url:
            kwargs = self._prepare_graphql_request(kwargs)

        return super().get(url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        if "graphql.imdb.com" in url:
            kwargs = self._prepare_graphql_request(kwargs, json)

        return super().post(url, data, json, **kwargs)

    # Helper methods

    @staticmethod
    def _get_session_id() -> str:
        digest = hashlib.md5(uuid.uuid4().bytes).digest()

        j = int.from_bytes(digest[:8], byteorder="big") & (2**64 - 1)
        fstr = "{:020d}".format(j)

        return "-".join([fstr[-17:][:3], fstr[-17:][3:10], fstr[-17:][10:]])

    @staticmethod
    def _dict_to_b64(d: dict) -> str:
        return base64.b64encode(json.dumps(d).encode()).decode()

    @staticmethod
    def _construct_user_agent(version: str) -> str:
        return f"Mozilla/5.0 (Linux; Android 13; sdk_gphone64_arm64 Build/TE1A.220922.028; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.71 Mobile Safari/537.36 IMDb/{version} (google|sdk_gphone64_arm64; Android 33; google) IMDb-flg/8.9.8 (1080,2154,440,440) IMDb-var/app-andr-ph"

    @staticmethod
    def _prepare_graphql_request(kwargs: dict, json_: Optional[dict] = None) -> dict:
        if json_:
            if "operationName" in json_:
                kwargs["headers"] = {
                    **kwargs.get("headers", {}),
                    "X-APOLLO-OPERATION-ID": json_["extensions"]["persistedQuery"]["sha256Hash"],
                    "X-APOLLO-OPERATION-NAME": json_["operationName"],
                }
                
        if kwargs.get("params"):
            if "operationName" in kwargs["params"]:
                kwargs["headers"] = {
                    **kwargs.get("headers", {}),
                    "Accept": "multipart/mixed; deferSpec=20220824, application/json",
                    "content-type": "application/json",
                    "X-APOLLO-OPERATION-ID": kwargs["params"]["extensions"]["persistedQuery"]["sha256Hash"],
                    "X-APOLLO-OPERATION-NAME": kwargs["params"]["operationName"],
                }

                kwargs["params"]["variables"] = json.dumps(kwargs["params"]["variables"], separators=(",", ":"))
                kwargs["params"]["extensions"] = json.dumps(kwargs["params"]["extensions"], separators=(",", ":"))

        return kwargs