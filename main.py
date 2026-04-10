import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from database import init_database
from forms import LoginForm, MainForm


class Application:

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        self.app.setStyleSheet(self.apply_styles())
        self.current_window = None

    def apply_styles(self):
        return """
        QWidget {
            background: #1a1a2e;
            color: #e0e0e0;
            font: 12px 'Segoe UI'
        }
        QPushButton {
            background: #5DBCD2;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
            min-height: 35px
        }
        QPushButton:hover {
            background: #4A9FB5
        }
        QLineEdit {
            background: #2d2d4a;
            color: #e0e0e0;
            border: 1px solid #4a4a6a;
            border-radius: 4px;
            padding: 6px;
            min-height: 32px
        }
        QLineEdit:focus { 
            border: 2px solid #5DBCD2;
            background: #353555
        }
        QTableWidget {
            background: #252540;
            color: #e0e0e0;
            border: 1px solid #4a4a6a;
            border-radius: 4px
        }
        QTabWidget::pane {
            border: 1px solid #4a4a6a;
            border-radius: 4px;
            background: #252540
        }
        QTabBar::tab:selected {
            background: #5DBCD2;
            color: white
        }
        QMenuBar {
            background: #252540;
            color: #e0e0e0
        }
        QMenu {
            background: #252540;
            color: #e0e0e0
        }
        QStatusBar {
            background: #252540;
            color: #aaa
        }
        """

    def show_login(self):
        login_form = LoginForm()
        if login_form.exec_() != LoginForm.Accepted:
            sys.exit(0)

        user = login_form.get_user()
        if not user:
            sys.exit(0)

        self.show_main(user)

    def show_main(self, user):
        self.current_window = MainForm(user)
        self.current_window.exit_requested.connect(self.on_exit_requested)
        self.current_window.show()

    def on_exit_requested(self):
        if self.current_window:
            self.current_window.close()
            self.current_window = None
        self.show_login()

    def run(self):
        if not init_database():
            print("Ошибка подключения к базе данных!")
            sys.exit(1)

        self.show_login()
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = Application()
    app.run()