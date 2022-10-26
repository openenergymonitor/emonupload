# emonUpload

Download latest OpenEnergyMonitor firmware via GitHub releases; upload and test.

# Features

- Auto downloads latest firmware via GitHub Releases
- Upload attempts to upload bootloader via ISP (AVR MkII programmer) then uploads latest firmware sketch via serial UART
- Auto detection of [USB to UART programmer](https://shop.openenergymonitor.com/programmer-usb-to-serial-uart/) serial port
- Serial output display upon upload
- Dedicated serial monitor (auto baudrate)
- If RFM69Pi / emonPi receiver is detected RF test will be performed (check RF received)
- [Unit testing via PlatformIO](http://docs.platformio.org/en/stable/plus/unit-testing.html)
- Expandable to include any other Git repositories

***

# Install

- requires Python 3

``` 
$ sudo apt-get install avrdude picocom python3 python3-pip esptool
& pip install requirements.txt
```

Allow non root acces to serail ports and install platformIO udev rules:

`sudo usermod -a -G dialout $USER`

`curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core/master/scripts/99-platformio-udev.rules | sudo tee /etc/udev/rules.d/99-platformio-udev.rules`

More info: https://docs.platformio.org/en/latest/faq.html#platformio-udev-rules

*Logout then log back in and un-plug re-plug your USB programmer for the change to take effect*

Tested on Ubuntu 20.04


# Run

`./emonupload.py`


## Example

```
Error: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST
Testing internet connection...
Internet connection detected
Already up-to-date: emonUpload
Already up-to-date. repos/openenergymonitor-emonth2
Already up-to-date. repos/openenergymonitor-emonth
Updating repo: repos/openenergymonitor-emonpi
Updating d622c04..1be8c5f
Fast-forward
 bash-rw-indicator | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
Already up-to-date. repos/openenergymonitor-emontxfirmware


Latest openenergymonitor/emonth2firmware: V3.1.0
  Downloading: firmware.hex Bytes: 40538
      40538  [100.00%]

Latest openenergymonitor/emonthfirmware: V2.6.0
  Downloading: emonTH_latest.hex Bytes: 36885
      36885  [100.00%]

Latest openenergymonitor/emonpifirmware: V2.5.0
  Downloading: firmware.hex Bytes: 53142
      53142  [100.00%]

Latest openenergymonitor/emontxfirmwarefirmware: V2.5.0
  Downloading: firmware.hex Bytes: 44613
      44613  [100.00%]


-------------------------------------------------------------------------------
OpenEnergyMonitor Firmware Upload V1.7.0

Upload >

(x) emonTx V3

(i) emonPi

(h) emonTH V2

(3) 3-phase emonTx
(e) emonESP
(w) IoTaWatt
(v) OpenEVSE
(r) WiFi MQTT Relay


(o) old emonTH V1 upload
(t) emonTH V2 sensor test
(s) view Serial Debug
(u) update firmware (web connection required)


Enter lettercode for required function >
```



## Install PlatformIO

*Not essential for upload: Required for unit testing and serial monitor view*

### Install PlatformIO 

See [PlatformIO website](http://docs.platformio.org/en/stable/installation.html) for Windows install guide.

#### Install required platformIO packages

`$ pio platform install atmelavr --with-package tool-avrdude`



## Licence

This software is available under the GNU GPL V3 license
