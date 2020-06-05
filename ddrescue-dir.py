#!env python3

import os
import subprocess
import argparse
import sys


def parseargs():
  parser = argparse.ArgumentParser(description='Recover files recursively using ddrescue')
  parser.add_argument('source-dir',
                     help='the directory that contains the files to recover')
  parser.add_argument('dest-dir',
                     help='the directory where to store the recovered files')
  parser.add_argument('--map-dir', default='/tmp/recovering',
                     help='the directory where to write ddrescue mapfiles in order to be able to pause/resume recovery')
  parser.add_argument('--debug-dir', default='/tmp/recovering',
                     help='the directory where to write script debug information (like recovery statistics per file')
  parser.add_argument('--ddrescue-args', default='--reverse -P6 -r6',
                     help='the arguments passed to ddrescue command line')
  parser.add_argument('--dry-run', dest='dry_run', action='store_true',
                     help='do not execute recovery but instead print what the script will do')
  parser.set_defaults(dry_run=False)
  return parser.parse_args()


def escape(string):
  return string.replace("'", "'\\''")

def totallyRecovered(output):
  return "pct rescued:  100.00%, read errors:        0," in output

def hasError(err):
  return bool(err and err.strip())

def debug(filename, message, inconsole=False):
  if inconsole:
    print('['+filename+'] '+message+'\n')
  else:
    with open(os.path.join(debugdir, 'debug.log'), 'a') as f:
      f.write('['+filename+'] '+message+'\n')

def run(source, dest, mapdir, ddrescueargs, dryrun):
  results = []
  for root, subdirs, files in os.walk(source):
    relative = os.path.relpath(root, source)
    print('')
    for subdir in subdirs:
      relativedir = os.path.join(relative, subdir)
      destdirectory = os.path.join(dest, relative, subdir)
      if not os.path.exists(destdirectory):
        debug(relativedir, '   create directory ' + destdirectory, dryrun)
        if not dryrun:
          os.makedirs(destdirectory)
      mapfiledirectory = os.path.join(mapdir, relative, subdir)
      if not os.path.exists(mapfiledirectory):
        debug(relativedir, '   create directory ' + mapfiledirectory, dryrun)
        if not dryrun:
          os.makedirs(mapfiledirectory)
  
    for filename in files:
      relativefile = escape(os.path.join(relative, filename))
      sourcefile = escape(os.path.join(source, relative, filename))
      destfile = escape(os.path.join(dest, relative, filename))
      mapfile = escape(os.path.join(mapdir, relative, filename+'.mapfile'))
      debug(relativefile, '   recover file ' + sourcefile + ' -> ' + destfile, dryrun)
      command = "ddrescue -vvvv "+ddrescueargs+" '"+sourcefile+"' '"+destfile+"' '"+mapfile+"'"
      debug(relativefile, '       '+command, dryrun)
      #os.system(command)
      if not dryrun:
        result = subprocess.run(command, shell=True, encoding='UTF-8', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        debug(relativefile, '       stdout='+result.stdout)
        debug(relativefile, '       stderr='+result.stderr)
        success = totallyRecovered(result.stdout) and not hasError(result.stderr)
        results.append({
          'file': relativefile, 
          'stdout': result.stdout, 
          'stderr': result.stderr, 
          'success': success
        })
        print(relativefile+'                  '+('OK' if success else 'FAILED'))
  return results


args = vars(parseargs())
debugdir = args['debug_dir']

results = run(args['source-dir'], args['dest-dir'], args['map_dir'], args['ddrescue_args'], args['dry_run'])

print('')
print('---------------------------------')
print('Files not fully recovered')
for res in results:
  if not res['success']:
    print(res['file'])
      
    
