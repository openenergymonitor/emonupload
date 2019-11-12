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


Configured by default to work with:

* emonTx
* emonTH V1
* emonTH V2
* emonTx V3
* emonESP
* OpenEVSE
* EmonEVSE
* WiFi Relay

***

# Install

- requires Python 2.7.9+
  -*use python virtual env if this version is not available via your system package manager*

```
$ git clone https://github.com/openenergymonitor/emonupload
$ sudo apt-get update
$ sudo apt-get install python python-pip avrdude git-core picocom -y
$ cd emonupload
$ pip install -r requirements.txt
```
- Tested with pip 8.1.2, picocom V3.2

Note: picocom may need to be compiled to obtain V3.x https://github.com/npat-efault/picocom

# Run

`./emonupload.py`

*`emon` can be installed in `/user/bin` to enable launching via `emon` command*

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


### Setup Python virtual env

*Only needed if your system only has support for python =< 2.6 e.g. Ubuntu 14.04 :-(*

```
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev
sudo pip install virtualenvwrapper

git clone https://github.com/yyuu/pyenv.git ~/.pyenv
git clone https://github.com/yyuu/pyenv-virtualenvwrapper.git ~/.pyenv/plugins/pyenv-virtualenvwrapper

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'pyenv virtualenvwrapper' >> ~/.bashrc
```

```
$ ~/.pyenv/bin/pyenv install 2.7.9
$ cd emonupload
$ python --version
Python 2.7.9
```

After shell has been reloaded `pyenv` can just be called directly without it's full path `~/.pyenv/bin/pyenv` do to the lines added to bashrc.

Local python version 2.7.9 will be used for `emonupload`. This is defined by `.python-version` in the root project folder.

For more info on pyenv python virtual enviroment: https://github.com/yyuu/pyenv



## Install PlatformIO

*Not essential for upload: Required for unit testing and serial monitor view*

### Install PlatformIO using Linux / Mac install script:

`$ sudo python -c "$(curl -fsSL https://raw.githubusercontent.com/platformio/platformio/master/scripts/get-platformio.py)"`

See [PlatformIO website](http://docs.platformio.org/en/stable/installation.html) for Windows install guide.

#### Install required platformIO packages

`$ pio platform install atmelavr --with-package tool-avrdude`



## Licence

This software is available under the GNU GPL V3 license
