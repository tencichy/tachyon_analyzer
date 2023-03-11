import pandas as pd
import re
import math
import main
from pprint import pprint


def isnan(string):
    return string != string

data = pd.read_csv('log.csv', sep=',', header=None)
parametersIndexRange = data.index[data[0] == '<CONTROLLER_CONFIG>']
extractedParameters = data.iloc[parametersIndexRange[0]:parametersIndexRange[1], 0:2]
# print(extractedParameters.head(20))
# print(extractedParameters.iloc[56, 1])
for index, row in extractedParameters.iterrows():
    if isnan(row[1]) is False:
        num = re.findall('(?<=\w.: )(\d+\.*\d*)', row[1])
        print(num)

# print(extractedParameters.iloc[96, 1])
# print(re.findall('(\d+\.\d+)', extractedParameters.iloc[1, 1]))
# '(\d+\.\d+)'