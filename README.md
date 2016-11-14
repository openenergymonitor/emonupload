# emonUpload

Download latest OpenEnergyMonitor firmware via GitHub releases; upload and test. 

# Features

- Auto downloads latest firmware via GitHub Releases
- Upload attemps to upload bootloader via ISP (AVR MkII programmer) then uploads latest firmware sketch via serial UART
- Auto detection of [USB to UART programmer](https://shop.openenergymonitor.com/programmer-usb-to-serial-uart/) serial port
- Serial output display upon upload
- Dedicated serial monitor (auto baudrate) 
- If RFM69Pi / emonPi receiver is detected RF test will be performed (check RF received)
- [Unit testing via PlatformIO](http://docs.platformio.org/en/stable/plus/unit-testing.html)
- Expandable to include any other git repositories


Configured by default to work with:

* emonTx 
* emonTH V1
* emonTH V2
* emonTx V3

***

# Install

- requires Python 2.7.9+ 
  -*use python virtual env if this version is not avaialble via your systems package maange*

```
$ git clone https://github.com/openenergymonitor/emonupload
$ sudo apt-get update
$ sudo apt-get install python avrdude git-core -y
$ cd emonupload
$ pip install -r requirements.txt
```
- Tested with pip 8.1.2

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
OpenEnergyMonitor Upload V1.2.2


Enter >

(x) for emonTx

(i) for emonPi

(h) for emonTH V2
(t) for emonTH V2 sensor test


(o) for old emonTH V1
(s) to view Serial
(u) to check for updates
(d) to enable DEBUG
(e) to EXIT
```


### Setup Python virtual env

*Only needed if your system only has support for python =< 2.6 e.g. Ubuntu 14.04 :-(*

```
sudo apt-get update
sudo apt-get install git python-pip make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev -y
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

After shell has been reloaded `pyenv` can just be called directly without it's full path `~/.pyenv/bin/pyenv` do to the lines addded to bashrc.

Local python version 2.79 will be used for `emonupload` this is defined by `.python-version` in root project folder

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
