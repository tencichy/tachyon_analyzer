import re

import pandas as pd


# TODO dodać wczytywanie nazw parametrów
def get_parameters(filename):
    def isnan(string):
        return string != string

    data = pd.read_csv(filename, sep=',', header=None)
    parameters_index_range = data.index[data[0] == '<CONTROLLER_CONFIG>']
    extracted_parameters = data.iloc[parameters_index_range[0]:parameters_index_range[1], 0:2]

    params = []
    for index, row in extracted_parameters.iterrows():
        if isnan(row[1]) is False:
            num = re.findall(
                '(?<=[a-zA-Z].: )((\d+\.*\d*)([a-zA-Z]{0,3}))([A-Za-z0-9/\-]+( [A-Za-z0-9/]+)+)\s\([A-Za-z0-9_/]+\)([A-Za-z0-9-]+( [A-Za-z0-9-]+)+)',
                row[1])
            if len(num) > 0:
                params.append(num[0][0:4])
    params_df = pd.DataFrame(params, columns=['Compound', 'Value', 'Unit', 'Name'])
    return params_df


def isnan(string):
    return string != string


data = pd.read_csv('log.csv', sep=',', header=None)
parameters_index_range = data.index[data[0] == '<CONTROLLER_CONFIG>']
extracted_parameters = data.iloc[parameters_index_range[0]:parameters_index_range[1], 0:2]

params = []
for index, row in extracted_parameters.iterrows():
    if isnan(row[1]) is False:
        num = re.findall('([A-Za-z0-9/\-]+( [A-Za-z0-9/]+)+)\s\([A-Za-z0-9_/]+\)|([A-Za-z0-9-]+( [A-Za-z0-9-]+)+)',
                         row[1])
        print(num)
#         if len(num) > 0:
#             params.append(num[0][0:4])
# params_df = pd.DataFrame(params, columns=['Compound', 'Value', 'Unit', 'Name'])
