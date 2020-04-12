# BlueIris

## Description

Integration with Blue Iris Video Security Software. Creates the following components:

* Camera - per-camera defined.
* MQTT Binary Sensors (MOTION, AUDIO, WATCHDOG) - per-camera defined.
* Switch (Arm / Unarmed) - only when profiles and admin username and password are provided.
* Support HLS Streams instead of H264.
* Support SSL with self-signed certificate.


## Change-log
Apr 12 2020
* Fix issue #37 - Restart of HASS causes all entities to be renamed to defaults <br/>
  improving the way the component is loading, unloading and discover new entities (sensors and device trackers).  <br/>
  the main issue as reported in the past was that once changing the entity_id / name it will return to the original after restart.  <br/>
  another issue that caused by the way it was handled, upon changing the options (settings) - it took few seconds to present the new entities and sometimes it happened only after restart.  <br/>
  In that version, the entity_id, name will remain as manually set and changes of options will take place immediately

Feb 28 2020
* Removed hard-dependency on MQTT, if MQTT integration was not set, binary sensors will not be created - Issue #32
* Username and password are now optional, if not set, will not create profile's switches
* Added validation for host, port and SSL state in configuration, if URL is not accessible, will throw an error
* Validate administrator username and password, in case entered wrong credentials, will throw an error
* Fix issue #28 - entities not available after restart
* Fix issue #27 - when changing switch it doesn't work smoothly and after restart
* Resources (strings) fixed

Feb 07 2020 - v2.0.0 - Breaking change!!! 
* BlueIris 5 JSON API integration
* UI configuration support instead of YAML
* Less configurations, takes configurations from BI server (all cameras are loaded, audio binary sensor will not created unless needed)
* More details per camera in the attributes 
* Switch functionality changed, each profile is being represented with a switch, `is armed` switch removed
* Added support for HACS
Feb 05 2020 - No need to declare binary_sensor, switch and camera as those are being auto-discoverd 
Jan 17 2020 - Fixed binary sensor for motion / audio to work without zones (no need to define MOTION_A to get its off event)  


## Configuration

#### From the UI (Configuration -> Integration)
```
host: hostname or ip
port: port 
username: Username 
password: Password 
ssl: should use ssl?
```
## Components
From now, components are not being displayed in the entities of the integration and available only through states (Developer -> States)

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

### Blue Iris API Configuration
If you intent to use any of the Blue Iris REST API commands (such as profile switching), it's recommended you create a separate Administrator user for Home Assitant to connect to, and limit access to LAN only.  Use this username and password in your Home Assistant configuration (shown in the next section). This keeps any accesses or limitations you may wish to set on Home Assistant separate from the primary Administrator.

![Blue Iris Edit User](/docs/images/bi-edit_user.png)

### Blue Iris Web Server Configuration
Enable the Blue Iris Web Server. Select the  `Advanced...` button to proceed to the next step.

![Blue Iris Web Server](/docs/images/bi-web_server.png)

Set Authentication to be `Non-LAN only`. Leave `Use secure session keys and login page` unchecked. The secure session option uses `HTTP_DIGEST_AUTHENTICATION`, which isn't fully supported throughout the Home Assistant codebase yet. Also, in the case you want to use Casting and/or Streaming, some media player devices don't support using authentication.

![Blue Iris Web Server Advanced](/docs/images/bi-web_server_advanced.png)

Configure the Encoding settings so they’re compatible for Chromecast devices: `H.264` video, `AAC` audio, and `Resize output frame width x height` should be set to `1920 x 1080`:

![Blue Iris Encoder Options](/docs/images/bi-web_server_encoder.png)

Finally, enable re-encoding. Set `Hardware accelerated decode (restart)` to a setting appropriate to your hardware (e.g. `Intel(R)+VideoPostPRoc`).

![Blue Iris Cameras Options](/docs/images/bi-cameras.png)

### Lovelace UI Configuration

```YAML
# Example ui-lovelace.yaml view entry
title: Blue Iris
icon: mdi:eye

cards:
  - type: custom:vertical-stack-in-card
    cards:
      # System cameras
      - type: horizontal-stack
        cards:
          - type: custom:vertical-stack-in-card
            cards:
              - type: picture-entity
                entity: camera.all
                name: All
                show_state: false
          - type: custom:vertical-stack-in-card
            cards:
              - type: picture-entity
                entity: camera.cycle
                name: Cycle
                show_state: false
      # Blue Iris Armed / Disarm Profiles
      - type: entities
        title: Blue Iris
        show_header_toggle: false
        entities:
          - entity: switch.blueiris_alerts
            name: Arm / Disarm

  # Front Door camera
  - type: custom:vertical-stack-in-card
    cards:
      - type: picture-entity
        entity: camera.front_door
        name: Front Door
        show_state: false
      - type: glance
        entities:
          - entity: binary_sensor.front_door_motion
            name: Motion
          - entity: binary_sensor.front_door_audio
            name: Audio
          - entity: binary_sensor.front_door_connectivity
            name: Connectivity

  # Front Drive camera
  - type: custom:vertical-stack-in-card
    cards:
      - type: picture-entity
        entity: camera.front_drive
        name: Front Drive
        show_state: false
      - type: glance
        entities:
          - entity: binary_sensor.front_drive_motion
            name: Motion
          - entity: binary_sensor.front_drive_audio
            name: Audio
          - entity: binary_sensor.front_drive_connectivity
            name: Connectivity  

  # Garage camera
  - type: custom:vertical-stack-in-card
    cards:
      - type: picture-entity
        entity: camera.garage
        name: Garage
        show_state: false
      - type: glance
        entities:
          - entity: binary_sensor.garage_motion
            name: Motion
          - entity: binary_sensor.garage_audio
            name: Audio
          - entity: binary_sensor.garage_connectivity
            name: Connectivity
```

### Blue Iris MQTT Configuration

In order to support the MQTT binary sensors for the camera, some additional configuration needs to be performed on both Home Assistant and Blue Iris:

Assuming you are using the built-in MQTT server or the add-on Mosquitto broker, in the Home Assistant `Configuration | Users panel`, create a new user for Blue Iris to connect to the MQTT broker with. This user may be placed in the Users Group, to limit the scope of its access, since it is only required to connect to the MQTT broker. Otherwise, create a user appropriate for Blue Iris in your chosen MQTT broker.

In the Blue Iris Options panel, on the `Digital IO and IoT` tab under `MQTT`, select `"Configure..."` and enter the host and port of the Home Assistant MQTT server, and the username and password created for the Blue Iris user.

**NOTE:** Do not press the "Test" button, it is intended to test MQTT connections to (not from) the Blue Iris MQTT broker and will crash Blue Iris.

![Blue Iris Edit MQTT Server](/docs/images/bi-edit_mqtt_server.png)

For each camera you wish to monitor, select `"Camera properties..."` and on the `Alerts` tab, check `"Post to a web address or MQTT server"` and then select `"Configure..."`.

Binary sensors for motion, audio and watchdog (connectivity) per camera,
In order to configure it in BlueIris you will need to go to:
#### Motion
Camera settings -> Alerts:
Fire when: This camera is triggered

Motion zones must be checked

At least 1 zone must be checked (A-H) with Any selected in the camera's drop-down
OR

All selected in the camera's drop-down

Action section:
Click on `On alert`, 

in the popup window, create new (or modify) alert for MQTT with the following settings:
```
Topic - BlueIris/&CAM/Status
Payload - { "type": "&TYPE", "trigger": "ON" }
```

for `On reset` do the same with payload:
`{ "type": "&TYPE", "trigger": "OFF" }`


The alert should be sent for the profile you would like it to trigger

![Blue Iris Motion](/docs/images/bi-motion-alerts.png)

![Blue Iris MQTT Alert](/docs/images/bi-alerts-list.png)
![Blue Iris MQTT Alert](/docs/images/bi-alerts-settings.png)

#### Audio
Camera settings -> Audio -> Options:<br/>
Check the `Trigger the camera during profiles` and mark all profiles you would like it to trigger<br/>
Check the `Use 1 second average intensity` and set the sensitivity level to the desired level<br/>

Payloads will be sent according to the definition in the Alert's section defined above using the same settings.

![Blue Iris Alerts](/docs/images/bi-audio-alerts.png)

#### Watchdog (Connectivity)
Camera settings -> Watchdog<br/>
in the action's section click on `On loss of signal`, <br/>
then in the popup window, create new (or modify) alert for MQTT with the following settings:
```
Topic - BlueIris/&CAM/Status
Payload - { "type": "Connectivity", "trigger": "OFF" }
```

for `On signal restoration` do the same with payload:
`{ "type": "&TYPE", "trigger": "ON" }` 

The alert should be sent for the profile you would like it to trigger

![Blue Iris Alerts](/docs/images/bi-watchdog-alerts.png)

#### Troubleshooting MQTT

Things to check:

* Do you have a MQTT broker set up and configured? It is recommend to use the [Mosquitto MQTT broker](https://www.home-assistant.io/addons/mosquitto/) add-on, instead of the HA embedded broker - Mosquitto appears to be much more robust. Check that the broker is starting up clean and the topics are coming in without pitching errors.
* Do you have the [MQTT Integration configured](https://www.home-assistant.io/addons/mosquitto/#home-assistant-configuration)? It's not sufficient to just install/start the broker. Make sure to check the `Enable discovery` box when you configure the integration.
  
  ![Integrations MQTT](/docs/images/ha-integrations_mqtt.png)
  
  ![Integrations MQTT Configure](/docs/images/ha-integrations_mqtt_configure.png)

## Casting

Currently the Stream Component is a bit ragged to use to cast Blue Iris video streams, which don't need proxying.

**NOTE:** programmatic creation of `input_select` groups are still on the development plan. Until then, casting can be manually configured.

### Home Assistant MQTT Configuration

```YAML
# Example configuration.yaml entry
# NOTE: replace {BI_HOST}:{BI_PORT} with the Blue Iris server IP and Port
# https://www.home-assistant.io/components/input_select/
input_select:
  camera_dropdown:
    name: Cast camera
    options:
      - All Cameras
      - Cycle Cameras
      - Front Door
      - Front Drive
      - Garage
    initial: All Cameras
    icon: mdi:camera
  cast_to_screen_dropdown:
    name: To Screen
    options:
      - Entryway Display
      - Living Room Display
    initial: Living Room Display
    icon: mdi:cast

# https://www.home-assistant.io/components/script/
script:
  execute_cast_dropdown:
    alias: Press to execute
    sequence:
      # https://www.home-assistant.io/components/media_player/
      - service: media_player.play_media
        data_template:
          entity_id: >
            {% if is_state('input_select.cast_to_screen_dropdown', 'Entryway Display') %}
              media_player.entryway_display
            {% elif is_state('input_select.cast_to_screen_dropdown', 'Living Room Display') %}
              media_player.living_room_display
            {% endif %}
          media_content_id: >
            {% if is_state('input_select.camera_dropdown', 'Front Door') %}
              http://192.168.0.10:8081/mjpg/CAM4/video.mjpg
            {% elif is_state('input_select.camera_dropdown', 'Front Drive') %}
              http://192.168.0.10:8081/mjpg/CAM5/video.mjpg
            {% elif is_state('input_select.camera_dropdown', 'Garage') %}
              http://192.168.0.10:8081/mjpg/CAM6/video.mjpg
            {% elif is_state('input_select.camera_dropdown', 'Cycle Cameras') %}
              http://192.168.0.10:8081/mjpg/@index?/video.mjpg
            {% elif is_state('input_select.camera_dropdown', 'All Cameras') %}
              http://192.168.0.10:8081/mjpg/index?/video.mjpg
            {% endif %}
          media_content_type: 'image/jpg'
```

### Lovelace UI Casting Configuration

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

### Auto-generate configurations:
`blueiris.generate_advanced_configurations` service will create YAML with all the configurations in the config directory under blueiris.advanced_configurations.yaml:
* input select (drop-downs)
* script to cast based on the selection
* UI of all the components created by BlueIris based on the description above

## Track Updates

This custom card can be tracked with the help of custom-updater.

In your configuration.yaml

```YAML
custom_updater:
  track:
    - components
  component_urls:
    - https://raw.githubusercontent.com/elad-bar/ha-blueiris/master/blueiris.json
```

## Contributors

<a href="https://github.com/darkgrue">@darkgrue</a>
