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
Look for "Integration with Blue Iris NVR" and install

#### Integration settings
###### Basic configuration (Configuration -> Integrations -> Add BlueIris)
```
host: hostname or ip
port: port 
username: Username of admin user for BI
password: Password of admin user for BI 
ssl: should use ssl?
```

###### Integration options (Configuration -> Integrations -> BlueIris Integration -> Options)  
```
Username: Username of admin user for BI 
Password: Password of admin user for BI
Clear credentials: Checkbox, workaround to clear the textbox of username & password due to an issue while filling partially form in HA Options, default=False
Exclude system camera: should include / exclude system camera (All / Cycle), default=False
```

###### Configuration validations
Upon submitting the form of creating an integration or updating options,

Component will try to login to the BlueIris server to verify new settings, following errors can appear:
- BlueIris integration ({name}) already configured
- Invalid administrator credentials - credentials are invalid or user is not an admin
- Invalid server details - Cannot reach the server

###### Password protection
Password is being saved in integration settings to `.storage` encrypted,

In the past password saved in clear text, to use the encryption, please remove the integration, restart HA and re-add integration,

As long as the password will remain in clear text saved in integration setting, the following warning log message will appear during restart:
```
EdgeOS password is not encrypted, please remove integration and reintegrate
```

## Components

###### Binary Sensor - Alerts
```
State: represents whether there is an active alert or not
Attributes:
    Active alerts #
    System name
    Version
    License
    Support expiration
    Logged in User
    Latitude
    Longitude
```

###### Binary Sensor - Connectivity - Non-system-camera
```
State: represents whether the camera is online or not (based on MQTT message)
```

###### Binary Sensor - Audio - Non-system-camera and camera supports audio
```
State: represents whether the camera is triggered for noise or not (based on MQTT message)
```

###### Binary Sensor - Motion - Non-system-camera
```
State: represents whether the camera is triggered for motion or not (based on MQTT message)
```

###### Camera
```
State: Idle
Attributes:
    FPS
    Audio support
    Width
    Height
    Is Online
    Is Recording
    Issue (Camera is yellow)
    Alerts #
    Triggers #
    Clips #
    No Signal #
    Error
```

###### Switch - Profile (Per profile)
If you are turning off one of the switch it will work according to the following order:
Profile #1 turned off, will turn on Profile #0
All the other profiles upon turning off, will turn on Profile #1

```
State: Allows to set the active profile, only one of the profile switches can be turned on at a time
```


## Lovelace UI Configuration
[Example of UI layout](https://github.com/elad-bar/ha-blueiris/blob/master/docs/config/casting/configuration.yaml)

## Casting

Currently the Stream Component is a bit ragged to use to cast Blue Iris video streams, which don't need proxying.

#### Auto-generating configurations service:
`blueiris.generate_advanced_configurations` service will create YAML with all the configurations in the config directory under blueiris.advanced_configurations.yaml:
- Input select (drop-downs)
- Script to cast based on the selection
- UI of all the components created by BlueIris based on the description above

[Example of configuration output](https://github.com/elad-bar/ha-blueiris/blob/master/docs/config/casting/configuration.yaml)

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

[Example of configuration output](https://github.com/elad-bar/ha-blueiris/blob/master/docs/config/casting/ui-lovelace.yaml)

## Contributors

<a href="https://github.com/darkgrue">@darkgrue</a>
