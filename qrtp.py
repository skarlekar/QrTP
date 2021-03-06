#!/usr/bin/env python

import base64
import hashlib
import time

import click
import cv2 as cv
import numpy
import pyqrcode
from pyzbar.pyzbar import decode

MESSAGE_BEGIN = '-----BEGIN MESSAGE-----'
MESSAGE_END = '-----END MESSAGE-----'
HEADER_BEGIN = '-----BEGIN HEADER-----'
HEADER_END = '-----END HEADER-----'


class QrSend(object):
    # Split the data into to equal sizes
    data = None
    raw = None

    def __init__(self, size=30, data=None):
        self.size = size
        self.raw = data
        self.data = self._chunks(data, self.size)

    def _chunks(self, l, size=None):
        n = size if size else self.size
        n = max(1, n)
        if l is None:
            data_length = 0
        else:
            data_length = len(l)
        return [l[i:i + n] for i in range(0, data_length, n)]

    def _headers(self):
        dataStr = str(self.raw)
        encodedStr = dataStr.encode()
        hash = hashlib.sha1(encodedStr)
        hexDigest = hash.hexdigest()
        #print('hexDigest:' + hexDigest)
        return [
            MESSAGE_BEGIN,
            HEADER_BEGIN,
            'LEN:{0}'.format(len(self.data)),
            'HASH:{0}'.format(hexDigest),
            HEADER_END
        ]

    def _printqr(self, payload):
        #print(payload)
        data = pyqrcode.create(payload)
        print(data.terminal(quiet_zone=1))

    def send(self):
        if not self.data:
            raise Exception('No Data to Send')
        for header in self._headers():
            self._printqr(header)
            time.sleep(0.2)
        counter = 0
        print("No. of parts:" + str(len(self.data)))
        for part in self.data:
            payload = '{0:010d}:{1}'.format(counter, base64.b64encode(part).decode())
            self._printqr(payload)
            counter += 1
            dataLen = len(self.data)
            print('{0}/{1}'.format(counter, len(self.data)))
            time.sleep(0.2)
        self._printqr(MESSAGE_END)

    def sample_size(self, size=None):
        message = "QrTP Rocks!"
        test_size = size if size else self.size
        #data = pyqrcode.create('{0}'.format('A' * (test_size + 10)))
        data = pyqrcode.create('{0}'.format(message))
        print(data.terminal())


class QrReceive(object):
    window_name = 'Preview'
    data = b''
    start = False

    length = None
    hash = None
    position = 0
    received_iterations = []

    def __init__(self):
        cv.namedWindow(self.window_name, cv.WINDOW_AUTOSIZE)
        self.capture = cv.VideoCapture(0)
        if not self.capture.isOpened():
             print("Cannot open camera")
             exit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.capture = None

    def process_frames(self):

        while True:
            ret,frame = self.capture.read()
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break

            imgray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            decodedObjects = decode(imgray)


            # Process the frames
            for object in decodedObjects:
                if not self.process_symbol(object):
                    return

            # Update the preview window
            cv.imshow(self.window_name, frame)
            cv.waitKey(5)

    def process_symbol(self, symbol):
        payload = symbol.data.decode()
        print('Payload: {}'.format(payload))
        if payload == MESSAGE_BEGIN:
            print("found message begin")
            self.start = True
            return True

        if payload == HEADER_BEGIN:
            print("found header begin")
            return True

        if 'LEN' in payload:
            print("found LEN")
            self.length = payload.split(':')[1]
            click.secho('[*] The message will come in {0} parts'.format(self.length), fg='green')
            return True

        if 'HASH' in payload:
            print("found HASH")
            self.hash = payload.split(':')[1]
            click.secho('[*] The message has hash: {0}'.format(self.hash), fg='green')
            return True

        if payload == HEADER_END:
            if not self.length or not self.hash:
                raise Exception('Header read failed. No lengh or hash data.')
            return True

        if not self.start:
            raise Exception('Received message without proper Message Start Header')

        # Cleanup On Message End
        if payload == MESSAGE_END:
            # integrity check!
            print("Starting final integrity check")
            strData = str(self.data)
            encodedStrData = strData.encode()
            final_hash = hashlib.sha1(encodedStrData).hexdigest()
            print("Final hash is: {}".format(final_hash))

            if final_hash != self.hash:
                click.secho('[*] Warning! Hashcheck failed!', fg='red')
                click.secho('[*] Expected: {0}, got: {1}'.format(self.hash, final_hash), fg='red', bold=True)
            else:
                click.secho('[*] Data checksum check passed.', fg='green')
            cv.destroyWindow(self.window_name)
            return False

        iteration, data = int(payload.split(':')[0]), base64.b64decode(payload.split(':')[1], validate=True)
        print("Base64Encoded Data is {}".format(data))

        if iteration in self.received_iterations:
            return True
        else:
            self.received_iterations.append(iteration)

        if self.position != iteration:
            click.secho(
                '[*] Position lost! Transfer will fail! Expected {0} but got {1}'.format(self.position,
                                                                                         iteration), fg='red')
            self.position = iteration

        self.position += 1
        self.data = self.data + data

        click.secho('[*] {0}:{1}'.format(iteration, data), fg='green', bold=True)

        return True


@click.group()
def cli():
    pass


@cli.command()
@click.option('--size', '-s', default=30, help='Set the size to preview a QR code with.')
def preview(size):
    qr = QrSend()
    qr.sample_size(size=size)


@cli.command()
@click.option('--input', '-i', required=True, type=click.File('rb'))
@click.option('--size', '-s', default=30)
def send(input, size):
    qr = QrSend(data=input.read(), size=size)
    qr.send()


@cli.command()
@click.option('--destination', '-d', required=True, type=click.File('wb'))
def receive(destination):
    while True:

        try:
            click.secho('[*] Starting Video Capture', fg='green')

            with QrReceive() as qr:
                qr.process_frames()

            destination.write(qr.data)
            click.secho('Wrote received data to: {0}\n\n'.format(destination.name))

        except Exception as e:
            click.secho('[*] An exception occured: {0}'.format(e), fg='red')

        time.sleep(2)


if __name__ == '__main__':
    cli()
