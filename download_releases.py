#!/usr/bin/env python

# https://developer.github.com/v3/repos/releases/
# GET /repos/:owner/:repo/releases

# requires python 2.7.9 +
# use python virtual env in needed https://github.com/yyuu/pyenv

import requests, urllib, os, time


download_folder = 'firmware'
allowed_extensions = ['bin', 'hex']

# get list of github repos from file, one repo per line. e.g 'openenergymonitor/emonpi'
repo_file = open('repos.conf', 'r')
repo = repo_file.readlines()
number_repos = len(repo)
print 'Found ' + str(number_repos) + ' github repos in repos.conf:\n'
for repo_index in range(number_repos):
  repo[repo_index] = repo[repo_index].rstrip('\n')
  print str(repo_index+1) + '. ' + repo[repo_index]

# Creates a number of empty lists to store repo info, each of 4 items, all set to 0
# used to store: 'index, tag_name, release_title, release_date'
w, h = 4, (len(repo))
firmware = [[0 for x in range(w)] for y in range(h)] 

# Check download folder exists if not create
if not os.path.isdir(download_folder):
  os.mkdir(download_folder) # make folder to store the firmware if not exist
  

# Itterate over repos 
for repo_index in range(len(repo)):
  current_repo = str(repo[repo_index].split('/')[-1])
  print '\n-----------------------------------------------------------------------------------'
  print "\nGetting available github releases for " + current_repo +'\n'
  r = requests.get('https://api.github.com/repos/openenergymonitor/'+current_repo+'/releases')
  resp = r.json()
  time.sleep(2)
  print 'Found ' + str(len(resp)) + ' releases for ' + current_repo + ':' +'\n'
  
  # Iterate over releases
  for index in range(len(resp)):
    assets = resp[index]['assets']                  # multi dimentional array containing current_repo release assets
    
    
    release_name=resp[index]['name']
    release_version = resp[index]['tag_name']
    release_date = assets[0]['created_at']          # assume the firmware we want is the first asset in the release e.g. assets[0]
    
    firmware[index] = [ str(index+1) , release_version , release_name , release_date ]
    print '\n'
    print ': '.join(firmware[index])
    # get the download URL of the first release asset (assume we only have one asset per release for now)
    # e.g. 'https://github.com/openenergymonitor/emonesp/releases/download/2.0.0/firmware.bin'
    download_url = assets[0]['browser_download_url']
    extension = download_url.split('.')[-1]
    
    # check firmware extension is a allowed firmware extension
    if extension in allowed_extensions:
      # Download firmware and save to disk in download_folder/repo-version.XX e.g. emonesp-2.0.0.bin
      save_file_name = current_repo + '-' + release_version + '.' + extension
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
      print '  WARN: Skipping download: ' + current_repo + ' ' + release_version + 'release file extension .' + extension + ' does not match allowed extensions: ' + ', '.join(allowed_extensions)

