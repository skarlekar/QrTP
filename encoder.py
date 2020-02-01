import base64
import hashlib
import time
import click

#data = b''
#chunks=[]
#fileName = ''

def getChunks(mydata, chunkSize=20):
    dataLen = len(mydata)
    return [mydata[i:i + chunkSize] for i in range(0, dataLen, chunkSize)]

def writeChunks(chunks, fileName):
    chunksFileName = fileName + '.chunks'
    chunksFile = open(chunksFileName, 'w')
    for c in chunks:
        #print("Raw chunk is:[{}]".format(c))
        payload = base64.b64encode(c).decode()
        #print("Payload is:[{}]".format(payload))
        #print("Length of payload is: {}".format(len(payload)))
        #chunksFile.write(payload)
        print(payload, file=chunksFile)
    print("Written chunks to file: {}".format(chunksFileName))

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
@click.option('--input', '-i', required=True, type=click.File('rb'))
@click.option('--size', '-s', default=20)
def encode_file(input, size):
    fileName = input.name
    print("Reading from file: {}".format(fileName))
    data=input.read()
    chunks = getChunks(data, size)
    print('No. of chunks:{}'.format(len(chunks)))

    writeChunks(chunks,fileName)

    hexDigestChunks = getHash(chunks)
    print('Hash of chunks is: {}'.format(hexDigestChunks))

    hexDigest = getHash(data)
    print('Hash of data is: {}'.format(hexDigest))

if __name__ == '__main__':
    cli()
