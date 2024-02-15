from __future__ import annotations

from typing import Any, Dict, List, Optional

from .exceptions import GraphQLException, TitleNotFoundException
from .session import Session
from .title import Title


class IMDb:
    def __init__(
        self, 
        language: str = "en-US", 
        region: Optional[str] = None, 
        version: Optional[str] = None
    ) -> None:
        self.session = Session(language, region, version)

    def by_id(self, imdb_id: str) -> Title:
        params = {}

        for name, id_ in (
            (
                "TitleReduxOverviewQuery",
                "416ba392ac33c0dc246ac47df17518f9f5503ecb9e05255bcf90f9bf3fb222e0",
            ),
            (
                "TitleGenresQuery",
                "4be2fa3fed145fedc77af013e530e63eee8da745e14e5a98177834e4fa53ae08",
            ),
        ):
            params.update(self._gql(name, id_, {"id": imdb_id}))
            
        if not params["titleType"]:
            raise TitleNotFoundException(imdb_id)

        if params["titleType"]["id"] == "tvSeries":
            params.update({"episodes": self._episodes(imdb_id)})

        return Title(params)

    # Helper methods
    
    def _gql(self, operation_name: str, operation_id: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        res = self.session.get(
            url="https://graphql.imdb.com",
            params={
                "operationName": operation_name,
                "variables": variables,
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": operation_id,
                    }
                },
            },
        ).json()

        if "errors" in res:
            raise GraphQLException(res["errors"][0]["message"])

        return res["data"]["title"] if "title" in res["data"] else res

    def _episodes(self, imdb_id: str) -> List[Title]:
        episodes = []

        for season in [
            i["node"]["season"]
            for i in self._gql(
                "TitleSeasonsQuery",
                "9377599c1dc364839cf15dba16dbe2557298fe88b95ea10569d648248a6344ab",
                {"tconst": imdb_id, "first": 99999, "after": ""},
            )["episodes"]["displayableSeasons"]["edges"]
        ]:
            tebsq = self._gql(
                "TitleEpisodesBySeasonQuery",
                "f1f9a6d9d62047e017b7400ec3b7fca4922d5bc37ffbd24a3fa9611856de5980",
                {"tconst": imdb_id, "season": season, "first": 99999, "after": ""},
            )["episodes"]["episodes"]["edges"]

            episodes.extend([i["node"] for i in tebsq])

        tpmq = self._gql(
            "TitlesPersistedMetadataQuery",
            "000ca09de7daa97c9448aec28685a5f3ef8603f8743c45fe3aa4726c35b90878",
            {
                "tconsts": [i["id"] for i in episodes],
                "link": "ANDROID",
                "filter": {
                    "countries": [self.session.region],
                    "wideRelease": "WIDE_RELEASE_ONLY",
                },
                "includeWatchOptions": False,
                "platformId": "ANDROID",
                "numReleaseDates": 5,
            },
        )["data"]["titles"]

        tnpmq = self._gql(
            "TitlesNonPersistedMetadataQuery",
            "e548ae7626f7da936ea67e7c6e96114e37ccb46e38cd9b813ba364a993d30fac",
            {
                "tconsts": [i["id"] for i in episodes],
                "lincludeUserRating": False,
            },
        )["data"]["titles"]

        for _, __, ___ in zip(tpmq, tnpmq, episodes):
            ___.update({**_, **__})

        return [Title(e) for e in episodes]

__all__ = ("IMDb",)