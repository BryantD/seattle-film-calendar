import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from filmcalendar import filmcalendar


class FilmCalendarGrandIllusion(filmcalendar.FilmCalendar):
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.address = "1403 NE 50th St., Seattle, WA 98105"

    def __str__(self):
        return super().__str__()

    def _parse_duration(self, duration_raw):
        # Return duration in seconds
        if duration_match := re.match(r"^(\d+)", duration_raw):
            return timedelta(minutes=int(duration_match[0]))
        else:
            return timedelta(minutes=120)

    def fetch_films(self):
        try:
            req = requests.get(
                "https://grandillusioncinema.org/", headers=self.req_headers
            )
        except requests.exceptions.RequestException:
            raise

        soup = BeautifulSoup(req.text, "html.parser")

        for film in soup.find_all("div", class_="film-teaser"):
            film_location = f"{self.theater}: {self.address}"
            try:
                film_h2 = film.find("h2", class_="film-teaser--title")
                film_title = film_h2.get_text()
                film_url = film_h2.find("a")["href"]
            except TypeError as error:
                raise ValueError("Couldn't find film name") from error

            try:
                film_duration_raw = film.find(
                    "div", class_="film-teaser--format"
                ).string.strip()
                film_duration = self._parse_duration(film_duration_raw)
            except (TypeError, AttributeError):
                film_duration = timedelta(minutes=120)

            try:
                for screening in film.find("div", class_="screenings").stripped_strings:
                    screen_date, screen_times = screening.split(": ")
                    for screen_time in screen_times.split(", "):
                        # Bit of a hack to handle a one-off, but it should catch
                        # future instances of this as well.
                        if " at " in screen_time:
                            screen_time = screen_time.split(" at ")[0]
                            film_location = (
                                "Check listing for the location of this screening."
                            )
                        try:
                            film_date = datetime.strptime(
                                f"{screen_date} {screen_time} {datetime.now().year}",
                                "%A, %b %d %I:%M %p %Y",
                            )
                            self.add_event(
                                summary=film_title,
                                dtstart=film_date,
                                duration=film_duration,
                                url=film_url,
                                location=film_location,
                            )
                        except ValueError as error:
                            raise ValueError("Couldn't parse date and time") from error
            except AttributeError:
                next
