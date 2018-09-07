import logging

log = logging.getLogger(__name__)

import requests
import requests.exceptions

import botologist.plugin


def get_owm_data(url, query_params):
    return requests.get(url, query_params, timeout=4).json()


class WeatherPlugin(botologist.plugin.Plugin):
    def __init__(self, bot, channel):
        super().__init__(bot, channel)
        self.api_key = self.bot.config.get("openweathermap_apikey")

    @botologist.plugin.command("weather")
    def weather(self, cmd):
        """Find out what the weather is somewhere.

		Example: !weather amsterdam
		"""
        if len(cmd.args) < 1:
            return "Usage: !weather city"

        city = " ".join(cmd.args)
        url = "http://api.openweathermap.org/data/2.5/weather"
        query_params = {"q": city, "units": "metric", "APPID": self.api_key}

        try:
            data = get_owm_data(url, query_params=query_params)
        except (requests.exceptions.RequestException, ValueError):
            log.warning("OpenWeatherMap request caused an exception", exc_info=True)
            return "An HTTP error occured, try again later!"

        status = int(data["cod"])

        if status == 404:
            return "Error: City not found"
        elif status != 200:
            return data["message"]

        location = data["name"]
        if "country" in data["sys"]:
            location += ", {}".format(data["sys"]["country"])
        weather = data["weather"][0]["description"]

        retval = "Weather in {}: {}".format(location, weather)
        if "temp" in data["main"]:
            retval += " - temperature: {}°C".format(data["main"]["temp"])
        if "wind" in data:
            retval += " - wind: {}m/s".format(data["wind"]["speed"])

        return retval
