from graphql import GraphQLClient
from mouser import MouserClient
from pathlib import Path
from timeit import default_timer as timer

import configparser
import pandas as pd
import pickle
import re
import time

print("#"*80 + "\n" * 3 + "Welcome to YCD Parser.\n")

# Get API Keys from config file
print("\n" * 4 + "Loading config...")
config = configparser.ConfigParser()

# Check if config.ini exists, if not write it
if not Path('config.ini').exists():
  print("\nUnable to find config file! Generating new config file...")
  with open('config.ini', 'w') as configfile:
    config['API Keys'] = {'octopart': '', 'mouser': ''}
    config.write(configfile)
else:
  config.read('config.ini')
octopart_api_key = config.get('API Keys', 'octopart')
mouser_api_key = config.get('API Keys', 'mouser')

# Check if Octopart API key exists, if not write it
if not octopart_api_key:
  octopart_api_key = input("Couldn't find Octopart API key! Please input your Octopart API key and hit enter.\n:")
  config['API Keys']['octopart'] = octopart_api_key
  with open('config.ini', 'w') as configfile:
    config.write(configfile)
  print("API Key saved!")
  
# Check if Mouser API key exists, if not write it
if not mouser_api_key:
  mouser_api_key = input("\nCouldn't find Mouser API key! Please input your Mouser API key and hit enter.\n:")
  config['API Keys']['mouser'] = mouser_api_key
  with open('config.ini', 'w') as configfile:
    config.write(configfile)
  print("API Key saved!")
print("Done")

# Get reference dictionary of parts
print("\nLoading part reference dictionary...")
try:
  ref_dict = pickle.load(open("ref_dict.p", "rb"))
except:
  print("Unable to find part reference dictionary! Generating new file...")
  ref_dict = {}
  pickle.dump(ref_dict, open("ref_dict.p", "wb"))
print("Done.")

# Setup GraphQL Client
print("\nSetting up API endpoints...")
gql = GraphQLClient('https://octopart.com/api/v4/endpoint')
gql.inject_token(octopart_api_key)
mouser = MouserClient(mouser_api_key)
print("Done.")

print("\nLoading complete.")

# Get BOM files and YCD files
BOM = None
YCDs = []

#Check if directories exist
if not Path('BOM here/').exists():
  Path('BOM here/').mkdir()
if not Path('YCD here/').exists():
  Path('YCD here/').mkdir()
if not Path('Output/').exists():
  Path('Output/').mkdir()

while not BOM or not YCDs:
  input("\n\n\nPlease place YCD files into the 'YCD here' folder, and the BOM file into the 'BOM here' folder and press ENTER to continue.")
  # Get BOM
  try:
    BOM = list(Path('BOM here/').glob('*.xlsx'))[0]
    if not BOM:
      raise FileNotFound
    print("\nFound BOM")
  except:
    print("\nCouldn't find a BOM file! Please make sure a BOM file is inside the 'BOM here' folder.")

  # Get YCDs
  try:
    YCDs = list(Path('YCD here/').glob('*.ycd'))
    if not YCDs:
      raise FileNotFound
    print("\nFound {} YCD file{}".format(len(YCDs), 's'*(len(YCDs[0:2])-1)))
  except:
    print("\nCouldn't find a YCD file! Please make sure a YCD file is inside the 'YCD here' folder.")

# Get row that contains headers
head_row = 0
while not head_row:
  try:
    head_row = int(input("\nPlease input the row number (1+) that contains the headers in the BOM.\n:"))
    if head_row < 1:
      head_row = 0
      raise OutOfBounds
  except:
    print("\nThat was an invalid number! Please input the row number and try again.\n")

# Set start time
start = timer()

# Parse BOM with pandas
print("\nParsing BOM...")
bom_df = pd.read_excel(BOM, header = head_row-1, encoding = 'utf-8')

# Find relevant columns to put into YCD files
partnum_col = None
try:
  partnum_col = list(bom_df.columns.str.contains(r'.*part.*num.*|.*p/n.*', case = False, regex = True)).index(True)
except:
  while not partnum_col:
    try:
      partnum_col = int(input("\nCouldn't find Part Number column!\nPlease input the column number (1+) for the Part Number in the BOM.\n:"))
      if partnum_col not in range(1,len(bom_df.columns)):
        partnum_col = 0
        raise OutOfBounds
    except:
      print("\nThat was an invalid number! Please input the column number between 1 and {} and try again.\n".format(len(bom_df.columns)))
    partnum_col -= 1
partnum_col = bom_df.columns[partnum_col]

desc_col = None
try:
  desc_col = list(bom_df.columns.str.contains('desc', case = False)).index(True)
except:
  while not desc_col:
    try:
      desc_col = int(input("\nCouldn't find Description column!\nPlease input the column number (1+) for the Descriptions in the BOM.\n:"))
      if desc_col not in range(1,len(bom_df.columns)):
        desc_col = 0
        raise OutOfBounds
    except:
      print("\nThat was an invalid number! Please input the column number between 1 and {} and try again.\n".format(len(bom_df.columns)))
    desc_col -= 1
desc_col = bom_df.columns[desc_col]

# Ensure part numbers and descriptions are set as strings
bom_df[partnum_col] = bom_df[partnum_col].astype(str)
bom_df[desc_col] = bom_df[desc_col].astype(str)
print('\nBOM parse complete!')

# Parse YCD files with pandas and crosscheck all part numbers and add them to reference dictionary
print('\nParsing YCD files...')

# Set last mouser check to current time - 10
last_mouser_check = timer() - 10


for ycd in YCDs:
  # Remove double spaces in description column of ycd files
  new_ycd = []
  with open(str(ycd), 'r+') as f:
    i = 0
    for line in f:
      if '[PartListEnd]' in line:
        break
      if i > 16:
        ycd_description = re.split(r'\s{2,}',line,6)[6]
        new_description = re.sub(r'\s{2,}', ' ', ycd_description)
        new_ycd.append(line.replace(ycd_description, new_description))
      else:
        new_ycd.append(line)
      i += 1
      
  with open(str(ycd), 'w+') as f:
    for line in new_ycd:
      f.write(line)
  
  ycd_df = pd.read_csv(ycd, delimiter = r'\s{2,}', header = 0, skiprows = range(0,17), skipfooter = 1, engine = 'python', encoding = 'utf-8')
  quit()
  # Ensure part numbers and packages are set as strings
  ycd_df['P/N'] = ycd_df['P/N'].astype(str)
  ycd_df['Pkg'] = ycd_df['Pkg'].astype(str)
  # Sort by reference designator
  ycd_df = ycd_df.sort_values(by = ['RefID.'])
  
  # Iterate over each row of YCD file
  for i, row in ycd_df.iterrows():
    pn = row['P/N']
    
    # Check if part number is in reference dictionary
    if pn not in ref_dict and pn.lower() not in ['dni', 'dnp']:
      desc = bom_df.loc[bom_df[partnum_col] == pn,desc_col].iloc[0]
      
      # Lookup on Octopart
      try:
        data = gql.get_part_specs(pn)
      
        # Get package, prioritizing Imperial Case Codes over Metric, if it exists
        pkg = ''
        for each in data:
          if not pkg and each['attribute']['name'] == 'Case/Package':
            pkg = each['display_value']
          if each['attribute']['name'] == 'Case Code (Imperial)':
            pkg = each['display_value']
      except:
        pkg = ''
          
      # Get package from Mouser if not found on Octopart, or if package name is strange
      if not pkg or not re.search(r'\d', pkg):
        if int(timer() - last_mouser_check) < 10:
          time.sleep(int(timer() - last_mouser_check))
        last_mouser_check = timer()
        pkg = mouser.get_part_specs(pn)
      
      # Strip - from package name
      if pkg:
        pkg = re.sub('-', '', pkg)
      
      # Manual check for strange package names
      if pkg and not re.search(r'\d', pkg):
        answer = ''
        while not answer:
          print("\nFound package name: " + pkg + " for " + pn)
          answer = input("\nDoes this look correct?\n(y/n):")
          if 'y' in answer.lower():
            break
          elif 'n' in answer.lower():
            pkg = ''
          else:
            answer = ''
            print("\nPlease type yes (y) or no (n)!")
      
      # Manually input package name if unable to find one on Octopart or Mouser
      if not pkg:
        print("\nUnable to find case/package info for " + pn +"!")
        while not pkg:
          pkg = str(input("\nPlease manually input correct case/package name for " + pn + "\n:"))
          if not pkg:
            print("\nPackage name invalid!")
      
      # Check if 4 digit case code, then apply C, R, L to the end if the reference designator matches
      if re.search('^\d\d\d\d$', pkg):
        # Capacitors, Resistors, and inductors
        if row['RefID.'].lower().startswith(('c', 'r', 'l')):
          pkg = pkg + row['RefID.'][0]
        # Ferrite bead inductors
        if row['RefID.'].lower().startswith('fb'):
          pkg = pkg + 'L'
        # Diodes
        if row['RefID.'].lower().startswith('d'):
          if re.search(r'LED', desc):
            pkg = pkg + 'LED'
          else:
            answer = ''
            while not answer:
              answer = input("\nIs " + pn + " an LED?\n(y/n):")
              if 'y' in answer.lower():
                pkg = pkg + 'LED'
              elif 'n' in answer.lower():
                pkg = pkg + 'D'
              else:
                answer = ''
                print("\nPlease type yes (y) or no (n)!")
      
      # Save new part to reference dictionary
      ref_dict[pn] = [desc,pkg]
      pickle.dump(ref_dict, open("ref_dict.p", "wb"))
      print("\n" + pn + " added to part reference dictionary as " + pkg)
    
    # Check for DNI and add it if it isn't there
    if pn.lower() in ['dni', 'dnp'] and pn not in ref_dict:
      ref_dict[pn] = [pn, pn]
      pickle.dump(ref_dict, open("ref_dict.p", "wb"))
    
    # Set new values to row
    if ycd_df.iloc[i]['Extension'] == '----':
      ycd_df.set_value(i,'Extension', ref_dict[pn][0])
    ycd_df.set_value(i,'Pkg', ref_dict[pn][1])
  
  # Write new YCD as tsv file for use with YesTech CAD Utility
  tsv_path = Path('Output') / Path(str(ycd.stem) + '.tsv')
  print("\nSaving " + tsv_path.name + " to Output folder...")
  ycd_df.to_csv(tsv_path, index = False, header = False, sep = '\t')
  print("\nDone.")


print("\n\nProgram complete!")
print("\nTime elapsed: " + str(int(timer()-start)) + " seconds.")
input("\nPress ENTER to exit.")
