import configparser
import copy
import json
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PyQt5 import uic
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QDialog, QInputDialog, QLineEdit,
                             QListWidget, QMessageBox, QMenuBar, QAction, QCheckBox)
from plotly.subplots import make_subplots

import parameters


# --------------#
#              #
#   Classes    #
#              #
# --------------#

class DataPacket:
    def __init__(self, data, time, labels, input_params):
        self.data = data
        self.time = time
        self.labels = labels
        self.controller_params = input_params


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

    # Delete rest of Time (s) columns
    colToDrop = []
    for i in range(0, len(data.iloc[0, :])):
        if data.iloc[0, i] == "Time (s)":
            colToDrop.append(i)

    data.drop(data.columns[colToDrop], axis=1, inplace=True)

    # Delete all empty columns and reset index
    data.dropna(how='all', axis=1, inplace=True)
    data = data.T.reset_index(drop=True).T

    # Assign labels from file
    labels = list(data.iloc[0, :])

    # Add labels from first row, to DataFrame labels, and delete first row
    data.columns = data.iloc[0]
    data = data[1:]

    # Change data types to float
    data[labels] = data[labels].apply(pd.to_numeric, errors='coerce', axis=1)

    # Extracting controller parameters from end of the csv file
    controller_params = parameters.get_parameters(filepath)

    return DataPacket(data, time, labels, controller_params)


def updateDataList(labels, dataListView):
    for label in labels:
        dataListView.addItem(label)


def showMessage(text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(text)
    msg.setWindowTitle("Tachyon Data Analyzer")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()


def showEditBox(self, text):
    text, okPressed = QInputDialog.getText(self, "Tachyon Data Analyzer", text, QLineEdit.Normal, "")
    if okPressed and text != '':
        return text
    return None


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

        self.dataListWidget = self.findChild(QListWidget, 'dataListWidget')  # Getting ListWidget for data from file

        self.dataFileListWidget = self.findChild(QListWidget, 'dataFileListWidget')
        self.dataFileListWidget.clicked.connect(self.handleFileClick)

        self.chartsListWidget = self.findChild(QListWidget, 'chartsListWidget')
        self.chartsListWidget.clicked.connect(self.handleChartClick)
        self.chartsListWidget.doubleClicked.connect(self.handleEditChartName)

        self.dataChartListWidget = self.findChild(QListWidget, 'dataChartListWidget')
        self.dataChartListWidget.doubleClicked.connect(self.handleEditDataName)
        # TODO Setting names of data in single chart
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

        self.alignDataCheckbox = self.findChild(QCheckBox, 'alignData')

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

    # Handling file opening and updating data ListWidget
    def handleOpenFile(self):
        fileNames, _ = QFileDialog.getOpenFileNames(self, "Select file", "", "CSV (*.csv)")

        if fileNames[0]:
            self.dataListWidget.clear()
            self.dataFileListWidget.clear()
            self.data.clear()
            self.dataFileIndex.clear()
            updateDataList(getData(fileNames[0]).labels, self.dataListWidget)

        for index, fileName in enumerate(fileNames):
            self.data.append(getData(fileName))
            self.dataFileIndex[os.path.basename(fileName)] = index
            self.dataFileListWidget.addItem(os.path.basename(fileName))

        if os.path.isfile('ta_config.ini') and fileNames[0]:
            config = configparser.ConfigParser()
            config.read('ta_config.ini')
            if config['DEFAULT']['config_file'] != '':
                file = open(config['DEFAULT']['config_file'])
                fileCharts = json.load(file)
                file.close()
                for ch in fileCharts:
                    self.charts.append(Chart(ch['name'], ch['labels'], ch['dataID']))
                    self.chartsListWidget.addItem(ch['name'])

                self.handleShowCharts()

    def handleFileClick(self):
        self.dataListWidget.clear()
        updateDataList(self.data[self.dataFileIndex[self.dataFileListWidget.selectedIndexes()[0].data()]].labels,
                       self.dataListWidget)

    # Handling adding charts
    def handleAddChart(self):
        if len(self.charts) == 0:
            self.charts.append(Chart("Chart 0", {}, []))
            self.chartsListWidget.addItem("Chart 0")
        else:
            chartName = str("Chart " + str(len(self.charts)))
            self.charts.append(Chart(chartName, {}, []))
            self.chartsListWidget.addItem(chartName)

    def handleEditChartName(self):
        newName = showEditBox(self, "Enter new chart name:")
        if newName is not None:
            element = list(filter(lambda c: c.name == self.chartsListWidget.selectedIndexes()[0].data(), self.charts))
            for i, o in enumerate(self.charts):
                if o.name == newName:
                    showMessage("Chart name must be unique!")
                    break
                if o.name == element[0].name:
                    self.charts[i].name = newName
                    self.chartsListWidget.selectedItems()[0].setText(newName)
                    break

    def handleDeleteChart(self):
        if self.chartsListWidget.selectedIndexes():
            element = list(filter(lambda c: c.name == self.chartsListWidget.selectedIndexes()[0].data(), self.charts))
            for i, o in enumerate(self.charts):
                if o.name == element[0].name:
                    del self.charts[i]
                    break

            self.chartsListWidget.takeItem(self.chartsListWidget.currentRow())
            self.dataChartListWidget.clear()
        else:
            showMessage("Make sure that you've selected chart")

    def handleChartClick(self):
        self.dataChartListWidget.clear()
        element = list(filter(lambda c: c.name == self.chartsListWidget.selectedIndexes()[0].data(), self.charts))
        if element[0].labels:
            for label in element[0].labels:
                self.dataChartListWidget.addItem(label)

    # Handling adding data to chart
    def handleAddData(self):
        if self.dataListWidget.selectedIndexes() and self.chartsListWidget.selectedIndexes() and self.dataFileListWidget.selectedIndexes():
            element = list(filter(lambda c: c.name == self.chartsListWidget.selectedIndexes()[0].data(), self.charts))
            element[0].labels[str(str(self.dataListWidget.selectedIndexes()[0].data()) + " - " + str(
                self.dataFileIndex[self.dataFileListWidget.selectedIndexes()[0].data()]))] = \
                self.dataListWidget.selectedIndexes()[0].data()

            element[0].dataID.append(self.dataFileIndex[self.dataFileListWidget.selectedIndexes()[0].data()])
            self.dataChartListWidget.clear()
            for label in element[0].labels:
                self.dataChartListWidget.addItem(label)

        else:
            showMessage("Make sure that you've selected data file, data and chart.")

    def handleEditDataName(self):
        newName = showEditBox(self, "Enter new chart name:")
        if newName is not None:
            for ch in self.charts:
                if self.dataChartListWidget.selectedIndexes()[0].data() in ch.labels and ch.name == \
                        self.chartsListWidget.selectedIndexes()[0].data():
                    if newName not in ch.labels:
                        ch.labels[newName] = ch.labels[self.dataChartListWidget.selectedIndexes()[0].data()]
                        ch.labels.pop(self.dataChartListWidget.selectedIndexes()[0].data())
                        self.dataChartListWidget.selectedItems()[0].setText(newName)
                    else:
                        showMessage("Data name must be unique across the current chart!")
                        break

    def handleDeleteData(self):
        if self.dataChartListWidget.selectedIndexes() and self.chartsListWidget.selectedIndexes():
            # element = list(
            #     filter(
            #         lambda c: self.dataChartListWidget.selectedIndexes()[0].data() in c.labels and c.name ==
            #                   self.chartsListWidget.selectedIndexes()[0].data(),
            #         self.charts
            #     )
            # )
            for ch in self.charts:
                if self.dataChartListWidget.selectedIndexes()[0].data() in ch.labels and ch.name == \
                        self.chartsListWidget.selectedIndexes()[0].data():
                    ch.dataID.pop(list(ch.labels.keys()).index(self.dataChartListWidget.selectedIndexes()[0].data()))
                    ch.labels.pop(self.dataChartListWidget.selectedIndexes()[0].data())

            self.dataChartListWidget.takeItem(self.dataChartListWidget.currentRow())
        else:
            showMessage("Make sure that you've selected chart data")

    def handleShowCharts(self):
        if self.charts:
            dataCopy = copy.deepcopy(self.data)
            if self.alignDataCheckbox.isChecked():
                for dt in dataCopy:
                    dt.time = list(map(lambda x: x - dt.time[0], dt.time))
            subplot_layout = []
            # creating subplot layout according to amount of charts
            for index, value in enumerate(self.charts):
                if index == 0:
                    subplot_layout.append([{'type': 'table', 'rowspan': len(self.charts)}, {'type': 'scatter'}])
                else:
                    subplot_layout.append([None, {'type': 'scatter'}])

            print(subplot_layout)
            fig = make_subplots(rows=len(self.charts), cols=2, subplot_titles=list(map(lambda x: x.name, self.charts)),
                                specs=subplot_layout, column_widths=[0.2, 0.8])
            df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/Mining-BTC-180.csv")

            for chartID, ch in enumerate(self.charts):
                for labelID, label in enumerate(ch.labels.values()):
                    fig.add_trace(go.Scatter(x=dataCopy[ch.dataID[labelID]].time,
                                             y=dataCopy[ch.dataID[labelID]].data.iloc[1:,
                                               dataCopy[ch.dataID[labelID]].labels.index(label)],
                                             name=list(ch.labels.keys())[labelID]), row=chartID + 1, col=2)
            fig.add_trace(go.Table(
                header=dict(values=["Date", "Number<br>Transactions", "Output<br>Volume (BTC)"], font=dict(size=10),
                            align="left"), cells=dict(values=[df[k].tolist() for k in df.columns[1:4]], align="left")),
                          row=1, col=1)
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
                self.chartsListWidget.addItem(ch['name'])

    def handleSetDefaultConfiguration(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Select configuration file", "",
                                                  "TA Configuration file (*.json)")
        if fileName:
            config = configparser.ConfigParser()
            config['DEFAULT']['config_file'] = str(fileName)
            with open('ta_config.ini', 'w') as configfile:
                config.write(configfile)

    @staticmethod
    def handleClearDefaultConfiguration():
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
