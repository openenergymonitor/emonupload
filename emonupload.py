#!/usr/bin/env python

# Script for RaspberryPi with RFM12Pi / RFM69Pi
# Automated upload and test
# Upload code to emonTx via ISP and check for RF data received

# By Glyn Hudson
# Part of the openenergymonitor.org project
# GNU GPL V3

# $ pip install -r requirements.txt
import serial, sys, string, commands, time, subprocess, os, urllib2, requests, urllib, json, git
from subprocess import Popen, PIPE, STDOUT
from os.path import expanduser

#--------------------------------------------------------------------------------------------------
DEBUG       = 0
UPDATE      = 1      # Update firmware releases at startup
VERSION = 'V1.6.0'

download_folder = 'latest/'
repo_folder = 'repos/'
uno_bootloader = 'bootloaders/optiboot_atmega328.hex'

allowed_extensions = ['bin', 'hex']
github_repo = ['openenergymonitor/emonth2', 'openenergymonitor/emonth', 'openenergymonitor/emonpi', 'openenergymonitor/emontx3', 'openenergymonitor/emontx-3phase', 'openenergymonitor/emonesp', 'boblemaire/IoTaWatt', 'OpenEVSE/ESP8266_WiFi_v2.x' ]
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# RFM settings
#--------------------------------------------------------------------------------------------------
rfm_group = '210g'
rfm_freq =  '4b'
rfm_port =  '/dev/ttyAMA0'
rfm_baud =  '38400'
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Expected RF nodeID's
#--------------------------------------------------------------------------------------------------
emontx_nodeid      = [8, 7]
emontx_baud        = 115200

emontx_3phase_nodeid  = [11]
emontx_3phase_baud    = 115200

emonth_nodeid      = [23, 24, 25, 26]
emonth_baud        = 115200

emonpi_nodeid      = [5]
emonpi_baud        = 38400

emonesp_baud       = 115200
iotawatt_baud      = 115200
openevse_baud      = 115200
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

# Check download folder exists if not create
if not os.path.isdir(download_folder):
  os.mkdir(download_folder)

#--------------------------------------------------------------------------------------------------
# Check interent connectivity
#--------------------------------------------------------------------------------------------------
def interent_connected(url):
  print 'Testing internet connection...'
  connected = False
  req = urllib2.Request(url)
  try:
    resp = urllib2.urlopen(req)
  except urllib2.HTTPError as e:
    if e.code == 404:
      print bcolors.WARNING + 'No internet connection detected..update aborted\n' + bcolors.ENDC
  except urllib2.URLError as e:
    # Not an HTTP-specific error (e.g. connection refused)
    print bcolors.WARNING + 'No internet connection detected..update aborted\n' + bcolors.ENDC
  else:
    # 200
    body = resp.read()
    print bcolors.OKGREEN + 'Internet connection detected' + bcolors.ENDC
    connected = True
  return connected
#-------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Update emonupload
#--------------------------------------------------------------------------------------------------
def update_emonupload(filename):
  if (DEBUG): print 'Checking for emonUpload updates...'
  dir_path=os.path.dirname(os.path.realpath(filename))
  if (DEBUG): print 'git abs path' + dir_path
  g = git.cmd.Git(dir_path)
  r = g.pull()
  if (DEBUG): print g
  if r != 'Already up-to-date.':
    print r
    print bcolors.WARNING + 'UPDATE FOUND....emonUpload restart required\nEXITING...' + bcolors.ENDC
    os.system("rm -rf " + download_folder)
    os.system("rm -rf " + repo_folder)
    if (DEBUG): raw_input("\nPress Enter to continue...\n")
    quit()
  else:
    print bcolors.OKGREEN + 'Already up-to-date: emonUpload' + bcolors.ENDC
    if (DEBUG): raw_input("\nPress Enter to continue...\n")
  return r
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Check Linux package is installed$ pip install -r requirements.txt -
# not used requires python-apt
#--------------------------------------------------------------------------------------------------
# def check_package(package_name):
#   cache = apt.Cache()
#   if cache[package_name].is_installed:
#     print bcolors.OKGREEN + package_name + " is installed" + bcolors.ENDC
#   else:
#     print bcolors.FAIL + 'FATAL ERROR: ' + package_name + " is NOT installed" + bcolors.ENDC
#     quit()

#--------------------------------------------------------------------------------------------------
# Clone / update github repos into repo folder
#--------------------------------------------------------------------------------------------------
def repo_clone_update(github_repo, repo_folder):
  for i in range(len(github_repo)):
    remote_url = 'https://github.com/' + github_repo[i] + '.git'
    repo_dir_path=repo_folder + github_repo[i].split('/')[-2] + '-' + github_repo[i].split('/')[-1]  # e.g repos/openenergymonitor-emonth2
    if os.path.isdir(repo_dir_path):
      if (DEBUG): print '\nDEBUG: Repo ' + repo_dir_path + ' already exists checking for updates...'
      if os.path.isfile(repo_dir_path + '/README.md'):
        repo_dir_abs_path=os.path.dirname(os.path.realpath(repo_dir_path + '/README.md'))
        if (DEBUG): print repo_dir_abs_path
      if os.path.isfile(repo_dir_path + '/Readme.md'):
        repo_dir_abs_path=os.path.dirname(os.path.realpath(repo_dir_path + '/Readme.md'))
        if (DEBUG): print repo_dir_abs_path
      if os.path.isfile(repo_dir_path + '/readme.md'):
        repo_dir_abs_path=os.path.dirname(os.path.realpath(repo_dir_path + '/readme.md'))
        if (DEBUG): print repo_dir_abs_path

      # git pull origin master
      repo = git.Repo(repo_dir_abs_path)
      repo.git.checkout('master')
      r = repo.git.pull(remote_url)
      if r != 'Already up-to-date.':
        print bcolors.WARNING + 'Updating repo: ' + repo_dir_path + bcolors.ENDC
        print r
      else: print bcolors.OKGREEN + r + ' ' + repo_dir_path + bcolors.ENDC
    # If local repo does not exist then clone it
    else:
      print bcolors.OKGREEN + ' Cloning ' + remote_url + bcolors.ENDC
      if (DEBUG): print '\nDEBUG: Cloning ' + github_repo[i] + '\nFrom: ' + remote_url + '\nInto: ' + repo_dir_path
      cmd = 'git clone ' + remote_url + ' ' + repo_dir_path
      subprocess.call(cmd, shell=True)
  if (DEBUG): raw_input("\nPress Enter to continue...\n")
  return




#--------------------------------------------------------------------------------------------------
# Get latest GitHub release info using GitHub releases API
#--------------------------------------------------------------------------------------------------
def get_releases_info(current_repo):
  release_api_url = 'https://api.github.com/repos/' + current_repo + '/releases/latest'
  if (DEBUG): print 'DEBUG: API URL: ' + release_api_url + '\n'
  try:
    r = requests.get(release_api_url)
  except requests.exceptions.RequestException as e:
    print bcolors.FAIL + '\nERROR contacting GitHub API ' + release_api_url + '\n' + bcolors.ENDC
    sys.exit(1)
  resp = r.json()
  if 'tag_name' in resp:
    release_version = resp['tag_name']
  else : release_version = 'N/A'
  print bcolors.OKGREEN + 'Latest ' + current_repo + 'firmware: V' + release_version + bcolors.ENDC
  if (DEBUG): print '\n' + json.dumps(resp, sort_keys=True, indent=4, separators=(',', ': ')) + '\n'
  return resp
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# DOWNLOAD FILE
#--------------------------------------------------------------------------------------------------
def file_download(download_url, current_repo, download_folder):
  save_file_name = download_folder + current_repo.split('/')[-2] + '-' + current_repo.split('/')[-1] + '.' + download_url.split('.')[-1]
  # Check download folder exists if not create
  if not os.path.isdir(download_folder):
    os.mkdir(download_folder)
  u = urllib.urlopen(download_url)
  f = open(save_file_name, 'wb')
  meta = u.info()
  file_size = int(meta.getheaders('Content-Length')[0])
  print '  Downloading: %s Bytes: %s' % (download_url.split('/')[-1], file_size)
  if (DEBUG): print 'DEBUG:  from ' + download_url
  if (DEBUG): print 'DEBUG:  Saving to: ' + save_file_name
  file_size_dl = 0
  block_sz = 8192
  while True:
      buffer = u.read(block_sz)
      if not buffer:
          break
      file_size_dl += len(buffer)
      f.write(buffer)
      status = r'%10d  [%3.2f%%]' % (file_size_dl, file_size_dl * 100. / file_size)
      status = status + chr(8)*(len(status)+1)
      print status,
  f.close()
  print '\n'
  return;
  #--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# RFM
# Check communication with RFM69Pi and set settings
#--------------------------------------------------------------------------------------------------
def rfm(rfm_port, rfm_baud, rfm_group, rfm_freq):
  RFM = False
  try:
    ser = serial.Serial(rfm_port, rfm_baud, timeout=2)
    time.sleep(0.2)
    ser.write('0g') #keep RF awake by changing it's group
    time.sleep(0.5)
    ser.write(rfm_group)
    time.sleep(0.5)
    ser.write(rfm_freq)
    time.sleep(0.5)
    ser.write("1q") #quite mode
    time.sleep(0.5)
    ser.close()
    RFM = True
    print bcolors.OKBLUE + '\nRFM69Pi detected' + bcolors.ENDC
  except serial.serialutil.SerialException:
    print bcolors.WARNING + '\nError: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST' + bcolors.ENDC
    RFM = False
  return RFM

#--------------------------------------------------------------------------------------------------
# Burn Bootloader
#--------------------------------------------------------------------------------------------------
def burn_bootloader(bootloader_path):
  print bcolors.OKGREEN + '\nBurning Bootloader\n' + bcolors.ENDC
  cmd = 'sudo avrdude -p atmega328p -c avrispmkII -P usb -e -U efuse:w:0x05:m -U hfuse:w:0xD6:m -U lfuse:w:0xFF:m -U flash:w:' + bootloader_path + ':i -Ulock:w:0x0f:m'
  print cmd
  subprocess.call(cmd, shell=True)
  return;
#--------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
# Serial Upload
#--------------------------------------------------------------------------------------------------
def serial_upload(firmware_path):
  print bcolors.OKGREEN + '\nSerial upload ' + firmware_path + '\n' + bcolors.ENDC

  # Autodetect ttyUSB port 0 - 12 ttyUSB[x]
  serial_port = False
  for i in range(12):
    try_port='/dev/ttyUSB' +str(i)
    try:
      ser = serial.Serial(port=try_port, timeout=1)
      ser.read()
      ser.close()
      print bcolors.OKGREEN + "Found serial programmer on " + try_port + bcolors.ENDC
      serial_port = try_port
      break
    except serial.serialutil.SerialException:
      if (DEBUG): print 'ERROR: USB serial programmer NOT found on ' + try_port + bcolors.ENDC

  if (serial_port!=False):
    cmd = 'avrdude  -uV -c arduino -p ATMEGA328P -P' + serial_port + ' -b 115200 -U flash:w:' + firmware_path
    print cmd
    subprocess.call(cmd, shell=True)
  else: print bcolors.FAIL + 'ERROR: USB serial programmer NOT found' + bcolors.ENDC

  return serial_port
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Test receive RF
#--------------------------------------------------------------------------------------------------
def test_receive_rf(nodeid, rfm_port, rfm_baud):
  print  bcolors.HEADER + 'Checking for received RF...' + bcolors.ENDC
  ser = serial.Serial(rfm_port, rfm_baud, timeout=5)
  # read x number of lines of serial from RFM
  rf_receive = False
  for l in range(3):
    linestr = ser.readline()
    if len(linestr) > 0: print linestr
    if linestr[:2] == 'OK':
      for i in range(len(nodeid)):
        if nodeid < 10: # if nodeID is single digits
          if int(linestr[4]) == nodeid[i]:
            rf_receive = True
            break
        else:
          if int(linestr[3:5]) == nodeid[i]:
            rf_receive = True
            break
      break
  ser.close()
  if (rf_receive): print bcolors.OKGREEN + bcolors.UNDERLINE +'PASS!...RF RECEIVED' + bcolors.ENDC
  else: print bcolors.FAIL + bcolors.UNDERLINE + 'FAIL...RF NOT received' + bcolors.ENDC
  return rf_receive;

#--------------------------------------------------------------------------------------------------
# View x number of serial output from unit (not used)
#--------------------------------------------------------------------------------------------------
def serial_output(serial_port, serial_baud, num_lines):
  os.system('clear') # clear terminal screen Linux specific
  ser = serial.Serial(serial_port, serial_baud, timeout=5)
  linestr = ''
  for i in range(num_lines):
    linestr = ser.readline()
    print linestr
  ser.close()
  return;
#--------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------
# Reset unit
#--------------------------------------------------------------------------------------------------
def reset(serial_port):
  print 'Reset ' + str(serial_port)
  if (serial_port!=False):
    cmd = 'avrdude  -uV -c arduino -p ATMEGA328P -P' + serial_port
    subprocess.call(cmd, shell=True)
  return
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# PlatformIO unit test
# --------------------------------------------------------------------------------------------------
def pio_unit_test(test_path, env):
  if os.path.isdir(expanduser('~/.platformio')) and os.path.isdir(test_path):
    if DEBUG: print bcolors.OKGREEN + 'PlatformIO is installed' + bcolors.ENDC
    print bcolors.OKGREEN + '\nUnit Test: \n' + bcolors.ENDC
    cmd = 'pio test -d' + test_path + ' -e' + env
    print cmd
    subprocess.call(cmd, shell=True)
    raw_input("\nDone. Press Enter to return to menu >\n")
    os.system('clear') # clear terminal screen Linux specific
    return True
  else:
    print bcolors.FAIL + 'Error PlatformIO NOT installed' + bcolors.ENDC
    print 'Or test path cannot be found: ' + test_path
    return False
# --------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------
# PlatformIO Serial Monitor
# --------------------------------------------------------------------------------------------------
def serial_monitor(baud):
  os.system('clear') # clear terminal screen Linux specific
  if os.path.isdir(expanduser('~/.platformio')):
    if DEBUG: print bcolors.OKGREEN + 'PlatformIO is installed' + bcolors.ENDC
    cmd = 'sudo pio device monitor -b' + str(baud)
    subprocess.call(cmd, shell=True)
    return True
  else:
    print bcolors.FAIL + 'Error PlatformIO avrdude is NOT installed' + bcolors.ENDC
    return False
# --------------------------------------------------------------------------------------------------

def serial_menu():
  while(1):
    print '\n-------------------------------------------------------------------------------'
    print bcolors.OKBLUE + 'View Serial Output: ' + bcolors.ENDC
    print '\nEnter >\n'
    print bcolors.OKGREEN + '\n(x) for emonTx V3 Serial @ ' + str(emontx_baud) + bcolors.ENDC
    print bcolors.OKGREEN + '\n(i) for emonPi Serial @ ' + str(emonpi_baud) + bcolors.ENDC
    print bcolors.OKGREEN + '\n(h) for emonTH V2 Serial @ ' + str(emonth_baud) + bcolors.ENDC
    print bcolors.OKGREEN + '\n(0) for older units serial @9600 ' + bcolors.ENDC
    print bcolors.OKBLUE + '\n\n(m) To Return to main menu > ' + bcolors.ENDC
    nb = raw_input('> ')

    if nb == 'x':
      serial_monitor(emontx_baud)
      break
    elif nb == 'i':
      serial_monitor(emonpi_baud)
      break
    elif nb == 'h':
      serial_monitor(emonth_baud)
      break
    elif nb == 'o':
      serial_monitor(9600)
      break
    elif nb == 'm':
      break
    else:
      print bcolors.FAIL + 'Invalid selection' + bcolors.ENDC
    return




#--------------------------------------------------------------------------------------------------
# BEGIN
#--------------------------------------------------------------------------------------------------
os.system('clear') # clear terminal screen Linux specific

# Setup RFM
RFM = rfm(rfm_port, rfm_baud, rfm_group, rfm_freq)

#--------------------------------------------------------------------------------------------------
# Update Firmware - download latest releases
#--------------------------------------------------------------------------------------------------
if interent_connected('https://api.github.com'):

  if (UPDATE):  # If startup update is requested

    # Update emonUpload (git pull)
    update_emonupload('upload_latest.py')
    # Clone or (update if already cloned) repos defined in github_repo list
    repo_clone_update(github_repo, repo_folder)
    print '\n'

    # Update firware releases for github releases
    for i in range(len(github_repo)):
      current_repo = github_repo[i]
      resp = get_releases_info(current_repo)
      if 'assets' in resp:
        assets = resp['assets']
        if len(assets) > 0:
          download_url = assets[0]['browser_download_url']
          extension = download_url.split('.')[-1]
          if (DEBUG): print download_url
          if extension in allowed_extensions and UPDATE==True:
            file_download(download_url, current_repo, download_folder)
        if len(assets) > 1:
            # If more than one release asset check to see if it's ESP spiffs filesyste, if so then download it with name
            if assets[1]['name'] == 'spiffs.bin':
                if (DEBUG): print "Downloading spiffs....."
                extension = download_url.split('.')[-1]
                download_url = assets[1]['browser_download_url']
                if (DEBUG): print download_url
                if (DEBUG): print current_repo
                if extension in allowed_extensions and UPDATE==True:
                  file_download(download_url, current_repo + '-spiffs', download_folder)

    time.sleep(5)

  else: print 'Startup update disabled'

# Check required packages are installed
# check_package('avrdude')


while(1):
  print '\n-------------------------------------------------------------------------------'
  os.system('clear') # clear terminal screen Linux specific
  print ' '
  print bcolors.OKBLUE + 'OpenEnergyMonitor Firmware Upload ' + VERSION + bcolors.ENDC
  print '\nEnter >\n'
  print bcolors.OKGREEN + '(x) for emonTx V3\n' + bcolors.ENDC
  print bcolors.OKGREEN + '(i) for emonPi\n' + bcolors.ENDC
  print bcolors.OKGREEN + '(h) for emonTH V2\n' + bcolors.ENDC

  print '\n'
  print bcolors.OKGREEN + '(3) for 3-phase emonTx' + bcolors.ENDC
  print bcolors.OKGREEN + '(e) for emonESP' + bcolors.ENDC
  print bcolors.OKGREEN + '(w) for IoTaWatt' + bcolors.ENDC
  print bcolors.OKGREEN + '(v) for OpenEVSE' + bcolors.ENDC

  print '\n'
  #print bcolors.OKGREEN + '(r) for RFM69Pi' + bcolors.ENDC
  print bcolors.OKBLUE + '(o) for old emonTH V1 upload' + bcolors.ENDC
  print bcolors.OKBLUE + '(t) for emonTH V2 sensor test' + bcolors.ENDC
  print bcolors.HEADER + '(s) to view Serial' + bcolors.ENDC
  print bcolors.HEADER + '(u) to check for updates' + bcolors.ENDC
  print bcolors.HEADER + '(d) to enable DEBUG' + bcolors.ENDC
  print bcolors.HEADER + '(e) to EXIT' + bcolors.ENDC
  nb = raw_input('> ')
  os.system('clear') # clear terminal screen Linux specific

  # emonTx
  if nb=='x':
    print bcolors.OKGREEN + '\nemonTx Upload\n' + bcolors.ENDC
    burn_bootloader(uno_bootloader)
    serial_port = serial_upload(download_folder + 'openenergymonitor-emontx3.hex:i')
    if (RFM):
      if test_receive_rf(emontx_nodeid, rfm_port, rfm_baud) == False:
        rfm(rfm_port, rfm_baud , rfm_group, rfm_freq) # 'poke RFM'
        reset(serial_port) # reset and try again if serial is not detected
        test_receive_rf(emontx_nodeid, rfm_port, rfm_baud)
    else: print bcolors.WARNING + '\nError: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST' + bcolors.ENDC

    if raw_input("\nDone emonTx upload. Press Enter to return to menu or (s) to view serial output>\n"):
      serial_monitor(emontx_baud)
    os.system('clear') # clear terminal screen Linux specific

  # emonTx 3-phase
  if nb=='3':
    print bcolors.OKGREEN + '\nemonTx 3-phase Upload\n' + bcolors.ENDC
    burn_bootloader(uno_bootloader)
    serial_port = serial_upload(download_folder + 'openenergymonitor-emontx-3phase.hex:i')
    if (RFM):
      if test_receive_rf(emontx_3phase_nodeid, rfm_port, rfm_baud) == False:
        rfm(rfm_port, rfm_baud , rfm_group, rfm_freq) # 'poke RFM'
        reset(serial_port) # reset and try again if serial is not detected
        test_receive_rf(emontx_3phase_nodeid, rfm_port, rfm_baud)
    else: print bcolors.WARNING + '\nError: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST' + bcolors.ENDC

    if raw_input("\nDone emonTx 3-phase upload. Press Enter to return to menu or (s) to view serial output>\n"):
      serial_monitor(emontx_3phase_baud)
    os.system('clear') # clear terminal screen Linux specific

  # emonPi
  elif nb=='i':
    print bcolors.OKGREEN + '\nemonPi Upload\n' + bcolors.ENDC
    burn_bootloader(uno_bootloader)
    serial_port = serial_upload(download_folder + 'openenergymonitor-emonpi.hex:i')
    if (RFM):
      if test_receive_rf(emonpi_nodeid, rfm_port, rfm_baud) == False:
        rfm(rfm_port, rfm_baud , rfm_group, rfm_freq) # 'poke RFM'
        reset(serial_port) # reset and try again if serial is not detected
        test_receive_rf(emonpi_nodeid, rfm_port, rfm_baud)
    else: print bcolors.WARNING + '\nError: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST' + bcolors.ENDC

    if raw_input("\nDone emonPi Upload. Press Enter to return to menu or (s) to view serial output>\n"):
      serial_monitor(emonpi_baud)
    os.system('clear') # clear terminal screen Linux specific


  # emonTH V2
  elif nb=='h':
    print bcolors.OKGREEN + '\nemonTH V2 Upload\n' + bcolors.ENDC
    burn_bootloader(uno_bootloader)
    serial_port = serial_upload(download_folder + 'openenergymonitor-emonth2.hex:i')
    if (RFM):
      if test_receive_rf(emonth_nodeid, rfm_port, rfm_baud) == False:
        rfm(rfm_port, rfm_baud , rfm_group, rfm_freq) # 'poke RFM'
        reset(serial_port) # reset and try again if serial is not detected
        test_receive_rf(emonth_nodeid, rfm_port, rfm_baud)
    else: print bcolors.WARNING + '\nError: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST' + bcolors.ENDC

    if raw_input("\nDone emonTH V2 upload. Press Enter to return to menu or (s) to view serial output>\n"):
      serial_monitor(emonth_baud)
    os.system('clear') # clear terminal screen Linux specific

  # emonESP
  elif nb=='e':
    print bcolors.OKGREEN + '\nemonESP Upload\n' + bcolors.ENDC
    cmd = 'pip freeze --disable-pip-version-check | grep esptool'
    if subprocess.call(cmd, shell=True) != ' ':
      # If esptool is installed
      cmd = 'esptool.py write_flash 0x000000 ' + download_folder + 'openenergymonitor-emonesp.bin' + ' 0x300000 ' +  download_folder + 'openenergymonitor-emonesp-spiffs.bin'
      print cmd
      subprocess.call(cmd, shell=True)
      if raw_input("\nDone emonESP upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
              serial_monitor(emonesp_baud)
    else:
      if raw_input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
        serial_monitor(emonesp_baud)
        
        
  # IoTaWatt
  elif nb=='w':
    print bcolors.OKGREEN + '\nIoTaWatt Upload\n' + bcolors.ENDC
    cmd = 'pip freeze --disable-pip-version-check | grep esptool'
    if subprocess.call(cmd, shell=True) != ' ':
      # If esptool is installed
      cmd = 'esptool.py write_flash 0x000000 ' + download_folder + 'boblemaire-IoTaWatt.bin'
      print cmd
      subprocess.call(cmd, shell=True)
      if raw_input("\nDone IoTaWatt upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
              serial_monitor(emonesp_baud)
    else:
      if raw_input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
        serial_monitor(emonesp_baud)
  
    # OpenEVSE
  elif nb=='v':
    print bcolors.OKGREEN + '\nOpenEVSE Upload\n' + bcolors.ENDC
    cmd = 'pip freeze --disable-pip-version-check | grep esptool'
    if subprocess.call(cmd, shell=True) != ' ':
      # If esptool is installed
      cmd = 'esptool.py write_flash 0x000000 ' + download_folder + 'OpenEVSE-ESP8266_WiFi_v2.x.bin'
      print cmd
      subprocess.call(cmd, shell=True)
      if raw_input("\nDone OpenEVSE upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
              serial_monitor(emonesp_baud)
    else:
      if raw_input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
        serial_monitor(emonesp_baud)
    os.system('clear') # clear terminal screen Linux specific

    # emonTH V1
  elif nb=='o':
    print bcolors.OKGREEN + '\nemonTH V1 Upload\n' + bcolors.ENDC
    burn_bootloader(uno_bootloader)
    serial_port = serial_upload(download_folder + 'openenergymonitor-emonth.hex:i')
    if (RFM):
      if test_receive_rf(emonth_nodeid, rfm_port, rfm_baud) == False:
        rfm(rfm_port, rfm_baud , rfm_group, rfm_freq) # 'poke RFM'
        reset(serial_port) # reset and try again if serial is not detected
        test_receive_rf(emonth_nodeid, rfm_port, rfm_baud)
    else: print bcolors.WARNING + '\nError: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST' + bcolors.ENDC

    if raw_input("\nDone emonTH V1 upload. Press Enter to return to menu or (s) to view serial output>\n"):
      serial_monitor(9600)
    os.system('clear') # clear terminal screen Linux specific




  # emonTH V2 Unit Sensor test
  elif nb=='t':
    pio_unit_test(repo_folder + 'openenergymonitor-emonth2/firmware', 'emonth2')
    raw_input("\nDone. Press Enter to return to menu >\n")
    os.system('clear') # clear terminal screen Linux specific

  elif nb=='u':
    print bcolors.OKGREEN + 'Checking for updates.. ' + bcolors.ENDC
    # Update emonUpload (git pull)
    update_emonupload('emonupload.py')
    # Clone or (update if already cloned) repos defined in github_repo list
    repo_clone_update(github_repo, repo_folder)
    print '\n'
    # Update firware releases for github releases
    for i in range(len(github_repo)):
      current_repo = github_repo[i]
      resp = get_releases_info(current_repo)
      if 'assets' in resp:
        assets = resp['assets']
        download_url = assets[0]['browser_download_url']
        extension = download_url.split('.')[-1]
        if (DEBUG): print download_url
        if extension in allowed_extensions and UPDATE==True:
          file_download(download_url, current_repo, download_folder)

  elif nb=='d':
    print bcolors.OKGREEN + '\nDebug enabled' + bcolors.ENDC
    DEBUG = True
    raw_input("\nPress Enter to continue... or [CTRL + C] to exit\n")

  elif nb=='e':
    shutdown_choice = raw_input("\nShutdown system after exit? Enter (y) or (n)\n")
    if shutdown_choice == 'y':
      print bcolors.FAIL + '\nSystem Shutdown....in 10s. [CTRL + C] to cancel' + bcolors.ENDC
      time.sleep(10)
      cmd = 'sudo halt'
      subprocess.call(cmd, shell=True)
      sys.exit
    if shutdown_choice == 'n':
      quit()

  # Serial Optons
  elif nb=='s':
    serial_menu()

  # else:
    # print bcolors.FAIL + 'Invalid selection' + bcolors.ENDC


  # If RFM69Pi is present 'poke' it by re-settings its settings to keep t alive :-/
  if (RFM): rfm(rfm_port, rfm_baud , rfm_group, rfm_freq)
