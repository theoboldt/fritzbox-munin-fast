#!/usr/bin/env python
"""
  fritzbox_energy - A munin plugin for Linux to monitor AVM Fritzbox energy
  stats
  Copyright (C) 2019 Rene Walendy
  Author: Rene Walendy
  Like Munin, this plugin is licensed under the GNU GPL v2 license
  http://www.opensource.org/licenses/GPL-2.0

  Add the following section to your munin-node's plugin configuration:

  [fritzbox_*]
  env.fritzbox_ip [ip address of the fritzbox]
  env.fritzbox_password [fritzbox password]
  env.fritzbox_user [fritzbox user, set any value if not required]
  env.energy_modes [power] [devices] [uptime]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf
"""

import os
import re
import sys
import json
import fritzbox_helper as fh

PAGE = 'data.lua'
PARAMS = {'xhr':1, 'lang':'de', 'page':'energy', 'xhrId':'all', 'useajax':1, 'no_sidrenew':None}
DEVICES = ['system', 'cpu', 'wifi', 'dsl', 'ab', 'usb', 'lan']
HASPOWERSTATS = {'system':1, 'cpu':1, 'wifi':1, 'dsl':1, 'ab':1, 'usb':1, 'lan':0}
INFO = {
  'system' : 'Fritzbox overall power consumption',
  'cpu' : 'Fritzbox central processor power consumption',
  'wifi' : 'Fritzbox wifi power consumption',
  'dsl' : 'Fritzbox dsl power consumption',
  'ab' : 'Fritzbox analog phone ports power consumption',
  'usb' : 'Fritzbox usb devices power consumption'
}

# date-from-text extractor foo
locale = os.environ.get('locale', 'de')
patternLoc = {"de": "(\d+)\s(Tag|Stunden|Minuten)",
              "en": "(\d+)\s(days|hours|minutes)"}
dayLoc = {"de": "Tag", "en": "days"}
hourLoc = {"de": "Stunden", "en": "hours"}
minutesLoc = {"de": "Minuten", "en": "minutes"}
pattern = re.compile(patternLoc[locale])

def get_modes():
  return os.environ['energy_modes'].split(' ')

def print_energy_stats():
    """print the current energy statistics"""
    
    modes = get_modes()

    server = os.environ['fritzbox_ip']
    password = os.environ['fritzbox_password']
    user = os.environ['fritzbox_user']

    # download the graphs
    data = fh.post_page_with_login(server, user, password, PAGE, data=PARAMS)
    jsondata = json.loads(data)['data']['drain']

    if 'power' in modes:
      print("multigraph power")
      for i in range(len(DEVICES)):
        if not HASPOWERSTATS[DEVICES[i]]:
          continue
        val = jsondata[i]['actPerc']
        print(DEVICES[i] + ".value " + str(val))
    
    if 'devices' in modes:
      print("multigraph devices")
      # this is an array
      statuses_wifi = jsondata[DEVICES.index('wifi')]['statuses']
      if len(statuses_wifi) == 2:
        line = statuses_wifi[1]
        num = line.split()[0]
        print('wifi.value ' + num)
      # this is a string (AVM, whyyy?)
      status_lan = jsondata[DEVICES.index('lan')]['statuses']
      num = status_lan.split()[0]
      print('lan.value ' + num)
      
    if 'uptime' in modes:
      print("multigraph uptime")
      status_uptime = jsondata[DEVICES.index('system')]['statuses']
      matches = re.finditer(pattern, status_uptime)
      if matches:
        hours = 0.0
        for m in matches:
            if m.group(2) == dayLoc[locale]:
                hours += 24 * int(m.group(1))
            if m.group(2) == hourLoc[locale]:
                hours += int(m.group(1))
            if m.group(2) == minutesLoc[locale]:
                hours += int(m.group(1)) / 60.0
        uptime = hours / 24
        print "uptime.value %.2f" % uptime

def print_config():
    modes = get_modes()

    if 'power' in modes:
      print("multigraph power")
      print("graph_title AVM Fritz!Box Power Consumption")
      print("graph_vlabel %")
      print("graph_args --lower-limit 0 --upper-limit 100 --rigid")
      print("graph_category system")
      order = ""
      for d in DEVICES:
        if HASPOWERSTATS[d]:
          order += " " + d
      print("graph_order" + order)
      for d in DEVICES:
        if not HASPOWERSTATS[d]:
          continue
        print(d + ".label " + d)
        print(d + ".type GAUGE")
        print(d + ".graph LINE1")
        print(d + ".min 0")
        print(d + ".max 100")
        print(d + ".info " + INFO[d])

    if 'devices' in modes:
      print("multigraph devices")
      print("graph_title AVM Fritz!Box Connected Devices")
      print("graph_vlabel Number of devices")
      print("graph_args --base 1000")
      print("graph_category network")
      print("wifi.type GAUGE")
      print("wifi.graph LINE1")
      print("wifi.label wifi")
      print("wifi.info Wifi Connections on 2.4 & 5 Ghz")
      print("lan.type GAUGE")
      print("lan.graph LINE1")
      print("lan.label lan")
      print("lan.info LAN Connections")

    if 'uptime' in modes:
      print("multigraph uptime")
      print("graph_title AVM Fritz!Box Uptime")
      print("graph_vlabel uptime in days")
      print("graph_args --base 1000 -l 0")
      print("graph_scale no")
      print("graph_category system")
      print("uptime.label uptime")
      print("uptime.draw AREA")

    if os.environ.get('host_name'):
        print("host_name " + os.environ['host_name'])


if __name__ == "__main__":
  if len(sys.argv) == 2 and sys.argv[1] == 'config':
    print_config()
  elif len(sys.argv) == 2 and sys.argv[1] == 'autoconf':
    print("yes")  # Some docs say it'll be called with fetch, some say no arg at all
  elif len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == 'fetch'):
    try:
      print_energy_stats()
    except:
      sys.exit("Couldn't retrieve fritzbox energy stats")