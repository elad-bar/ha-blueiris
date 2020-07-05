# BlueIris Server Settings

#### User
If you intend to use any of the Blue Iris REST API commands (such as profile switching), it's recommended you create a separate Administrator user for Home Assitant to connect to, and limit access to LAN only. Use this username and password in your Home Assistant configuration (shown in the next section). This keeps any accesses or limitations you may wish to set on Home Assistant separate from the primary Administrator.

![Blue Iris Edit User](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-edit_user.png)

#### Web Server 
Enable the Blue Iris Web Server. Select the  `Advanced…` button to proceed to the next step.

![Blue Iris Web Server](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-web_server.png)

Set Authentication to be `Non-LAN only`. Leave `Use secure session keys and login page` unchecked. The secure session option uses `HTTP_DIGEST_AUTHENTICATION`, which isn't fully supported throughout the Home Assistant codebase yet. Also, in the case you want to use Casting and/or Streaming, some media player devices don't support using authentication.

![Blue Iris Web Server Advanced](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-web_server_advanced.png)

Configure the Encoding settings so they’re compatible for Chromecast devices: `H.264` video, `AAC` audio, and `Resize output frame width x height` should be set to `1920 x 1080`:

![Blue Iris Encoder Options](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-web_server_encoder.png)

Finally, enable re-encoding. Set `Hardware accelerated decode (restart)` to a setting appropriate to your hardware (e.g. `Intel(R)+VideoPostPRoc`).

![Blue Iris Cameras Options](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-cameras.png)

#### MQTT

In order to support the MQTT binary sensors for the camera, some additional configuration needs to be performed on both Home Assistant and Blue Iris:

Assuming you are using the built-in MQTT server or the add-on Mosquitto broker, in the Home Assistant `Configuration | Users panel`, create a new user that Blue Iris can use to connect to the MQTT broker. This user may be placed in the Users Group, to limit the scope of its access, since it is only required to connect to the MQTT broker. 

If you are using another MQTT broker, create a user appropriate for Blue Iris there.

To connect Blue Iris to MQTT broker go to the Blue Iris `Settings/Info` options panel, then on the `Digital IO and IoT` tab under `MQTT`, select `Configure…` and enter the host and port of the Home Assistant MQTT server, and the username and password created for the Blue Iris user.

![Blue Iris Edit MQTT Server](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-edit_mqtt_server.png)

###### Troubleshooting

* Do you have a MQTT broker set up and configured? It is recommend to use the [Mosquitto MQTT broker](https://www.home-assistant.io/addons/mosquitto/) add-on, instead of the HA embedded broker - Mosquitto appears to be much more robust and the built-in broke is deprecated. Check that the broker is starting up cleanly and the topics are coming in without pitching errors. [MQTT Explorer](http://mqtt-explorer.com) is a useful free tool for checking the flow of MQTT messages.
* Do you have the [MQTT Integration configured](https://www.home-assistant.io/addons/mosquitto/#home-assistant-configuration)? It's not sufficient to just install/start the broker. Make sure to check the `Enable discovery` box when you configure the integration.
  
  ![Integrations MQTT](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/ha-integrations_mqtt.png)
  
  ![Integrations MQTT Configure](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/ha-integrations_mqtt_configure.png)


#### Event triggers

We'll need to individually configure MQTT alerts for motion, audio, and connectivity for each camera you wish to monitor. For all three of these alert types, start by selecting `Camera Settings…` for a given camera in Blue Iris then follow the steps below.

##### Motion Alerts

- `Camera settings` -> `Alerts` tab
- In the `Trigger sources and zones` section:
  - Fire when: This camera is triggered
  - Motion zones must be checked
  - At least 1 zone must be checked (A-H) with Any selected in the camera's drop-down
  - OR All selected in the camera's drop-down

- In the `Actions` section:
  - Click on `On alert…`
  - Click the `+` button to add a new alert. Select `Web request or MQTT`
  - In the dialog that comes up, check all of the trigger sources (such as `DIO`, `Extern`, etc) other than `Audio`
  - Change the drop down from `http:` to `MQTT topic`
  - Configure the fields like so:
     - MQTT topic - `BlueIris/&CAM/Status`
     - Post/payload - `{ "type": "Motion", "trigger": "ON" }`
  - Click `OK` to save.
  - Click on `On reset…` and repeat the steps above, but with a payload of `{ "type": "Motion", "trigger": "OFF" }`
  
- Repeat the above steps for each profile from which you want alerts.

![Blue Iris Motion](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-motion-alerts.png)

![Blue Iris MQTT Alert](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-alerts-list.png)
![Blue Iris MQTT Alert](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-alerts-settings.png)

##### Audio Alerts

- `Camera settings` -> `Audio` tab
- In the `Options` section:
  - Check the `Trigger the camera during profiles` and mark all profiles you would like it to trigger
  - Check the `Use 1 second average intensity` and set the sensitivity level to the desired level

- Go back to the `Alerts` tab to set up alerts for the audio triggers
  - Repeat all of the steps for the motion alerts above, but for audio:
    - Click on `On alert…`
    - Click the `+` button to create a new alert, in addition to the existing motion one. Select `Web request or MQTT`
    - In the dialog, select _only_ the `Audio` trigger source
    - Configure the MQTT topic and payload like so:
      - MQTT topic - `BlueIris/&CAM/Status`
      - Post/payload - `{ "type": "Audio", "trigger": "ON" }`
    - Click `OK` and repeat for `On reset…` using the payload `{ "type": "Audio", "trigger": "OFF" }`
    - Repeat for each profile where you want audio alerts.

![Blue Iris Alerts](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-audio-alerts.png)

##### Watchdog (Connectivity) Alerts

- `Camera settings` -> `Watchdog` tab
- In the `Signal loss` section:
  - Click on `On loss of signal…`
  - In the dialog, create a new MQTT alert from the `+` button
  - In the alert dialog, leave everything checked in `Trigger sources and zones`
  - Set the MQTT topic and payload to:
    - MQTT topic - `BlueIris/&CAM/Status`
    - Post/payload - `{ "type": "Connectivity", "trigger": "OFF" }` (Note that the `trigger` is reversed from other alerts).
  - For `On signal restoration…` do the same, but with the payload `{ "type": "Connectivity", "trigger": "ON" }` 
- Repeat the above steps for each profile from which you want alerts.

![Blue Iris Alerts](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-watchdog-alerts.png)
