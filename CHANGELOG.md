# Changelog

## 1.0.12

- Fix for missing camera models/types introduced in 1.0.11
- Cleaned up some redundant calls to get Camera and System Device names
- Added exception handling when setting the log level

## 1.0.11

- !NOTE! This update impacts the name of the integration instance. It was always supposed to default to the Server name as specified in the Blue Iris server options. It does now. This should only take effect if you remove and re-add the integration.
- Added additional device info for Camera type and Server version

## 1.0.10

- New Feature: Added a service (Move to Preset) for moving a specified camera to a specified preset

## 1.0.9

- New Feature: Added a service (Trigger Camera) for triggering cameras and camera groups

## 1.0.8

- Fix for 2021.9.0 Breaking Change: Custom integrations: Cameras* [\#127](https://github.com/elad-bar/ha-blueiris/issues/127)
- Fixed Info logging message when setting profile and schedule

## 1.0.7

- Upgraded code to support breaking changes of HA v2012.12.0

## 2021-07-31 (1.0.6)

**Fixed bugs:**
- Cannot import MQTT Message (HA Core Breaking Change) >=2021.8.* [\#120](https://github.com/elad-bar/ha-blueiris/issues/120)

## 2021-07-31 (1.0.6b2)

**Fixed bugs:**
- Cannot import MQTT Message (HA Core Breaking Change) >=2021.8.* [\#120](https://github.com/elad-bar/ha-blueiris/issues/120)

## 2021-07-30 (1.0.6b1)

**Fixed bugs:**
- Cannot import MQTT Message (HA Core Breaking Change) >=2021.8.* [\#120](https://github.com/elad-bar/ha-blueiris/issues/120)

## 2021-02-16

**Fixed bugs:**

- Fix FPS for H264's stream to be aligned with camera settings [\#83](https://github.com/elad-bar/ha-blueiris/issues/83)

## 2021-01-31

**Fixed bugs:**

- Fix error adding entities for domain binary_sensor with platform blueiris [\#100](https://github.com/elad-bar/ha-blueiris/issues/100)

## 2021-01-30

**Fixed bugs:**

- Fix issue on initial install (HA v2012.2b) [\#98](https://github.com/elad-bar/ha-blueiris/issues/98)

## 2020-09-17

**Fixed bugs:**

- Integration setup errors caused by invalid credentials (User input malformed / Unknown error occurred) [\#79](https://github.com/elad-bar/ha-blueiris/issues/79) [\#81](https://github.com/elad-bar/ha-blueiris/issues/81)

## 2020-08-08

**Implemented enhancements:**

- New integration's option to control whether the camera component is using the `Stream` component or not, requires restart, default is without `Stream` support [\#75](https://github.com/elad-bar/ha-blueiris/issues/75)

## 2020-07-23 #2

**Fixed bugs:**

- Fixed Is Online: N/A [\#77](https://github.com/elad-bar/ha-blueiris/issues/77)

## 2020-07-23

**Implemented enhancements:**

- Moved encryption key of component to .storage directory
- Removed support for non encrypted password (**Breaking Change**)

**Fixed bugs:**

- Better handling of password parsing

## 2020-07-21

**Fixed bugs:**

- Don't block startup of Home Assistant

## 2020-07-20

**Implemented enhancements:**

- Reduced duplicate code - Connectivity, Motion, External and DIO share the same class
- Removed NONE option from drop-down, NONE was workaround for a validation issue in Integration's Options and fixed as part of HA v0.112.0
- Reduced code of camera's configuration in Integration's Options
- Improved generate configuration file process

**Fixed bugs:**
- Fixed - Generate configuration files

## 2020-07-17

**Implemented enhancements:**

- Added ability to set stream type in integration's options (Originally was hard-coded), Default=H264, initiated due to [\#75](https://github.com/elad-bar/ha-blueiris/issues/75)
- Upgrade pre-commit to 2.6.0
- Fix pre-commit errors (F541 f-string is missing placeholders)
- Added support for External and DIO events (Related to #74)

**Note:** All camera will have 2 additional sensors, to disable use integration's options

## 2020-06-30

**Fixed bugs:**

- Profile Switch [\#70](https://github.com/elad-bar/ha-blueiris/issues/70) - Set lock=1 (Schedule=HOLD) when changing profile to lock the profile as set in switch

**Implemented enhancements:**

- Moved some of INFO log level messages into DEBUG for clearer debugging
- Added CircleCI support to build and run tests

## 2020-05-21

**Fixed bugs:**

- BinarySensorDevice is deprecated [\#69](https://github.com/elad-bar/ha-blueiris/issues/69)

## 2020-05-01

**Implemented enhancements:**

- Better handling configuration changes
- Integration's title is now being taken from BlueIris server

## 2020-04-30

**Implemented enhancements:**

- More enhancements to options, ability to change setup details (Edit hostname, port and SSL flag)
- Support new translation format of HA 0.109.0

## 2020-04-29

**Implemented enhancements:**

- New feature under options - Control which camera, binary sensor or profile switch are being created

## 2020-04-28

**Fixed bugs:**

- Fix disabled entity check throws an exception in logs

## 2020-04-27

**Fixed bugs:**

- Fix disabled entities still being triggered for updates

## 2020-04-26

**Fixed bugs:**

- Removed limitation of one instance only
- Fix [\#62](https://github.com/elad-bar/ha-blueiris/issues/62) disabled entities are getting enabled after periodic update (update interval)

## 2020-04-25 #2

**Fixed bugs:**

- Fix log message restored appeared when it shouldn't

## 2020-04-25 #1

**Implemented enhancements:**

- Moved auto-generating configurations service `blueiris.generate_advanced_configurations` to Integration -> Options
- Added ability to configure the log level of the component from Integration - Options, more details in README

**Fixed bugs:**

- Fix [\#60](https://github.com/elad-bar/ha-blueiris/issues/60) configuration generating process and README links

## 2020-04-24 #2

**Fixed bugs:**

- Fix [\#56](https://github.com/elad-bar/ha-blueiris/issues/51) moved dependency on MQTT to optional
- Fix missing resources

## 2020-04-24 #1

**Implemented enhancements:**

- Refactored camera to use basic camera component instead of generic

## 2020-04-20

**Fixed bugs:**

- Added validation if state is not available to restore it [\#54](https://github.com/elad-bar/ha-blueiris/issues/54)

## 2020-04-19

**Fixed bugs:**

- Fix issue [\#51](https://github.com/elad-bar/ha-blueiris/issues/51) in config_flow
- Validation of server existence made 2 calls to server instead of 1

## 2020-04-18

**Implemented enhancements:**

- Added CHANGELOG.md
- Improved README.md
- Separated BlueIris Server setting from README.md

**Fixed bugs:**

- Fix issue caused by integration removal - duplicate call for removing event listener

## 2020-04-15

**Implemented enhancements:**

- Major change of file structure
- Improved communication between BI API and HA
- Fix component update upon change
- Avoid API get details requests upon change of switch or when an MQTT message is being received
- Better management of entities and devices
- Added more log messages for faster debugging

## 2020-04-12

**Fixed bugs:**

- Fix issue [\#37](https://github.com/elad-bar/ha-blueiris/issues/37) - Restart of HASS causes all entities to be renamed to defaults <br/>
  improving the way the component is loading, unloading and discover new entities (sensors, camera and switch).  <br/>
  the main issue as reported in the past was that once changing the entity_id / name it will return to the original after restart.  <br/>
  another issue that caused by the way it was handled, upon changing the options (settings) - it took few seconds to present the new entities and sometimes it happened only after restart.  <br/>
  In that version, the entity_id, name will remain as manually set and changes of options will take place immediately

## 2020-02-28

**Fixed bugs:**

- Removed hard-dependency on MQTT, if MQTT integration was not set, binary sensors will not be created - Issue [\#32](https://github.com/elad-bar/ha-blueiris/issues/32)
- Fix issue [\#28](https://github.com/elad-bar/ha-blueiris/issues/28) - entities not available after restart
- Fix issue [\#27](https://github.com/elad-bar/ha-blueiris/issues/27) - when changing switch it doesn't work smoothly and after restart
- Resources (strings) fixed


**Implemented enhancements:**

- Username and password are now optional, if not set, will not create profile's switches
- Added validation for host, port and SSL state in configuration, if URL is not accessible, will throw an error
- Validate administrator username and password, in case entered wrong credentials, will throw an error


## 2020-02-07 - v2.0.0 - Breaking change!!!

**Implemented enhancements:**

- BlueIris 5 JSON API integration
- UI configuration support instead of YAML
- Less configurations, takes configurations from BI server (all cameras are loaded, audio binary sensor will not created unless needed)
- More details per camera in the attributes
- Switch functionality changed, each profile is being represented with a switch, `is armed` switch removed
- Added support for HACS

## 2020-02-05

**Implemented enhancements:**

- No need to declare binary_sensor, switch and camera as those are being auto-discovered

## 2020-01-17

**Implemented enhancements:**

- Fixed binary sensor for motion / audio to work without zones (no need to define MOTION_A to get its off event)
