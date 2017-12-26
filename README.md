# Elk M1 Alarm Plugin for Indigo
## About

This is a plugin for the Elk M1 and M1G alarm panels. It connects to an M1XEP ethernet module attached to your alarm panel, it does not currently support serial connections to the alarm. It has been tested with Indigo 7.0.

This plugin will keep the device names in sync with how they're described on the M1. It will also set the description of the zones to the type of zone they're configured as on the M1. You can disable this option if you want to use custom names or descriptions for your zone devices.

# Breaking changes
## Upgrading from previous versions
- This uses a new CFBundleIdentifier, as a result devices discovered or created in versions prior to this release (2.0.0) are incompatible.
- Disable previous Elk Plugin
- Delete previous Elk Plugin -- remove from: /Library/Application Support/Perceptive Automation/Indigo 7/Plugins (Disabled)
- Document and then delete any triggers, scripts, or devices that were made in version prior to v2.0.0
- Install new plugin
- Re-create triggers, scripts, or devices with new v2.0.0.
- In theory, going from pre-2.0.0 to 2.0.0 will be the only time this should occur, and future upgrades will not have this issue.

# Changes
- Initial Release
- Reformatting of XML
- CFBundleIdentifier
- Addition of CFBundleName
- Increment Version
- Change CFBundleURLName

## Known issues
Effectively this is the same code from 1.1.1 with some minor alterations. Functionality at this point is essentially the same.
- As with the versions prior, this requires use of the "non-secure port" which is usually tcp/2101

## System Requirements
This plugin is developed and maintained on:
- Indigo v7.1.1
- macOS El Capitan 10.11.6
- Elk M1-XEP Firmware v2.0.42, Boot v2.0.4, Hardware v1.0
- Elk M1G Firmware v5.2.10, Boot v3.3.6, Hardware 0.13

## Opening Issues
Anything outside the versions mentioned above have the potential for unexpected results. In the event you encounter a problem, or have a question, please feel free to [open an Issue](https://github.com/billchurch/indigo-elk-m1-plugin/issues/new) with the following information:
- Version of Indigo
- Version of macOS
- Version of Firmware, Boot, and Hardware for your M1-XEP
- Version of Firmware, Boot, and Hardware for your M1 panel
- Any relevant error messages

## Donations
If you find this plugin helpful, consider donating for future upkeep. Any amount is greatly appreciated and will help prevent this plugin from being abandoned again ;) [https://paypal.me/billchurch](https://paypal.me/billchurch)

## Origins
This is originally the work of Jeremy Cary and Mark Lyons and as the plugin has been considered abandoned it's been picked up by Bill Church as of 20171214 and is maintained at [https://github.com/billchurch/indigo-elk-m1-plugin](https://github.com/billchurch/indigo-elk-m1-plugin).
