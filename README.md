# emonUpload

Download, flash and manage OpenEnergyMonitor firmware

*Designed primarily for internal & factory use*

***

# In Development

***

# Install

`$ git clone https://github.com/openenergymonitor/emonupload`

- requires Python 2.7.9+
- use python virtual env in needed (see below)

## Setup Python virtual env

Only needed if your system only has support for python =< 2.6 e.g. Ubuntu 14.04 :-(

```
$ sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \ libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils
$ curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
`$ ~/.pyenv/bin/pyenv install 2.7.9`
$ cd emonupload
$ python --version
Python 2.7.9
```
Local python version 2.79 will be used for `emonupload` this is defined by `.python-version` in root project folder

For more info on pyenv python virtual enviroment: https://github.com/yyuu/pyenv


## Install Python Modules

```
$ cd emonupload
$ pip install -r requirements.txt
```

## Install Dependencys

`$ sudo apt get install avrdude python-apt`

## Install PlatformIO

*Required for unit testing*

`$ sudo python -c "$(curl -fsSL https://raw.githubusercontent.com/platformio/platformio/master/scripts/get-platformio.py)"`


## Run at startup

To run at startup add to `/etc/rc.local`

```
cd /home/pi/emonpi
su pi -c '.emonupload.py
```

## Licence

This software is available under the GNU GPL V3 license
