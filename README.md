# Elk M1 Alarm Plugin for Indigo
## About

This is a plugin for the Elk M1 and M1G alarm panels. It connects to an M1XEP ethernet module attached to your alarm panel, it does not currently support serial connections to the alarm. It has been tested with Indigo 7.0.

This plugin will keep the device names in sync with how they're described on the M1. It will also set the description of the zones to the type of zone they're configured as on the M1. You can disable this option if you want to use custom names or descriptions for your zone devices.

## Upgrading from previous versions
This is the slightly painful part. Parly to to conform to the new requirements of the plugin store, and partly normalize some of the variables I made a change that would prevent this plugin from working with devices created in plugings <2.0.0. Therefore, you will need to do a little bit of housekeeping and re-create any triggers, scripts, or devices that were made in version prior to v2.0.0. In theory, going from pre-2.0.0 to 2.0.0 will be the only time this should occur, and future upgrades will not cause this problem.

## Known issues
Effectively this is the same code from 1.1.1

## Origins
This is originally the work of Jeremy Cary and Mark Lyons and as the plugin has been considered abandoned it's been picked up by Bill Church as of 20171214 and is maintained at https://github.com/billchurch/indigo-elk-m1-plugin.
