# BlueIris Server Settings

#### User

If you intent to use any of the Blue Iris REST API commands (such as profile switching),

it's recommended you create a separate Administrator user for Home Assistant to connect to, and limit access to LAN only.

Use this username and password in your Home Assistant configuration (shown in the next section).

This keeps any accesses or limitations you may wish to set on Home Assistant separate from the primary Administrator.

![Blue Iris Edit User](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-edit_user.png)

#### Web Server

Enable the Blue Iris Web Server. Select the `Advanced...` button to proceed to the next step.

![Blue Iris Web Server](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-web_server.png)

Set Authentication to be `Non-LAN only`. Leave `Use secure session keys and login page` unchecked. The secure session option uses `HTTP_DIGEST_AUTHENTICATION`, which isn't fully supported throughout the Home Assistant codebase yet. Also, in the case you want to use Casting and/or Streaming, some media player devices don't support using authentication.

![Blue Iris Web Server Advanced](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-web_server_advanced.png)

Configure the Encoding settings so they’re compatible for Chromecast devices: `H.264` video, `AAC` audio, and `Resize output frame width x height` should be set to `1920 x 1080`:

![Blue Iris Encoder Options](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-web_server_encoder.png)

Finally, enable re-encoding. Set `Hardware accelerated decode (restart)` to a setting appropriate to your hardware (e.g. `Intel(R)+VideoPostPRoc`).

![Blue Iris Cameras Options](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-cameras.png)

#### MQTT

In order to support the MQTT binary sensors for the camera, some additional configuration needs to be performed on both Home Assistant and Blue Iris:

Assuming you are using the built-in MQTT server or the add-on Mosquitto broker,

in the Home Assistant `Configuration | Users panel`,

create a new user for Blue Iris to connect to the MQTT broker with.

This user may be placed in the Users Group, to limit the scope of its access, since it is only required to connect to the MQTT broker.

Otherwise, create a user appropriate for Blue Iris in your chosen MQTT broker.

In the Blue Iris Options panel, on the `Digital IO and IoT` tab under `MQTT`, select `"Configure..."` and enter the host and port of the Home Assistant MQTT server, and the username and password created for the Blue Iris user.

![Blue Iris Edit MQTT Server](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-edit_mqtt_server.png)

###### Troubleshooting

- Do you have a MQTT broker set up and configured? It is recommend to use the [Mosquitto MQTT broker](https://www.home-assistant.io/addons/mosquitto/) add-on, instead of the HA embedded broker - Mosquitto appears to be much more robust. Check that the broker is starting up clean and the topics are coming in without pitching errors.
- Do you have the [MQTT Integration configured](https://www.home-assistant.io/addons/mosquitto/#home-assistant-configuration)? It's not sufficient to just install/start the broker. Make sure to check the `Enable discovery` box when you configure the integration.

  ![Integrations MQTT](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/ha-integrations_mqtt.png)

  ![Integrations MQTT Configure](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/ha-integrations_mqtt_configure.png)

#### Event triggers

For each camera you wish to monitor, select `"Camera properties..."` and on the `Alerts` tab, check `"Post to a web address or MQTT server"` and then select `"Configure..."`.

Binary sensors for motion, external, DIO, audio and watchdog (connectivity) per camera,
In order to configure it in BlueIris you will need to go to:

##### Motion / External / DIO

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

The alert should be sent for the profile you would like it to trigger.

Note: Triggering the camera manually in BlueIris sends a different &TYPE and will not trigger the motion sensor. Motion must be detected on the camera for the sensor change to be detected.

![Blue Iris Motion](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-motion-alerts.png)

![Blue Iris MQTT Alert](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-alerts-list.png)
![Blue Iris MQTT Alert](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-alerts-settings.png)

##### Audio

Camera settings -> Audio -> Options:<br/>
Check the `Trigger the camera during profiles` and mark all profiles you would like it to trigger<br/>
Check the `Use 1 second average intensity` and set the sensitivity level to the desired level<br/>

Payloads will be sent according to the definition in the Alert's section defined above using the same settings.

![Blue Iris Alerts](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-audio-alerts.png)

##### Watchdog (Connectivity)

Camera settings -> Watchdog<br/>
in the action's section click on `On loss of signal`, <br/>
then in the popup window, create new (or modify) alert for MQTT with the following settings:

```
Topic - BlueIris/&CAM/Status
Payload - { "type": "Connectivity", "trigger": "OFF" }
```

for `On signal restoration` do the same with payload:
`{ "type": "Connectivity", "trigger": "ON" }`

The alert should be sent for the profile you would like it to trigger

![Blue Iris Alerts](https://github.com/elad-bar/ha-blueiris/blob/master/docs/images/bi-watchdog-alerts.png)
