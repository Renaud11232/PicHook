import logging
import sys
import json
import threading
import os
import random
import pause
from datetime import datetime
from croniter import croniter
from discord import Webhook, RequestsWebhookAdapter, File


class PicHook:

    def __init__(self, config):
        self.__init_logger()
        self.__load_config(config)
        self.__list_lock = threading.Lock()
        self.__restore_sent_files()
        self.__found_files = set()
        self.__remaining_files = set()

    def __init_logger(self):
        self.__logger = logging.getLogger("PicHook")
        self.__logger.setLevel(logging.INFO)
        stdout_handler = logging.StreamHandler(sys.stdout)
        log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stdout_handler.setFormatter(log_format)
        self.__logger.addHandler(stdout_handler)

    def __restore_sent_files(self):
        self.__sent_files = set()
        try:
            with open(self.__history, "r") as history:
                self.__logger.info("Restoring sent files list fron history file...")
                hist = json.load(history)
                for file in hist["history"]:
                    self.__sent_files.add(file)
                self.__logger.info("Sent files list restored, %d files sent" % len(self.__sent_files))
        except EnvironmentError:
            self.__logger.warning("Not restoring the sent files list")

    def __load_config(self, config):
        self.__logger.info("Loading configuration file...")
        with open(config, "r") as config_file:
            config = json.load(config_file)
            self.__cron = config["cron"]
            self.__directories = config["directories"]
            self.__hook = Webhook.from_url(config["hook_url"], adapter=RequestsWebhookAdapter())
            self.__extensions = config["extensions"]
            self.__history = config["history"]
            self.__logger.info("Config loaded")

    def scan_files(self):
        self.__list_lock.acquire()
        self.__scan_files()
        self.__list_lock.release()

    def __scan_files(self):
        self.__logger.info("Scanning for files...")
        self.__found_files.clear()
        for directory in self.__directories:
            for root, _, filenames in os.walk(directory):
                for file in filenames:
                    if file.lower().endswith(tuple(self.__extensions)):
                        self.__found_files.add(os.path.join(root, file))
        self.__logger.info("Scan is done, found %d files" % len(self.__found_files))
        self.__logger.info("Updating sent files list")
        old_sent_list = self.__sent_files
        self.__sent_files = set()
        for file in old_sent_list:
            if file in self.__found_files:
                self.__sent_files.add(file)
        self.__logger.info("Done updating sent files list, %d files sent" % len(self.__sent_files))
        self.__logger.info("Updating remaining files list")
        self.__remaining_files = set()
        for file in self.__found_files:
            if file not in self.__sent_files:
                self.__remaining_files.add(file)
        self.__logger.info("Done updating remaining files list, %d files remaining", len(self.__remaining_files))

    def reset_sent_files(self):
        self.__list_lock.acquire()
        self.__reset_sent_files()
        self.__list_lock.release()

    def __reset_sent_files(self):
        self.__logger.info("Resetting the list of sent files")
        self.__remaining_files = self.__sent_files
        self.__sent_files = set()
        self.__logger.info("Reset done")

    def send_file(self):
        self.__list_lock.acquire()
        self.__send_file()
        self.__list_lock.release()

    def __send_file(self):
        file_sent = False
        while not file_sent:
            if len(self.__remaining_files) == 0:
                self.__reset_sent_files()
            if len(self.__remaining_files) == 0:
                self.__logger.info("No file to send...")
                return
            file = random.sample(self.__remaining_files, 1)[0]
            self.__remaining_files.remove(file)
            self.__logger.info("Sending file...")
            try:
                self.__hook.send(file=File(file))
                self.__logger.info("Sent %s" % file)
                self.__sent_files.add(file)
                file_sent = True
            except EnvironmentError:
                self.__logger.warning("Failed to send %s, trying another file..." % file)

    def save_sent_files(self):
        self.__logger.info("Saving sent files...")
        history = dict(
            history=list(self.__sent_files)
        )
        with open(self.__history, "w") as hist:
            json.dump(history, hist)
        self.__logger.info("Saved...")

    def run(self):
        self.scan_files()
        cron = croniter(self.__cron, datetime.now())
        try:
            while True:
                next_execution = cron.get_next(datetime)
                self.__logger.info("Waiting until %s", next_execution.strftime("%d/%m/%Y, %H:%M:%S"))
                pause.until(next_execution)
                self.send_file()
        except KeyboardInterrupt:
            self.save_sent_files()
            self.__logger.info("Goodbye...")
