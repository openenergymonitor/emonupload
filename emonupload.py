#!/usr/bin/env python

# https://developer.github.com/v3/repos/releases/
# GET /repos/:owner/:repo/releases

# requires python 2.7.9 +
# use python virtual env in needed https://github.com/yyuu/pyenv

# By Glyn Hudson
# Part of OpenEnergyMonitor.org project
# GNU GPL V3

# Startup
# - Check for network connectivity
# - Update emonUpload
# - Update releaes

# Flash Bootloder
# - Arduino Uno bootloder via platformIO AVRdude


# Flash bootloader
# Upload firmware via serial
# Download latest firmware from GitHub releases

# Upload firmware
# - Find available boards, releases and latest release
# - Select board
# - Select version or latest

# Test unit

from download_releases import debug, get_repos, update_download_releases
import time, urllib

## Uncomment to enable debug
# debug()

#--------------------------------------------------------------------------------------------------
VERSION = 'V0.0.2'
download_folder = 'firmware/'
allowed_extensions = ['bin', 'hex']
repo_config_file = 'repos.conf'
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Check interent connectivity
#--------------------------------------------------------------------------------------------------
def interent_connected():
  global e
  try:
      stri = "https://github.com"
      data = urllib.urlopen(stri)
      if (DEBUG): print "Internet connected"
      return True
  except e:
      if (DEBUG): print "No Interent connection: " ,e
      return False
#--------------------------------------------------------------------------------------------------

# Terminal colours
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
#--------------------------------------------------------------------------------------------------


# STARTUP
now = time.strftime("%c")
print bcolors.HEADER + bcolors.UNDERLINE + '\nemonUpload: ' + VERSION + bcolors.ENDC
print 'Today: ' + time.strftime("%c") + '\n'
print '\n-------------------------------------------------------------------------------'

print interent_connected()
quit()

# get repo release info from GitHub for the repos listed in repo config file
repo = get_repos(repo_config_file)
number_repos = len(repo)

# update / download releaes for each repo and save to download folder
update_download_releases(repo, number_repos, download_folder)


print '\n-------------------------------------------------------------------------------'
print bcolors.WARNING + '\nDONE.\n' + bcolors.ENDC

