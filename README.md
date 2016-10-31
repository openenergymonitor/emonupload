# emonUpload

Download, flash and manage OpenEnergyMonitor firmware

# Features

- Auto downloads latest firmware via GitHub Releases
- Upload attemps to upload bootloder via ISP (AVR MkII programmer) then uploads firmware via serial UART
- Auto detection of programmer serial port
- Serial output display upon upload (option)
- Dedicated serial monitor
- If emonPi / RFM69Pi is detected RF test will be performed (check RF received)
- Unit testing via PlatfromIO
- Expandable to include any other git repositories

***

# Install

- requires Python 2.7.9+ (use python virtual env in needed (see below)
 
```
$ git clone https://github.com/openenergymonitor/emonupload
$ sudo apt get install python avrdude git-core -y
$ cd emonupload
$ sudo pip install -r requirements.txt
```

# Run

`./emonupload.py`

*`emon` can be installed in `/user/bin` to enable launching via `emon` command*


### Setup Python virtual env

*Only needed if your system only has support for python =< 2.6 e.g. Ubuntu 14.04 :-(*

```
sudo apt-get install git python-pip make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev
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

*Not essentail for upload: Required for unit testing and serial montor view*

`$ sudo python -c "$(curl -fsSL https://raw.githubusercontent.com/platformio/platformio/master/scripts/get-platformio.py)"`




## Licence

This software is available under the GNU GPL V3 license
