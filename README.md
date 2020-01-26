# fritzbox-munin-fast

A collection of munin plugins to monitor your AVM FRITZ!Box router. The scripts have been developed using a FRITZ!Box 7590 running FRITZ!OS 7.12.

If you are using the scripts on a different Fritz!Box model please let me know by

- opening an issue
- submitting a pull request

## Introduction

   These python scripts are [Munin](http://munin-monitoring.org) plugins for monitoring the [Fritz!Box](http://avm.de/produkte/fritzbox/) router by AVM. They're build upon [fritzbox-munin](https://github.com/Tafkas/fritzbox-munin) with the goal to make use of the modern APIs that FritzOS 7 provides. No HTML Scraping is used. All data is fetched either through the TR-064 interface or the JSON API.
   
   Contrary to the original version this fork uses multigraphs. This removes the need to query the same API endpoint multiple times. All multigraph plugins have configuration options to switch individual graphs on and off. Munin 1.4.0 or later is required.

## fritzbox_connection_uptime
Shows the WAN connection uptime (requires fritzconnection)

## fritzbox_dsl
Multigraph plugin, showing:
 - DSL checksum errors
 - DSL transmission errors
 - line loss
 - link capacity
 - signal-to-noise ratio
 
 (requires password)

## fritzbox_ecostat
Multigraph plugin, showing:
 - memory usage
 - CPU load
 - CPU temperature
 
(requires password)

## fritzbox_smart_home_temperature

## fritzbox_energy
Multigraph plugin, showing:
 - power consumption for CPU, WiFi, WAN, Fon, USB and total
 - devices connected on WiFi and LAN
 - system uptime
 
(requires password)

## fritzbox_link_saturation
Multigraph plugin, showing saturation of WAN uplink and downlink by QoS priority (requries password)

## fritzbox_traffic
Similar to fritzbox_link_saturation, but single-graph and without QoS monitoring (requires fritzconnection)

## fritzbox_wifi_load
Multigraph plugin, showing for 2.4GHz and 5GHz
 - WiFi uplink and downlink bandwidth usage
 - neighbor APs on same and on different channels

## Installation & Configuration

1. Pre-requesites for the `fritzbox_traffic` and `fritzbox_connection_uptime` plugins are the [fritzconnection](https://pypi.python.org/pypi/fritzconnection) and [requests](https://pypi.python.org/pypi/requests) package. To install it

        pip install -r requirements.txt

2. Make sure the FritzBox has UPnP status information enabled. (German interface: Heimnetz > Heimnetzübersicht > Netzwerkeinstellungen > Statusinformationen über UPnP übertragen)

3. Copy all the scripts to `/usr/share/munin/plugins`

4. Create entry in `/etc/munin/plugin-conf.d/munin-node`:

        [fritzbox_*]
        env.fritzbox_ip <ip_address_to_your_fritzbox>
        env.fritzbox_password <fritzbox_password>
        env.fritzbox_user <fritzbox_user>
        host_name fritzbox
   
   See the plugin files for plugin-specific configuration options.

5. For each plugin you want to activate, create a symbolic link to `/etc/munin/plugins`.

6. Restart the munin-node daemon: `service munin-node restart`.

7. Done. You should now start to see the charts on the Munin pages.

## Localization

The `fritzbox_energy` script depends on the language selected in your fritzbox. Currently, two locales are
supported:

1. German: `de` (default)
2. English: `en`

You can change the used locale by setting an environment variable in your plugin configuration:

    env.locale en

## Different hosts for the FritzBox and your system

You can split the graphs of your FritzBox from the localhost graphs by following the next steps:

1. Use the following as your host configuration in `/etc/munin/munin.conf`

        [home.yourhost.net;server]
            address 127.0.0.1
            use_node_name yes


        [home.yourhost.net;fritzbox]
            address 127.0.0.1
            use_node_name no

1. Restart your munin-node: `service restart munin-node`

## Environment Settings

  Do not forget to restart the munin-node daemon as described in step 3 of the installation instructions above.
