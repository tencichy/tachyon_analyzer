import pandas as pd
import re
import main
from pprint import pprint
data = pd.read_csv('log.csv', sep=',', header=None)
parametersIndexRange = data.index[data[0] == '<CONTROLLER_CONFIG>']
extractedParameters = data.iloc[parametersIndexRange[0]:parametersIndexRange[1], 0:2]
# print(extractedParameters.head(20))
print(extractedParameters.iloc[56,1])
# for i in enumerate(extractedParameters):
#     num = re.findall(extractedParameters.iloc[i])
#     print(num)
print(extractedParameters.iloc[96, 1])
print(re.findall('(\d+\.\d+)', extractedParameters.iloc[96, 1]))
