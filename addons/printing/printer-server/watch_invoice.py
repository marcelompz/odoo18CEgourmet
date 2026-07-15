import os
import time

from printer import send_print_job


def watch_invoice():
    while True:
        if os.path.isfile('invoice.png'):
            print('printing invoice')
            send_print_job('DeskJet_2700', 'invoice.png')
        time.sleep(2)


if __name__ == '__main__':
    watch_invoice()
