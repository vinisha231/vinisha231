#!/usr/bin/env python3
"""Regenerate tokyo_banner.svg with live Tokyo time/weather. Run on a schedule via GitHub Actions."""
import json
import math
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TOKYO = ZoneInfo("Asia/Tokyo")
LAT, LON = 35.6762, 139.6503

WEATHER_MAP = {
    0: ("Clear", "clear"), 1: ("Mostly Clear", "clear"), 2: ("Partly Cloudy", "cloudy"),
    3: ("Overcast", "cloudy"), 45: ("Fog", "fog"), 48: ("Fog", "fog"),
    51: ("Drizzle", "rain"), 53: ("Drizzle", "rain"), 55: ("Drizzle", "rain"),
    56: ("Freezing Drizzle", "rain"), 57: ("Freezing Drizzle", "rain"),
    61: ("Rain", "rain"), 63: ("Rain", "rain"), 65: ("Heavy Rain", "rain"),
    66: ("Freezing Rain", "rain"), 67: ("Freezing Rain", "rain"),
    71: ("Snow", "snow"), 73: ("Snow", "snow"), 75: ("Heavy Snow", "snow"), 77: ("Snow Grains", "snow"),
    80: ("Rain Showers", "rain"), 81: ("Rain Showers", "rain"), 82: ("Heavy Showers", "rain"),
    85: ("Snow Showers", "snow"), 86: ("Snow Showers", "snow"),
    95: ("Thunderstorm", "storm"), 96: ("Thunderstorm", "storm"), 99: ("Thunderstorm", "storm"),
}

WEATHER_EMOJI = {"clear_day": "☀️", "clear_night": "\U0001f319", "cloudy": "☁️",
                 "rain": "\U0001f327️", "storm": "⛈️", "snow": "❄️", "fog": "\U0001f32b️"}


def fetch_weather():
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
           f"&current_weather=true&daily=sunrise,sunset&timezone=Asia%2FTokyo&past_days=1&forecast_days=2")
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.load(resp)


def parse_local(dt_str):
    return datetime.fromisoformat(dt_str).replace(tzinfo=TOKYO)


def lerp(a, b, t):
    return a + (b - a) * t


def build_svg(now, label, condition, phase, sun_moon_x, sun_moon_y, temp_c):
    is_day = phase == "day"
    is_clear = condition == "clear"
    show_sun = is_day and is_clear
    show_moon = (not is_day) and is_clear
    show_clouds = condition in ("cloudy", "rain", "storm", "fog")
    show_rain = condition in ("rain", "storm")
    show_snow = condition == "snow"
    show_storm_flash = condition == "storm"
    show_fog = condition == "fog"

    if is_day and condition == "clear":
        sky_stops = [("0%", "#3a7bd5"), ("55%", "#78c6e8"), ("100%", "#ffe3a3")]
    elif is_day and condition == "cloudy":
        sky_stops = [("0%", "#5c7a99"), ("55%", "#8b9fb3"), ("100%", "#c3cdd6")]
    elif is_day and condition in ("rain", "storm"):
        sky_stops = [("0%", "#2b323d"), ("55%", "#3d4652"), ("100%", "#525b66")]
    elif is_day and condition == "fog":
        sky_stops = [("0%", "#aeb6bd"), ("55%", "#c6ccd1"), ("100%", "#dde1e4")]
    elif (not is_day) and condition == "clear":
        sky_stops = [("0%", "#060611"), ("60%", "#0d1117"), ("100%", "#1a1b2e")]
    else:
        sky_stops = [("0%", "#040508"), ("60%", "#0a0d13"), ("100%", "#12141c")]

    sky_gradient = "\n".join(f'      <stop offset="{o}" stop-color="{c}"/>' for o, c in sky_stops)

    weather_key = "clear_day" if show_sun else ("clear_night" if show_moon else condition)
    emoji = WEATHER_EMOJI.get(weather_key, "")
    footer_stop_color = sky_stops[-1][1]

    celestial = ""
    if show_sun:
        celestial = f'''
  <g filter="url(#glow-sun)">
    <circle cx="{sun_moon_x:.0f}" cy="{sun_moon_y:.0f}" r="26" fill="#fff3c4"/>
    <circle cx="{sun_moon_x:.0f}" cy="{sun_moon_y:.0f}" r="18" fill="#ffdd6b"/>
  </g>'''
    elif show_moon:
        celestial = f'''
  <circle cx="{sun_moon_x:.0f}" cy="{sun_moon_y:.0f}" r="22" fill="#c9b99a" opacity="0.85"/>
  <circle cx="{sun_moon_x + 12:.0f}" cy="{sun_moon_y - 7:.0f}" r="19" fill="{sky_stops[0][1]}"/>'''

    stars = ""
    if show_moon:
        star_data = [(22,18,1.2,3.1,0),(78,42,0.9,2.4,0.7),(145,14,1.4,4,1.2),(210,32,1.0,2.8,0.3),
                     (270,12,1.3,3.5,1.8),(340,25,0.8,2.2,0.5),(410,9,1.5,3,2.1),(470,30,0.9,2.6,0.9),
                     (535,16,1.2,4.2,1.4),(595,38,1.0,3,0.2),(660,22,1.3,2.9,1.6),(720,10,0.8,3.7,0.4),
                     (760,44,1.1,2.5,2),(875,28,1.0,3.3,0.8),(175,50,1.0,5,0.6),(445,48,1.1,3.8,1.1),
                     (690,52,1.0,4,1.9),(380,68,0.9,3,0.4)]
        stars = "\n  <g>\n" + "\n".join(
            f'    <circle cx="{x}" cy="{y}" r="{r}" fill="white"><animate attributeName="opacity" '
            f'values="1;0.2;1" dur="{d}s" repeatCount="indefinite" begin="{b}s"/></circle>'
            for x, y, r, d, b in star_data) + "\n  </g>"

    clouds = ""
    if show_clouds:
        cloud_fill = "#e8edf2" if is_day else "#3a4250"
        cloud_opacity = "0.55" if is_day else "0.4"
        clouds = f'''
  <g fill="{cloud_fill}" opacity="{cloud_opacity}">
    <ellipse cx="120" cy="55" rx="55" ry="16"/><ellipse cx="165" cy="48" rx="38" ry="13"/>
    <ellipse cx="480" cy="35" rx="60" ry="17"/><ellipse cx="530" cy="42" rx="40" ry="13"/>
    <ellipse cx="760" cy="60" rx="50" ry="15"/><ellipse cx="805" cy="52" rx="34" ry="12"/>
  </g>'''

    rain = ""
    if show_rain:
        drops = []
        for i in range(28):
            x = (i * 33) % 900
            dur = 0.6 + (i % 5) * 0.08
            begin = (i % 7) * 0.15
            drops.append(f'    <line x1="{x}" y1="-10" x2="{x-8}" y2="20" stroke="#9fc3ff" stroke-width="1.5" opacity="0.55">'
                         f'<animateTransform attributeName="transform" type="translate" from="0 0" to="-40 300" '
                         f'dur="{dur:.2f}s" repeatCount="indefinite" begin="{begin:.2f}s"/></line>')
        rain = '\n  <g clip-path="url(#clip)">\n' + "\n".join(drops) + "\n  </g>"

    snow = ""
    if show_snow:
        flakes = []
        for i in range(24):
            x = (i * 38) % 900
            dur = 4 + (i % 5)
            begin = (i % 6) * 0.6
            flakes.append(f'    <circle cx="{x}" cy="-10" r="2" fill="white" opacity="0.8">'
                          f'<animateTransform attributeName="transform" type="translate" from="0 0" to="10 300" '
                          f'dur="{dur}s" repeatCount="indefinite" begin="{begin}s"/></circle>')
        snow = '\n  <g clip-path="url(#clip)">\n' + "\n".join(flakes) + "\n  </g>"

    fog_overlay = ""
    if show_fog:
        fog_overlay = '\n  <rect width="900" height="280" fill="#e8ecef" opacity="0.28"/>'

    storm_flash = ""
    if show_storm_flash:
        storm_flash = ('\n  <rect width="900" height="280" fill="white" opacity="0">'
                        '<animate attributeName="opacity" values="0;0;0;0.5;0;0.25;0;0;0;0;0;0;0;0;0;0" '
                        'dur="6s" repeatCount="indefinite"/></rect>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 302" width="900" height="302">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
{sky_gradient}
    </linearGradient>
    <linearGradient id="road" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#12121f"/>
      <stop offset="100%" stop-color="#0a0a15"/>
    </linearGradient>
    <filter id="glow-pink" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glow-blue" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glow-text" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glow-car" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glow-sun" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="8" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="clip"><rect width="900" height="280"/></clipPath>
  </defs>

  <!-- Sky -->
  <rect width="900" height="280" fill="url(#sky)"/>
{celestial}
{stars}
{clouds}

  <!-- BACK BUILDINGS -->
  <g fill="#131d35">
    <rect x="0"   y="118" width="55"  height="127"/>
    <rect x="50"  y="138" width="42"  height="107"/>
    <rect x="88"  y="98"  width="65"  height="147"/>
    <rect x="148" y="128" width="36"  height="117"/>
    <rect x="179" y="108" width="55"  height="137"/>
    <rect x="229" y="92"  width="46"  height="153"/>
    <rect x="270" y="123" width="50"  height="122"/>
    <rect x="315" y="103" width="42"  height="142"/>
    <rect x="352" y="133" width="55"  height="112"/>
    <rect x="402" y="88"  width="62"  height="157"/>
    <rect x="459" y="113" width="46"  height="132"/>
    <rect x="500" y="98"  width="56"  height="147"/>
    <rect x="551" y="118" width="42"  height="127"/>
    <rect x="588" y="92"  width="62"  height="153"/>
    <rect x="645" y="108" width="50"  height="137"/>
    <rect x="690" y="128" width="42"  height="117"/>
    <rect x="727" y="98"  width="65"  height="147"/>
    <rect x="787" y="118" width="50"  height="127"/>
    <rect x="832" y="103" width="46"  height="142"/>
    <rect x="873" y="122" width="27"  height="123"/>
  </g>
  <!-- Back windows -->
  <g fill="#fffacd" opacity="0.3">
    <rect x="6"   y="126" width="5" height="7"/><rect x="15"  y="126" width="5" height="7"/><rect x="24"  y="126" width="5" height="7"/><rect x="33"  y="126" width="5" height="7"/>
    <rect x="6"   y="139" width="5" height="7"/><rect x="24"  y="139" width="5" height="7"/><rect x="33"  y="139" width="5" height="7"/>
    <rect x="15"  y="152" width="5" height="7"/><rect x="33"  y="152" width="5" height="7"/>
    <rect x="94"  y="106" width="5" height="7"/><rect x="103" y="106" width="5" height="7"/><rect x="112" y="106" width="5" height="7"/><rect x="121" y="106" width="5" height="7"/>
    <rect x="94"  y="119" width="5" height="7"/><rect x="112" y="119" width="5" height="7"/><rect x="121" y="119" width="5" height="7"/>
    <rect x="103" y="132" width="5" height="7"/><rect x="121" y="132" width="5" height="7"/>
    <rect x="234" y="100" width="5" height="7"/><rect x="243" y="100" width="5" height="7"/><rect x="252" y="100" width="5" height="7"/>
    <rect x="234" y="113" width="5" height="7"/><rect x="252" y="113" width="5" height="7"/>
    <rect x="408" y="96"  width="5" height="7"/><rect x="417" y="96"  width="5" height="7"/><rect x="426" y="96"  width="5" height="7"/><rect x="435" y="96"  width="5" height="7"/>
    <rect x="408" y="109" width="5" height="7"/><rect x="426" y="109" width="5" height="7"/>
    <rect x="417" y="122" width="5" height="7"/><rect x="435" y="122" width="5" height="7"/>
    <rect x="593" y="100" width="5" height="7"/><rect x="602" y="100" width="5" height="7"/><rect x="611" y="100" width="5" height="7"/>
    <rect x="593" y="113" width="5" height="7"/><rect x="611" y="113" width="5" height="7"/>
    <rect x="602" y="126" width="5" height="7"/>
    <rect x="732" y="106" width="5" height="7"/><rect x="741" y="106" width="5" height="7"/><rect x="750" y="106" width="5" height="7"/>
    <rect x="732" y="119" width="5" height="7"/><rect x="750" y="119" width="5" height="7"/>
    <rect x="741" y="132" width="5" height="7"/>
  </g>

  <!-- MID BUILDINGS -->
  <g fill="#0d1525">
    <rect x="0"   y="152" width="46"  height="93"/>
    <rect x="42"  y="164" width="52"  height="81"/>
    <rect x="89"  y="148" width="42"  height="97"/>
    <rect x="126" y="160" width="55"  height="85"/>
    <rect x="176" y="142" width="46"  height="103"/>
    <rect x="217" y="157" width="60"  height="88"/>
    <rect x="272" y="150" width="48"  height="95"/>
    <rect x="315" y="162" width="52"  height="83"/>
    <rect x="362" y="145" width="42"  height="100"/>
    <rect x="399" y="153" width="56"  height="92"/>
    <rect x="450" y="148" width="48"  height="97"/>
    <rect x="493" y="160" width="55"  height="85"/>
    <rect x="543" y="144" width="46"  height="101"/>
    <rect x="584" y="157" width="52"  height="88"/>
    <rect x="631" y="150" width="48"  height="95"/>
    <rect x="674" y="162" width="46"  height="83"/>
    <rect x="715" y="147" width="55"  height="98"/>
    <rect x="765" y="157" width="48"  height="88"/>
    <rect x="808" y="150" width="50"  height="95"/>
    <rect x="853" y="160" width="47"  height="85"/>
  </g>
  <!-- Mid windows -->
  <g fill="#ffe88a" opacity="0.55">
    <rect x="5"   y="160" width="6" height="8"/><rect x="15"  y="160" width="6" height="8"/><rect x="25"  y="160" width="6" height="8"/>
    <rect x="5"   y="173" width="6" height="8"/><rect x="25"  y="173" width="6" height="8"/>
    <rect x="15"  y="186" width="6" height="8"/>
    <rect x="95"  y="156" width="6" height="8"/><rect x="105" y="156" width="6" height="8"/><rect x="115" y="156" width="6" height="8"/>
    <rect x="95"  y="169" width="6" height="8"/><rect x="115" y="169" width="6" height="8"/>
    <rect x="182" y="150" width="6" height="8"/><rect x="192" y="150" width="6" height="8"/><rect x="202" y="150" width="6" height="8"/>
    <rect x="182" y="163" width="6" height="8"/><rect x="202" y="163" width="6" height="8"/>
    <rect x="192" y="176" width="6" height="8"/><rect x="202" y="176" width="6" height="8"/>
    <rect x="405" y="161" width="6" height="8"/><rect x="415" y="161" width="6" height="8"/><rect x="425" y="161" width="6" height="8"/><rect x="435" y="161" width="6" height="8"/>
    <rect x="405" y="174" width="6" height="8"/><rect x="425" y="174" width="6" height="8"/>
    <rect x="415" y="187" width="6" height="8"/><rect x="435" y="187" width="6" height="8"/>
    <rect x="549" y="152" width="6" height="8"/><rect x="559" y="152" width="6" height="8"/><rect x="569" y="152" width="6" height="8"/>
    <rect x="549" y="165" width="6" height="8"/><rect x="569" y="165" width="6" height="8"/>
    <rect x="559" y="178" width="6" height="8"/>
    <rect x="721" y="155" width="6" height="8"/><rect x="731" y="155" width="6" height="8"/><rect x="741" y="155" width="6" height="8"/><rect x="751" y="155" width="6" height="8"/>
    <rect x="721" y="168" width="6" height="8"/><rect x="741" y="168" width="6" height="8"/><rect x="751" y="168" width="6" height="8"/>
    <rect x="731" y="181" width="6" height="8"/><rect x="751" y="181" width="6" height="8"/>
  </g>

  <!-- FRONT BUILDINGS -->
  <g fill="#07090f">
    <rect x="0"   y="188" width="55"  height="57"/>
    <rect x="50"  y="177" width="70"  height="68"/>
    <rect x="115" y="192" width="50"  height="53"/>
    <rect x="160" y="181" width="65"  height="64"/>
    <rect x="220" y="173" width="56"  height="72"/>
    <rect x="271" y="185" width="60"  height="60"/>
    <rect x="326" y="179" width="48"  height="66"/>
    <rect x="369" y="190" width="55"  height="55"/>
    <rect x="419" y="175" width="65"  height="70"/>
    <rect x="479" y="185" width="55"  height="60"/>
    <rect x="529" y="177" width="60"  height="68"/>
    <rect x="584" y="187" width="52"  height="58"/>
    <rect x="631" y="173" width="65"  height="72"/>
    <rect x="691" y="185" width="50"  height="60"/>
    <rect x="736" y="176" width="65"  height="69"/>
    <rect x="796" y="187" width="55"  height="58"/>
    <rect x="846" y="179" width="54"  height="66"/>
  </g>
  <!-- Front windows bright -->
  <g fill="#fff5b0" opacity="0.9">
    <rect x="56"  y="185" width="7" height="9"/><rect x="68"  y="185" width="7" height="9"/><rect x="80"  y="185" width="7" height="9"/>
    <rect x="56"  y="199" width="7" height="9"/><rect x="80"  y="199" width="7" height="9"/>
    <rect x="68"  y="213" width="7" height="9"/>
    <rect x="226" y="181" width="7" height="9"/><rect x="238" y="181" width="7" height="9"/><rect x="250" y="181" width="7" height="9"/>
    <rect x="226" y="195" width="7" height="9"/><rect x="250" y="195" width="7" height="9"/>
    <rect x="238" y="209" width="7" height="9"/><rect x="250" y="209" width="7" height="9"/>
    <rect x="425" y="183" width="7" height="9"/><rect x="437" y="183" width="7" height="9"/><rect x="449" y="183" width="7" height="9"/><rect x="461" y="183" width="7" height="9"/>
    <rect x="425" y="197" width="7" height="9"/><rect x="449" y="197" width="7" height="9"/><rect x="461" y="197" width="7" height="9"/>
    <rect x="437" y="211" width="7" height="9"/><rect x="461" y="211" width="7" height="9"/>
    <rect x="637" y="181" width="7" height="9"/><rect x="649" y="181" width="7" height="9"/><rect x="661" y="181" width="7" height="9"/><rect x="673" y="181" width="7" height="9"/>
    <rect x="637" y="195" width="7" height="9"/><rect x="661" y="195" width="7" height="9"/><rect x="673" y="195" width="7" height="9"/>
    <rect x="649" y="209" width="7" height="9"/>
    <rect x="742" y="184" width="7" height="9"/><rect x="754" y="184" width="7" height="9"/><rect x="766" y="184" width="7" height="9"/><rect x="778" y="184" width="7" height="9"/>
    <rect x="742" y="198" width="7" height="9"/><rect x="766" y="198" width="7" height="9"/>
    <rect x="754" y="212" width="7" height="9"/><rect x="778" y="212" width="7" height="9"/>
  </g>

  <!-- NEON SIGNS -->
  <g filter="url(#glow-pink)">
    <rect x="163" y="186" width="48" height="13" fill="none" stroke="#e94560" stroke-width="1.5" rx="2"/>
    <text x="187" y="197" text-anchor="middle" fill="#e94560" font-size="8" font-family="monospace" font-weight="bold">TOKYO</text>
  </g>
  <g filter="url(#glow-blue)">
    <rect x="328" y="184" width="36" height="12" fill="none" stroke="#5983FC" stroke-width="1.5" rx="1"/>
    <text x="346" y="194" text-anchor="middle" fill="#5983FC" font-size="7" font-family="monospace">24/7</text>
  </g>
  <g filter="url(#glow-pink)">
    <text x="557" y="194" text-anchor="middle" fill="#bf8fff" font-size="10" font-family="monospace" font-weight="bold">ラーメン</text>
  </g>
  <g filter="url(#glow-blue)">
    <text x="714" y="194" text-anchor="middle" fill="#00d4ff" font-size="9" font-family="monospace" font-weight="bold">
      BAR
      <animate attributeName="opacity" values="1;0.2;1;0.7;1;0.4;1" dur="5s" repeatCount="indefinite"/>
    </text>
  </g>
  <g filter="url(#glow-pink)">
    <text x="810" y="195" text-anchor="middle" fill="#ff6b9d" font-size="8" font-family="monospace" font-weight="bold">
      HOTEL
      <animate attributeName="opacity" values="1;1;0.3;1;1;0.5;1" dur="6s" repeatCount="indefinite" begin="1s"/>
    </text>
  </g>
{fog_overlay}
{storm_flash}

  <!-- ROAD -->
  <rect y="244" width="900" height="36" fill="url(#road)"/>
  <rect y="242" width="900" height="3" fill="#1a1a30"/>
  <!-- Center dashes -->
  <g fill="white" opacity="0.25">
    <rect x="0"   y="262" width="28" height="2"/><rect x="48"  y="262" width="28" height="2"/>
    <rect x="96"  y="262" width="28" height="2"/><rect x="144" y="262" width="28" height="2"/>
    <rect x="192" y="262" width="28" height="2"/><rect x="240" y="262" width="28" height="2"/>
    <rect x="288" y="262" width="28" height="2"/><rect x="336" y="262" width="28" height="2"/>
    <rect x="384" y="262" width="28" height="2"/><rect x="432" y="262" width="28" height="2"/>
    <rect x="480" y="262" width="28" height="2"/><rect x="528" y="262" width="28" height="2"/>
    <rect x="576" y="262" width="28" height="2"/><rect x="624" y="262" width="28" height="2"/>
    <rect x="672" y="262" width="28" height="2"/><rect x="720" y="262" width="28" height="2"/>
    <rect x="768" y="262" width="28" height="2"/><rect x="816" y="262" width="28" height="2"/>
    <rect x="864" y="262" width="28" height="2"/>
  </g>

  <!-- CARS GOING RIGHT -->
  <g clip-path="url(#clip)">
    <g><animateTransform attributeName="transform" type="translate" from="-120 0" to="950 0" dur="8s"  repeatCount="indefinite" begin="0s"/>
      <rect x="0" y="249" width="60" height="14" fill="#1e2a4a" rx="3"/>
      <rect x="10" y="243" width="35" height="10" fill="#253354" rx="2"/>
      <circle cx="58" cy="256" r="4" fill="#fffde0" filter="url(#glow-car)" opacity="0.9"/>
      <circle cx="2"  cy="256" r="3" fill="#cc0000" opacity="0.8"/>
    </g>
    <g><animateTransform attributeName="transform" type="translate" from="-260 0" to="950 0" dur="6.5s" repeatCount="indefinite" begin="2.5s"/>
      <rect x="0" y="251" width="55" height="13" fill="#2a1e3a" rx="3"/>
      <rect x="8" y="245" width="32" height="9"  fill="#332538" rx="2"/>
      <circle cx="53" cy="257" r="4" fill="#fff5b0" filter="url(#glow-car)" opacity="0.85"/>
      <circle cx="2"  cy="257" r="3" fill="#dd0000" opacity="0.75"/>
    </g>
    <g><animateTransform attributeName="transform" type="translate" from="-60  0" to="950 0" dur="10s"  repeatCount="indefinite" begin="4.5s"/>
      <rect x="0" y="248" width="62" height="15" fill="#182030" rx="3"/>
      <rect x="9" y="242" width="36" height="10" fill="#20293e" rx="2"/>
      <circle cx="60" cy="255" r="4" fill="#ffffe0" filter="url(#glow-car)" opacity="0.9"/>
      <circle cx="2"  cy="255" r="3" fill="#ff2200" opacity="0.8"/>
    </g>
  </g>

  <!-- CARS GOING LEFT -->
  <g clip-path="url(#clip)">
    <g><animateTransform attributeName="transform" type="translate" from="950 0" to="-120 0" dur="9s"   repeatCount="indefinite" begin="1s"/>
      <rect x="0" y="263" width="58" height="13" fill="#1c1f40" rx="3"/>
      <rect x="12" y="257" width="32" height="9" fill="#242545" rx="2"/>
      <circle cx="2"  cy="269" r="4" fill="#fffde0" filter="url(#glow-car)" opacity="0.9"/>
      <circle cx="55" cy="269" r="3" fill="#cc0000" opacity="0.8"/>
    </g>
    <g><animateTransform attributeName="transform" type="translate" from="950 0" to="-200 0" dur="7s"   repeatCount="indefinite" begin="3.5s"/>
      <rect x="0" y="265" width="55" height="12" fill="#1a1232" rx="3"/>
      <rect x="10" y="259" width="30" height="8" fill="#22193c" rx="2"/>
      <circle cx="2"  cy="271" r="3.5" fill="#fff0a0" filter="url(#glow-car)" opacity="0.85"/>
      <circle cx="53" cy="271" r="2.5" fill="#ee1100" opacity="0.75"/>
    </g>
    <g><animateTransform attributeName="transform" type="translate" from="950 0" to="-150 0" dur="5.5s"  repeatCount="indefinite" begin="6.5s"/>
      <rect x="0" y="261" width="60" height="14" fill="#14102c" rx="3"/>
      <rect x="11" y="255" width="34" height="10" fill="#1c1838" rx="2"/>
      <circle cx="2"  cy="268" r="4" fill="#fffbe0" filter="url(#glow-car)" opacity="0.9"/>
      <circle cx="57" cy="268" r="3" fill="#dd1100" opacity="0.8"/>
    </g>
  </g>
{rain}
{snow}

  <!-- TEXT CENTERED IN SKY -->
  <g filter="url(#glow-text)">
    <text x="450" y="108" text-anchor="middle" font-family="'Segoe UI',Arial,sans-serif" font-size="38" font-weight="bold" fill="white" letter-spacing="3">Vinisha</text>
  </g>
  <text x="450" y="134" text-anchor="middle" font-family="'Courier New',monospace" font-size="13" fill="#5983FC" letter-spacing="1">CLMS, UW and AI Engineer, Avanade</text>
  <line x1="270" y1="144" x2="630" y2="144" stroke="#5983FC" stroke-width="0.5" opacity="0.4"/>

  <!-- FOOTER: live Tokyo time + weather -->
  <rect y="280" width="900" height="22" fill="{footer_stop_color}"/>
  <line x1="0" y1="280" x2="900" y2="280" stroke="#5983FC" stroke-width="0.5" opacity="0.3"/>
  <text x="450" y="295" text-anchor="middle" font-family="'Courier New',monospace" font-size="11" fill="#9fb3d9" letter-spacing="0.5">{emoji}  Tokyo &#183; {label} &#183; {temp_c:.0f}&#176;C</text>
</svg>
'''


def main():
    data = fetch_weather()
    cw = data["current_weather"]
    code = cw["weathercode"]
    temp_c = cw["temperature"]
    desc, condition = WEATHER_MAP.get(code, ("Clear", "clear"))

    now = datetime.now(TOKYO)

    daily = data["daily"]
    sunrises = [parse_local(t) for t in daily["sunrise"]]
    sunsets = [parse_local(t) for t in daily["sunset"]]
    # past_days=1 & forecast_days=2 -> [yesterday, today, tomorrow]
    y_rise, t_rise, tm_rise = sunrises
    y_set, t_set, tm_set = sunsets

    if t_rise <= now < t_set:
        phase = "day"
        fraction = (now - t_rise) / (t_set - t_rise)
        x = lerp(90, 810, fraction)
        y = 235 - math.sin(math.pi * fraction) * 195
    elif now >= t_set:
        phase = "night"
        night_end = tm_rise
        fraction = (now - t_set) / (night_end - t_set)
        x = lerp(90, 810, fraction)
        y = 235 - math.sin(math.pi * fraction) * 195
    else:
        phase = "night"
        fraction = (now - y_set) / (t_rise - y_set)
        x = lerp(90, 810, fraction)
        y = 235 - math.sin(math.pi * fraction) * 195

    hour12 = now.strftime("%I:%M").lstrip("0") or "12:00"
    label = f"{hour12} {now.strftime('%p')} JST"

    svg = build_svg(now, label, condition, phase, x, y, temp_c)
    with open("tokyo_banner.svg", "w") as f:
        f.write(svg)

    print(f"phase={phase} condition={condition} desc={desc} temp={temp_c}C time={label} sun/moon=({x:.0f},{y:.0f})")


if __name__ == "__main__":
    main()
