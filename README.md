# emonUpload

Download, flash and manage OpenEnergyMonitor firmware

***

# In Development

***

# Install

`$ git clone https://github.com/openenergymonitor/emonupload`

- requires pythin 2.7.9+
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

For more info on pyenv: https://github.com/yyuu/pyenv


## Install modules

`$ cd emonupload`
`$ pip install -r requirements.txt`


 

## Licence

This software is available under the GNU GPL V3 license
