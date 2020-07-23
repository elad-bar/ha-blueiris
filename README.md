# BlueIris

## Description

Integration with Blue Iris Video Security Software. Creates the following components:

* Camera - per-camera defined.
* MQTT Binary Sensors (MOTION, AUDIO, WATCHDOG) - per-camera defined.
* Switch (Arm / Unarmed) - only when profiles and admin username and password are provided.
* Support HLS Streams instead of H264.
* Support SSL with self-signed certificate.

[Changelog](https://github.com/elad-bar/ha-blueiris/blob/master/CHANGELOG.md)

## How to

#### Requirements
- BlueIris Server available with a user
- To control profiles, user must have 'admin' level permissions
- MQTT Integration is optional - it will allow to listen to BlueIris event
- Read the [BlueIris manual](https://github.com/elad-bar/ha-blueiris/blob/master/docs/blueiris-server.md) for this component

#### Installations via HACS
Look for "Blue Iris NVR" and install

#### Integration settings
###### Basic configuration (Configuration -> Integrations -> Add BlueIris)
Fields name | Type | Required | Default | Description
--- | --- | --- | --- | --- |
Host | Texbox | + | None | Hostname or IP address of the BlueIris server
Port | Textbox | + | 0 | HTTP Port to access BlueIris server
SSL | Check-box | + | Unchecked | Is SSL supported?
Username | Textbox | - | | Username of admin user for BlueIris server
Password | Textbox | - | | Password of admin user for BlueIris server

###### Integration options (Configuration -> Integrations -> BlueIris Integration -> Options)  
Fields name | Type | Required | Default | Description
--- | --- | --- | --- | --- |
Host | Texbox | + | ast stored hostname | Hostname or IP address of the BlueIris server
Port | Textbox | + | 0ast stored port | HTTP Port to access BlueIris server
SSL | Check-box | + | Last stored SSL flag | Is SSL supported?
Username | Textbox | - | Last stored username | Username of admin user for BlueIris server
Password | Textbox | - | Last stored password | Password of admin user for BlueIris server
Clear credentials | Check-box | + | Unchecked | Workaround to clear the username & password since there is not support for optional fields (Not being stored under options)
Generate configurations | Check-box | + | Unchecked |  Will take generate store and configuration for HA, more details below (Not being stored under options)
Log level | Drop-down | + | Default | Changes component's log level (more details below)
Reset components settings to default | Check-box | + | Unchecked |  Will reset drown-downs of componet's creation to their default (Not being stored under options) 
Camera components | Drop-down | - | All camera | Will create camera for each of the chosen camera
Motion sensors | Drop-down | - | All non-system camera | Will create binary sensor for each of the chosen camera
Connectivity sensors | Drop-down | - | All non-system camera | Will create connectivity binary sensor for each of the chosen camera
Audio sensors | Drop-down | - | All audio supported non-system camera | Will create audio binary sensor for each of the chosen camera
Profile switches | Drop-down | - | All profiles | Will create switch for each of the chosen profiles
Stream type | Drop-down | - | H264 | Defines the stream type H264 / MJPG

**Integration's title**
Title will be extracted from BlueIris server's configuration, it will be set upon adding the server, and after every Option's change

Note that in case there are 2 integrations with the same integration's title, components will be overwritten by both integrations.

**Log Level's drop-down**
New feature to set the log level for the component without need to set log_level in `customization:` and restart or call manually `logger.set_level` and loose it after restart.

Upon startup or integration's option update, based on the value chosen, the component will make a service call to `logger.set_level` for that component with the desired value,

In case `Default` option is chosen, flow will skip calling the service, after changing from any other option to `Default`, it will not take place automatically, only after restart

**Control component's creation**
New feature to control which of the components will be created:

- Sensors drop-down will be available only when MQTT component is defined
- Audio sensors drop-down will include only audio support non-system camera
- Connectivity and Motion sensors will be created only for non-system camera
- Profile's drop-down will be available only when admin user's credentials set to the integration
- Once configuration manually changed, new camera that will be added will require manually setting configuration
- To restore defaults which allows automatically adding new camera, check the check-box of Reset components settings to default

###### Auto-generating configurations files:
Will create YAML with all the configurations in the config directory under blueiris.advanced_configurations.yaml:
- Input select (drop-downs)
- Script to cast based on the selection
- UI of all the components created by BlueIris based on the description above

[Example of configuration output](https://github.com/elad-bar/ha-blueiris/blob/master/docs/configs/casting/configuration.yaml)


###### Configuration validations
Upon submitting the form of creating an integration or updating options,

Component will try to login to the BlueIris server to verify new settings, following errors can appear:
- BlueIris integration ({host}) already configured
- Invalid administrator credentials - credentials are invalid or user is not an admin
- Invalid server details - Cannot reach the server

###### Encryption key got corrupted
If a persistent notification popped up with the following message:
```
Encryption key got corrupted, please remove the integration and re-add it
```

It means that encryption key was modified from outside the code,
Please remove the integration and re-add it to make it work again.

## Components

###### Binary Sensor - Alerts
Represents whether there is an active alert or not

Attributes | 
--- | 
Active alerts # |
System name |
Version |
License |
Support expiration |
Logged in User |
Latitude |
Longitude |

###### Binary Sensor - Connectivity - Non-system-camera
Represents whether the camera is online or not (based on MQTT message)

###### Binary Sensor - Audio - Non-system-camera and camera supports audio
Represents whether the camera is triggered for noise or not (based on MQTT message)

###### Binary Sensor - Motion - Non-system-camera
Represents whether the camera is triggered for motion or not (based on MQTT message)

###### Binary Sensor - DIO - Non-system-camera
Represents whether the camera is triggered for digital I/O event or not (based on MQTT message)

###### Binary Sensor - External - Non-system-camera
Represents whether the camera is triggered for external / ONVIF event or not (based on MQTT message)

###### Camera
State: Idle

Attributes | 
--- | 
FPS |
Audio support |
Width |
Height |
Is Online |
Is Recording |
Issue (Camera is yellow) |
Alerts # |
Triggers # |
Clips # |
No Signal # |
Error |

###### Switch - Profile (Per profile)
Allows to set the active profile, only one of the profile switches can be turned on at a time

If you are turning off one of the switch it will work according to the following order:
Profile #1 turned off, will turn on Profile #0
All the other profiles upon turning off, will turn on Profile #1

## Lovelace UI Configuration
[Example of UI layout](https://github.com/elad-bar/ha-blueiris/blob/master/docs/configs/casting/configuration.yaml)

## Casting

Currently the Stream Component is a bit ragged to use to cast Blue Iris video streams, which don't need proxying.

#### Lovelace UI for casting

```YAML
# Example ui-lovelace.yaml view entry
  - type: entities
    title: Cast Camera to Screen
    show_header_toggle: false
    entities:
      - entity: input_select.camera_dropdown
      - entity: input_select.cast_to_screen_dropdown
      - entity: script.execute_cast_dropdown
```

[Example of configuration output](https://github.com/elad-bar/ha-blueiris/blob/master/docs/configs/casting/ui-lovelace.yaml)

## Contributors

<a href="https://github.com/darkgrue">@darkgrue</a>
