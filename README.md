# Home assistant custom component for Azure IoT Hub

Based on Wictor Wilén (@wictorwilen) [script](https://gist.github.com/wictorwilen/cf2de4ff98105eff4dfb16dd04c879d4).
The original script was migrated for using the latest version (2.0) of Azure IoT Hub Device Client python SDK.
In order to use the plugin SDK must be installed into environment:

```bash
pip3 install azure-iot-device
```


**Example configuration.yaml:**

```yaml
# Example configuration.yaml entry
azure_iot_hub:
    host: <azure-iot-host>
    devices:
        <azure-iot-device-name>:
        auth_key: <auth-key>
        include:
          - <sensors>
        <another-azure-iot-device-name>:
        auth_key: <auth-key>
        include:
          - <sensors>
```
A full configuration example can be found below:

```yaml
# Example configuration.yaml entry
azure_iot_hub:
    host: myazureiothub
    devices:
      hass_device_1:
        auth_key: ABC1230ABC1230ABC1230ABC1230ABC1230ABC12300=
        include:
          - sun.sun
          - sensor.dht_sensor_temperature
          - sensor.yr_temperature
      hass_device_2:
        auth_key: ABC1230ABC1230ABC1230ABC1230ABC1230ABC12300=
        include:
          - group.phones
          - group.computers
```


**Configuration variables:**

Key | Type | Required | Description
-- | -- | -- | --
`azure-iot-host` | `string` | `True` |  Name of your Azure IoT Hub host (without .azure-devices.net)
`azure-iot-device-name` | `string` | `True` |  Name of your Azure IoT Hub device
`auth-key` | `string` | `True` |  The authentication key for the device
`sensors` | `array` | `False` |  The sensor values you want to send to the Azure IoT hub.<br/> _Note: not specifying any sensors will send all event changes to Azure IoT_


***
