"""
A bot that notifies me about new WCA competitions in my country
"""

from datetime import datetime, timedelta
from typing import List, cast
import json
import requests
import asyncio
from dataclasses import dataclass

import geopy, geopy.distance
import telegram
import telegram.ext


from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_API_TOKEN = cast(str, os.getenv("TELEGRAM_API_TOKEN"))
TELEGRAM_USER_ID = cast(str, os.getenv("TELEGRAM_USER_ID"))
HOME_ADDRESS = cast(str, os.getenv("HOME_ADDRESS"))
COUNTRY_FILTER = cast(str, os.getenv("COUNTRY_FILTER"))

if (
    not TELEGRAM_API_TOKEN
    or not TELEGRAM_USER_ID
    or not HOME_ADDRESS
    or not COUNTRY_FILTER
):
    raise Exception("Invalid env variables")


@dataclass
class Competition:
    name: str
    city: str
    date_range: str
    url: str
    latitude_degrees: float
    longitude_degrees: float


async def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = telegram.ext.Application.builder().token(TELEGRAM_API_TOKEN).build()

    new_competitions = await find_new_competitions()
    if not new_competitions:
        return

    message = f"There are new competitions:\n\n"

    for comp in new_competitions:
        distance = await get_distance(comp)
        comp_description = telegram.helpers.escape_markdown(
            f"{comp.name} in {comp.city} ({comp.date_range}), {distance} km away",
            2,
        )
        message += f"[{comp_description}]({comp.url})"

    await application.bot.send_message(
        chat_id=TELEGRAM_USER_ID,
        text=message,
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )


async def get_distance(comp: Competition) -> str:
    try:
        geolocator = geopy.Nominatim(user_agent="wca_competitions_notifier")
        home = geolocator.geocode(HOME_ADDRESS)
        target = geolocator.reverse(
            f"{comp.latitude_degrees}, {comp.longitude_degrees}"
        )
        distance = geopy.distance.distance(
            (home.latitude, home.longitude),
            (target.latitude, target.longitude),
        )
        return str(round(distance.km))
    except:
        return "ERROR"


async def find_new_competitions() -> List[Competition]:
    all_raw_comps = []
    # TODO: parallelize
    for page in range(1, 4):
        res = requests.get(
            f"https://www.worldcubeassociation.org/api/v0/competitions?country_iso2={COUNTRY_FILTER}&page={page}"
        )
        all_raw_comps.extend(json.loads(res.text))

    new_comps: List[Competition] = []
    # can't use today because then we might miss comps that were announced after the script has run on the same day
    yesterday = datetime.now() + timedelta(days=-19)  # TODO: change -19 (test) to -1
    for comp in all_raw_comps:
        announced_at = datetime.fromisoformat(comp.get("announced_at"))
        if (
            announced_at.year == yesterday.year
            and announced_at.month == yesterday.month
            and announced_at.day == yesterday.day
        ):
            new_comps.append(
                Competition(
                    name=comp.get("name"),
                    city=comp.get("city"),
                    date_range=comp.get("date_range"),
                    url=comp.get("url"),
                    latitude_degrees=comp.get("latitude_degrees"),
                    longitude_degrees=comp.get("longitude_degrees"),
                )
            )

    return new_comps


if __name__ == "__main__":
    asyncio.run(main())
