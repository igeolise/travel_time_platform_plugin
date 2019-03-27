import os
import webbrowser
from qgis.PyQt.QtCore import Qt, QSettings, QDateTime
from qgis.PyQt.QtWidgets import QDialog, QDateTimeEdit, QWidget
from qgis.PyQt import uic

from qgis.core import QgsMessageLog

from processing.gui.wrappers import WidgetWrapper

from . import auth
from .utils import tr


class ConfigDialog(QDialog):

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui', 'ConfigDialog.ui'), self)

        self.getKeyButton.pressed.connect(self.get_key)
        self.countResetButton.pressed.connect(self.reset_count)
        self.buttonBox.accepted.connect(self.accept)

    def showEvent(self, *args, **kwargs):
        super().showEvent(*args, **kwargs)

        # Get the current keys
        app_id, api_key = auth.get_app_id_and_api_key()

        self.appIDLineEdit.setText(app_id)
        self.apiKeyLineEdit.setText(api_key)

        # Get the settings
        s = QSettings()
        # warning enabled
        self.warningGroupBox.setChecked(s.value('travel_time_platform/warning_enabled', True, type=bool))
        # warning limit
        self.warningSpinBox.setValue(s.value('travel_time_platform/warning_limit', 10, type=int))
        # current count
        self.refresh_count_display()
        # logs calls
        self.logCallsCheckBox.setChecked(s.value('travel_time_platform/log_calls', False, type=bool))

    def get_key(self):
        webbrowser.open('http://docs.traveltimeplatform.com/overview/getting-keys/')

    def reset_count(self):
        QSettings().setValue('travel_time_platform/current_count', 0)
        self.refresh_count_display()

    def refresh_count_display(self):
        c = QSettings().value('travel_time_platform/current_count', 0, type=int)
        self.countSpinBox.setValue(c)

    def accept(self, *args, **kwargs):
        # Save keys
        auth.set_app_id_and_api_key(self.appIDLineEdit.text(), self.apiKeyLineEdit.text())

        # Save settings
        s = QSettings()
        # warning enabled
        s.setValue('travel_time_platform/warning_enabled', self.warningGroupBox.isChecked())
        # warning limit
        s.setValue('travel_time_platform/warning_limit', self.warningSpinBox.value())
        # logs calls
        s.setValue('travel_time_platform/log_calls', self.logCallsCheckBox.isChecked())

        super().accept(*args, **kwargs)


class SplashScreen(QDialog):

    def __init__(self, main):
        super().__init__(main.iface.mainWindow())
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui', 'SplashScreen.ui'), self)

        # self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.main = main

        # Load html files
        help_dir = os.path.join(os.path.dirname(__file__), 'help')

        html_path = os.path.join(help_dir, '{tab}.{locale}.html')
        locale = QSettings().value('locale/userLocale')[0:2]

        css_path = os.path.join(help_dir, 'help.css')
        css = open(css_path).read()

        for tab_key, tab_name in [('about', tr('About')), ('apikey', tr('API key')), ('start', tr('Getting started')),
                                  ('tm_simplified', tr('TimeMap - Simplified')), ('tm_advanced', tr('TimeMap - Advanced')),
                                  ('issues', tr('Report issues'))]:

            path = html_path.format(tab=tab_key, locale=locale)
            if not os.path.isfile(path):
                path = html_path.format(tab=tab_key, locale='en')

            body = open(path, 'r').read()
            html = '<html><head><style>{css}</style></head><body>{body}</body></html>'.format(css=css, body=body)
            page = HelpWidget(self.main, html)

            self.tabWidget.addTab(page, tab_name)

        self.buttonBox.accepted.connect(self.accept)

    def showEvent(self, *args, **kwargs):
        super().showEvent(*args, **kwargs)

        # Get the settings
        s = QSettings()
        # warning enabled
        self.dontShowAgainCheckBox.setChecked(s.value('travel_time_platform/spashscreen_dontshowagain', False, type=bool))

    def accept(self, *args, **kwargs):
        # Save settings
        s = QSettings()
        # warning enabled
        s.setValue('travel_time_platform/spashscreen_dontshowagain', self.dontShowAgainCheckBox.isChecked())
        super().accept(*args, **kwargs)


class HelpWidget(QWidget):

    def __init__(self, main, html, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'ui', 'HelpContent.ui'), self)

        self.main = main
        self.htmlWidget.anchorClicked.connect(self.open_link)
        self.htmlWidget.setText(html)
        self.htmlWidget.setSearchPaths(help_dir)

    def open_link(self, url):

        # self.main.splash_screen.hide()

        if url.url() == '#show_config':
            self.main.show_config()
        elif url.url() == '#show_toolbox':
            self.main.show_toolbox()
        elif url.url()[0:4] == 'http':
            webbrowser.open(url.url())
        else:
            QgsMessageLog.logMessage('Unknown url : {}'.format(url.url()), 'TimeTravelPlatform')


class IsoDateTimeWidgetWrapper(WidgetWrapper):

    def createWidget(self):
        dateEdit = QDateTimeEdit(QDateTime.currentDateTimeUtc())
        dateEdit.setDisplayFormat("yyyy-MM-dd HH:mm")
        dateEdit.setTimeSpec(Qt.TimeZone)
        return dateEdit

    def setValue(self, value):
        return self.widget.setDateTime(QDateTime().fromString(value, Qt.ISODate))

    def value(self):
        return self.widget.dateTime().toString(Qt.ISODate)
