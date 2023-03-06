import numpy as np
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PyQt5 import uic
from PyQt5.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QKeyEvent
)
from PyQt5.QtCore import QDir, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QDialog,
    QListView,
    QAbstractItemView,
    QMessageBox,
    QMenuBar,
    QAction
)
import sys
import json
import configparser


# -------------#
#              #
#   Classes    #
#              #
# -------------#

class DataPacket:
    def __init__(self, data, time, labels):
        self.data = data
        self.time = time
        self.labels = labels


class Chart:
    def __init__(self, name, labels, dataID):
        self.name = name
        self.labels = labels
        self.dataID = dataID

    def __str__(self):
        return f"{self.name}: {self.labels}"

    def __repr__(self):
        return str(self)


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

    return DataPacket(data, time, labels)


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


# --------------------------------------#
#                                       #
#   Window class with object handlers   #
#                                       #
# --------------------------------------#


class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('form.ui', self)

        self.data = []
        self.charts = []
        self.dataFileIndex = {}

        self._createActions()
        self._createMenuBar()

        self.dataListView = self.findChild(QListView, 'dataListView')  # Getting ListView for data from file
        self.dataListViewModel = QStandardItemModel()  # Creating new ItemModel
        self.dataListView.setModel(self.dataListViewModel)  # Setting new ItemModel
        self.dataListView.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Set ListView to non-modifiable

        self.dataFileListView = self.findChild(QListView, 'dataFileListView')
        self.dataFileListViewModel = QStandardItemModel()
        self.dataFileListView.setModel(self.dataFileListViewModel)
        self.dataFileListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dataFileListView.clicked.connect(self.handleFileClick)

        self.chartsListView = self.findChild(QListView, 'chartsListView')
        self.chartsListViewModel = QStandardItemModel()
        self.chartsListView.setModel(self.chartsListViewModel)
        # TODO Setting name of chart
        self.chartsListView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.chartsListView.clicked.connect(self.handleChartClick)

        self.dataChartListView = self.findChild(QListView, 'dataChartListView')
        self.dataChartListViewModel = QStandardItemModel()
        self.dataChartListView.setModel(self.dataChartListViewModel)
        # TODO Setting names of data in single chart
        self.dataChartListView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.openFileAction.triggered.connect(self.handleOpenFile)

        addChartButton = self.findChild(QPushButton, 'addChartButton')
        addChartButton.clicked.connect(self.handleAddChart)

        deleteChartButton = self.findChild(QPushButton, 'deleteChartButton')
        deleteChartButton.clicked.connect(self.handleDeleteChart)

        addDataButton = self.findChild(QPushButton, 'addDataButton')
        addDataButton.clicked.connect(self.handleAddData)

        deleteDataButton = self.findChild(QPushButton, 'removeDataButton')
        deleteDataButton.clicked.connect(self.handleDeleteData)

        showChartsButton = self.findChild(QPushButton, 'showChartsButton')
        showChartsButton.clicked.connect(self.handleShowCharts)

        self.saveConfigAction.triggered.connect(self.handleSaveConfiguration)

        self.openConfigAction.triggered.connect(self.handleOpenConfiguration)

        self.setDefaultConfigAction.triggered.connect(self.handleSetDefaultConfiguration)

        self.clearDefaultConfigAction.triggered.connect(self.handleClearDefaultConfiguration)

        self.show()

    def _createActions(self):
        self.openFileAction = QAction("&Open...", self)
        self.openFileAction.setShortcut("Ctrl+O")

        self.openConfigAction = QAction("&Open...", self)
        self.openConfigAction.setShortcut("Ctrl+Alt+O")

        self.saveConfigAction = QAction("&Save", self)
        self.saveConfigAction.setShortcut("Ctrl+Alt+S")

        self.setDefaultConfigAction = QAction("&Set default", self)
        self.setDefaultConfigAction.setShortcut("Ctrl+Alt+D")

        self.clearDefaultConfigAction = QAction("&Clear default", self)
        self.clearDefaultConfigAction.setShortcut("Ctrl+Alt+C")

    def _createMenuBar(self):
        menuBar = QMenuBar(self)
        fileMenu = menuBar.addMenu("&Data")

        fileMenu.addAction(self.openFileAction)

        configMenu = menuBar.addMenu("&Configuration")

        configMenu.addAction(self.openConfigAction)
        configMenu.addAction(self.saveConfigAction)

        configDefaultMenu = configMenu.addMenu("&Default")

        configDefaultMenu.addAction(self.setDefaultConfigAction)
        configDefaultMenu.addAction(self.clearDefaultConfigAction)

        self.setMenuBar(menuBar)

    # Handling file opening and updating data ListView
    def handleOpenFile(self):
        fileNames, _ = QFileDialog.getOpenFileNames(self, "Select file", "", "CSV (*.csv)")

        if fileNames[0]:
            self.dataListViewModel.clear()
            self.dataFileListViewModel.clear()
            self.data.clear()
            self.dataFileIndex.clear()
            updateDataList(getData(fileNames[0]).labels, self.dataListViewModel)

        for index, fileName in enumerate(fileNames):
            self.data.append(getData(fileName))
            self.dataFileIndex[os.path.basename(fileName)] = index
            self.dataFileListViewModel.appendRow(QStandardItem(os.path.basename(fileName)))

        if os.path.isfile('ta_config.ini') and fileNames[0]:
            config = configparser.ConfigParser()
            config.read('ta_config.ini')
            if config['DEFAULT']['config_file'] != '':
                file = open(config['DEFAULT']['config_file'])
                fileCharts = json.load(file)
                file.close()
                for ch in fileCharts:
                    self.charts.append(Chart(ch['name'], ch['labels'], ch['dataID']))
                    self.chartsListViewModel.appendRow(QStandardItem(ch['name']))

                self.handleShowCharts()

    def handleFileClick(self):
        self.dataListViewModel.clear()
        updateDataList(self.data[self.dataFileIndex[self.dataFileListView.selectedIndexes()[0].data()]].labels, self.dataListViewModel)

    # Handling adding charts
    def handleAddChart(self):
        if len(self.charts) == 0:
            self.charts.append(Chart("Chart 0", [], []))
            self.chartsListViewModel.appendRow(QStandardItem("Chart 0"))
        else:
            chartName = str("Chart " + str(len(self.charts)))
            self.charts.append(Chart(chartName, [], []))
            self.chartsListViewModel.appendRow(QStandardItem(chartName))

    def handleDeleteChart(self):
        if self.chartsListView.selectedIndexes():
            element = list(
                filter(
                    lambda c: c.name == self.chartsListView.selectedIndexes()[0].data(),
                    self.charts
                )
            )
            for i, o in enumerate(self.charts):
                if o.name == element[0].name:
                    del self.charts[i]
                    break

            self.chartsListViewModel.removeRow(self.chartsListView.selectedIndexes()[0].row())
            self.dataChartListViewModel.clear()
        else:
            showMessage("Make sure that you've selected chart")

    def handleChartClick(self):
        self.dataChartListViewModel.clear()
        element = list(
            filter(
                lambda c: c.name == self.chartsListView.selectedIndexes()[0].data(),
                self.charts
            )
        )
        if element[0].labels:
            for label in element[0].labels:
                self.dataChartListViewModel.appendRow(QStandardItem(label))

    # Handling adding data to chart
    def handleAddData(self):
        if self.dataListView.selectedIndexes() and self.chartsListView.selectedIndexes() and self.dataFileListView.selectedIndexes():
            element = list(
                filter(
                    lambda c: c.name == self.chartsListView.selectedIndexes()[0].data(),
                    self.charts
                )
            )
            element[0].labels.append(self.dataListView.selectedIndexes()[0].data())
            element[0].dataID.append(self.dataFileIndex[self.dataFileListView.selectedIndexes()[0].data()])

            self.dataChartListViewModel.clear()
            for label in element[0].labels:
                self.dataChartListViewModel.appendRow(QStandardItem(label))

        else:
            showMessage("Make sure that you've selected data file, data and chart.")

    def handleDeleteData(self):
        if self.dataChartListView.selectedIndexes() and self.chartsListView.selectedIndexes():
            # element = list(
            #     filter(
            #         lambda c: self.dataChartListView.selectedIndexes()[0].data() in c.labels and c.name ==
            #                   self.chartsListView.selectedIndexes()[0].data(),
            #         self.charts
            #     )
            # )
            for ch in self.charts:
                if self.dataChartListView.selectedIndexes()[0].data() in ch.labels and ch.name == \
                        self.chartsListView.selectedIndexes()[0].data():
                    ch.dataID.pop(ch.labels.index(self.dataChartListView.selectedIndexes()[0].data()))
                    ch.labels.remove(self.dataChartListView.selectedIndexes()[0].data())

            self.dataChartListViewModel.removeRow(self.dataChartListView.selectedIndexes()[0].row())
        else:
            showMessage("Make sure that you've selected chart data")

    def handleShowCharts(self):
        if self.charts:
            fig = make_subplots(rows=len(self.charts), cols=1)
            for chartID, ch in enumerate(self.charts):
                for labelID, label in enumerate(ch.labels):
                    fig.add_trace(go.Scatter(x=self.data[ch.dataID[labelID]].time,
                                             y=self.data[ch.dataID[labelID]].data.iloc[1:, self.data[ch.dataID[labelID]].labels.index(label)],
                                             name=label), row=chartID + 1, col=1)

            fig.update_xaxes(title_text='Time (s)')
            fig.show()

    def handleSaveConfiguration(self):
        jsonToSave = json.dumps([ch.__dict__ for ch in self.charts])

        dialog = QFileDialog()
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('json')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['TA Configuration File (*.json)'])

        if dialog.exec_() == QDialog.Accepted:
            file = open(dialog.selectedFiles()[0], "w")
            file.write(jsonToSave)
            file.close()

    def handleOpenConfiguration(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Select configuration file", "",
                                                  "TA Configuration file (*.json)")
        if fileName:
            file = open(fileName)
            fileCharts = json.load(file)
            file.close()
            for ch in fileCharts:
                self.charts.append(Chart(ch['name'], ch['labels'], ch['dataID']))
                self.chartsListViewModel.appendRow(QStandardItem(ch['name']))


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
