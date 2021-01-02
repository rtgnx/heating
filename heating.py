#!/usr/local/bin/python3
import os
import sys
import time
import json
import click
import asyncio
import logging

from datetime import datetime

EMAIL = os.environ.get('MEROSS_EMAIL') or "a.cybulski@protonmail.ch"
PASSWORD = os.environ.get('MEROSS_PASSWORD')

from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager


def tparse(t):
  return datetime.strptime(t, "%H:%M")

schedule = {}



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
          print(f"[+] Checking Schedule for: {dev.name}")
          await dev.async_update()
          if dev.name not in schedule.keys():
            print(f'[-] Device {dev.name} not in schedule')
            continue

          s = schedule[dev.name]

          print(s)
          for window in s:
            now = datetime.now()
            start = now.replace(hour=window[0].hour, minute=window[0].minute)
            end = now.replace(hour=window[1].hour, minute=window[1].minute)
            print(f"Time now: {now}\tSchedule Start: {start}\t Schedule End: {end}")
            if now > start and now < end:
              print(f"[+] Turning {dev.name} on")
              await dev.async_turn_on(channel=0)
              break

            print(f"[-] Turning {dev.name} off")
            await dev.async_turn_off(channel=0)



    # Close the manager and logout from http_api
    manager.close()
    await http_api_client.async_logout()


@click.command()
@click.option("--config", default='./config.json', help="Schedule file (Yaml)")
def cli(config):
    global schedule

    if not os.path.isfile(config):
      logging.error(f"Config file not found: {config}")
      sys.exit(1)

    with open(config, "r") as fd:
      schedule = json.load(fd)


    for k, _ in schedule.items():
      schedule[k] = [(tparse(v[0]), tparse(v[1]) ) for v in schedule[k]]

    print(schedule)

    # On Windows + Python 3.8, you should uncomment the following
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()


if __name__ == '__main__':
  cli()
