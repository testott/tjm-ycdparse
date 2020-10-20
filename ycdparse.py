import pandas as pd
from pathlib import Path

print("\n\nWelcome to YCD Parser.\n")

#Get BOM files and YCD files
BOM = None
YCDs = []
while not BOM or not YCDs:
  input("\nPlease place YCD files into the 'YCD here' folder, and the BOM file into the 'BOM here' folder and press ENTER to continue.")
  #Get BOM
  try:
    BOM = list(Path('BOM here/').glob('*.xlsx'))[0]
    if not BOM:
      raise FileNotFound
    print("\nFound BOM")
  except:
    print("\nCouldn't find a BOM file! Please make sure a BOM file is inside the 'BOM here' folder.")

  #Get YCDs
  try:
    YCDs = list(Path('YCD here/').glob('*.ycd'))
    if not YCDs:
      raise FileNotFound
    print("\nFound {} YCD file{}".format(len(YCDs), 's'*(len(YCDs[0:2])-1)))
  except:
    print("\nCouldn't find a YCD file! Please make sure a YCD file is inside the 'YCD here' folder.")

#Get row that contains headers
head_row = 0
while not head_row:
  try:
    head_row = int(input("\nPlease input the row number (1+) that contains the headers in the BOM.\n:"))
    if head_row < 1:
      head_row = 0
      raise OutOfBounds
  except:
    print("\nThat was an invalid number! Please input the row number and try again.\n")

#Find BOM file and parse with pandas
bom_df = pd.read_excel(BOM,header = head_row-1).dropna()

#Find relevant columns to put into YCD files
partnum_col = None
try:
  partnum_col = list(bom_df.columns.str.contains(r'.*part.*num.*', case = False, regex = True)).index(True)
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

print(partnum_col, desc_col)