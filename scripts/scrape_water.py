#!/usr/bin/env python3
"""Scrape Sofia water stops using Playwright. Outputs plain text to stdout."""
import asyncio
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


URL = "https://gispx.sofiyskavoda.bg/WebApp.InfoCenter/?a=0&tab=0"


def parse_water_stops(html: str) -> list[dict]:
    stops = []
    soup = BeautifulSoup(html, 'lxml')

    sections = [
        {'id': 'infrastructureAlertsContent', 'category': 'current'},
        {'id': 'sanitaryBackupContent', 'category': 'planned'},
    ]

    for section in sections:
        section_div = soup.find('div', id=section['id'])
        if not section_div:
            continue
        table = section_div.find('table', class_='tableWaterStopInfo')
        if not table:
            continue
        rows = table.find_all('tr', class_='trRowDefault')
        for row in rows:
            cell = row.find('td')
            if not cell:
                continue
            text = cell.get_text(separator='\n', strip=True)
            location = extract_field(text, '\u041c\u0435\u0441\u0442\u043e\u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u0435:')
            stop_type = extract_field(text, '\u0422\u0438\u043f:')
            start_time = extract_field(text, '\u041d\u0430\u0447\u0430\u043b\u043e:')
            end_time = extract_field(text, '\u041a\u0440\u0430\u0439:')
            if location or start_time or end_time:
                stops.append({
                    'location': location or 'Unknown',
                    'type': stop_type or 'Unknown',
                    'start': start_time or 'N/A',
                    'end': end_time or 'N/A',
                    'category': section['category'],
                })
    return stops


def extract_field(text: str, field_name: str) -> str | None:
    if field_name not in text:
        return None
    parts = text.split(field_name, 1)
    if len(parts) < 2:
        return None
    remaining = parts[1]
    markers = ['\u0422\u0438\u043f:', '\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435:', '\u041d\u0430\u0447\u0430\u043b\u043e:', '\u041a\u0440\u0430\u0439:']
    next_pos = len(remaining)
    for m in markers:
        pos = remaining.find(m)
        if pos != -1 and pos < next_pos:
            next_pos = pos
    val = remaining[:next_pos].strip()
    return val if val else None


async def main():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(URL, wait_until='load', timeout=30000)
            await page.wait_for_timeout(3000)
            try:
                await page.wait_for_selector('div#divSplashScreenContainer', state='hidden', timeout=10000)
            except Exception:
                pass
            try:
                await page.evaluate("""
                    const accordion = document.getElementById('divAccordianImagesanitaryBackup');
                    if (accordion) accordion.click();
                """)
                await page.wait_for_timeout(2000)
            except Exception:
                pass
            await page.wait_for_timeout(2000)
            html = await page.content()
            await browser.close()

        stops = parse_water_stops(html)
        if not stops:
            print("No water interruptions reported.")
        else:
            current = [s for s in stops if s['category'] == 'current']
            planned = [s for s in stops if s['category'] == 'planned']
            if current:
                print(f"CURRENT STOPS ({len(current)}):")
                for s in current:
                    print(f"  \u2022 {s['location']} ({s['start']} \u2192 {s['end']}) [{s['type']}]")
            if planned:
                print(f"PLANNED STOPS ({len(planned)}):")
                for s in planned:
                    print(f"  \u2022 {s['location']} ({s['start']} \u2192 {s['end']}) [{s['type']}]")
    except Exception as e:
        print(f"No water interruptions reported.", file=sys.stdout)
        print(f"Error: {e}", file=sys.stderr)


if __name__ == '__main__':
    asyncio.run(main())
