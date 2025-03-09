import sys
import socket
import iso8583
from iso8583.specs import default_ascii as spec
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit

class PaymentTerminalClient(QWidget):
    def init(self):
        super().init()
        self.setWindowTitle('Payment Terminal Client')
        self.setGeometry(100, 100, 400, 300)

        # GUI элементы
        self.layout = QVBoxLayout()
        self.label_card = QLabel("Card Number:")
        self.card_input = QLineEdit(self)
        self.label_amount = QLabel("Amount:")
        self.amount_input = QLineEdit(self)
        self.send_button = QPushButton("Send Request", self)
        self.response_text = QTextEdit(self)
        self.response_text.setReadOnly(True)

        # Добавляем виджеты в layout
        self.layout.addWidget(self.label_card)
        self.layout.addWidget(self.card_input)
        self.layout.addWidget(self.label_amount)
        self.layout.addWidget(self.amount_input)
        self.layout.addWidget(self.send_button)
        self.layout.addWidget(self.response_text)
        self.setLayout(self.layout)

        # Связываем кнопку с функцией
        self.send_button.clicked.connect(self.send_payment_request)

    def send_payment_request(self):
        card_number = self.card_input.text()
        amount = self.amount_input.text()

        if not card_number or not amount:
            self.response_text.setText("Please enter both card number and amount.")
            return

        self.send_button.setEnabled(False)

        try:
            # Подготовка данных для отправки
            amount = str(int(float(amount) * 100)).zfill(12)  # Преобразование в формат ISO8583
            decoded = {
                "t": "0200",
                "2": card_number,  # Номер карты
                "3": "000000",     # Код обработки (покупка)
                "4": amount,       # Сумма
                "7": "1215123456", # Дата и время передачи
                "11": "123456",    # Системный контрольный номер
                "41": "T1234567",  # Номер терминала
                "42": "M12345678901234",  # Идентификатор мерчанта
            }
            encoded_raw, _ = iso8583.encode(decoded, spec)

            # Отправляем данные серверу
            response = self.send_to_server(encoded_raw)
            if response:
                decoded_response, _ = iso8583.decode(response, spec)
                if decoded_response.get("39") == "00":
                    self.response_text.setText("Payment successful.")
                    self.response_text.setStyleSheet("color: green")
                else:
                    self.response_text.setText(f"Error: {decoded_response.get('39')}")
                    self.response_text.setStyleSheet("color: red")
        except Exception as e:
            self.response_text.setText(f"Error: {str(e)}")
        finally:
            self.card_input.clear()
            self.amount_input.clear()
            self.send_button.setEnabled(True)

    def send_to_server(self, message):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', 12345))
            client_socket.send(message)
            response = client_socket.recv(1024)
            client_socket.close()
            return response
        except Exception as e:
            self.response_text.setText(f"Connection error: {str(e)}")
            return None

if name == "main":
    app = QApplication(sys.argv)
    client = PaymentTerminalClient()
    client.show()
    sys.exit(app.exec_())