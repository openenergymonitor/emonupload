#!/usr/bin/env python

# https://developer.github.com/v3/repos/releases/
# GET /repos/:owner/:repo/releases

# requires python 2.7.9 +
# use python virtual env in needed https://github.com/yyuu/pyenv

import requests, urllib, os, time, simplejson, shutil, sys

DEBUG = 1

download_folder = 'firmware'
allowed_extensions = ['bin', 'hex']
repo_config_file = 'repos.conf'

now = time.strftime("%c")
print '\nemonUpload' + time.strftime("%c") + '\n'

#--------------------------------------------------------------------------------------------------
# get list of github repos to consider from file, one repo per line. e.g 'openenergymonitor/emonpi'
repo_file = open(repo_config_file, 'r')
repo = repo_file.readlines()
number_repos = len(repo)
print 'Considering ' + str(number_repos) + ' github repos from ' + repo_config_file + ':\n'
for repo_index in range(number_repos):
  repo[repo_index] = repo[repo_index].rstrip('\n')
  print str(repo_index+1) + '. ' + repo[repo_index]
print '\n-----------------------------------------------------------------------------------'

# Check download folder exists if not create
if not os.path.isdir(download_folder):
  os.mkdir(download_folder) # make folder to store the firmware if not exist
  
  # Creates a number of empty lists to store repo info, each of 4 items, all set to 0
#w, h = 4, (len(repo))
#firmware = [[0 for x in range(w)] for y in range(h)] 
#old_firmware = [[0 for x in range(w)] for y in range(h)] 

# Load old cached firmware info from file 
# - list storing each release for each repo. Format: 
# 'username/repo', 'version_number(tag name)', 'release_title', 'release_date'
firmware_file = 'firmware/versions.json'
if os.path.isfile(firmware_file) and os.path.getsize(firmware_file) > 0:
  f = open('firmware/versions.json', 'r')
  print 'Loading cached firmware manifest ' + firmware_file
  old_firmware = simplejson.load(f) 
  if (DEBUG): print '\n' + str(old_firmware) + '\n'  
  print "Found cached firmware: \n"
  for index in range(len(old_firmware)):
    print str(index+1) + '. ' + str(old_firmware[index])
else:
  old_firmware=''
    
# Itterate over github repos 
for repo_index in range(number_repos):
  current_repo = str(repo[repo_index])
  print '\n-----------------------------------------------------------------------------------'
  print "\nGetting latest releases for " + current_repo
  release_api_url = 'https://api.github.com/repos/' + current_repo + '/releases'
  print 'from: ' + release_api_url + '\n'
  try:
    r = requests.get(release_api_url)
  except requests.exceptions.RequestException as e:  # This is the correct syntax
    print e
    print "\nERROR contacting GitHub API " + release_api_url
    sys.exit(1)
  resp = r.json()
  time.sleep(2)
  number_releases = len(resp)
  print 'Found ' + str(number_releases) + ' releases for ' + current_repo + ':' +'\n'
  
  # Iterate over github releases
  for index in range(number_releases):
    assets = resp[index]['assets']                  # multi dimentional list containing current_repo release assets
      
    release_name=resp[index]['name']
    release_version = resp[index]['tag_name']
    release_date = assets[0]['created_at']   # assume the firmware fime we want is the first asset in the release e.g. assets[0]
    # Create lisr 
    current_release_list = [ current_repo , release_version , release_name , release_date ]
    
    # check to see if firmware release has already been cached
    if str([current_release_list]) in old_firmware:
       #print 'Already cached: ' + str(index+1) + '. ' + ': '.join(current_release_list[0]) 
        print 'Already cached: ' + str(current_release_list)
    else: # if not then download new release
      #print 'NEW release...downloading: ' + str(index+1) + '. ' + ': '.join(current_release_list[0]) 
      print 'NEW release...downloading: ' + str(current_release_list) 


      # get the download URL of the first release asset (assume we only have one asset per release for now)
      # e.g. 'https://github.com/openenergymonitor/emonesp/releases/download/2.0.0/firmware.bin'
      download_url = assets[0]['browser_download_url']
      extension = download_url.split('.')[-1]

      # check firmware extension is a allowed firmware extension
      if extension in allowed_extensions:
        # add new firmare to the list
        if 'firmware' in locals():
          firmware.append(current_release_list)
        else: firmware = [current_release_list]
        # Download firmware and save to disk in download_folder/repo-version.XX e.g. emonesp-2.0.0.bin
        save_file_name = current_repo.split('/')[0] + '-' + current_repo.split('/')[-1] + '-' + release_version + '.' + extension
        download_file_name = download_url.split('/')[-1]
        u = urllib.urlopen(download_url)
        f = open(download_folder+'/'+save_file_name, 'wb')
        meta = u.info()
        file_size = int(meta.getheaders('Content-Length')[0])
        print '  Downloading: %s Bytes: %s' % (download_file_name, file_size)
        print '  from ' + download_url
        print '  Saving to: ' + download_folder+'/'+save_file_name

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
      else:
        print '  WARN: Skipping download, release file extension .' + extension + ' does not match allowed extensions: ' + ', '.join(allowed_extensions)
    


print 'Saving cached firmware version info to ' + firmware_file 
f = open(firmware_file, 'w')
simplejson.dump(firmware, f)
f.close() 

if (DEBUG): print '\n' + firmware + '\n'
print 'DONE.'





