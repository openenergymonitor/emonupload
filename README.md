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

sudo apt-get install git python-pip make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev
sudo pip install virtualenvwrapper

git clone https://github.com/yyuu/pyenv.git ~/.pyenv
git clone https://github.com/yyuu/pyenv-virtualenvwrapper.git ~/.pyenv/plugins/pyenv-virtualenvwrapper

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'pyenv virtualenvwrapper' >> ~/.bashrc

```
$ sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils
$ sudo pip install virtualenvwrapper
$ curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'pyenv virtualenvwrapper' >> ~/.bashrc

$ ~/.pyenv/bin/pyenv install 2.7.9
$ cd emonupload
$ python --version
Python 2.7.9
```

After shell has been reloaded `pyenv` can just be called directly without it's full path `~/.pyenv/bin/pyenv` do to the lines addded to bashrc.

Local python version 2.79 will be used for `emonupload` this is defined by `.python-version` in root project folder

For more info on pyenv python virtual enviroment: https://github.com/yyuu/pyenv


## Install Python Modules

```
$ cd emonupload
$ pip install -r requirements.txt
```

## Install Dependencys

`$ sudo apt get install avrdude`

## Install PlatformIO

*Required for unit testing and serial montor view*

`$ sudo python -c "$(curl -fsSL https://raw.githubusercontent.com/platformio/platformio/master/scripts/get-platformio.py)"`


## Run at startup

To run at startup add to `/etc/rc.local`

```
cd /home/pi/emonpi
su pi -c '.emonupload.py
```

## Licence

This software is available under the GNU GPL V3 license
