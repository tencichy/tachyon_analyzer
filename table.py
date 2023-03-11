import pandas as pd
import re


class Parameter:
    def __init__(self, in_tuple):
        self.composed = in_tuple[0]
        self.value = in_tuple[1]
        self.unit = in_tuple[2]

    def __str__(self):
        return f"{self.composed},{self.value},{self.unit}"

    def __repr__(self):
        return "[% s, % s, % s]" % (self.composed, self.value, self.unit)


def get_parameters(filename):
    def isnan(string):
        return string != string

    data = pd.read_csv('log.csv', sep=',', header=None)
    parameters_index_range = data.index[data[0] == '<CONTROLLER_CONFIG>']
    extracted_parameters = data.iloc[parameters_index_range[0]:parameters_index_range[1], 0:2]

    params = []
    for index, row in extracted_parameters.iterrows():
        if isnan(row[1]) is False:
            num = re.findall('(?<=[a-zA-Z].: )((\d+\.*\d*)([a-zA-Z]{0,3}))', row[1])
            if len(num) > 0:
                params.append(Parameter(num[0][0:3]))
    return params
