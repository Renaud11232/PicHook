import argparse
import signal
import platform
from pichook.hook import PicHook


def main():
    parser = argparse.ArgumentParser(description="Starts the PicHook")
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    pic_hook = PicHook(args.config)
    if platform.system() == "Linux":
        signal.signal(signal.SIGHUP, lambda signum, frame: pic_hook.scan_files())
        signal.signal(signal.SIGUSR1, lambda signum, frame: pic_hook.send_file())
        signal.signal(signal.SIGUSR2, lambda signum, frame: pic_hook.reset_sent_files())
        signal.signal(signal.SIGTERM, lambda signum, frame: pic_hook.quit())
        signal.signal(signal.SIGINT, lambda signum, frame: pic_hook.quit())
    pic_hook.run()
