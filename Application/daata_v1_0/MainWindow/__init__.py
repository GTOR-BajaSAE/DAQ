from PyQt5 import uic, QtWidgets, QtGui
from PyQt5.QtCore import QSettings

from functools import partial
import threading
import os

from Layouts.Homepage import Layout_Homepage
from Layouts.DataCollection import Layout_DataCollection
from Layouts.Layout_Test import Widget_Test

from Utilities.Popups import popup_ParentChildrenTree
from Utilities.Popups import popup_closeTabConfirmation
import DataAcquisition


is_data_collecting = threading.Event()  # Creates an event to know if the data collection has started
data_collection_thread = threading.Thread(target=DataAcquisition.collect_data)  # Creates thread for collecting data


Ui_MainWindow, _ = uic.loadUiType(r'MainWindow\MainWindow.ui')  # loads the .ui file from QT Desginer


tabInstances = 0    # a counter for the number of tabs created in current session


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        data_collection_thread.start()

        self.setupUi(self)
        self.dict_layouts = {}  # instantiates dictionary that holds objects for widgets
        self.import_Widgets()
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'icon_application.svg')))

        self.resetTabs_tabWidget()
        self.populate_menubar()


        self.connectSignalsSlots()

        self.create_homepage()

        self.settings = QSettings('DAATA', 'MainWindow')
        try:
            self.resize(self.settings.value('window size'))
            self.move(self.settings.value('window position'))
        except:
            pass

    def populate_menubar(self):
        ## Make an action to create a tab for each imported widget
        for key in self.dict_layouts.keys():
            self.dict_layouts[key]['Menu Action'] = QtWidgets.QAction(self)
            self.dict_layouts[key]['Menu Action'].setCheckable(False)
            self.dict_layouts[key]['Menu Action'].setToolTip('Open a new tab for ' + key)
            self.dict_layouts[key]['Menu Action'].setText(key)
            self.menuAddLayout.addAction(self.dict_layouts[key]['Menu Action'])

        ## Make an action in the File menu to display current parent and children tree
        self.action_parentChildren = QtWidgets.QAction(self)
        self.action_parentChildren.setToolTip(
            'Display a tree of all parent objects and their respective children for the current UI layout')
        self.action_parentChildren.setText('Display parent/children tree')
        self.menuFile.addAction(self.action_parentChildren)


    def import_Widgets(self):
        self.dict_layouts = {
            'Data Collection': {
                'Create Layout': partial(Layout_DataCollection, data_collection_thread, is_data_collecting)
            },

            'Layout Test': {
                'Create Layout': Widget_Test
            }
        }

    def create_homepage(self):
        self.homepage = Layout_Homepage()
        self.homepage.setObjectName("Homepage")
        self.gridLayout_tab_homepage.addWidget(self.homepage)

        # self.tabWidget.setCornerWidget(self.homepage.button, corner = Qt.Corner.TopRightCorner)

    ## Creates tab widget for apps
    def resetTabs_tabWidget(self):
        for index in range(self.tabWidget.count()):
            self.tabWidget.removeTab(0)
        self.create_layoutTab('Data Collection')                       # sets default tab that pops up in Layouts
        self.tabWidget_central.setCurrentIndex(self.tabWidget_central.indexOf(self.tab_homepage)) ## temporary measure to default to homepage on startup
        self.tabWidget.setStyleSheet("""

        """)


    def create_layoutTab(self, key):
        global tabInstances
        tab = self.dict_layouts[key]['Create Layout']()
        tab.setObjectName(key + " (instance " + str(tabInstances) + ")")           # set object names for each tab's widget (allows duplicate widgets to have a functional parent/child relationship)
        self.tabWidget.addTab(tab, key)
        self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(tab))
        self.tabWidget_central.setCurrentIndex(self.tabWidget_central.indexOf(self.tab_layouts))
        tabInstances += 1

    def closeEvent(self, event):
        self.settings.setValue('window size', self.size())
        self.settings.setValue('window position', self.pos())

    def rename_object(self, index):
        text, okPressed = QtWidgets.QInputDialog.getText(self, "Rename Object", "New Name:", QtWidgets.QLineEdit.Normal, "")
        if okPressed and text != '':
            self.tabWidget.setTabText(index, text)



    def connectSignalsSlots(self):
        for key in self.dict_layouts.keys():
            self.dict_layouts[key]['Menu Action'].triggered.connect(partial(self.create_layoutTab, key))
        self.tabWidget.tabBarDoubleClicked.connect(self.rename_object)
        self.tabWidget.tabCloseRequested.connect(partial(popup_closeTabConfirmation,self))
        self.action_parentChildren.triggered.connect(partial(popup_ParentChildrenTree, self))
        # self.action_parentChildren.triggered.connect(popup_ParentChildrenTree(self))
