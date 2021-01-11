# hacore_opcua

opcua custom component for home assistant

## installation

copy the opcua folder into your /config/custom_components/ directory.


## Configuration

Connections to various opcua targets are configured under the opcua domain. The component is based on https://github.com/FreeOpcUa/python-opcua and its connections capabilities are more or less carried over into the cofiguration setup.

At a minimum a "name" and "url" are require.  

If configuring encryption you will need to generate an application certification and private key that matchs the "application_uri". Below the certificate and private key from the client examples of FreeOpcUa are used. (and can be used for testing)

More than one opcua target can be specified.

```yaml
opcua:
  - name: target1
    url: "opc.tcp://172.17.0.2:4840/"
    application_uri: "urn:example.org:FreeOpcUa:python-opcua"
    session_timeout: 600000
    secure_timeout: 600000
    security_string: "Basic256Sha256,SignAndEncrypt,/ssl/certificate-example.der,/ssl/private-key-example.pem"
```


## Sensors

Sensors are configured by providing a "name", "hub" and "nodeid", "unit_of_measurement" are also supported.

```yaml
sensor:
  platform: opcua
  nodes:
    - name: Sensor1
      hub: target1
      nodeid: "ns=1;i=43840"
      unit_of_measurement: degrees

    - name: Sensor2
      hub: target2
      nodeid: "ns=1;i=51028"
      unit_of_measurement: degrees

    - name: Sensor3
      hub: target1
      nodeid: "ns=1;s=integer"
```

## Services

The opcus domain will publish a "set_value" service which can be called by home assistant. The service data requires a "nodeid", "hub" and a "value" which can be a template value or more or less any opc type data.

```yaml
nodeid: ns=1;i=51028
value: '{{states("sensor.sensor1")}}'
hub: target1
```

The opcua domain will also publish a "connect" and "close" service.  These can be used to reconnect an opcua session in the event it is closed by the opcua server. or to prematurely close a connection to a server.

Only the target "hub" is required to be specified.

```yaml
hub: target1
```
