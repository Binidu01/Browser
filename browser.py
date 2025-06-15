import sys
import os
import re
import requests
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtGui import QIcon

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.block_list = [
            ".*google-analytics.*",
            ".*doubleclick.*",
            ".*facebook.*",
            ".*track.*",
            ".*banner.*",
            ".*[?&]ad=[^&]+", 
            ".*youtube.com/ptracking.*",
            ".*youtube.com/api/stats/ads.*",
            ".*youtube.com/pagead.*",
            ".*adservice.google.*",
            ".*googlesyndication.*"
        ]
        self.load_easylist()

    def load_easylist(self):
        block_list_url = "https://easylist.to/easylist/easylist.txt"
        try:
            response = requests.get(block_list_url, timeout=10)
            if response.status_code == 200:
                rules = response.text.splitlines()
                for line in rules:
                    if line.startswith("||") and "^" in line:
                        domain = line.split("^")[0].replace("||", "")
                        pattern = ".*" + re.escape(domain) + ".*"
                        self.block_list.append(pattern)
        except Exception as e:
            print("Failed to load EasyList:", e)

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        for pattern in self.block_list:
            if re.search(pattern, url, re.IGNORECASE):
                info.block(True)
                return
        info.block(False)

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up ad blocker
        interceptor = AdBlocker()
        profile = QWebEngineProfile.defaultProfile()
        profile.setUrlRequestInterceptor(interceptor)

        # Create a navigation bar (top bar)
        navbar = QToolBar()
        navbar.setIconSize(QSize(20, 20))
        navbar.setMovable(False)
        navbar.setStyleSheet("""
            QToolBar {
                border: none;
                padding: 0 5px;
            }
            QToolButton {
                background: transparent;
                border: none;
                margin: 0 2px;
            }
            QToolButton:hover {
                background:rgb(126, 128, 129);
                border-radius: 4px;
            }
        """)

        # Back button
        back_btn = QAction(QIcon(resource_path("icons/arrow.png")), "Back", self)
        back_btn.triggered.connect(lambda: self.current_tab().back())
        navbar.addAction(back_btn)

        # Forward button
        forward_btn = QAction(QIcon(resource_path("icons/right-arrow.png")), "Forward", self)
        forward_btn.triggered.connect(lambda: self.current_tab().forward())
        navbar.addAction(forward_btn)

        # Reload button
        reload_btn = QAction(QIcon(resource_path("icons/reload.png")), "Reload", self)
        reload_btn.triggered.connect(lambda: self.current_tab().reload())
        navbar.addAction(reload_btn)

        # Home button
        home_btn = QAction(QIcon(resource_path("icons/home.png")), "Home", self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        # Address bar
        self.url_bar = QLineEdit()
        self.url_bar.setFixedHeight(28)
        self.url_bar.setStyleSheet("""
            QLineEdit {
                background: #fff;
                color: #000;
                border: 1px solid #dcdcdc;
                border-radius: 14px;
                padding-left: 10px;
                padding-right: 10px;
            }
            QLineEdit:focus {
                border: 1px solid #8ab4f8;
            }
        """)
        self.url_bar.setPlaceholderText("Search or enter address")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        # Create tab widget (tab bar)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)

        # New tab button
        new_tab_btn = QPushButton(QIcon(resource_path("icons/add.png")), "", self)
        new_tab_btn.clicked.connect(lambda: self.add_new_tab(QUrl("https://www.google.com")))

        # Adding new tab button to the corner as a widget
        self.tabs.setCornerWidget(new_tab_btn)

        # Layout arrangement: Navigation bar at the top, Tab bar below it
        layout = QVBoxLayout()
        layout.addWidget(navbar)  # Navigation bar is now at the top
        layout.addWidget(self.tabs)  # Tab bar is below the navigation bar

        # Main widget to hold layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setWindowTitle("New Tab")
        self.showMaximized()

        # Open the first tab
        self.add_new_tab(QUrl("https://www.google.com"))

    def add_new_tab(self, qurl=None):
        if qurl is None:
            qurl = QUrl("https://www.google.com")
        browser = QWebEngineView()
        browser.setUrl(qurl)

        # Update tab text and window title on page title change
        browser.titleChanged.connect(lambda title, br=browser: self.update_tab_title(br, title))

        # Add to tab widget
        i = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(i)

        # Update URL bar on URL change
        browser.urlChanged.connect(lambda url, br=browser: self.update_urlbar(br, url))
        return browser

    def update_tab_title(self, browser, title):
        index = self.tabs.indexOf(browser)
        if index != -1:
            self.tabs.setTabText(index, title if title else "New Tab")
        if self.current_tab() == browser:
            self.setWindowTitle(title if title else "New Tab")

    def current_tab(self):
        return self.tabs.currentWidget()

    def close_tab(self, index):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(index)

    def current_tab_changed(self, index):
        browser = self.current_tab()
        if browser:
            self.url_bar.setText(browser.url().toString())
            self.setWindowTitle(browser.title() if browser.title() else "New Tab")

    def navigate_home(self):
        self.current_tab().setUrl(QUrl("https://www.google.com"))

    def navigate_to_url(self):
        url = self.url_bar.text().strip()
        if not url.startswith("http"):
            if "." not in url:
                url = "https://www.google.com/search?q=" + url
            else:
                url = "http://" + url
        self.current_tab().setUrl(QUrl(url))

    def update_urlbar(self, browser, url):
        if self.current_tab() == browser:
            self.url_bar.setText(url.toString())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("PyQt5 Browser")
    window = Browser()
    sys.exit(app.exec_())
