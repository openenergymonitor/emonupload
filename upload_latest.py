#!/usr/bin/env python

# Script for RaspberryPi with RFM12Pi / RFM69Pi
# Automated upload and test
# Upload code to emonTx via ISP and check for RF data received

# By Glyn Hudson
# Part of the openenergymonitor.org project
# GNU GPL V3

# $ pip install -r requirements.txt
import serial, sys, string, commands, time, subprocess, os, urllib2, requests, urllib, json, git, apt
from subprocess import Popen, PIPE, STDOUT
from os.path import expanduser

download_folder = 'firmware'

#--------------------------------------------------------------------------------------------------
DEBUG = 0
UPDATE = 0      # Update firmware releases at startup
VERSION = 'V0.0.2'

download_folder = 'latest/'
repo_folder = 'repos/'
avrdude_config = '~/.platformio/packages/tool-avrdude/avrdude.conf'
uno_bootloader = 'bootloaders/optiboot_atmega328.hex'

allowed_extensions = ['bin', 'hex']
github_repo = ['openenergymonitor/emonth2', 'openenergymonitor/emonth', 'openenergymonitor/emonpi', 'openenergymonitor/emontxfirmware', 'openenergymonitor/rfm2pi']
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# RFM settings
#--------------------------------------------------------------------------------------------------
rfm_port = '/dev/ttyAMA0'
rfm_baud = '38400'
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Expected RF nodeID's
#--------------------------------------------------------------------------------------------------
emontx_nodeid = [8, 7]
emonth_nodeid = [23, 24, 25, 26]
emonpi_nodeid = [5]
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
    print bcolors.WARNING + 'UPDATE FOUND....emonUpload RESTART REQUIRED\n' + bcolors.ENDC
    if (DEBUG): raw_input("\nPress Enter to continue...\n")
    os.execv(filename, sys.argv)
    sys.exit(0)
  else:
    print bcolors.OKGREEN + 'Already up-to-date: emonUpload' + bcolors.ENDC
    if (DEBUG): raw_input("\nPress Enter to continue...\n")
  return r
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Check Linux package is installed$ pip install -r requirements.txt
#--------------------------------------------------------------------------------------------------
def check_package(package_name):
  cache = apt.Cache()
  if cache[package_name].is_installed:
    print bcolors.OKGREEN + package_name + " is installed" + bcolors.ENDC
  else:
    print bcolors.FAIL + 'FATAL ERROR: ' + package_name + " is NOT installed" + bcolors.ENDC
    quit()
    
#--------------------------------------------------------------------------------------------------
# Clone / update github repos into repo folder
#--------------------------------------------------------------------------------------------------
def repo_clone_update(github_repo, repo_folder):
  if not os.path.isdir(repo_folder):
    os.mkdir(repo_folder)
  for i in range(len(github_repo)):
    repo_dir_path=repo_folder + github_repo[i].split('/')[-2] + '-' + github_repo[i].split('/')[-1]  # e.g repos/openenergymonitor-emonth2
    if os.path.isdir(repo_dir_path):
      if (DEBUG): print '\nDEBUG: Repo ' + repo_dir_path + ' already exists checking for updates...'
      repo_dir_abs_path=os.path.dirname(repo_dir_path)
      g = git.cmd.Git(repo_dir_abs_path)
      r = g.pull()
      if r != 'Already up-to-date.': print bcolors.WARNING + 'Updating repo: ' + repo_dir_path + bcolors.ENDC
      else: print bcolors.OKGREEN + 'Already up-to-date: ' + repo_dir_path + bcolors.ENDC
    else:
      remote_url = 'https://github.com/' + github_repo[i] + '.git'
      if (DEBUG): print '\nDEBUG: Cloning ' + github_repo[i] + '\nFrom: ' + remote_url + '\nInto: ' + repo_dir_path
      os.mkdir(repo_dir_path)
      repo = git.Repo.init(repo_dir_path)
      origin = repo.create_remote('origin',remote_url)
      origin.fetch()
      origin.pull(origin.refs[0].remote_head)
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
# Burn Bootloader
#--------------------------------------------------------------------------------------------------
def burn_bootloader(bootloader_path):
  if os.path.isfile(expanduser((avrdude_config))):
    print bcolors.OKGREEN + '\nBurning Bootloader\n' + bcolors.ENDC
    cmd = 'avrdude -V -C ' + avrdude_config + ' -p atmega328p -c stk500v2 -P usb -U flash:w:' + bootloader_path +':i -Ulock:w:0xcf:m'
    print cmd
    subprocess.call(cmd, shell=True)
  else:
    print bcolors.FAIL + 'ERROR: Missing PlatformIO avrdude.conf, check PlatformIO is installed' + bcolors.ENDC
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
  ser = serial.Serial(rfm_port, rfm_baud, timeout=1)
  linestr = ser.readline()
  print linestr
  if (DEBUG): print len(linestr)
  if len(linestr)>0:
    if int(linestr[3] + linestr[4]) == nodeid:
      print bcolors.OKGREEN +'PASS!...RF RECEIVED' + bcolors.ENDC
    else:
      print bcolors.FAIL + 'FAIL...Incorrect RF received' + bcolors.ENDC
  else:
    print bcolors.FAIL + 'FAIL...RF NOT received' + bcolors.ENDC
  ser.close()
  

#--------------------------------------------------------------------------------------------------
# BEGIN
#--------------------------------------------------------------------------------------------------
os.system('clear') # clear terminal screen Linux specific

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
        download_url = assets[0]['browser_download_url']
        extension = download_url.split('.')[-1]
        if (DEBUG): print download_url
        if extension in allowed_extensions and UPDATE==True:
          file_download(download_url, current_repo, download_folder)
  else: print 'Startup update disabled'

# Check required packages are installed
check_package('avrdude')
if os.path.isdir(expanduser('~/.platformio')):
  print bcolors.OKGREEN + 'PlatformIO is installed' + bcolors.ENDC
else:
  print bcolors.FAIL + 'Error PlatformIO is NOT installed' + bcolors.ENDC

# Check communication with RFM69Pi
try:
  ser = serial.Serial(rfm_port, rfm_baud, timeout=10)
  ser.write("210g")
  time.sleep(1)
  ser.write("4b")
  ser.close()
  RFM = True

except serial.serialutil.SerialException:
  print bcolors.WARNING + '\nError: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST' + bcolors.ENDC
  RFM = False


print '\n-------------------------------------------------------------------------------'
print bcolors.OKBLUE + 'OpenEnergyMonitor Upload ' + VERSION + bcolors.ENDC

while(1):
	print ' '
	print '\nEnter >'
	print bcolors.OKGREEN + '(x) for emonTx' + bcolors.ENDC
	print bcolors.OKGREEN + '(h) for emonTH' + bcolors.ENDC
	print bcolors.OKGREEN + '(i) for emonPi' + bcolors.ENDC
	print bcolors.OKGREEN + '(r) for RFM69Pi' + bcolors.ENDC
	print bcolors.OKGREEN + '(2) for emonTH V2' + bcolors.ENDC
	print bcolors.OKGREEN + '(e) to EXIT and shutdown' + bcolors.ENDC
	nb = raw_input('> ')
        print(nb)

	if nb=='x':
		print '\nemonTx firmware upload via Serial....'
		burn_bootloader(uno_bootloader)
		serial_upload(download_folder + 'openenergymonitor-emontxfirmware.hex:i')
		
		# If RFM69Pi Exist
		if (RFM):
		  test_receive_rf(emontx_nodeid, rfm_port)


	if nb=='h':
		print 'emonTH firmware upload via ISP....'
		cmd = 'sudo avrdude -V -u -p atmega328p -c avrispmkII -P usb -e -Ulock:w:0x3F:m -Uefuse:w:0x05:m -Uhfuse:w:0xDE:m -Ulfuse:w:0xFF:m -U flash:w:' + download_folder + '/openenergymonitor-emonth.hex:i'
		subprocess.call(cmd, shell=True)
                time.sleep(1)
		if (RFM):
		  ser = serial.Serial('/dev/ttyAMA0', 38400, timeout=1)
  		linestr = ser.readline()
  		print linestr
  		if (len(linestr)>0):
  			if ((int(linestr[3] + linestr[4])==19) | (int(linestr[3] + linestr[4])==23)):
  				print bcolors.OKGREEN +'PASS!...RF RECEIVED' + bcolors.ENDC
  			else:
  				print bcolors.UNDERLINE + 'FAIL...Incorrect RF received' + bcolors.ENDC
  		else:
  			print bcolors.UNDERLINE + 'FAIL...RF NOT received' + bcolors.ENDC
  		ser.close()


	if nb=='i':
		print 'emonPi firmware upload via ISP....'
		cmd = 'sudo avrdude -V -u -p atmega328p -c avrispmkII -P usb -e -Ulock:w:0x3F:m -Uefuse:w:0x05:m -Uhfuse:w:0xDE:m -Ulfuse:w:0xFF:m -U flash:w:' + download_folder + '/openenergymonitor-emonpi.hex:i'
		subprocess.call(cmd, shell=True)
                time.sleep(1)
		if (RFM):
		  ser = serial.Serial('/dev/ttyAMA0', 38400, timeout=1)
  		linestr = ser.readline()
  		print linestr
  		if (len(linestr)>0):
  			if (int(linestr[2] + linestr[3])==5):
  				print bcolors.OKGREEN +'PASS!...RF RECEIVED' + bcolors.ENDC
  			else:
  				print bcolors.UNDERLINE + 'FAIL...Incorrect RF received' + bcolors.ENDC
  		else:
  			print bcolors.UNDERLINE + 'FAIL...RF NOT received' + bcolors.ENDC
  		ser.close()

	if nb=='2':
		print 'emonTH V2 upload via ISP'
		cmd = 'sudo avrdude -V -u -p atmega328p -c avrispmkII -P usb -e -Ulock:w:0x3F:m -Uefuse:w:0x05:m -Uhfuse:w:0xDE:m -Ulfuse:w:0xFF:m -U flash:w:' + download_folder + '/openenergymonitor-emonth2.hex:i'

		subprocess.call(cmd, shell=True)
                time.sleep(1)
		if (RFM):
		  ser = serial.Serial('/dev/ttyAMA0', 38400, timeout=1)
  		linestr = ser.readline()
  		print linestr
  		if (len(linestr)>0):
  			if (int(linestr[2] + linestr[3])==23):
  				print bcolors.OKGREEN +'PASS!...RF RECEIVED' + bcolors.ENDC
  			else:
  				print bcolors.UNDERLINE + 'FAIL...Incorrect RF received' + bcolors.ENDC
  		else:
  			print bcolors.UNDERLINE + 'FAIL...RF NOT received' + bcolors.ENDC
  		ser.close()

	if nb=='e':
		print 'END'
		print 'Raspberry Pi Shutdown NOW!....'
		time.sleep(2)
		cmd = 'sudo halt'
		subprocess.call(cmd, shell=True)
        	sys.exit







	#if ((nb!=8) and (nb!=4)):
	#	print 'Invalid selection, please restart script and select b or w'
