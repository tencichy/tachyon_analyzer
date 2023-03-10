import pandas as pd

import main
from pprint import pprint
data = pd.read_csv('log.csv', sep=',', header=None)
parametersIndexRange = data.index[data[0] == '<CONTROLLER_CONFIG>']
extractedParameters = data.iloc[parametersIndexRange[0]:parametersIndexRange[1], 0:2]
print(extractedParameters)

