import threading
import time
import socket
import iso8583
from iso8583.specs import default_ascii as spec

# Настройки теста
NUM_THREADS = 50  # Количество потоков (одновременных клиентов)
REQUESTS_PER_THREAD = 5  # Количество запросов от каждого клиента
SERVER_HOST = 'localhost'
SERVER_PORT = 12345

def test_client(thread_id):
    """Функция для отправки запросов в тестовом клиенте"""
    for i in range(REQUESTS_PER_THREAD):
        try:
            # Данные запроса
            card_number = f"1234567890123456"
            amount = str(10000).zfill(12)
            pin_code = "1234".ljust(16, '0')

            # Формирование ISO8583 сообщения
            decoded = {
                "t": "0200",
                "2": card_number,
                "3": "000000",
                "4": amount,
                "7": "1215123456",
                "11": f"{thread_id:06}",
                "41": "T1234567",
                "42": "M12345678901234",
                "52": pin_code,
            }
            encoded_raw, _ = iso8583.encode(decoded, spec)

            # Отправка сообщения на сервер
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            client_socket.send(encoded_raw)

            # Получение ответа
            response = client_socket.recv(1024)
            decoded_response, _ = iso8583.decode(response, spec)
            response_code = decoded_response.get("39")

            if response_code == "00":
                print(f"[Поток {thread_id}] Успех: Код ответа 00")
            else:
                print(f"[Поток {thread_id}] Ошибка: Код ответа {response_code}")

            client_socket.close()
        except Exception as e:
            print(f"[Поток {thread_id}] Ошибка: {str(e)}")


if __name__ == "__main__":
    threads = []
    start_time = time.time()

    # Создание и запуск потоков
    for thread_id in range(NUM_THREADS):
        thread = threading.Thread(target=test_client, args=(thread_id,))
        threads.append(thread)
        thread.start()

    # Ожидание завершения всех потоков
    for thread in threads:
        thread.join()

    end_time = time.time()
    print(f"Тест завершён. Всего запросов: {NUM_THREADS * REQUESTS_PER_THREAD}")
    print(f"Общее время: {end_time - start_time:.2f} секунд")
    print(f"Средняя производительность: {NUM_THREADS * REQUESTS_PER_THREAD / (end_time - start_time):.2f} запросов в секунду")
