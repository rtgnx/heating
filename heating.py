#!/usr/local/bin/python3
import os
import sys
import json
import click
import asyncio
import logging
import requests as r

from datetime import datetime

EMAIL = os.environ.get('MEROSS_EMAIL')
PASSWORD = os.environ.get('MEROSS_PASSWORD')
SCHEDULE_URL = os.environ.get('SCHEDULE_URL')

from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager


def tparse(t):
  return datetime.strptime(t, "%H:%M")

schedule = None

async def check_device_schedule(dev):
  print(f"[+] Checking Schedule for: {dev.name}")
  await dev.async_update()

  if dev.name not in schedule.keys():
    logging.info(f'[-] Device {dev.name} not in schedule')
    return False

  s = schedule[dev.name]

  for window in s:
    now = datetime.now()
    start = now.replace(hour=window[0].hour, minute=window[0].minute)
    end = now.replace(hour=window[1].hour, minute=window[1].minute)

    logging.info(f"Time now: {now}\tSchedule Start: {start}\t Schedule End: {end}")

    if now > start and now < end:
      logging.info(f"[+] Turning {dev.name} on")
      await dev.async_turn_on(channel=0)
      return True

  logging.info(f"[-] Turning {dev.name} off")
  await dev.async_turn_off(channel=0)


async def main():
    # Setup the HTTP client API from user-password
    http_api_client = await MerossHttpClient.async_from_user_password(email=EMAIL, password=PASSWORD)

    # Setup and start the device manager
    manager = MerossManager(http_client=http_api_client)
    await manager.async_init()

    # Retrieve all the MSS310 devices that are registered on this account
    await manager.async_device_discovery()
    plugs = manager.find_devices(device_type="mss210")

    if len(plugs) < 1:
        print("No MSS210 plugs found...")
    else:
        # Turn it on channel 0
        # Note that channel argument is optional for MSS310 as they only have one channel

        for dev in plugs:
          await check_device_schedule(dev)

    # Close the manager and logout from http_api
    manager.close()
    await http_api_client.async_logout()


@click.command()
def cli():
    global schedule

    try:
      res = r.get(SCHEDULE_URL)
      if res.status_code != 200:
        sys.exit(1)
      schedule = json.loads(res.content)
    except:
      sys.exit(1)

    for k, _ in schedule.items():
      schedule[k] = [(tparse(v[0]), tparse(v[1]) ) for v in schedule[k]]

    # On Windows + Python 3.8, you should uncomment the following
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()


if __name__ == '__main__':
  cli()
