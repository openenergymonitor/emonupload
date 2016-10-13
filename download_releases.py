#!/usr/bin/env python

# https://developer.github.com/v3/repos/releases/
# GET /repos/:owner/:repo/releases

# requires python 2.7.9 +
# use python virtual env in needed https://github.com/yyuu/pyenv

# By Glyn Hudson
# Part of OpenEnergyMonitor.org project
# GNU GPL V3

#--------------------------------------------------------------------------------------------------
import requests, urllib, os, shutil, sys, json



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
# Create global debug variable if debug() function is called
#--------------------------------------------------------------------------------------------------
DEBUG=0
def debug():
  global DEBUG
  DEBUG=1
  return
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# get list of github repos to consider from file, one repo per line. e.g 'openenergymonitor/emonpi'
#--------------------------------------------------------------------------------------------------
def get_repos( repo_config_file ):
  repo_file = open(repo_config_file, 'r')
  repo = repo_file.readlines()
  number_repos = len(repo)
  print bcolors.UNDERLINE + 'Considering ' + str(number_repos) + ' github repos from ' + repo_config_file + ':\n' + bcolors.ENDC
  for repo_index in range(number_repos):
    repo[repo_index] = repo[repo_index].rstrip('\n')
    print str(repo_index+1) + '. ' + repo[repo_index]
  return repo
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Load old cached firmware info from file
# - list storing each release for each repo.
# File-name: e.g 'openenergymonitor-emonth.json'
# Format: 'username/repo', 'version_number(tag name)', 'release_title', 'release_date'
#--------------------------------------------------------------------------------------------------
def get_downloaded_releases(firmware_file):
  if os.path.isfile(firmware_file) and os.path.getsize(firmware_file) > 0:
    f = open(firmware_file, 'r')
    print bcolors.UNDERLINE + '\nFound downloaded releases: \n' + bcolors.ENDC
    old_firmware = json.load(f)
    if (DEBUG): print '\nDEBUG: ' + str(old_firmware) + '\n'
    for index in range(len(old_firmware)):
      print str(index+1) + '. ' + json.dumps(old_firmware[index])
  else:
    old_firmware=''
    if (DEBUG): 'No downloaded releases found'
  return old_firmware
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Get latest GitHub release info using GitHub releases API
#--------------------------------------------------------------------------------------------------
def get_releases_info(current_repo):
  release_api_url = 'https://api.github.com/repos/' + current_repo + '/releases'
  if (DEBUG): print 'DEBUG: API URL: ' + release_api_url + '\n'
  try:
    r = requests.get(release_api_url)
  except requests.exceptions.RequestException as e:
    print bcolors.FAIL + '\nERROR contacting GitHub API ' + release_api_url + '\n' + bcolors.ENDC
    sys.exit(1)
  resp = r.json()
  if (DEBUG): print '\n' + json.dumps(resp, sort_keys=True, indent=4, separators=(',', ': ')) + '\n'
  return resp
#--------------------------------------------------------------------------------------------------
    
#--------------------------------------------------------------------------------------------------
# DOWNLOAD FILE
#--------------------------------------------------------------------------------------------------
def file_download(download_url, current_repo, download_folder, release_version):
  save_file_name = download_folder + current_repo.split('/')[-2] + '-' + current_repo.split('/')[-1] + '-' + release_version + download_url.split('.')[-1]
  # Check download folder exists if not create
  if not os.path.isdir(download_folder):
    os.mkdir(download_folder)
  u = urllib.urlopen(download_url)
  f = open(save_file_name, 'wb')
  meta = u.info()
  file_size = int(meta.getheaders('Content-Length')[0])
  print '  Downloading: %s Bytes: %s' % (download_url.split('/')[-1], file_size)
  print '  from ' + download_url
  print '  Saving to: ' + save_file_name
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
# Download / Update releases from GitHub
#--------------------------------------------------------------------------------------------------
def update_download_releases(repo, number_repos, download_folder, allowed_extensions):
  # Itterate over github repos
  for repo_index in range(number_repos):
    current_repo = str(repo[repo_index])
    repo_name = str(current_repo.split('/')[-1])
    gh_username = str(current_repo.split('/')[-2])
    
    print bcolors.HEADER + bcolors.UNDERLINE + '\n' + current_repo + '\n'  + bcolors.ENDC
  
    firmware_file = download_folder + gh_username + '-' + repo_name + '.json'
    if (DEBUG): print 'Opening ' + firmware_file
    
    old_firmware = get_downloaded_releases(firmware_file)
      
    resp = get_releases_info(current_repo)
    number_releases = len(resp)
    print bcolors.OKBLUE + '\nFound ' + str(number_releases) + ' GitHub releases for ' + current_repo + ':' +'\n' + bcolors.ENDC
    
    # Iterate over github releases
    for index in range(number_releases):
      if (DEBUG): print '\n' + json.dumps(resp[index], sort_keys=True, indent=4, separators=(',', ': ')) + '\n'
      assets = resp[index]['assets']                  # multi dimentional list containing current_repo release assets
      release_name=resp[index]['name']
      release_version = resp[index]['tag_name']
      release_date = assets[0]['created_at']   # assume the firmware fime we want is the first asset in the release e.g. assets[0]
      # Create current firmware list
      current_release_list = [ current_repo, release_version, release_name, release_date ]
      print str(index+1) + '. ' + json.dumps(current_release_list)
      download =1
      # check to see if firmware release has already been cached
      for old_index in range(len(old_firmware)):
        if current_release_list == old_firmware[old_index]:
          download=0
          if (DEBUG):
            print '\nDEBUG: Cached: ' + str(old_firmware[old_index])
            print 'DEBUG: Latest: ' + str(current_release_list)
      
      if download==0: print bcolors.OKGREEN + '    Already cached.' + bcolors.ENDC
  
      # get the download URL of the first release asset (assume we only have one asset per release for now)
      # e.g. 'https://github.com/openenergymonitor/emonesp/releases/download/2.0.0/firmware.bin'
      download_url = assets[0]['browser_download_url']
      extension = download_url.split('.')[-1]
  
      # check firmware extension is a allowed firmware extension
      if extension in allowed_extensions and download==1:
        print bcolors.WARNING + '    NEW RELEASE...downloading: ' + bcolors.ENDC
        # append new firmare to the list to be saved
        if 'firmware' in locals():
          firmware.append(current_release_list)
        else: firmware = [current_release_list]
        # Download firmware and save to disk in download_folder/repo-version.XX e.g. emonesp-2.0.0.bin
        save_file_name = current_repo.split('/')[0] + '-' + current_repo.split('/')[-1] + '-' + release_version + '.' + extension
        
        file_download(download_url, current_repo, download_folder, release_version)
        
      if extension not in allowed_extensions:
        if (DEBUG): print '\nDEBUG: Skipping download, release file extension .' + extension + ' does not match allowed extensions: ' + ', '.join(allowed_extensions)
    # Save firmware file info .json
    if 'firmware' in locals():
      print 'Saving downloaded firmware version info to ' + firmware_file
      f = open(firmware_file, 'w')
      json.dump(firmware, f)
      f.close()
      if (DEBUG): print '\nDEBUG: ' + str(firmware) + '\n'
    print '\n-------------------------------------------------------------------------------\n'
  #--------------------------------------------------------------------------------------------------



















