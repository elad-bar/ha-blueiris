# BlueIris


## Description

Integration with Blue Iris Video Security Software. Creates the following components:
* Camera - per-camera defined.
* MQTT Binary Sensors (MOTION, AUDIO, EXTERNAL, WATCHDOG) - per-camera defined. The MQTT topic configured in Blue Iris should be `BlueIris/&CAM/&TYPE` for all cameras. Blue Iris will replace the macros with the correct camera short name and the alert type. Enter `ON` for the payload when triggered, and `OFF` for when trigger is reset. Make sure to check `Alert again when trigger is reset` to that Home Assistant gets notified when the alert ends.
* Switch (Arm / Unarmed) - only when profiles and admin username and password are provided.
* Support HLS Streams instead of H264.
* Support SSL with self-signed certificate.

## Configuration

### Blue Iris API Configuration

If you intent to use any of the Blue Iris REST API commands (such as profile switching), it's recommended you create a separate Administrator user for Home Assitant to connect to, and limit access to LAN only.  Use this username and password in your Home Assistant configuration (shown in the next section). This keeps any accesses or limitations you may wish to set on Home Assistant separate from the primary Administrator.

![Blue Iris Edit User](/docs/images/bi-edit_user.png)


### Home Assistant Configuration

```
# Example configuration.yaml entry
blueiris:
  # Hostname or IP of Blue Iris WebServer
  host: !secret blueiris_host
  # Port of Blue Iris WebServer
  port: !secret blueiris_port
  # [optional] Blue Iris profile numbers - will create switch if defined
  #   -1 is Default profile
  #   0 is Inactive profile
  #   1-7 profile set range     
  profile:
    # armed profile number
    armed: !secret blueiris_profile_armed
    # unarmed profile number
    unarmed: !secret blueiris_profile_unarmed
  # [optional] Blue Iris admin username and password - required to arm / unarm
  username: !secret blueiris_api_username
  password: !secret blueiris_api_password
  # List of camera objects
  camera:
    # Camera short name in Blue Iris
    - id: Kitchen
      # [optional] Name of the camera for display
      name: 'Kitchen Camera'
      # [optional] Room name (adds as attribute)
      room: Ground Floor

# Camera
# https://www.home-assistant.io/components/camera
camera:
  # Creates cameras according to the camera defined in the platform.
  - platform: blueiris

# Binary Sensor
# https://www.home-assistant.io/components/binary_sensor/
binary_sensor:
  # Creates binary sensors (MOTION, AUDIO, EXTERNAL, WATCHDOG) per-camera.
  - platform: blueiris

# Switch
# https://www.home-assistant.io/components/switch
switch:
  # Creates switch to arm and disarm Blue Iris.
  - platform: blueiris
```

### Blue Iris MQTT Configuration

In order to support the MQTT binary sensors for the camera, some additional configuration needs to be performed on both Home Assistant and Blue Iris:

Assuming you are using the built-in MQTT server or the add-on Mosquitto broker, in the Home Assistant `Configuration | Users panel`, create a new user for Blue Iris to connect to the MQTT broker with. This user may be placed in the Users Group, to limit the scope of its access, since it is only required to connect to the MQTT broker. Otherwise, create a user appropriate for Blue Iris in your chosen MQTT broker.

In the Blue Iris Options panel, on the `Digital IO and IoT` tab under `MQTT`, select `"Configure..."` and enter the host and port of the Home Assistant MQTT server, and the username and password created for the Blue Iris user.
**NOTE:** Do not press the "Test" button, it will crash Blue Iris, and is intended to test MQTT connections to the Blue Iris MQTT broker.

![Blue Iris Edit MQTT Server](/docs/images/bi-edit_mqtt_server.png)

For each camera you wish to monitor, select `"Camera properties..."` and on the `Alerts` tab, check `"Post to a web address or MQTT server"` and then select `"Configure..."`.

![Blue Iris Alerts](/docs/images/bi-alerts.png)

In the `Configure Web or MQTT Alert` dialog, set the options as shown below. The MQTT topic should be `BlueIris/&CAM/&TYPE` for all cameras. Blue Iris will replace the macros with the correct camera short name and the alert type. Enter `ON` for the payload when triggered, and `OFF` for when trigger is reset. Make sure to check `Alert again when trigger is reset` to that Home Assistant gets notified when the alert ends.

![Blue Iris MQTT Alert](/docs/images/bi-alerts_mqtt.png)

Similarly, configure the connectivity alert for the camera by going to the `Watchdog` tab and selecting `"Configure Watchdog Alerts"`. On the `Alerts` tab, check `"Post to a web address or MQTT server"` and then select `"Configure..."`. In the `Configure Web or MQTT Alert` dialog, set the options again (same as for Alerts).
**NOTE:** Even though connectivity is down when the Watchdog is triggered, the MQTT payload is still `ON`. The meaning is inverted in the component logic in order to keep the configuration straightforward.

![Blue Iris Watchdog](/docs/images/bi-watchdog.png)


## Track Updates

This custom card can be tracked with the help of custom-updater.

In your configuration.yaml

```
custom_updater:
  track:
    - components
  component_urls:
    - https://raw.githubusercontent.com/elad-bar/ha-blueiris/master/blueiris.json
```
