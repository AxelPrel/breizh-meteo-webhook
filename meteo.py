from __future__ import annotations

import os
import sys
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageDraw, ImageFont

API_URL = "https://api.open-meteo.com/v1/forecast"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
TZ = ZoneInfo("Europe/Paris")

CITIES = [
    {"name": "Brest", "department": "Finistère", "lat": 48.3904, "lon": -4.4861},
    {"name": "Saint-Brieuc", "department": "Côtes-d’Armor", "lat": 48.5142, "lon": -2.7658},
    {"name": "Vannes", "department": "Morbihan", "lat": 47.6582, "lon": -2.7608},
    {"name": "Rennes", "department": "Ille-et-Vilaine", "lat": 48.1173, "lon": -1.6778},
]

# Open-Meteo WMO weather interpretation codes.
WEATHER = {
    0: ("Ensoleillé", "☀"),
    1: ("Peu nuageux", "🌤"),
    2: ("Partiellement nuageux", "⛅"),
    3: ("Couvert", "☁"),
    45: ("Brouillard", "🌫"),
    48: ("Brouillard givrant", "🌫"),
    51: ("Bruine légère", "🌦"),
    53: ("Bruine", "🌦"),
    55: ("Bruine forte", "🌧"),
    56: ("Bruine verglaçante", "🌧"),
    57: ("Bruine verglaçante forte", "🌧"),
    61: ("Pluie faible", "🌧"),
    63: ("Pluie", "🌧"),
    65: ("Forte pluie", "🌧"),
    66: ("Pluie verglaçante", "🌧"),
    67: ("Forte pluie verglaçante", "🌧"),
    71: ("Neige faible", "🌨"),
    73: ("Neige", "🌨"),
    75: ("Forte neige", "🌨"),
    77: ("Grains de neige", "🌨"),
    80: ("Averses faibles", "🌦"),
    81: ("Averses", "🌧"),
    82: ("Fortes averses", "🌧"),
    85: ("Averses de neige", "🌨"),
    86: ("Fortes averses de neige", "🌨"),
    95: ("Orage", "⛈"),
    96: ("Orage et grêle", "⛈"),
    99: ("Orage et forte grêle", "⛈"),
}

# Keep the artwork self-contained: Pillow's default font is available everywhere.
W, H = 1500, 1040
NAVY = (14, 30, 52)
PANEL = (24, 47, 73)
WHITE = (245, 249, 255)
MUTED = (174, 194, 214)
CYAN = (89, 211, 229)
GOLD = (255, 207, 102)


def font(size: int):
    # GitHub's Ubuntu runner includes DejaVu fonts; fall back to Pillow default.
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def get_weather(city: dict) -> dict:
    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
        ]),
        "timezone": "Europe/Paris",
        "forecast_days": 2,
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }
    response = requests.get(API_URL, params=params, timeout=25)
    response.raise_for_status()
    payload = response.json()
    daily = payload["daily"]
    today = datetime.now(TZ).date().isoformat()
    try:
        idx = daily["time"].index(today)
    except ValueError:
        idx = 0

    code = int(daily["weather_code"][idx])
    description, symbol = WEATHER.get(code, ("Conditions variables", "☁"))
    return {
        **city,
        "date": daily["time"][idx],
        "code": code,
        "description": description,
        "symbol": symbol,
        "min": daily["temperature_2m_min"][idx],
        "max": daily["temperature_2m_max"][idx],
        "feels": daily["apparent_temperature_max"][idx],
        "rain_mm": daily["precipitation_sum"][idx],
        "rain_pct": daily["precipitation_probability_max"][idx],
        "wind": daily["wind_speed_10m_max"][idx],
        "gust": daily["wind_gusts_10m_max"][idx],
    }


def fmt(value, suffix="", decimals=0):
    if value is None:
        return "—"
    return f"{value:.{decimals}f}{suffix}"


def make_card_image(data: list[dict]) -> BytesIO:
    image = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(image)

    # Subtle decorative circles in the background.
    draw.ellipse((1110, -220, 1630, 300), fill=(19, 54, 77))
    draw.ellipse((-250, 770, 240, 1260), fill=(18, 43, 67))

    now = datetime.now(TZ)
    date_label = now.strftime("%A %d %B %Y").capitalize()
    draw.text((72, 48), "BREIZH  /  BULLETIN MÉTÉO", font=font(24), fill=CYAN)
    draw.text((72, 94), "La météo en Bretagne", font=font(56), fill=WHITE)
    draw.text((76, 174), date_label, font=font(25), fill=MUTED)
    draw.rounded_rectangle((72, 232, W - 72, 306), radius=20, fill=(19, 61, 82))
    draw.text((100, 252), "4 départements · Prévisions du jour · Source : Open-Meteo",
              font=font(25), fill=WHITE)

    margin = 72
    gap = 24
    card_w = (W - 2 * margin - gap) // 2
    card_h = 300
    start_y = 340

    for i, item in enumerate(data):
        col, row = i % 2, i // 2
        x = margin + col * (card_w + gap)
        y = start_y + row * (card_h + 24)
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=24, fill=PANEL)
        draw.text((x + 28, y + 24), item["name"], font=font(34), fill=WHITE)
        draw.text((x + 30, y + 70), item["department"], font=font(20), fill=MUTED)
        draw.text((x + 28, y + 111), item["description"], font=font(25), fill=CYAN)
        draw.text((x + 28, y + 158),
                  f'{fmt(item["min"], "°")}  /  {fmt(item["max"], "°")}',
                  font=font(43), fill=WHITE)
        draw.text((x + 30, y + 216),
                  f'Ressenti max. {fmt(item["feels"], "°")}',
                  font=font(19), fill=MUTED)
        draw.text((x + 30, y + 253),
                  f'Pluie {fmt(item["rain_pct"], "%")} · {fmt(item["rain_mm"], " mm", 1)}',
                  font=font(21), fill=WHITE)
        draw.text((x + card_w // 2 + 10, y + 253),
                  f'Vent {fmt(item["wind"], " km/h")}',
                  font=font(21), fill=GOLD)

    footer_y = H - 45
    draw.text((72, footer_y), "Prévisions indicatives · open-meteo.com",
              font=font(18), fill=MUTED)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output


def post_to_discord(image_bytes: BytesIO, data: list[dict]) -> None:
    if not WEBHOOK_URL:
        raise RuntimeError("La variable DISCORD_WEBHOOK_URL est absente.")

    today = datetime.now(TZ).strftime("%d/%m/%Y")
    summary = " • ".join(
        f'{item["name"]} {fmt(item["min"], "°")}/{fmt(item["max"], "°")}'
        for item in data
    )
    payload = {
        "username": "Breizh Météo",
        "content": f"🌦️ **Le bulletin météo breton du {today}**\n{summary}\n_Source : Open-Meteo_",
        "allowed_mentions": {"parse": []},
    }
    response = requests.post(
        WEBHOOK_URL,
        data={"payload_json": __import__("json").dumps(payload, ensure_ascii=False)},
        files={"file": ("breizh-meteo.png", image_bytes, "image/png")},
        timeout=30,
    )
    if response.status_code not in (200, 204):
        raise RuntimeError(
            f"Discord a répondu HTTP {response.status_code}: {response.text[:1000]}"
        )


def main() -> int:
    try:
        data = [get_weather(city) for city in CITIES]
        image_bytes = make_card_image(data)
        post_to_discord(image_bytes, data)
        print("Bulletin météo envoyé avec succès.")
        for item in data:
            print(
                f'{item["name"]}: {item["min"]}–{item["max"]} °C, '
                f'pluie max {item["rain_pct"]} %, vent max {item["wind"]} km/h'
            )
        return 0
    except Exception as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
