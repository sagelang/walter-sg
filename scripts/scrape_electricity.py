#!/usr/bin/env python3
"""Scrape Sofia electricity outages from ERM Zapad. Outputs plain text to stdout."""
import asyncio
import json
import re
import sys
from bs4 import BeautifulSoup
import aiohttp


BASE_URL = "https://info.ermzapad.bg/webint/vok/avplan.php"


def parse_municipality_ids(html: str) -> list[tuple]:
    municipalities = []
    soup = BeautifulSoup(html, 'html.parser')
    for li in soup.find_all('li', onclick=True):
        onclick = li.get('onclick', '')
        match = re.search(r"show_obstina\('([A-Z]+\d+)','([A-Z]+)'\)", onclick)
        if match:
            muni_id = match.group(1)
            region_code = match.group(2)
            if region_code != 'SOF':
                continue
            muni_name = li.get_text(strip=True)
            muni_name = re.sub(r'^община\s*', '', muni_name, flags=re.IGNORECASE).strip()
            municipalities.append((muni_id, muni_name))
    return municipalities


async def fetch_municipality_details(session, muni_id: str, muni_name: str) -> list[dict]:
    stops = []
    data = {'action': 'draw', 'gm_obstina': muni_id, 'lat': '0', 'lon': '0'}
    async with session.post(BASE_URL, data=data) as response:
        text = await response.text()
        if text.startswith('\ufeff'):
            text = text[1:]
        if not text or text in ('[]', '{}'):
            return stops
        try:
            result = json.loads(text)
            for key, outage in result.items():
                if key == 'cnt' or not isinstance(outage, dict):
                    continue
                type_dist = outage.get('typedist', '').lower()
                is_planned = '\u043f\u043b\u0430\u043d\u0438\u0440\u0430\u043d' in type_dist
                stops.append({
                    'location': outage.get('city_name') or outage.get('cities') or muni_name,
                    'start': outage.get('begin_event', 'N/A'),
                    'end': outage.get('end_event', 'N/A'),
                    'category': 'planned' if is_planned else 'unplanned',
                })
        except json.JSONDecodeError:
            pass
    return stops


async def main():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL) as response:
                html = await response.text()

            munis = parse_municipality_ids(html)
            if not munis:
                print("No electricity outages reported.")
                return

            all_stops = []
            for muni_id, muni_name in munis:
                try:
                    stops = await fetch_municipality_details(session, muni_id, muni_name)
                    all_stops.extend(stops)
                except Exception:
                    continue

            # Deduplicate
            seen = set()
            unique = []
            for s in all_stops:
                key = (s['location'], s['start'], s['end'], s['category'])
                if key not in seen:
                    seen.add(key)
                    unique.append(s)

            if not unique:
                print("No electricity outages reported.")
            else:
                unplanned = [s for s in unique if s['category'] == 'unplanned']
                planned = [s for s in unique if s['category'] == 'planned']
                if unplanned:
                    print(f"CURRENT OUTAGES ({len(unplanned)}):")
                    for s in unplanned:
                        print(f"  \u2022 {s['location']} ({s['start']} \u2192 {s['end']})")
                if planned:
                    print(f"PLANNED MAINTENANCE ({len(planned)}):")
                    for s in planned:
                        print(f"  \u2022 {s['location']} ({s['start']} \u2192 {s['end']})")

    except Exception as e:
        print("No electricity outages reported.", file=sys.stdout)
        print(f"Error: {e}", file=sys.stderr)


if __name__ == '__main__':
    asyncio.run(main())
