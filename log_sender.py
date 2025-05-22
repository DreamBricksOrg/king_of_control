import csv
import time
import requests
import parameters
from datetime import datetime
import threading


class LogSender:
    csv_filename = 'logs/datalogs.csv'
    backup_filename = 'logs/datalogs_backup.csv'

    def __init__(self, log_api, project_id, upload_delay=120):
        self.project_id = project_id
        self.log_api = log_api
        self.upload_delay = upload_delay
        self._init_csv(self.csv_filename)
        self._init_csv(self.backup_filename)

        threading.Thread(target=self._process_csv_and_send_logs, daemon=True).start()

    @staticmethod
    def _init_csv(filename):
        try:
            with open(filename, mode='x', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['status', 'project', 'additional', 'timePlayed'])
        except FileExistsError:
            pass

    def log(self, status, additional=''):
        time_played = datetime.now()
        formatted_time_played = time_played.strftime("%Y-%m-%dT%H:%M:%SZ")

        project = self.project_id
        time_played = formatted_time_played

        with open(self.csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([status, project, additional, time_played])
        print(f"{time_played} - {status} - salvo com sucesso!")

    def _send_log(self, status, project, additional, time_played):
        url = self.log_api + "/datalog/upload"
        timestamp = datetime.now()
        data = {
            'status': status,
            'project': project,
            'additional': additional,
            'timePlayed': time_played
        }

        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print(f'{timestamp} - Requisição bem-sucedida')
                return True
            else:
                print(f'{timestamp} -  Falha na requisição:', response.status_code)
                return False
        except requests.exceptions.ConnectionError:
            print(f'{timestamp} - Falha na conexão: Não foi possível conectar ao servidor')
            return False

    def _process_csv_and_send_logs(self):
        while True:
            rows_to_keep = []
            rows_to_backup = []

            with open(self.csv_filename, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    success = self._send_log(row['status'], row['project'], row['additional'], row['timePlayed'])
                    if success:
                        rows_to_backup.append(row)
                    else:
                        rows_to_keep.append(row)

            with open(self.csv_filename, mode='w', newline='') as file:
                fieldnames = ['status', 'project', 'additional', 'timePlayed']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows_to_keep)

            with open(self.backup_filename, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writerows(rows_to_backup)

            print("Sending logs")

            time.sleep(self.upload_delay)


if __name__ == "__main__":
    import parameters as param
    log_sender = LogSender(param.LOG_API, param.LOG_PROJECT_ID, 5)
    log_sender.log("CTA")
    time.sleep(10)