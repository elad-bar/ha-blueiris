# BlueIris

## Description

Integration with Blue Iris Video Security Software. Creates the following components:

* Camera - per-camera defined.
* MQTT Binary Sensors (MOTION, AUDIO, EXTERNAL, WATCHDOG) - per-camera defined. The MQTT topic configured in Blue Iris should be `BlueIris/&CAM/&TYPE` for all cameras. Blue Iris will replace the macros with the correct camera short name and the alert type. Enter `ON` for the payload when triggered, and `OFF` for when trigger is reset. Make sure to check `Alert again when trigger is reset` to that Home Assistant gets notified when the alert ends.
* Switch (Arm / Unarmed) - only when profiles and admin username and password are provided.
* Support HLS Streams instead of H264.
* Support SSL with self-signed certificate.

## Configuration

Basic configuration of the Component follows:

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

### Home Assistant Configuration

```YAML
# Example configuration.yaml entry
blueiris:
  host: !secret blueiris_host
  port: !secret blueiris_port
  # [optional] Blue Iris admin username and password
  username: !secret blueiris_admin_username
  password: !secret blueiris_admin_password
  # [optional] Blue Iris profile numbers - will create switch if defined
  #   -1 is Default profile
  #   0 is Inactive profile
  #   1-7 profile range
  profile:
    # armed profile number
    armed: -1
    # unarmed profile number
    unarmed: 3
  # List of camera objects
  camera:
      # Camera short name in Blue Iris
    - id: Cam4
      # [optional] Name of the camera for display
      name: 'Front Door'
      # [optional] Room name (adds as attribute)
      room: 'Front Door'
      # BlueIris camera's short name
    - id: Cam5
      # name of the camera for display
      name: 'Front Drive'
      # Room name (adds as attribute)
      room: 'Front Drive'
      # BlueIris camera's short name
    - id: Cam6
      # name of the camera for display
      name: 'Garage'
      # Room name (adds as attribute)
      room: 'Garage'

# Binary Sensor
# https://www.home-assistant.io/components/binary_sensor/
binary_sensor:
  # Creates binary sensors according cameras defined in the platform
  - platform: blueiris

# Camera
# https://www.home-assistant.io/components/camera
camera:
  # Creates cameras according to those defined in the platform
  - platform: blueiris

# Stream
# https://www.home-assistant.io/components/stream
stream:

# Switch
# https://www.home-assistant.io/components/switch
switch:
  # Creates switch to arm and disarm BlueIris (available only when profiles and admin password are provided)
  - platform: blueiris
```

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
          - entity: binary_sensor.front_door_watchdog
            name: Watchdog

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
          - entity: binary_sensor.front_drive_watchdog
            name: Watchdog  

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
          - entity: binary_sensor.garage_watchdog
            name: Watchdog
```

### Blue Iris MQTT Configuration

In order to support the MQTT binary sensors for the camera, some additional configuration needs to be performed on both Home Assistant and Blue Iris:

Assuming you are using the built-in MQTT server or the add-on Mosquitto broker, in the Home Assistant `Configuration | Users panel`, create a new user for Blue Iris to connect to the MQTT broker with. This user may be placed in the Users Group, to limit the scope of its access, since it is only required to connect to the MQTT broker. Otherwise, create a user appropriate for Blue Iris in your chosen MQTT broker.

In the Blue Iris Options panel, on the `Digital IO and IoT` tab under `MQTT`, select `"Configure..."` and enter the host and port of the Home Assistant MQTT server, and the username and password created for the Blue Iris user.

**NOTE:** Do not press the "Test" button, it is intended to test MQTT connections to (not from) the Blue Iris MQTT broker and will crash Blue Iris.

![Blue Iris Edit MQTT Server](/docs/images/bi-edit_mqtt_server.png)

For each camera you wish to monitor, select `"Camera properties..."` and on the `Alerts` tab, check `"Post to a web address or MQTT server"` and then select `"Configure..."`.

![Blue Iris Alerts](/docs/images/bi-alerts.png)

In the `Configure Web or MQTT Alert` dialog, set the options as shown below. The MQTT topic should be `BlueIris/&CAM/&TYPE` for all cameras. Blue Iris will replace the macros with the correct camera short name and the alert type. Enter `ON` for the payload when triggered, and `OFF` for when trigger is reset. Make sure to check `Alert again when trigger is reset` to that Home Assistant gets notified when the alert ends.

**NOTE:** Blue Iris appends the motion zone that triggered to the `&TYPE` macro (e.g. "MOTION_A"). The Component will only automatically create a binary sensor for the "MOTION_A" topic (i.e. for a single motion trigger zone). If you need to utilize multiple motion zones, you may:

* Set the topic without using a macro (e.g. "BlueIris/&CAM/MOTION_A"); this will cause `AUDIO` and `EXTERNAL` events to also trigger as `MOTION_A` events (but will fix all problems with motion zones).
* Manually create additional sensors and automation in your Home Assistant configuration to process the additional MQTT topics.

![Blue Iris MQTT Alert](/docs/images/bi-alerts_mqtt.png)

Similarly, configure the connectivity alert for the camera by going to the `Watchdog` tab and selecting `"Configure Watchdog Alerts"`. On the `Alerts` tab, check `"Post to a web address or MQTT server"` and then select `"Configure..."`. In the `Configure Web or MQTT Alert` dialog, set the options again (same as for Alerts).

**NOTE:** Even though connectivity is down when the Watchdog is triggered, the MQTT payload is still `ON`. The meaning is inverted in the component logic in order to keep the configuration straightforward.

![Blue Iris Watchdog](/docs/images/bi-watchdog.png)

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
