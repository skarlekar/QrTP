import base64
import hashlib
import time
import click
import os

def getData(input):
    data = b''
    for line in input:
        line = line.rstrip()
        decodedLine = base64.b64decode(line, validate=True)
        data += decodedLine
    return data

def reconstructFileFromData(input):
    inputFileName = input.name
    data = getData(input)
    baseFileName= os.path.basename(inputFileName)
    fileDir = os.path.dirname(inputFileName)
    reconstructedFileName = os.path.join(fileDir, 'reconstructed-' + baseFileName.replace('.chunks',''))
    reconstructedFile = open(reconstructedFileName, 'wb')
    reconstructedFile.write(data)
    return data, reconstructedFileName

def getHash(data):
    dataStr = str(data)
    encodedStr = dataStr.encode()
    hash = hashlib.sha1(encodedStr)
    hexDigest = hash.hexdigest()
    return hexDigest

@click.group()
def cli():
    pass

@cli.command()
@click.option('--input', '-i', required=True, type=click.File('r'))
def decode_file(input):
    fileName = input.name
    print("Reading from file: {}".format(fileName))
    data, reconstructedFileName = reconstructFileFromData(input)
    print("Reconstructed file {} from chunks".format(reconstructedFileName))
    hexDigest = getHash(data)
    print('Hash of reconstructed data is: {}'.format(hexDigest))

if __name__ == '__main__':
    cli()
