#!/usr/bin/env python

# Script for RaspberryPi with RFM12Pi / RFM69Pi
# Automated upload and test
# Upload code to emonTx via ISP and check for RF data received

# By Glyn Hudson
# Part of the openenergymonitor.org project
# GNU GPL V3

# $ pip install -r requirements.txt
import serial, sys, string, commands, time, subprocess, os, urllib2, requests, urllib, json
from subprocess import Popen, PIPE, STDOUT
from os.path import expanduser

#--------------------------------------------------------------------------------------------------
DEBUG             = 0
UPDATE            = 1            # Update firmware releases at startup
VERSION = 'V2.2.2'

download_folder = 'latest/'
repo_folder = 'repos/'
uno_bootloader = 'bootloaders/optiboot_atmega328.hex'

allowed_extensions = ['bin', 'hex']
github_repo = ['openenergymonitor/emonth2', 'openenergymonitor/emonpi', 'openenergymonitor/emontx3', 'openenergymonitor/emontx-3phase', 'openenergymonitor/emonesp', 'OpenEVSE/ESP8266_WiFi_v2.x', 'openenergymonitor/mqtt-wifi-mqtt-single-channel-relay', 'openenergymonitor/open_evse', 'openenergymonitor/EmonTxV3CM', 'OpenEVSE/ESP32_WiFi_V3.x'  ]
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# RFM settings
#--------------------------------------------------------------------------------------------------
RFM = False
rfm_group = '210g'
rfm_freq =    '4b'
rfm_port =    '/dev/ttyAMA0'
rfm_baud =    '38400'
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Expected RF nodeID's
#--------------------------------------------------------------------------------------------------
emontx_nodeid            = [8, 7, 15, 14]
emontx_baud                = 115200

emontx_3phase_nodeid    = [11]
emontx_3phase_baud        = 9600

emonth_nodeid            = [23, 24, 25, 26]
emonth_baud                = 115200

emonpi_nodeid            = [5]
emonpi_baud                = 38400

emonesp_baud             = 115200
openevse_baud            = 115200
wifi_relay_baud        = 115200
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
    print '    Downloading: %s Bytes: %s' % (download_url.split('/')[-1], file_size)
    if (DEBUG): print 'DEBUG:    from ' + download_url
    if (DEBUG): print 'DEBUG:    Saving to: ' + save_file_name
    file_size_dl = 0
    block_sz = 8192
    while True:
            buffer = u.read(block_sz)
            if not buffer:
                    break
            file_size_dl += len(buffer)
            f.write(buffer)
            status = r'%10d    [%3.2f%%]' % (file_size_dl, file_size_dl * 100. / file_size)
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
    print bcolors.OKGREEN + '\nBurning Bootloader..try avrispmkII\n' + bcolors.ENDC
    cmd = ' avrdude -p atmega328p -c avrispmkII -P usb -e -U efuse:w:0x05:m -U hfuse:w:0xD6:m -U lfuse:w:0xFF:m -U flash:w:' + bootloader_path + ':i -Ulock:w:0x0f:m'
    print cmd
    subprocess.call(cmd, shell=True)
    print bcolors.OKGREEN + '\nBurning Bootloader..try usbasp\n' + bcolors.ENDC
    cmd = ' avrdude -p atmega328p -c usbasp -P usb -e -U efuse:w:0x05:m -U hfuse:w:0xD6:m -U lfuse:w:0xFF:m -U flash:w:' + bootloader_path + ':i -Ulock:w:0x0f:m'
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
        cmd = 'avrdude    -uV -c arduino -p ATMEGA328P -P' + serial_port + ' -b 115200 -U flash:w:' + firmware_path
        print cmd
        subprocess.call(cmd, shell=True)
    else: print bcolors.FAIL + 'ERROR: USB serial programmer NOT found' + bcolors.ENDC

    return serial_port
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Test receive RF
#--------------------------------------------------------------------------------------------------
def test_receive_rf(nodeid, rfm_port, rfm_baud):
    print    bcolors.HEADER + 'Checking for received RF...' + bcolors.ENDC
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
        cmd = 'avrdude    -uV -c arduino -p ATMEGA328P -P' + serial_port
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
# Serial Monitor
# --------------------------------------------------------------------------------------------------
def serial_monitor(baud,port):
    os.system('clear') # clear terminal screen Linux specific
    # picocom exit after x ms
    # excape chracter is [CTRL + c] then [CTRL + q] to quit
    # picocom v3.2a
    cmd = 'picocom -q -x 15000 -e c --omap crcrlf -b' + str(baud) + ' '+ str(port)
    subprocess.call(cmd, shell=True)
    return True
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
            serial_monitor(emontx_baud,serial_port)
            break
        elif nb == 'i':
            serial_monitor(emonpi_baud,serial_port)
            break
        elif nb == 'h':
            serial_monitor(emonth_baud,serial_port)
            break
        elif nb == 'o':
            serial_monitor(9600,serial_port)
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
if (RFM != False):
    RFM = rfm(rfm_port, rfm_baud, rfm_group, rfm_freq)

#--------------------------------------------------------------------------------------------------
# Update Firmware - download latest releases
#--------------------------------------------------------------------------------------------------
if interent_connected('https://api.github.com'):

    if (UPDATE):    # If startup update is requested

        # Update firware releases for github releases
        for i in range(len(github_repo)):
            current_repo = github_repo[i]
            resp = get_releases_info(current_repo)
            if 'assets' in resp:

                assets = resp['assets']

                if len(assets) == 1:
                    download_url = assets[0]['browser_download_url']
                    extension = download_url.split('.')[-1]
                    if (DEBUG): print download_url
                    if extension in allowed_extensions and UPDATE==True:
                        file_download(download_url, current_repo, download_folder)

                # if multiple rekease files then download them with their file name appended e.g. openenergymonitor-emonesp-firmware.bin and openenergymonitor-emonesp-spiffs.bin
                if len(assets) > 1:
                        for i in range(len(assets)):
                            if (DEBUG): print "Downloading multiple release" + str(i) + " with name "+ assets[i]['name']
                            extension = download_url.split('.')[-1]
                            download_url = assets[i]['browser_download_url']
                            if (DEBUG): print download_url
                            if (DEBUG): print current_repo
                            if extension in allowed_extensions and UPDATE==True:
                                file_download(download_url, current_repo + "-" + assets[i]['name'].split('.')[-0], download_folder)


        time.sleep(5)

    else: print 'Startup update disabled'

# Check required packages are installed
# check_package('avrdude')


while(1):
    print '\n-------------------------------------------------------------------------------'
    os.system('clear') # clear terminal screen Linux specific
    print ' '
    print bcolors.OKBLUE + 'OpenEnergyMonitor Firmware Upload ' + VERSION + bcolors.ENDC
    print '\nUpload >\n'
    print bcolors.OKGREEN + '(1) emonTx V3 discrete sampling (DS) [WITH battery holder]\n' + bcolors.ENDC
    print bcolors.OKGREEN + '(2) emonTx V3 continuous monitoring (CM)\n' + bcolors.ENDC
    print bcolors.OKGREEN + '(3) 3-phase emonTx\n' + bcolors.ENDC
    print bcolors.OKGREEN + '(4) emonPi\n' + bcolors.ENDC
    print bcolors.OKGREEN + '(5) emonTH V2\n' + bcolors.ENDC
    print bcolors.OKGREEN + '(6) emonESP\n' + bcolors.ENDC
    print bcolors.OKGREEN + '(7) Controller EmonEVSE (ISP)\n' + bcolors.ENDC
    print bcolors.OKGREEN + '(8) WiFi ESP8266 OpenEVSE/EmonEVSE\n' + bcolors.ENDC
    print bcolors.OKGREEN + '(9) Controller OpenEVSE (ISP)\n' + bcolors.ENDC
    print bcolors.OKGREEN + '(10) MQTT WiFi Relay\n' + bcolors.ENDC
    print bcolors.OKGREEN + '(11) WiFi ESP32 OpenEVSE/EmonEVSE' + bcolors.ENDC
    print '\n'
    #print bcolors.OKGREEN + '(r) for RFM69Pi' + bcolors.ENDC
    print bcolors.OKBLUE + '(c) to clear (erase) ESP8266 flash' + bcolors.ENDC
    print bcolors.HEADER + '(s) view Serial Debug' + bcolors.ENDC
    print bcolors.HEADER + '(u) update firmware (web connection required)' + bcolors.ENDC
    # print bcolors.HEADER + '(d) to enable DEBUG' + bcolors.ENDC
    # print bcolors.HEADER + '(e) to EXIT' + bcolors.ENDC
    # print '\n'
    # print bcolors.HEADER + '[CTRL + c] to exit' + bcolors.ENDC
    print '\n'

    nb = raw_input('Enter code for required function > ')
    os.system('clear') # clear terminal screen Linux specific

    # emonTx V3 DS
    if nb=='1':
        print bcolors.OKGREEN + '\nemonTx DS Upload\n' + bcolors.ENDC
        burn_bootloader(uno_bootloader)
        serial_port = serial_upload(download_folder + 'openenergymonitor-emontx3.hex:i')
        if (RFM):
            if test_receive_rf(emontx_nodeid, rfm_port, rfm_baud) == False:
                rfm(rfm_port, rfm_baud , rfm_group, rfm_freq) # 'poke RFM'
                reset(serial_port) # reset and try again if serial is not detected
                test_receive_rf(emontx_nodeid, rfm_port, rfm_baud)
        else: print bcolors.WARNING + '\nError: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST' + bcolors.ENDC

        if raw_input("\nDone emonTx upload. Press Enter to return to menu or (s) to view serial output>\n"):
            serial_monitor(emontx_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific
        
    # emonTx V3 CM
    if nb=='2':
        print bcolors.OKGREEN + '\nemonTx CM Upload\n' + bcolors.ENDC
        burn_bootloader(uno_bootloader)
        serial_port = serial_upload(download_folder + 'openenergymonitor-EmonTxV3CM.hex:i')
        if (RFM):
            if test_receive_rf(emontx_nodeid, rfm_port, rfm_baud) == False:
                rfm(rfm_port, rfm_baud , rfm_group, rfm_freq) # 'poke RFM'
                reset(serial_port) # reset and try again if serial is not detected
                test_receive_rf(emontx_nodeid, rfm_port, rfm_baud)
        else: print bcolors.WARNING + '\nError: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST' + bcolors.ENDC

        if raw_input("\nDone emonTx upload. Press Enter to return to menu or (s) to view serial output>\n"):
            serial_monitor(emontx_baud,serial_port)
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
            serial_monitor(emontx_3phase_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific

    # emonPi
    elif nb=='4':
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
            serial_monitor(emonpi_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific


    # emonTH V2
    elif nb=='5':
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
            serial_monitor(emonth_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific

    # emonESP
    elif nb=='6':
        print bcolors.OKGREEN + '\nemonESP Upload\n' + bcolors.ENDC
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = 'esptool.py write_flash 0x000000 ' + download_folder + 'openenergymonitor-emonesp-firmware.bin'
            print cmd
            subprocess.call(cmd, shell=True)
            if raw_input("\nDone emonESP upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if raw_input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(emonesp_baud,serial_port)

    # OpenEVSE ES8266 Wifi
    elif nb=='8':
        print bcolors.OKGREEN + '\nOpenEVSE WiFi Upload\n' + bcolors.ENDC
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = 'esptool.py write_flash 0x000000 ' + download_folder + 'OpenEVSE-ESP8266_WiFi_v2.x.bin'
            print cmd
            subprocess.call(cmd, shell=True)
            if raw_input("\nDone OpenEVSE upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if raw_input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(openevse_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific


    # EmonEVSE controller
    elif nb=='7':
        print bcolors.OKGREEN + '\nEmonEVSE Controller Upload (via ISP)\n' + bcolors.ENDC
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = ' avrdude -p atmega328p -c usbasp -P usb -e -U flash:w:' + download_folder + 'openenergymonitor-open_evse-emonevse.hex'
            print cmd
            subprocess.call(cmd, shell=True)
            raw_input("\nDone EmonEVSE controller upload. Press Enter to return to menu\n")
        os.system('clear') # clear terminal screen Linux specific

    # OpenEVSE controller
    elif nb=='9':
        print bcolors.OKGREEN + '\nOpenEVSE Controller Upload (via ISP)\n' + bcolors.ENDC
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = ' avrdude -p atmega328p -c usbasp -P usb -e -U flash:w:' + download_folder + 'openenergymonitor-open_evse-openevse.hex'
            print cmd
            subprocess.call(cmd, shell=True)
            raw_input("\nDone OpenEVSE controller upload. Press Enter to return to menu\n")
        os.system('clear') # clear terminal screen Linux specific


        # WIFI mqtt relay
    elif nb=='10':
        print bcolors.OKGREEN + '\nWiFi MQTT relay Upload\n' + bcolors.ENDC
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = 'esptool.py --baud 460800 write_flash --flash_freq 80m --flash_mode qio --flash_size 16m-c1 0x1000 ' + download_folder + 'openenergymonitor-mqtt-wifi-mqtt-single-channel-relay.bin'
            print cmd
            subprocess.call(cmd, shell=True)
            if raw_input("\nDone MQTT relay upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if raw_input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(wifi_relay_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific
    
        # OpenEVSE ESP32 Wifi
    elif nb=='11':
        print bcolors.OKGREEN + '\nOpenEVSE ESP32 WiFi Upload\n' + bcolors.ENDC
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = 'esptool.py --baud 921600 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000  ' + download_folder + 'OpenEVSE-ESP32_WiFi_V3.x-bootloader.bin 0x8000  ' + download_folder + 'OpenEVSE-ESP32_WiFi_V3.x-partitions.bin 0x10000  ' + download_folder + 'OpenEVSE-ESP32_WiFi_V3.x-firmware.bin'
            print cmd
            subprocess.call(cmd, shell=True)
            if raw_input("\nDone OpenEVSE ESP32 upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if raw_input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(openevse_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific

        # erase ESP8266 flash
    elif nb=='c':
        print bcolors.OKGREEN + '\nErase ESP8266 flash\n' + bcolors.ENDC
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = 'esptool.py erase_flash'
            print cmd
            subprocess.call(cmd, shell=True)
            if raw_input("\nDone erase ESP8266 flash, press enter to return to menu\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if raw_input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(wifi_relay_baud,serial_port)
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

    # elif nb=='d':
    #     print bcolors.OKGREEN + '\nDebug enabled' + bcolors.ENDC
    #     DEBUG = True
    #     raw_input("\nPress Enter to continue... or [CTRL + C] to exit\n")

    # elif nb=='e':
    #     shutdown_choice = raw_input("\nShutdown system after exit? Enter (y) or (n)\n")
    #     if shutdown_choice == 'y':
    #         print bcolors.FAIL + '\nSystem Shutdown....in 10s. [CTRL + C] to cancel' + bcolors.ENDC
    #         time.sleep(10)
    #         cmd = ' halt'
    #         subprocess.call(cmd, shell=True)
    #         sys.exit
    #     if shutdown_choice == 'n':
    #         quit()

    # Serial Optons
    elif nb=='s':
        serial_menu()

    # else:
        # print bcolors.FAIL + 'Invalid selection' + bcolors.ENDC


    # If RFM69Pi is present 'poke' it by re-settings its settings to keep t alive :-/
    if (RFM): rfm(rfm_port, rfm_baud , rfm_group, rfm_freq)
