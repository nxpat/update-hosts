#!/usr/bin/env python
"""\
Update system hosts with hosts file from Steven Black GitHub repository:
https://github.com/StevenBlack/hosts

Usage: updateHosts.py [-h] [-v] [-f FILE] [-a ALLOW [ALLOW ...]] [-e EXTENSIONS]

options:
  -f FILE 					  update from file
  -a ALLOW [ALLOW ...]	  allow sites
  -e EXTENSIONS  			  choose extensions: f, g, p, s


This script updates the system hosts on Fedora Linux:
1. Download hosts file or read from file
2. Verify the integrity of the hosts file
3. (optional) Save to disk
              Update system hosts 
              Restart NetworkManager to flush the DNS cache
"""

# script by patrice houlet - 2024 - GPLv3
__version__ = '1.1'

import sys
import os
import subprocess
import re
import argparse
from datetime import datetime

import requests
import dateutil.parser as dparser


# detect Python version
PY37 = sys.version_info >= (3, 7)
if not PY37:
   raise Exception('Python 3.7 or later required.')
      
# sudo command
SUDO = ["/usr/bin/env", "sudo"]

# hosts file
hosts = '/etc/hosts'

# hosts file database directory
database = "hosts"

# basename for hosts file saved to database
basename = "hosts"

# latest hosts file
hosts_latest = "hosts_latest"

# available extensions
extensions = {'f': 'fakenews', 'g': 'gambling', 'p': 'porn', 's': 'social'}

# hosts urls
urls = "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/{extensions}/hosts"


# command-line arguments
parser = argparse.ArgumentParser(description=f"Update system hosts with hosts file from Steven Black GitHub repository")
parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}')
parser.add_argument('-f', '--file', nargs=1, help='hosts file')
parser.add_argument('-a', '--allow', nargs='+', help='allow sites')
parser.add_argument('-e', '--extensions', nargs=1, help='extensions: f, g, p, s')


def main():
   # get args
   args = parser.parse_args()

   # read data
   if args.file is None:
      # get extensions
      ext = [extensions[e] for e in extensions if args.extensions is None or e in args.extensions[0]]
      # set url
      url = urls.format(extensions='-'.join(ext))
      # download latest unified hosts file with extensions
      print(f"# Reading data from: \n{url}")
      data = get_hosts_file(url)
   else:
      # read hosts file from disk
      print(f"# Reading data from: \n{args.file[0]}")
      data = read_hosts_file(args.file[0])

   # get hosts file date
   hdate, pdate = get_hosts_date(data)
   print(pdate[2:])

   # check if hosts file is up to date
   if os.path.isfile(hosts):
      if hdate <= get_hosts_date(read_hosts_file(hosts))[0]:
         print(f"{hosts} is up to date.\nNothing to do.")
         exit(0)
   
   # calculate the number of unique domains
   nc = calculate_nud(data)
   
   # read the number of unique domains
   nr, line = read_nud(data)
   
   # print the number of unique domains
   if line is None:
      print(f'Number of unique domains: {nc:,.0f} (calculated)')
   else:
      if nr != nc:
         line += f' (calculated: {nc:,.0f})'
      print(line)

   # print the number of lines and size of hosts file
   size = len("\n".join(data)+"\n")
   print(f"Number of lines: {len(data):,.0f}   size: {size:,.0f} bytes")

	# allow sites (remove them from hosts)
   if args.allow != None:
      allow_sites(data, args.allow)
	
   # get non-valid hosts lines
   bad_data = get_bad_lines(data)

   # remove non-valid hosts lines
   if bad_data != []:
      clean_data(data, bad_data)
      # calculate and write the number of unique domains
      nud = calculate_nud(data)
      write_nud(data, nud)
   
   # save hosts file,
   # update system hosts and 
   # flush the DNS cache
   if re.search(r'^y(es)?$', input(f"#\nUpdate {hosts} (y/N)?").lower()):
      # restore loopback entries of the original Fedora hosts file
      restore_org_le(data)
      
      # save to hosts database
      path = os.path.join(f"{database}", f"{basename}-{hdate}")
      
      print(f"# Saving to {path}")
      save_hosts("\n".join(data)+"\n", path)
      
      # save to hosts-latest
      print(f"# Saving to {hosts_latest}")
      save_hosts("\n".join(data)+"\n", hosts_latest)

      # update system hosts
      print(f"# Updating {hosts}")
      try:
         subprocess.run(SUDO + ['cp', hosts_latest, hosts], check=True)
      except subprocess.CalledProcessError as e:
         e.add_note(f">>> error updating {hosts} from {hosts_latest}")
      raise

      # flush the DNS cache
      print("# Restarting NetworkManager")
      try:
         subprocess.run(SUDO + ['/usr/bin/systemctl', 'restart', 'NetworkManager.service'])
      except Exception as e:
         e.add_note(">>> error restarting NetworkManager service")
         raise

      print("Completed.")
   else:
      print("Nothing done.")


def get_hosts_file(url):
   """Download latest hosts file.
   Args:
      url: url of the hosts file
   Returns:
      hosts file as list of strings
   """
   try:
      r = requests.get(url)
      return r.text.splitlines()
   except requests.exceptions.RequestException as e:
      e.add_note(f">>> error retrieving data from {url}")
      raise
      

def read_hosts_file(file):
   """Read hosts file.
   Args:
      file: hosts file
   Returns:
      hosts file as list of strings
   """
   try:
      with open(file, "r") as f:
         try:
            return f.read().splitlines()
         except OSError as e:
            e.add_note(f">>> error reading {file}")
            raise
   except (PermissionError, OSError) as e:
      e.add_note(f">>> error opening {file}")
      raise


def get_hosts_date(data):
   """Get the date of the hosts file.
   Args:
      data: hosts file lines as list of strings
   """

   prog = re.compile('^# Date: .+$')
   pdate = next((s for s in data if prog.search(s)), None)
   if pdate is None:
      raise ValueError(">>> could not read date from hosts file")
      
   fdate = dparser.parse(pdate, fuzzy=True).strftime('%y%m%d')
   
   return fdate, pdate


def calculate_nud(data):
   """Calculate the number of unique domains in the hosts file.
   Args:
      data: hosts file lines as list of strings
   Returns:
      nud: the number of unique domains
   """
   prog = re.compile(patterns('hl'))
   nud = sum(1 for line in data if prog.search(line))
   return nud
   
   
def read_nud(data):
   """Read the number of unique domains indicated in the host file.
   Args:
      data: hosts file lines as list of strings
   Returns:
      nud: the number of unique domains
      line: the full text line
   """
   
   prog = re.compile(patterns('nud'))
   line = next((s for s in data if prog.search(s)), None)
   
   if line is not None:
      nud = int(re.sub(",", "", prog.search(line).group(1)))
   else:
      nud = None
      
   return nud, line[2:]
      

def write_nud(data, nud):
   """Write the number of unique domains to data.
   Args:
      data: hosts file lines as list of strings
      nud: the number of unique domains
   """

   prog = re.compile(patterns('nud'))
   i, s = next(((i, s) for i, s in enumerate(data) if prog.search(s)), (None, None))

   if i is not None:
      data[i] = re.sub(r' [0-9,]{3,7}$', rf' {nud:,.0f}', s)
      print(data[i][2:])
   else:
      raise ValueError('line with number of unique domains not found')


def allow_sites(data, sites):
	"""remove domains for allowed sites
   Args:
      data: hosts file lines as list of strings
   Returns:
      sites: allowed sites
   """

	print("# Allowing sites:")
	for site in sites:
		s = '# ' + site
		if s in data:
			i = data.index(s)
			j = i + 1
			while data[j] != '':
				j += 1
			del data[i:j+1]
			print(f"{j-i-1} domains removed for {site}")
	
	
def get_bad_lines(data):
   """Verify integrity of the hosts file
   Args:
      data: hosts file lines as list of strings
   Returns:
      bad_data: non-valid hosts lines as list of strings
   """

   # get compromised or non-valid hosts lines
   prog = re.compile(patterns('xhl'))
   bad_data = [(i, line) for i, line in enumerate(data) if prog.search(line)]
   
   print("# Verifying hosts file integrity: ", end="")
   
   if bad_data != []:
      print()
      print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
      print(">>>>>>>>>>            Security Warning            >>>>>>>>>>")
      print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
      print(f">>> Non-valid lines = {len(bad_data)}")
      print("\n".join(f"{i}: {line}" for i, line in bad_data))
      print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
   else:
      print("OK.")

   return bad_data


def clean_data(data, bad_data):
   """Remove bad lines
   Args:
      data: hosts file lines as list of strings
      bad_data: non-valid hosts lines as list of strings
   """

   print("# Cleaning data:")
   
   # accepted hosts line: keep subdomains with '_'
   prog = re.compile(patterns('ahl'))
   
   # remove lines
   nr = 0
   for j in reversed(range(len(bad_data))):
      i, line = bad_data[j]
      if not prog.search(line):
         del data[i]
         del bad_data[j]
         nr += 1
         print(f"Removed line {i}: {line}")
   
   print(f"Removed {nr} lines.")
   
   # print kept lines
   print(f"Kept {len(bad_data)} lines:")
   for i, line in bad_data:
      print(f"Kept line {i}: {line}")
      
   print(rf'Total number of lines: {len(data):,.0f}')
   
   return


def restore_org_le(data):
   """Restore loopback entries of the original Fedora hosts file
   Args:
      data: hosts file lines as list of strings
   """
   i = data.index('127.0.0.1 localhost')
   data[i] = '127.0.0.1 localhost localhost.localdomain localhost4 localhost4.localdomain4'
   
   data.remove('127.0.0.1 localhost.localdomain')
   
   i = data.index('::1 localhost')
   data[i] = '::1 localhost localhost.localdomain localhost6 localhost6.localdomain6'
   
   return
   
   
def save_hosts(data, path):
   """Save to file.
   Args:
      data: hosts file lines as list of strings
      path: filename or path to save data to
   """
   
   try:
      with open(path, "w") as f:
         try:
            f.write(data)
         except OSError as e:
            e.add_note(f">>> error writing to {path}")
            raise
   except (PermissionError, OSError) as e:
         e.add_note(f">>> error creating {path}")
         raise


def patterns(pattern):
   """Returns regular expression pattern.
   Args:
      pattern:
         'd':   domain
         'd2':  domain2
         'ip4': ipv4
         'c':   comment
         'xhl': non-valid hosts line
         'ahl': accepted hosts line (subdomain with '_')
         'hl':  hosts line
         'nud': number of unique domains
      str: string to scan
   Returns:
      regular expression pattern
   """
   
   # dictionary of regex patterns
   p = {}
   
   # Restrictions on domain (DNS) names 
   # https://www.rfc-editor.org/rfc/rfc1035             (1987)
   # https://www.rfc-editor.org/rfc/rfc1123#page-13     (1989)
   # https://www.rfc-editor.org/rfc/rfc2181#section-11  (1997)
   # https://www.rfc-editor.org/rfc/rfc3696#section-2   (2004)
   # compatible with IDNA specification encoded with 'xn--'
   # https://www.rfc-editor.org/rfc/rfc3696#section-5

   # valid domain for a hosts file
   domain = (r'(?![^ ]{256,})'
             r'(?:(?!-)[a-z0-9-]{1,63}(?<!-)\.){1,126}'
             r'(?![0-9]+( |\t|$))(?!-)[a-z0-9-]{2,63}(?<!-)')
   p['d'] = domain
   
   # valid subdomains with '_'
   domain2 = (r'(?![^ ]{256,})(?!(?:.+?\.){127,})'
              r'(?:(?!-)[a-z0-9-_]{1,63}(?<!-)\.){0,125}'
              r'(?:(?!-)[a-z0-9-]{1,63}(?<!-)\.){1,126}'
              r'(?![0-9]+( |\t|$))(?!-)[a-z0-9-]{2,63}(?<!-)')
   p['d2'] = domain2
   
   # valid ipv4 address
   ipv4 = (r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
           r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')
   p['ip4'] = ipv4
   
   # valid comment
   comment = '[ \t]*#.*'
   p['c'] = comment

   # non-valid hosts line
   xhl = (rf'^(.*[\n\r\f\v\x0d\x0a\x0c\x0b].+|'
          rf'(?!{comment})'
          rf'(?!0\.0\.0\.0 (?:{domain}|{ipv4})(?:{comment})?)'
           r'(?!127\.0\.0\.1 localhost)'
           r'(?!127\.0\.0\.1 localhost\.localdomain)'
           r'(?!127\.0\.0\.1 local)'
           r'(?!255\.255\.255\.255 broadcasthost)'
           r'(?!::1 localhost)'
           r'(?!::1 ip6-localhost)'
           r'(?!::1 ip6-loopback)'
           r'(?!fe80::1%lo0 localhost)'
           r'(?!ff00::0 ip6-localnet)'
           r'(?!ff00::0 ip6-mcastprefix)'
           r'(?!ff02::1 ip6-allnodes)'
           r'(?!ff02::2 ip6-allrouters)'
           r'(?!ff02::3 ip6-allhosts)'
           r'.+)$'
         )
   p['xhl'] = xhl
   
   # accepted hosts line: keep subdomains with '_'
   ahl = rf'^0\.0\.0\.0 ({domain2}|{ipv4})({comment})?$'
   p['ahl'] = ahl
   
   # hosts line
   hl = r'^0\.0\.0\.0 (?!0\.0\.0\.0$)(?:[^#]+\.)*[^#]+.*$'
   p['hl'] = hl
   
   # number of unique domains
   nud = r'^# Number of unique domains: ([0-9,]{3,7})$'
   p['nud'] = nud

   return p[pattern]
   
   
if __name__ == "__main__":
   main()
