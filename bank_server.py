import socket
import threading
import iso8583
import sqlite3
from datetime import datetime
from iso8583.specs import default_ascii as spec


# Функция для записи транзакции в базу данных
def log_transaction(card_number, amount, status):
    try:
        conn = sqlite3.connect('transactions.db')
        cursor = conn.cursor()

        # Записываем транзакцию в таблицу
        cursor.execute("""
            INSERT INTO transactions_new_pin (card_number, amount, timestamp, status)
            VALUES (?, ?, ?, ?)
        """, (card_number, amount, datetime.now(), status))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")


# Функция для обработки каждого клиента
def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")
    try:
        # Получаем данные от клиента
        data = client_socket.recv(1024)
        if not data:
            return

        decoded, _ = iso8583.decode(data, spec)
        print(f"Received message from {client_address}: {decoded}")

        # Извлекаем данные из сообщения
        card_number = decoded.get("2", "")
        amount = int(decoded.get("4", "0")) / 100  # Сумма в рублях
        terminal_id = decoded.get("41", "")
        merchant_id = decoded.get("42", "")
        pin_code = decoded.get("52", "")  # Пин-код из сообщения

        print(f"Pin Code from Client: {pin_code}")  # Пин-код, полученный от клиента

        # Проверяем данные карты и пин-кода в базе
        conn = sqlite3.connect(r'C:\Users\Sam\PycharmProjects\FlaskTerminal(ISO)\transactions.db')
        cursor = conn.cursor()

        cursor.execute("SELECT balance, pin_code FROM cards_new_pin WHERE card_number = ?", (card_number,))
        result = cursor.fetchone()

        if not result:
            # Карта не найдена
            response_status = "14"
        else:
            balance, db_pin_code = result
            print(f"Pin Code from DB: {db_pin_code}")  # Пин-код, извлеченный из базы данных

            # Сравниваем пин-коды (убедимся, что они строки и одинаковые)
            if pin_code != db_pin_code:
                response_status = "55"  # Неверный пин-код
            elif balance < amount:
                # Недостаточно средств
                response_status = "51"
            else:
                # Успешная транзакция
                response_status = "00"
                new_balance = balance - amount
                cursor.execute("UPDATE cards_new_pin SET balance = ? WHERE card_number = ?", (new_balance, card_number))
                conn.commit()

        conn.close()

        # Записываем транзакцию в базу
        log_transaction(card_number, amount, response_status)

        # Формируем ответ
        response = {
            "t": "0210",
            "39": response_status,
            "41": terminal_id,
            "42": merchant_id,
        }
        encoded_raw, _ = iso8583.encode(response, spec)
        client_socket.send(encoded_raw)

        print(f"Sent response to {client_address}: {response}")
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"Connection with {client_address} closed.")


# Функция для запуска сервера
def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}...")

    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()


# Запуск сервера
if __name__ == "__main__":
    start_server('localhost', 12345)
