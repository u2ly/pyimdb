import datetime


class Title:
    def __init__(self, title: dict) -> None:
        type_ = {
            "tvSeries": "show",
            "tvEpisode": "episode",
        }.get(title["titleType"]["id"], title["titleType"]["id"])

        self.id = title["id"]
        self.title = (
            title["titleText"]["text"]
            if type_ != "episode"
            else title["series"]["series"]["titleText"]["text"]
        )
        self.original_title = (
            title["originalTitleText"]["text"]
            if type_ != "episode"
            else title["series"]["series"]["originalTitleText"]["text"]
        )
        
        self.type = type_

        if type_ == "episode":
            self.name = title["titleText"]["text"]
            self.original_name = title["originalTitleText"]["text"]
            self.season = title["series"]["displayableEpisodeNumber"]["displayableSeason"]["text"]
            self.number = title["series"]["displayableEpisodeNumber"]["episodeNumber"]["text"]

            if self.season.isdigit():
                self.season = int(self.season)
            if self.number.isdigit():
                self.number = int(self.number)

        if type_ != "episode":
            self.genres = [
                genre["genre"]["text"] for genre in title["titleGenres"]["genres"]
            ]

            self.year = title["releaseYear"]["year"] if title["releaseYear"] else None

        rlsdate = title["releaseDate"]
        self.release_date = datetime.date(
            rlsdate["year"] if rlsdate["year"] else 0,
            rlsdate["month"] if rlsdate["month"] else 1,
            rlsdate["day"] if rlsdate["day"] else 1,
        ).isoformat() if rlsdate else None

        self.runtime = int(title["runtime"]["seconds"] / 60) if title["runtime"] else None

        if type_ != "episode":
            self.rated = title["certificate"]["rating"] if title["certificate"] else None

        self.plot = title["plot"]["plotText"]["plainText"] if title["plot"] else None

        self.rating = {
            "imdb": {
                "score": title["ratingsSummary"]["aggregateRating"],
                "votes": title["ratingsSummary"]["voteCount"],
            },
            "metacritic": {
                "score": (
                    title["metacritic"]["metascore"]["score"]
                    if title["metacritic"]
                    else None
                ),
                "votes": (
                    title["metacritic"]["metascore"]["reviewCount"]
                    if title["metacritic"]
                    else None
                ),
            },
        }

        if type_ == "episode":
            self.rating = self.rating["imdb"]

        self.poster = title["primaryImage"]["url"] if title["primaryImage"] else None

        if self.type == "show":
            self.episodes = title["episodes"]

    def __str__(self) -> str:
        if self.type == "episode":
            return f"{self.title} S{self.season:02}E{self.number:02}: {self.name}"

        return f"{self.title} ({self.year})"


    def dumps(self) -> dict:
        """Returns a dictionary representation of Title"""
        return {
            k: v if k != "episodes" else [x.dumps() for x in v]
            for k, v in self.__dict__.items()
            if not k.startswith("__") and not callable(getattr(self, k))
        }
