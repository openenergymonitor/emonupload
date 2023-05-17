#!/usr/bin/env python3

# Script for RaspberryPi with RFM12Pi / RFM69Pi
# Automated upload and test
# Upload code to emonTx via ISP and check for RF data received

# By Glyn Hudson
# Part of the openenergymonitor.org project
# GNU GPL V3

# $ pip install -r requirements.txt
import serial, sys, string, subprocess, time, subprocess, os, urllib.request, urllib.error, urllib.parse, requests, urllib.request, urllib.parse, urllib.error, json, zipfile
from subprocess import Popen, PIPE, STDOUT
from os.path import expanduser

#--------------------------------------------------------------------------------------------------
DEBUG             = 0
UPDATE            = 1           # Update firmware releases at startup
VERSION = 'V2.6.1'

download_folder = 'latest/'
repo_folder = 'repos/'
uno_bootloader = 'bootloaders/optiboot_atmega328.hex'

allowed_extensions = ['bin', 'hex' ,'zip']
github_repo = ['openenergymonitor/emonesp', 'OpenEVSE/ESP8266_WiFi_v2.x', 'openenergymonitor/mqtt-wifi-mqtt-single-channel-relay', 'OpenEVSE/open_evse', 'OpenEVSE/ESP32_WiFi_V4.x']
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

# Check download folder exists if not create
if not os.path.isdir(download_folder):
    os.mkdir(download_folder)

#--------------------------------------------------------------------------------------------------
# Check interent connectivity
#--------------------------------------------------------------------------------------------------
def interent_connected(url):
    print('Testing internet connection...')
    connected = False
    req = urllib.request.Request(url)
    try:
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(bcolors.WARNING + 'No internet connection detected..update aborted\n' + bcolors.ENDC)
    except urllib.error.URLError as e:
        # Not an HTTP-specific error (e.g. connection refused)
        print(bcolors.WARNING + 'No internet connection detected..update aborted\n' + bcolors.ENDC)
    else:
        # 200
        body = resp.read()
        print(bcolors.OKGREEN + 'Internet connection detected' + bcolors.ENDC)
        connected = True
    return connected
#-------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Get latest GitHub release info using GitHub releases API
#--------------------------------------------------------------------------------------------------
def get_releases_info(current_repo):
    release_api_url = 'https://api.github.com/repos/' + current_repo + '/releases/latest'
    if (DEBUG): print('DEBUG: API URL: ' + release_api_url + '\n')
    try:
        r = requests.get(release_api_url)
    except requests.exceptions.RequestException as e:
        print(bcolors.FAIL + '\nERROR contacting GitHub API ' + release_api_url + '\n' + bcolors.ENDC)
        sys.exit(1)
    resp = r.json()
    if 'tag_name' in resp:
        release_version = resp['tag_name']
    else : release_version = 'N/A'
    print(bcolors.OKGREEN + 'Latest ' + current_repo + 'firmware: V' + release_version + bcolors.ENDC)
    if (DEBUG): print('\n' + json.dumps(resp, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')
    return resp
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# DOWNLOAD FILE
#--------------------------------------------------------------------------------------------------
def file_download(download_url, current_repo, download_folder):
    save_file_name = download_folder + current_repo.split('/')[-2] + '-' + current_repo.split('/')[-1] + '.' + download_url.split('.')[-1]
    extension = download_url.split('.')[-1]
    # Check download folder exists if not create
    if not os.path.isdir(download_folder):
        os.mkdir(download_folder)
    u = urllib.request.urlopen(download_url)
    f = open(save_file_name, 'wb')
    meta = u.info()
    file_size = int(meta.get_all("Content-Length")[0])
    print('    Downloading: %s Bytes: %s' % (download_url.split('/')[-1], file_size))
    if (DEBUG): print('DEBUG:    from ' + download_url)
    if (DEBUG): print('DEBUG:    Saving to: ' + save_file_name)
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
            print(status, end=' ')
    f.close()
    print('\n')
    # extract github actions artifacts
    if extension=="zip":
        print('Unzipping ' + save_file_name)
        with zipfile.ZipFile(save_file_name,"r") as zip_ref:
            zip_ref.extractall(download_folder)
        # github action zip files contain a single firmware.bin, we need to rename this to fit the schema
        os.rename(download_folder + '/firmware.bin' , download_folder + current_repo.split('/')[-2] + '-' + current_repo.split('/')[-1] + '.' + 'bin')
        # remove zip archive
        os.remove(save_file_name)

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
        print(bcolors.OKBLUE + '\nRFM69Pi detected' + bcolors.ENDC)
    except serial.serialutil.SerialException:
        print(bcolors.WARNING + '\nError: Cannot connect to RFM69Pi receiver. Upload only...NO RF TEST' + bcolors.ENDC)
        RFM = False
    return RFM

#--------------------------------------------------------------------------------------------------
# Burn Bootloader
#--------------------------------------------------------------------------------------------------
def burn_bootloader(bootloader_path):
    print(bcolors.OKGREEN + '\nBurning Bootloader..try avrispmkII\n' + bcolors.ENDC)
    cmd = ' avrdude -p atmega328p -c avrispmkII -P usb -e -U efuse:w:0x05:m -U hfuse:w:0xD6:m -U lfuse:w:0xFF:m -U flash:w:' + bootloader_path + ':i -Ulock:w:0x0f:m'
    print(cmd)
    subprocess.call(cmd, shell=True)
    print(bcolors.OKGREEN + '\nBurning Bootloader..try usbasp\n' + bcolors.ENDC)
    cmd = ' avrdude -p atmega328p -c usbasp -P usb -e -U efuse:w:0x05:m -U hfuse:w:0xD6:m -U lfuse:w:0xFF:m -U flash:w:' + bootloader_path + ':i -Ulock:w:0x0f:m'
    print(cmd)
    subprocess.call(cmd, shell=True)

    return;
#--------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
# Serial Upload
#--------------------------------------------------------------------------------------------------
def serial_upload(firmware_path):
    print(bcolors.OKGREEN + '\nSerial upload ' + firmware_path + '\n' + bcolors.ENDC)

    # Autodetect ttyUSB port 0 - 12 ttyUSB[x]
    serial_port = get_serial_port()

    if (serial_port!=False):
        cmd = 'avrdude    -uV -c arduino -p ATMEGA328P -P' + str(serial_port) + ' -b 115200 -U flash:w:' + firmware_path
        print(cmd)
        subprocess.call(cmd, shell=True)
    else: print(bcolors.FAIL + 'ERROR: USB serial programmer NOT found' + bcolors.ENDC)

    return serial_port
    
def get_serial_port():
    serial_port = False
    for i in range(12):
        try_port='/dev/ttyUSB' +str(i)
        try:
            ser = serial.Serial(port=try_port, timeout=1)
            ser.read()
            ser.close()
            print(bcolors.OKGREEN + "Found serial programmer on " + try_port + bcolors.ENDC)
            serial_port = try_port
            break
        except serial.serialutil.SerialException:
            if (DEBUG): print('ERROR: USB serial programmer NOT found on ' + try_port + bcolors.ENDC)
            
    return serial_port
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Test receive RF
#--------------------------------------------------------------------------------------------------
def test_receive_rf(nodeid, rfm_port, rfm_baud):
    print(bcolors.HEADER + 'Checking for received RF...' + bcolors.ENDC)
    ser = serial.Serial(rfm_port, rfm_baud, timeout=5)
    # read x number of lines of serial from RFM
    rf_receive = False
    for l in range(3):
        linestr = ser.readline()
        if len(linestr) > 0: print(linestr)
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
    if (rf_receive): print(bcolors.OKGREEN + bcolors.UNDERLINE +'PASS!...RF RECEIVED' + bcolors.ENDC)
    else: print(bcolors.FAIL + bcolors.UNDERLINE + 'FAIL...RF NOT received' + bcolors.ENDC)
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
        print(linestr)
    ser.close()
    return;
#--------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------
# Reset unit
#--------------------------------------------------------------------------------------------------
def reset(serial_port):
    print('Reset ' + str(serial_port))
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
        if DEBUG: print(bcolors.OKGREEN + 'PlatformIO is installed' + bcolors.ENDC)
        print(bcolors.OKGREEN + '\nUnit Test: \n' + bcolors.ENDC)
        cmd = 'pio test -d' + test_path + ' -e' + env
        print(cmd)
        subprocess.call(cmd, shell=True)
        input("\nDone. Press Enter to return to menu >\n")
        os.system('clear') # clear terminal screen Linux specific
        return True
    else:
        print(bcolors.FAIL + 'Error PlatformIO NOT installed' + bcolors.ENDC)
        print('Or test path cannot be found: ' + test_path)
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
        print('\n-------------------------------------------------------------------------------')
        print(bcolors.OKBLUE + 'View Serial Output: ' + bcolors.ENDC)
        print('\nEnter >\n')
        print(bcolors.OKGREEN + '\n(x) for emonTx V3 Serial @ ' + str(emontx_baud) + bcolors.ENDC)
        print(bcolors.OKGREEN + '\n(i) for emonPi Serial @ ' + str(emonpi_baud) + bcolors.ENDC)
        print(bcolors.OKGREEN + '\n(h) for emonTH V2 Serial @ ' + str(emonth_baud) + bcolors.ENDC)
        print(bcolors.OKGREEN + '\n(0) for older units serial @9600 ' + bcolors.ENDC)
        print(bcolors.OKBLUE + '\n\n(m) To Return to main menu > ' + bcolors.ENDC)
        nb = input('> ')

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
            print(bcolors.FAIL + 'Invalid selection' + bcolors.ENDC)
        return


serial_port = get_serial_port()

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
    print("Internet connected")
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
                    if (DEBUG): print("download_url " + download_url)
                    if extension in allowed_extensions and UPDATE==True:
                        file_download(download_url, current_repo, download_folder)

                # if multiple release files then download them with their file name appended e.g. openenergymonitor-emonesp-firmware.bin and openenergymonitor-emonesp-spiffs.bin
                if len(assets) > 1:
                        for i in range(len(assets)):
                            if (DEBUG): print("Downloading multiple release " + str(i) + " with name "+ assets[i]['name'])
                            download_url = assets[i]['browser_download_url']
                            extension = download_url.split('.')[-1]
                            if (DEBUG): print("download_url " + download_url)
                            if extension in allowed_extensions and UPDATE==True:
                                file_download(download_url, current_repo + "-" + assets[i]['name'].split('.')[-0], download_folder)


        time.sleep(5)

    else: print('Startup update disabled')
else: print("Internet not connected, or rate limit exceeded")
# Check required packages are installed
# check_package('avrdude')

first_run = True

while(1):
    print('\n-------------------------------------------------------------------------------')
    if not first_run:
        os.system('clear') # clear terminal screen Linux specific
        first_run = False
    print(' ')
    print(bcolors.OKBLUE + 'OpenEnergyMonitor Firmware Upload ' + VERSION + bcolors.ENDC)
    print('\nUpload >\n')
    print(bcolors.OKGREEN + '(6) emonESP\n' + bcolors.ENDC)
    print(bcolors.OKGREEN + '(7) Controller EmonEVSE (ISP)\n' + bcolors.ENDC)
    print(bcolors.OKGREEN + '(8) WiFi ESP8266 OpenEVSE/EmonEVSE\n' + bcolors.ENDC)
    print(bcolors.OKGREEN + '(9) Controller OpenEVSE (ISP)\n' + bcolors.ENDC)
    print(bcolors.OKGREEN + '(10) MQTT WiFi Relay\n' + bcolors.ENDC)
    print(bcolors.OKGREEN + '(11) WiFi ESP32 OpenEVSE/EmonEVSE\n' + bcolors.ENDC)
    print(bcolors.OKGREEN + '(12) Etherent ESP32 OpenEVSE/EmonEVSE\n' + bcolors.ENDC)
    print('\n')
    #print bcolors.OKGREEN + '(r) for RFM69Pi' + bcolors.ENDC
    print(bcolors.OKBLUE + '(c) to clear (erase) ESP8266 flash' + bcolors.ENDC)
    print(bcolors.HEADER + '(s) view Serial Debug' + bcolors.ENDC)
    print(bcolors.HEADER + '(u) update firmware (web connection required)' + bcolors.ENDC)
    # print bcolors.HEADER + '(d) to enable DEBUG' + bcolors.ENDC
    # print bcolors.HEADER + '(e) to EXIT' + bcolors.ENDC
    # print '\n'
    # print bcolors.HEADER + '[CTRL + c] to exit' + bcolors.ENDC
    print('\n')

    nb = input('Enter code for required function > ')
    os.system('clear') # clear terminal screen Linux specific

    # emonESP
    if nb=='6':
        print(bcolors.OKGREEN + '\nemonESP\n' + bcolors.ENDC)
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = 'esptool.py write_flash 0x000000 ' + download_folder + 'openenergymonitor-emonesp-firmware.bin'
            print(cmd)
            subprocess.call(cmd, shell=True)
            if input("\nDone emonESP upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(emonesp_baud,serial_port)

    # OpenEVSE ES8266 Wifi
    elif nb=='8':
        print(bcolors.OKGREEN + '\nOpenEVSE WiFi\n' + bcolors.ENDC)
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = 'esptool.py write_flash 0x000000 ' + download_folder + 'OpenEVSE-ESP8266_WiFi_v2.x.bin'
            print(cmd)
            subprocess.call(cmd, shell=True)
            if input("\nDone OpenEVSE upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(openevse_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific


    # EmonEVSE controller
    elif nb=='7':
        print(bcolors.OKGREEN + '\nEmonEVSE Controller ( SP)\n' + bcolors.ENDC)
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            print('setting fuses')
            cmd = ' avrdude -c USBasp -p m328p -U lfuse:w:0xFF:m -U hfuse:w:0xDF:m -U efuse:w:0xFD:m -B6'
            print(cmd)
            subprocess.call(cmd, shell=True)

            input("\nController fuses set press Enter to read back\n")
            cmd = ' avrdude -p atmega328p -c usbasp -P usb -e -U lfuse:r:-:i -v'
            subprocess.call(cmd, shell=True)

            input("\nPress Enter to flash EmonEVSE Controller FW\n")
            cmd = ' avrdude -p atmega328p -c usbasp -B5 -P usb -e -U flash:w:' + download_folder + 'OpenEVSE-open_evse-emonevse.hex'
            print(cmd)
            subprocess.call(cmd, shell=True)
            input("\nDone EmonEVSE controller upload. Press Enter to return to menu\n")
        os.system('clear') # clear terminal screen Linux specific

    # OpenEVSE controller
    elif nb=='9':
        print(bcolors.OKGREEN + '\nOpenEVSE Controller (ISP)\n' + bcolors.ENDC)
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            print('setting fuses')
            cmd = ' avrdude -c USBasp -p m328p -U lfuse:w:0xFF:m -U hfuse:w:0xDF:m -U efuse:w:0xFD:m -B6'
            print(cmd)
            subprocess.call(cmd, shell=True)

            input("\nController fuses set press Enter to read back\n")
            cmd = ' avrdude -p atmega328p -c usbasp -P usb -e -U lfuse:r:-:i -v'
            subprocess.call(cmd, shell=True)

            input("\nPress Enter to flash EmonEVSE Controller FW\n")
            cmd = ' avrdude -p atmega328p -c usbasp -B5 -P usb -e -U flash:w:' + download_folder + 'OpenEVSE-open_evse-openevse_eu.hex'
            print(cmd)
            subprocess.call(cmd, shell=True)
            input("\nDone OpenEVSE controller upload. Press Enter to return to menu\n")
        os.system('clear') # clear terminal screen Linux specific


        # WIFI mqtt relay
    elif nb=='10':
        print(bcolors.OKGREEN + '\nWiFi MQTT relay\n' + bcolors.ENDC)
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = 'esptool --baud 460800 write_flash --flash_freq 80m --flash_mode qio --flash_size 16m-c1 0x1000 ' + download_folder + 'openenergymonitor-mqtt-wifi-mqtt-single-channel-relay.bin'
            print(cmd)
            subprocess.call(cmd, shell=True)
            if input("\nDone MQTT relay upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(wifi_relay_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific

    # OpenEVSE ESP32 Wifi
    elif nb=='11':
        print(bcolors.OKGREEN + '\nOpenEVSE ESP32 WiFi\n' + bcolors.ENDC)
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = 'esptool --baud 921600 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000  ' + download_folder + 'OpenEVSE-ESP32_WiFi_V4.x-bootloader.bin 0x8000  ' + download_folder + 'OpenEVSE-ESP32_WiFi_V4.x-partitions.bin 0x10000  ' + download_folder + 'OpenEVSE-ESP32_WiFi_V4.x-openevse_wifi_v1_gui-v2.bin'
            print(cmd)
            subprocess.call(cmd, shell=True)
            if input("\nDone OpenEVSE ESP32 upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(openevse_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific

    # OpenEVSE ESP32 Etherent Gateway F & G
    elif nb=='12':
        print(bcolors.OKGREEN + '\nOpenEVSE ESP32 Etherent Gateway\n' + bcolors.ENDC)
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            cmd = 'esptool --before default_reset --after hard_reset write_flash 0x1000 ' + download_folder + 'OpenEVSE-ESP32_WiFi_V4.x-bootloader.bin 0x8000 ' + download_folder + 'OpenEVSE-ESP32_WiFi_V4.x-partitions.bin 0x10000 ' + download_folder + 'OpenEVSE-ESP32_WiFi_V4.x-openevse_esp32-gateway-f_gui-v2.bin'
            print(cmd)
            subprocess.call(cmd, shell=True)
            if input("\nDone OpenEVSE ESP32 Etherent Gateway Upload. Press Enter to return to menu or (s) to view serial output (reset required)>\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(openevse_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific
            
    elif nb=='c':
        print(bcolors.OKGREEN + '\nErase ESP8266 flash\n' + bcolors.ENDC)
        cmd = 'pip freeze --disable-pip-version-check | grep esptool'
        if subprocess.call(cmd, shell=True) != ' ':
            # If esptool is installed
            cmd = 'esptool erase_flash'
            print(cmd)
            subprocess.call(cmd, shell=True)
            if input("\nDone erase ESP8266 flash, press enter to return to menu\n"):
                            serial_monitor(emonesp_baud,serial_port)
        else:
            if input("\nERROR: esptool not installed. Press Enter to return to menu>\n"):
                serial_monitor(wifi_relay_baud,serial_port)
        os.system('clear') # clear terminal screen Linux specific

    elif nb=='u':
        print(bcolors.OKGREEN + 'Checking for updates.. ' + bcolors.ENDC)
        # Update emonUpload (git pull)
        update_emonupload('emonupload.py')
        # Clone or (update if already cloned) repos defined in github_repo list
        repo_clone_update(github_repo, repo_folder)
        print('\n')
        # Update firware releases for github releases
        for i in range(len(github_repo)):
            current_repo = github_repo[i]
            resp = get_releases_info(current_repo)
            if 'assets' in resp:
                assets = resp['assets']
                download_url = assets[0]['browser_download_url']
                extension = download_url.split('.')[-1]
                if (DEBUG): print(download_url)
                if extension in allowed_extensions and UPDATE==True:
                    file_download(download_url, current_repo, download_folder)


    # Serial Optons
    elif nb=='s':
        serial_menu()



    # If RFM69Pi is present 'poke' it by re-settings its settings to keep t alive :-/
    if (RFM): rfm(rfm_port, rfm_baud , rfm_group, rfm_freq)
