from PyQt5.QtWidgets import (
    QDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QComboBox, QHeaderView, QMenuBar, QMenu,
    QAction, QStatusBar, QTabWidget, QFormLayout, QDialogButtonBox,
    QGroupBox, QGridLayout, QStackedWidget
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from database import (
    get_user_by_login, verify_password, reset_failed_attempts,
    get_all_users, create_user, update_user,
    get_all_customers, get_order_cost_calculation,
    increment_failed_attempts, check_login_exists,
    get_all_roles
)
from datetime import datetime, timedelta
import os
import random

class CaptchaWidget(QWidget):
    verified = pyqtSignal(bool)
    failed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_order = [0, 1, 2, 3]
        self.attempts = 0
        self.max_attempts = 3
        self.first_click = None
        self._init_ui()
        self._shuffle_and_load_images()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        info = QLabel("Соберите изображение в правильном порядке:")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("font-weight: bold; color: #2e7d32;")
        layout.addWidget(info)

        self.grid_layout = QGridLayout()
        self.piece_buttons = []

        for i in range(4):
            btn = QPushButton(f"{i+1}")
            btn.setFixedSize(140, 90)
            btn.clicked.connect(lambda checked, idx=i: self._on_piece_click(idx))
            self.piece_buttons.append(btn)
            self.grid_layout.addWidget(btn, i // 2, i % 2)

        layout.addLayout(self.grid_layout)

        btn_layout = QHBoxLayout()
        self.verify_btn = QPushButton("Проверить")
        self.verify_btn.clicked.connect(self._verify)
        btn_layout.addWidget(self.verify_btn)

        cancel_btn = QPushButton("Назад ко входу")
        cancel_btn.clicked.connect(lambda: self.verified.emit(False))
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _shuffle_and_load_images(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.current_order = [0, 1, 2, 3]
        random.shuffle(self.current_order)

        for i, btn in enumerate(self.piece_buttons):
            img_index = self.current_order[i] + 1
            img_path = os.path.join(script_dir, f"{img_index}.png")

            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                if not pixmap.isNull():
                    btn.setIcon(QIcon(pixmap))
                    btn.setIconSize(QSize(130, 80))
                    btn.setText("")
            else:
                btn.setText(f"Фрагмент {i+1}")

    def _on_piece_click(self, index):
        if self.first_click is None:
            self.first_click = index
            self.piece_buttons[index].setStyleSheet("border: 3px solid #5DBCD2;")
            return

        if self.first_click == index:
            self.piece_buttons[index].setStyleSheet("")
            self.first_click = None
            return

        second_click = index
        btn1 = self.piece_buttons[self.first_click]
        btn2 = self.piece_buttons[second_click]

        icon1 = btn1.icon()
        icon2 = btn2.icon()

        btn1.setIcon(icon2)
        btn2.setIcon(icon1)
        btn1.setStyleSheet("")
        btn2.setStyleSheet("")

        self.current_order[self.first_click], self.current_order[second_click] = \
            self.current_order[second_click], self.current_order[self.first_click]

        self.first_click = None

    def _verify(self):
        if self.current_order == [0, 1, 2, 3]:
            self.verified.emit(True)
        else:
            self.attempts += 1
            self.failed.emit()

            if self.attempts >= self.max_attempts:
                QMessageBox.critical(
                    self, "Превышено попыток",
                    "Превышено количество попыток!\n\nОбратитесь к администратору."
                )
                self.verified.emit(False)
            else:
                QMessageBox.warning(
                    self, "Неверно",
                    f"Неверная сборка!\n\nОсталось попыток: {self.max_attempts - self.attempts}"
                )
                self._shuffle_and_load_images()

    def reset(self):
        self.attempts = 0
        self.first_click = None
        self._shuffle_and_load_images()

class RegisterWidget(QWidget):
    registered = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Регистрация нового пользователя")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2e7d32;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Молочный комбинат 'Полесье'")
        subtitle.setStyleSheet("font-size: 11px; color: #666;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        layout.addWidget(QLabel("Логин:"))
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Придумайте логин (минимум 3 символа)")
        self.login_input.setMinimumHeight(32)
        layout.addWidget(self.login_input)

        layout.addWidget(QLabel("Пароль:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Придумайте пароль (минимум 6 символов)")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(32)
        layout.addWidget(self.password_input)

        layout.addWidget(QLabel("Подтвердите пароль:"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Повторите пароль")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setMinimumHeight(32)
        layout.addWidget(self.confirm_input)

        layout.addSpacing(5)

        self.register_btn = QPushButton("Зарегистрироваться")
        self.register_btn.setMinimumHeight(38)
        self.register_btn.clicked.connect(self._register)
        layout.addWidget(self.register_btn)

        cancel_btn = QPushButton("Назад ко входу")
        cancel_btn.setMinimumHeight(32)
        cancel_btn.clicked.connect(lambda: self.registered.emit(False))
        layout.addWidget(cancel_btn)

        self.setLayout(layout)

    def _register(self):
        """Обработка регистрации нового пользователя"""
        login = self.login_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not login or not password or not confirm:
            QMessageBox.warning(
                self, "Ошибка ввода",
                "Все поля обязательны для заполнения!\n\nПожалуйста, заполните логин и пароль."
            )
            return

        if len(login) < 3:
            QMessageBox.warning(
                self, "Ошибка",
                f"Логин должен содержать минимум 3 символа!\n\nТекущая длина: {len(login)} символов."
            )
            return

        if len(password) < 6:
            QMessageBox.warning(
                self, "Ошибка",
                f"Пароль должен содержать минимум 6 символов!\n\nТекущая длина: {len(password)} символов."
            )
            return

        if password != confirm:
            QMessageBox.warning(
                self, "Ошибка",
                "Пароли не совпадают!\n\nПожалуйста, проверьте правильность ввода."
            )
            self.confirm_input.clear()
            self.confirm_input.setFocus()
            return

        existing_user = get_user_by_login(login)
        if existing_user:
            QMessageBox.critical(
                self, "Ошибка",
                "Пользователь с таким логином уже существует!\n\nПожалуйста, выберите другой логин."
            )
            self.login_input.setFocus()
            return

        # ✅ ПОЛУЧАЕМ ID РОЛИ ИЗ БД
        roles = get_all_roles()
        user_role_id = 1  # По умолчанию
        for role_id, role_name in roles:
            if role_name == "Пользователь":
                user_role_id = role_id
                break

        print(f"📝 Регистрация: login={login}, role_id={user_role_id}")

        if create_user(login, password, user_role_id):  # ✅ ПЕРЕДАЁМ role_id (число)
            QMessageBox.information(
                self, "Успешная регистрация",
                f"Пользователь '{login}' успешно зарегистрирован!\n\nТеперь вы можете войти в систему."
            )
            self.registered.emit(True)
        else:
            QMessageBox.critical(
                self, "Ошибка",
                "Не удалось зарегистрировать пользователя!\n\nПопробуйте позже или обратитесь к администратору."
            )

    def clear_fields(self):
        self.login_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()

class LoginForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход - Молочный комбинат 'Полесье'")
        self.setFixedSize(450, 550)
        self.setModal(True)
        self.current_user = None
        self.attempts = 0
        self._temp_user = None
        self._set_window_icon()
        self._init_ui()

    def _set_window_icon(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "image/ich", "image/iconka.png")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(30, 30, 30, 30)

        logo_label = QLabel()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "image/ich", "image/iconka.png")

        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(300, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("Молочный комбинат 'Полесье'")
            logo_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #5DBCD2;")

        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        layout.addSpacing(10)

        subtitle = QLabel("Авторизация в системе")
        subtitle.setStyleSheet("font-size: 14px; color: #666;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        self.stacked_widget = QStackedWidget()

        self.login_widget = self._create_login_widget()
        self.stacked_widget.addWidget(self.login_widget)

        self.captcha_widget = CaptchaWidget()
        self.captcha_widget.verified.connect(self._on_captcha_verified)
        self.captcha_widget.failed.connect(self._on_captcha_failed)
        self.stacked_widget.addWidget(self.captcha_widget)

        self.register_widget = RegisterWidget()
        self.register_widget.registered.connect(self._on_registered)
        self.stacked_widget.addWidget(self.register_widget)

        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def _create_login_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Логин:"))
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")
        self.login_input.setMinimumHeight(35)
        layout.addWidget(self.login_input)

        layout.addWidget(QLabel("Пароль:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(35)
        layout.addWidget(self.password_input)

        layout.addSpacing(15)

        self.login_btn = QPushButton("Войти")
        self.login_btn.setMinimumHeight(42)
        self.login_btn.clicked.connect(self._try_login)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #5DBCD2;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4A9FB5;
            }
            QPushButton:pressed {
                background-color: #3D8A9F;
            }
        """)
        layout.addWidget(self.login_btn)

        register_btn = QPushButton("Регистрация")
        register_btn.setMinimumHeight(38)
        register_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #7AC5CD;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #6AB5C0;
            }
        """)
        layout.addWidget(register_btn)

        widget.setLayout(layout)
        return widget

    def _try_login(self):
        login = self.login_input.text().strip()
        password = self.password_input.text()

        if not login or not password:
            QMessageBox.warning(
                self, "Ошибка ввода",
                "Поля Логин и Пароль обязательны для заполнения!\n\nПожалуйста, заполните все поля."
            )
            return

        user = get_user_by_login(login)

        if not user:
            self._failed("Вы ввели неверный логин или пароль. Пожалуйста проверьте ещё раз введенные данные")
            return

        if user['is_locked']:
            if user['locked_until'] and datetime.now() < user['locked_until']:
                QMessageBox.critical(
                    self, "Аккаунт заблокирован",
                    "Вы заблокированы.\n\nОбратитесь к администратору."
                )
                return
            else:
                reset_failed_attempts(user['user_id'])

        if not verify_password(password, user['password']):
            self._failed("Вы ввели неверный логин или пароль. Пожалуйста проверьте ещё раз введенные данные")
            return

        self.stacked_widget.setCurrentIndex(1)
        self.captcha_widget.reset()
        self._temp_user = user

    def _on_captcha_verified(self, success):
        if success:
            reset_failed_attempts(self._temp_user['user_id'])
            self.current_user = self._temp_user

            QMessageBox.information(
                self, "Успешная авторизация",
                "Вы успешно авторизовались."
            )
            self.accept()
        else:
            self.stacked_widget.setCurrentIndex(0)

    def _on_captcha_failed(self):
        if self._temp_user:
            attempts = increment_failed_attempts(self._temp_user['user_id'])
            if attempts >= 3:
                QMessageBox.critical(
                    self, "Аккаунт заблокирован",
                    "Вы заблокированы.\n\nОбратитесь к администратору."
                )
                self.stacked_widget.setCurrentIndex(0)

    def _on_registered(self, success):
        if success:
            self.stacked_widget.setCurrentIndex(0)
            self.register_widget.clear_fields()
        else:
            self.stacked_widget.setCurrentIndex(0)

    def _failed(self, message):
        self.attempts += 1

        user = get_user_by_login(self.login_input.text().strip())
        if user:
            attempts = increment_failed_attempts(user['user_id'])
            if attempts >= 3:
                QMessageBox.critical(
                    self, "Превышено попыток",
                    "Вы заблокированы.\n\nОбратитесь к администратору."
                )
                return

        QMessageBox.warning(self, "Ошибка", message)
        self.password_input.clear()
        self.login_input.setFocus()

    def get_user(self):
        return self.current_user

class UserManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_users()

    def _init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Управление пользователями")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #5DBCD2;")
        layout.addWidget(title)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["ID", "Логин", "Роль", "Попытки", "Статус"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setAlternatingRowColors(True)

        self.users_table.setStyleSheet("""
            QTableWidget {
                background-color: #f5f5f5;
                color: #212121;
                gridline-color: #dddddd;
                selection-background-color: #5DBCD2;
                selection-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #5DBCD2;
                color: white;
            }
            QHeaderView::section {
                background-color: #5DBCD2;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.users_table)

        self.no_users_label = QLabel("В базе данных нет пользователей")
        self.no_users_label.setStyleSheet("color: #ffa500; font-size: 14px; padding: 10px;")
        self.no_users_label.setAlignment(Qt.AlignCenter)
        self.no_users_label.setVisible(False)
        layout.addWidget(self.no_users_label)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self._add_user)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Изменить")
        edit_btn.clicked.connect(self._edit_user)
        btn_layout.addWidget(edit_btn)

        unlock_btn = QPushButton("Разблокировать")
        unlock_btn.clicked.connect(self._unlock_user)
        btn_layout.addWidget(unlock_btn)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._load_users)
        btn_layout.addWidget(refresh_btn)

        for btn in [add_btn, edit_btn, unlock_btn, refresh_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #5DBCD2;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4A9FB5;
                }
            """)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_users(self):
        try:
            users = get_all_users()

            print(f"Загрузка пользователей: найдено {len(users)} записей")

            if not users:
                self.users_table.setRowCount(0)
                self.no_users_label.setVisible(True)
                return

            self.no_users_label.setVisible(False)
            self.users_table.setRowCount(len(users))

            for row, user in enumerate(users):
                user_id = str(user[0]) if user[0] is not None else ""
                login = str(user[1]) if user[1] is not None else ""
                role = str(user[2]) if user[2] is not None else ""
                attempts = str(user[3]) if user[3] is not None else "0"
                is_locked = bool(user[4]) if user[4] is not None else False

                self.users_table.setItem(row, 0, QTableWidgetItem(user_id))
                self.users_table.setItem(row, 1, QTableWidgetItem(login))
                self.users_table.setItem(row, 2, QTableWidgetItem(role))
                self.users_table.setItem(row, 3, QTableWidgetItem(attempts))

                if is_locked:
                    status = "Заблокирован"
                    color = Qt.red
                else:
                    status = "Активен"
                    color = Qt.green

                status_item = QTableWidgetItem(status)
                status_item.setForeground(color)
                self.users_table.setItem(row, 4, status_item)

            print(f"Успешно загружено {len(users)} пользователей в таблицу")

        except Exception as e:
            print(f"Ошибка загрузки пользователей: {e}")
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить пользователей!\n\nОшибка: {e}"
            )

    def _add_user(self):
        dialog = UserEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            login, password, role = dialog.get_data()

            if not login or not password:
                QMessageBox.warning(self, "Ошибка", "Логин и пароль обязательны!")
                return

            if len(login) < 3:
                QMessageBox.warning(self, "Ошибка", "Логин минимум 3 символа!")
                return

            if len(password) < 6:
                QMessageBox.warning(self, "Ошибка", "Пароль минимум 6 символов!")
                return

            if check_login_exists(login):
                QMessageBox.critical(
                    self, "Ошибка",
                    "Пользователь с таким логином уже существует!\n\nПожалуйста, выберите другой логин."
                )
                return

            if create_user(login, password, role):
                QMessageBox.information(self, "Успех", f"Пользователь '{login}' добавлен!")
                self._load_users()
            else:
                QMessageBox.critical(self, "Ошибка", "Пользователь с таким логином уже существует!")

    def _edit_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя!")
            return

        user_id = int(self.users_table.item(row, 0).text())
        current_login = self.users_table.item(row, 1).text()
        current_role = self.users_table.item(row, 2).text()

        dialog = UserEditDialog(self, current_login, current_role, user_id)
        if dialog.exec_() == QDialog.Accepted:
            login, password, role = dialog.get_data()

            if login != current_login and check_login_exists(login, user_id):
                QMessageBox.critical(
                    self, "Ошибка",
                    "Пользователь с таким логином уже существует!\n\nПожалуйста, выберите другой логин."
                )
                return

            if update_user(user_id, login, role, False):
                QMessageBox.information(self, "Успех", "Данные обновлены!")
                self._load_users()

    def _unlock_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя!")
            return

        user_id = int(self.users_table.item(row, 0).text())
        status = self.users_table.item(row, 4).text()

        if "Заблокирован" not in status:
            QMessageBox.warning(
                self, "Ошибка",
                "Этот пользователь не заблокирован!"
            )
            return

        if update_user(user_id, "", "", False):
            QMessageBox.information(self, "Успех", "Блокировка снята!")
            self._load_users()


class UserEditDialog(QDialog):
    def __init__(self, parent=None, login="", role_name="", user_id=None):
        super().__init__(parent)
        self.is_edit = bool(login)
        self.user_id = user_id
        self.role_map = {}  # Связь название -> ID
        self.setWindowTitle("✏️ Редактирование" if self.is_edit else "➕ Добавление")
        self.setModal(True)
        self._init_ui(login, role_name)

    def _init_ui(self, login, role_name):
        layout = QFormLayout()
        layout.setSpacing(8)

        self.login_input = QLineEdit(login)
        self.login_input.setPlaceholderText("Введите логин")
        layout.addRow("Логин:", self.login_input)

        if not self.is_edit:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            self.password_input.setPlaceholderText("Минимум 6 символов")
            layout.addRow("Пароль:", self.password_input)
        self.role_combo = QComboBox()
        roles = get_all_roles()
        for role_id, role_name_db in roles:
            self.role_combo.addItem(role_name_db)
            self.role_map[role_name_db] = role_id

        if role_name:
            index = self.role_combo.findText(role_name)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)

        layout.addRow("Роль:", self.role_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("""
            QPushButton {
                background-color: #5DBCD2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4A9FB5;
            }
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_data(self):
        login = self.login_input.text().strip()
        password = ""
        if hasattr(self, 'password_input'):
            password = self.password_input.text()

        selected_role_name = self.role_combo.currentText()
        role_id = self.role_map.get(selected_role_name)

        return login, password, role_id

class AdminPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход для администратора")
        self.setFixedSize(350, 180)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Введите пароль администратора")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #5DBCD2;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        hint = QLabel("Для доступа к управлению пользователями")
        hint.setStyleSheet("font-size: 11px; color: #aaa;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        layout.addSpacing(10)

        layout.addWidget(QLabel("Пароль:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setMinimumHeight(35)
        self.password_input.returnPressed.connect(self._verify_password)
        layout.addWidget(self.password_input)

        layout.addSpacing(10)

        btn_layout = QHBoxLayout()

        ok_btn = QPushButton("Войти")
        ok_btn.setMinimumHeight(35)
        ok_btn.clicked.connect(self._verify_password)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a6a;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a5a7a;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _verify_password(self):
        password = self.password_input.text()

        if password == "admin123":
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Неверный пароль",
                "Введён неверный пароль!\n\nПожалуйста, попробуйте ещё раз."
            )
            self.password_input.clear()
            self.password_input.setFocus()

class MainForm(QMainWindow):
    exit_requested = pyqtSignal()  # ✅ Сигнал для выхода

    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.setWindowTitle("🏭 Молочный комбинат 'Полесье' - Система управления")
        self.setMinimumSize(1024, 768)
        self.resize(1200, 800)
        self._set_window_icon()

        role = user.get('role', '') or user.get('Role', '')
        if isinstance(role, bytes):
            try:
                role = role.decode('utf-8')
            except:
                role = str(role)
        self.is_admin = role.strip().lower() in ['администратор', 'administrator', 'admin', 'админ']

        self._init_ui()

    def _set_window_icon(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "image/ich", "image/iconka.png")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _init_ui(self):
        central = QTabWidget()
        central.setObjectName("main_tabs")
        self.setCentralWidget(central)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        header_layout = QHBoxLayout()
        logo_label = QLabel("🏭")
        logo_label.setStyleSheet("font-size: 48px;")
        header_layout.addWidget(logo_label)

        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(10, 0, 0, 0)

        title = QLabel("МОЛОЧНЫЙ КОМБИНАТ 'ПОЛЕСЬЕ'")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #5DBCD2;")
        title_layout.addWidget(title)

        subtitle = QLabel("Система управления производством")
        subtitle.setStyleSheet("font-size: 14px; color: #aaa;")
        title_layout.addWidget(subtitle)

        header_layout.addWidget(title_widget)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        main_layout.addSpacing(20)

        login = self.current_user.get('login', 'Пользователь')
        if isinstance(login, bytes):
            try:
                login = login.decode('utf-8')
            except:
                login = str(login)

        role = self.current_user.get('role', 'Пользователь')
        if isinstance(role, bytes):
            try:
                role = role.decode('utf-8')
            except:
                role = str(role)

        welcome_group = QGroupBox("Информация о пользователе")
        welcome_layout = QGridLayout(welcome_group)

        welcome_layout.addWidget(QLabel("Пользователь:"), 0, 0)
        welcome_layout.addWidget(QLabel(f"<b>{login}</b>"), 0, 1)

        welcome_layout.addWidget(QLabel("Роль:"), 1, 0)
        welcome_layout.addWidget(QLabel(f"<b>{role}</b>"), 1, 1)

        welcome_layout.addWidget(QLabel("Дата и время входа:"), 2, 0)
        welcome_layout.addWidget(QLabel(f"<b>{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</b>"), 2, 1)

        main_layout.addWidget(welcome_group)

        info_layout = QHBoxLayout()

        system_group = QGroupBox("О системе")
        system_layout = QVBoxLayout(system_group)
        system_info = QLabel(
            "Система автоматизации молочного комбината\n"
            "• Учёт продукции и материалов\n"
            "• Управление заказами\n"
            "• Расчёт себестоимости\n"
            "• Контроль производства"
        )
        system_info.setWordWrap(True)
        system_info.setStyleSheet("padding: 10px; line-height: 1.6;")
        system_layout.addWidget(system_info)
        info_layout.addWidget(system_group)

        features_group = QGroupBox("Возможности")
        features_layout = QVBoxLayout(features_group)
        features_text = QLabel(
            "✓ Авторизация и безопасность\n"
            "✓ Управление пользователями\n"
            "✓ База заказчиков\n"
            "✓ Учёт заказов\n"
            "✓ Автоматический расчёт"
        )
        features_text.setWordWrap(True)
        features_text.setStyleSheet("padding: 10px; line-height: 1.6;")
        features_layout.addWidget(features_text)
        info_layout.addWidget(features_group)

        main_layout.addLayout(info_layout)

        quick_access_group = QGroupBox("Быстрый доступ")
        quick_layout = QHBoxLayout(quick_access_group)

        btn_customers = QPushButton("Заказчики")
        btn_customers.clicked.connect(lambda: central.setCurrentIndex(1 if self.is_admin else 0))
        quick_layout.addWidget(btn_customers)

        btn_orders = QPushButton("Заказы")
        btn_orders.clicked.connect(lambda: central.setCurrentIndex(2 if self.is_admin else 1))
        quick_layout.addWidget(btn_orders)

        if not self.is_admin:
            btn_admin = QPushButton("Администратор")
            btn_admin.setStyleSheet("""
                QPushButton {
                    background-color: #7AC5CD;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #6AB5C0;
                }
            """)
            btn_admin.clicked.connect(self._show_admin_login)
            quick_layout.addWidget(btn_admin)

        main_layout.addWidget(quick_access_group)

        main_layout.addStretch()

        footer = QLabel("© 20026 Молочный комбинат 'Полесье'. Все права защищены (возможно).")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #666; padding: 10px;")
        main_layout.addWidget(footer)

        central.addTab(main_widget, "Главная")

        if self.is_admin:
            print("ДОБАВЛЯЕМ ВКЛАДКУ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ")
            user_mgmt = UserManagementWidget()
            central.addTab(user_mgmt, "Пользователи")

        customers_widget = self._create_customers_widget()
        central.addTab(customers_widget, "Заказчики")

        orders_widget = self._create_orders_widget()
        central.addTab(orders_widget, "Заказы")

        self._create_menu()

        self.statusBar().showMessage(
            f"{login} | {role}"
        )

    def _create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("📁 Файл")

        exit_action = QAction("Выход из учётной записи", self)
        exit_action.triggered.connect(self._on_exit_requested)
        file_menu.addAction(exit_action)

        file_menu.addSeparator()

        quit_action = QAction("Закрыть приложение", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    def _on_exit_requested(self):
        reply = QMessageBox.question(
            self,
            "Выход из системы",
            "Вы действительно хотите выйти из учётной записи?\n\n"
            "Приложение будет возвращено к форме входа.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.exit_requested.emit()

    def _create_customers_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("Заказчики")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #5DBCD2;")
        layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Код", "Наименование", "ИНН", "Адрес", "Телефон", "Тип"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)

        table.setStyleSheet("""
            QTableWidget {
                background-color: #f5f5f5;
                color: #212121;
                gridline-color: #dddddd;
                selection-background-color: #5DBCD2;
                selection-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #5DBCD2;
                color: white;
            }
            QHeaderView::section {
                background-color: #5DBCD2;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        try:
            customers = get_all_customers()
            table.setRowCount(len(customers))

            for row, cust in enumerate(customers):
                table.setItem(row, 0, QTableWidgetItem(str(cust[0])))
                table.setItem(row, 1, QTableWidgetItem(cust[1] if cust[1] else "  "))
                table.setItem(row, 2, QTableWidgetItem(cust[2] if cust[2] else "  "))
                table.setItem(row, 3, QTableWidgetItem(cust[3] if cust[3] else "  "))
                table.setItem(row, 4, QTableWidgetItem(cust[4] if cust[4] else "  "))

                cust_type = ""
                if cust[5] and cust[6]:
                    cust_type = "Поставщик и Покупатель"
                elif cust[5]:
                    cust_type = "Поставщик"
                elif cust[6]:
                    cust_type = "Покупатель"

                table.setItem(row, 5, QTableWidgetItem(cust_type))
        except Exception as e:
            print(f"Ошибка загрузки заказчиков: {e}")
            error_label = QLabel(f"Ошибка загрузки данных: {e}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)

        layout.addWidget(table)
        return widget

    def _create_orders_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("Расчёт стоимости заказов")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #5DBCD2;")
        layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "№ заказа", "Дата", "Заказчик", "Продукция",
            "Кол-во", "Цена", "Сумма", "Себестоимость", "Прибыль"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)

        table.setStyleSheet("""
            QTableWidget {
                background-color: #f5f5f5;
                color: #212121;
                gridline-color: #dddddd;
                selection-background-color: #5DBCD2;
                selection-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #5DBCD2;
                color: white;
            }
            QHeaderView::section {
                background-color: #5DBCD2;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        try:
            orders = get_order_cost_calculation()
            table.setRowCount(len(orders))

            for row, order in enumerate(orders):
                table.setItem(row, 0, QTableWidgetItem(str(order[0] if order[0] else "  ")))
                table.setItem(row, 1, QTableWidgetItem(str(order[1] if order[1] else "  ")))
                table.setItem(row, 2, QTableWidgetItem(order[2] if order[2] else "  "))
                table.setItem(row, 3, QTableWidgetItem(order[4] if order[4] else "  "))
                table.setItem(row, 4, QTableWidgetItem(str(order[5] if order[5] else "  ")))
                table.setItem(row, 5, QTableWidgetItem(str(order[6] if order[6] else "  ")))
                table.setItem(row, 6, QTableWidgetItem(str(order[7] if order[7] else "  ")))

                cost = round(order[9], 2) if order[9] else 0
                table.setItem(row, 7, QTableWidgetItem(str(cost)))

                profit = round(order[10], 2) if order[10] else 0
                table.setItem(row, 8, QTableWidgetItem(str(profit)))
        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")
            error_label = QLabel(f"Ошибка загрузки данных: {e}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)

        layout.addWidget(table)
        return widget

    def _show_admin_login(self):
        dialog = AdminPasswordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self._add_user_management_tab()

    def _add_user_management_tab(self):
        central = self.centralWidget()

        for i in range(central.count()):
            if central.tabText(i) == "Пользователи":
                central.setCurrentIndex(i)
                QMessageBox.information(
                    self,
                    "Доступ предоставлен",
                    "Вкладка управления пользователями уже открыта!"
                )
                return

        user_mgmt = UserManagementWidget()
        central.addTab(user_mgmt, "Пользователи")

        central.setCurrentIndex(central.count() - 1)

        menubar = self.menuBar()
        users_menu = menubar.addMenu("Пользователи")
        manage_action = QAction("Управление", self)
        manage_action.triggered.connect(self._show_user_management)
        users_menu.addAction(manage_action)

        QMessageBox.information(
            self,
            "Успешный вход",
            "Доступ к управлению пользователями предоставлен!\n\nТеперь вам доступна вкладка 'Пользователи'."
        )

    def _show_user_management(self):
        central = self.centralWidget()
        for i in range(central.count()):
            if central.tabText(i) == "Пользователи":
                central.setCurrentIndex(i)
                return

    def _show_about(self):
        QMessageBox.about(
            self, "О программе",
            "Молочный комбинат 'Полесье'\n\n"
            "Система управления производством\n\n"
            "Версия 1.0\n"
            "© 2025"
        )