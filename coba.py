import pandas
import pandas as pd
import numpy as np
from selectolax.parser import HTMLParser


def create_UPC():
   with open('GasScooters125KUPC.txt', 'r') as f:
      UPCS = f.readlines()
   UPCS_data = []
   for i in UPCS:
      UPCS_data.append({'UPC': i.replace('\n', ''), 'status': 'available'})
   df = pd.DataFrame(UPCS_data)
   df.to_csv('GasScooters125KUPC.csv', index=False)

if __name__ == '__main__':
   create_UPC()
