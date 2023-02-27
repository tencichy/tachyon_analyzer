import numpy as np
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QDialog,
    QListView,
    QAbstractItemView,
    QMessageBox
)
import sys
import json
import configparser


# -------------#
#              #
#   Classes    #
#              #
# -------------#

class dataPacket():
    def __init__(self, data, time, labels):
        self.data = data
        self.time = time
        self.labels = labels


class chart():
    def __init__(self, name, labels):
        self.name = name
        self.labels = labels

    def __str__(self):
        return f"{self.name}: {self.labels}"

    def __repr__(self):
        return str(self)

    # def toJSON(self):
    #     return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


# --------------#
#               #
#   Functions   #
#               #
# --------------#


def getData(filePath):
    # Create file path (for first file in directory)
    filepath = os.path.join(str(filePath))

    # Get data from file
    data = pd.read_csv(filepath, sep=',', header=None)

    # Delete <CONTROLLER_CONFIG> part of file
    indexOfConfigLine = 0
    for index, row in data.iterrows():
        if (row[0] == "<CONTROLLER_CONFIG>") and (indexOfConfigLine == 0):
            indexOfConfigLine = index
        if indexOfConfigLine > 0:
            data.loc[index, 0] = np.nan
            data.loc[index, 1] = np.nan

    # Clear empty rows where was <CONTROLLER_CONFIG> data
    data.dropna(how='all', axis=0, inplace=True)
    data.reset_index(drop=True, inplace=True)

    # Get time from first Time (s) column from file
    time = list(data.iloc[1:, 0])
    time = list(map(float, time))

    # Always make time start from 0
    # time = list(map(lambda x: x - time[0], time))

    # Delete rest of Time (s) columns
    data.drop(data.columns[[0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57, 60]], axis=1,
              inplace=True)

    # Delete all empty columns and reset index
    data.dropna(how='all', axis=1, inplace=True)
    data = data.T.reset_index(drop=True).T

    # Change data types to float
    data.iloc[1:, :9] = data.iloc[1:, :9].astype(float)
    data.iloc[1:, 10:14] = data.iloc[1:, 10:14].astype(float)
    data.iloc[1:, 16:] = data.iloc[1:, 16:].astype(float)

    # Assign labels from file
    labels = list(data.iloc[0, :])

    return dataPacket(data, time, labels)


def updateDataList(labels, dataListViewModel):
    for label in labels:
        dataListViewModel.appendRow(QStandardItem(label))


def showMessage(text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(text)
    msg.setWindowTitle("Tachyon Data Analyzer")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()


# ---------------------------------------#
#                                       #
#   Window class with object handlers   #
#                                       #
# ---------------------------------------#


class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('form.ui', self)

        self.data = None
        charts = []  # TODO Change this to self. type

        dataListView = self.findChild(QListView, 'dataListView')  # Getting ListView for data from file
        dataListViewModel = QStandardItemModel()  # Creating new ItemModel
        dataListView.setModel(dataListViewModel)  # Setting new ItemModel
        dataListView.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Set ListView to non-modifiable

        chartsListView = self.findChild(QListView, 'chartsListView')
        chartsListViewModel = QStandardItemModel()
        chartsListView.setModel(chartsListViewModel)
        # TODO Setting name of chart
        chartsListView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        dataChartListView = self.findChild(QListView, 'dataChartListView')
        dataChartListViewModel = QStandardItemModel()
        dataChartListView.setModel(dataChartListViewModel)
        # TODO Setting names of data in single chart
        dataChartListView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        openFileButton = self.findChild(QPushButton, 'openFileButton')  # Getting Button for opening file
        openFileButton.clicked.connect(
            lambda: self.handleOpenFile(dataListViewModel, charts, chartsListViewModel))  # Adding handler for opening file

        addChartButton = self.findChild(QPushButton, 'addChartButton')
        addChartButton.clicked.connect(lambda: self.handleAddChart(charts, chartsListViewModel))

        deleteChartButton = self.findChild(QPushButton, 'deleteChartButton')
        deleteChartButton.clicked.connect(lambda: self.handleDeleteChart(charts, chartsListView, chartsListViewModel, dataChartListViewModel))

        chartsListView.clicked.connect(lambda: self.handleChartClick(charts, chartsListView, dataChartListViewModel))

        addDataButton = self.findChild(QPushButton, 'addDataButton')
        addDataButton.clicked.connect(
            lambda: self.handleAddData(dataListView, chartsListView, charts, dataChartListViewModel))

        deleteDataButton = self.findChild(QPushButton, 'removeDataButton')
        deleteDataButton.clicked.connect(
            lambda: self.handleDeleteData(charts, chartsListView, dataChartListView, dataChartListViewModel))

        showChartsButton = self.findChild(QPushButton, 'showChartsButton')
        showChartsButton.clicked.connect(lambda: self.handleShowCharts(charts))

        saveConfigurationButton = self.findChild(QPushButton, 'saveConfigurationButton')
        saveConfigurationButton.clicked.connect(lambda: self.handleSaveConfiguration(charts))

        openConfigurationButton = self.findChild(QPushButton, 'openConfigurationButton')
        openConfigurationButton.clicked.connect(lambda: self.handleOpenConfiguration(charts, chartsListViewModel))

        setDefaultConfigurationButton = self.findChild(QPushButton, 'setDefaultConfig')
        setDefaultConfigurationButton.clicked.connect(lambda: self.handleSetDefaultConfiguration())

        clearDefaultConfigurationButton = self.findChild(QPushButton, 'clearDefaultConfig')
        clearDefaultConfigurationButton.clicked.connect(lambda: self.handleClearDefaultConfiguration())

        self.show()

    # Handling file opening and updating data ListView
    def handleOpenFile(self, dataListViewModel, charts, chartsListViewModel):
        fileName, _ = QFileDialog.getOpenFileName(self, "Select file", "", "CSV (*.csv)")
        if fileName:
            dp = getData(fileName)
            self.data = dp
            dataListViewModel.clear()
            updateDataList(dp.labels, dataListViewModel)
            if os.path.isfile('ta_config.ini'):
                config = configparser.ConfigParser()
                config.read('ta_config.ini')
                if config['DEFAULT']['config_file'] != '':
                    file = open(config['DEFAULT']['config_file'])
                    fileCharts = json.load(file)
                    file.close()
                    for ch in fileCharts:
                        charts.append(chart(ch['name'], ch['labels']))
                        chartsListViewModel.appendRow(QStandardItem(ch['name']))

                    self.handleShowCharts(charts)

    # Handling adding charts
    def handleAddChart(self, charts, chartsListViewModel):
        if len(charts) == 0:
            charts.append(chart("Chart 0", []))
            chartsListViewModel.appendRow(QStandardItem("Chart 0"))
        else:
            chartName = str("Chart " + str(len(charts)))
            charts.append(chart(chartName, []))
            chartsListViewModel.appendRow(QStandardItem(chartName))

    def handleDeleteChart(self, charts, chartsListView, chartsListViewModel, dataChartListViewModel):
        if chartsListView.selectedIndexes():
            element = list(
                filter(
                    lambda c: c.name == chartsListView.selectedIndexes()[0].data(),
                    charts
                )
            )
            for i, o in enumerate(charts):
                if o.name == element[0].name:
                    del charts[i]
                    break

            chartsListViewModel.removeRow(chartsListView.selectedIndexes()[0].row())
            dataChartListViewModel.clear()
        else:
            showMessage("Make sure that you've selected chart")

    def handleChartClick(self, charts, chartsListView, dataChartListViewModel):
        dataChartListViewModel.clear()
        element = list(
            filter(
                lambda c: c.name == chartsListView.selectedIndexes()[0].data(),
                charts
            )
        )
        if element[0].labels:
            for label in element[0].labels:
                dataChartListViewModel.appendRow(QStandardItem(label))

    # Handling adding data to chart
    def handleAddData(self, dataListView, chartsListView, charts, dataChartListViewModel):
        if dataListView.selectedIndexes() and chartsListView.selectedIndexes():
            # TODO Do not allow duplicates in charts
            element = list(
                filter(
                    lambda c: c.name == chartsListView.selectedIndexes()[0].data(),
                    charts
                )
            )
            element[0].labels.append(dataListView.selectedIndexes()[0].data())

            dataChartListViewModel.clear()
            for label in element[0].labels:
                dataChartListViewModel.appendRow(QStandardItem(label))

        else:
            showMessage("Make sure that you've selected data and chart.")

    def handleDeleteData(self, charts, chartsListView, dataChartListView, dataChartListViewModel):
        if dataChartListView.selectedIndexes() and chartsListView.selectedIndexes():
            element = list(
                filter(
                    lambda c: dataChartListView.selectedIndexes()[0].data() in c.labels and c.name ==
                              chartsListView.selectedIndexes()[0].data(),
                    charts
                )
            )
            for ch in charts:
                if dataChartListView.selectedIndexes()[0].data() in ch.labels and ch.name == \
                        chartsListView.selectedIndexes()[0].data():
                    ch.labels.remove(dataChartListView.selectedIndexes()[0].data())

            dataChartListViewModel.removeRow(dataChartListView.selectedIndexes()[0].row())
        else:
            showMessage("Make sure that you've selected chart data")

    def handleShowCharts(self, charts):
        if charts:
            fig = make_subplots(rows=len(charts), cols=1)
            for i, ch in enumerate(charts):
                for label in ch.labels:
                    fig.add_trace(go.Scatter(x=self.data.time, y=self.data.data.iloc[1:, self.data.labels.index(label)],
                                             name=label), row=i + 1, col=1)

            fig.update_xaxes(title_text='Time (s)')
            fig.show()

    def handleSaveConfiguration(self, charts):
        jsonToSave = json.dumps([ch.__dict__ for ch in charts])

        dialog = QFileDialog()
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('json')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['TA Configuration File (*.json)'])

        if dialog.exec_() == QDialog.Accepted:
            file = open(dialog.selectedFiles()[0], "w")
            file.write(jsonToSave)
            file.close()

    def handleOpenConfiguration(self, charts, chartsListViewModel):
        fileName, _ = QFileDialog.getOpenFileName(self, "Select configuration file", "",
                                                  "TA Configuration file (*.json)")
        if fileName:
            file = open(fileName)
            fileCharts = json.load(file)
            file.close()
            for ch in fileCharts:
                charts.append(chart(ch['name'], ch['labels']))
                chartsListViewModel.appendRow(QStandardItem(ch['name']))


    def handleSetDefaultConfiguration(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Select configuration file", "",
                                                  "TA Configuration file (*.json)")
        if fileName:
            config = configparser.ConfigParser()
            config['DEFAULT']['config_file'] = str(fileName)
            with open('ta_config.ini', 'w') as configfile:
                config.write(configfile)

    def handleClearDefaultConfiguration(self):
        if os.path.isfile('ta_config.ini'):
            config = configparser.ConfigParser()
            config['DEFAULT']['config_file'] = ''
            with open('ta_config.ini', 'w') as configfile:
                config.write(configfile)

if __name__ == "__main__":
    # get window and run app
    app = QApplication(sys.argv)
    window = Ui()
    app.exec_()
