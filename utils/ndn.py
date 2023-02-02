import asyncio
from random import choice, expovariate
from common.zipf import zipf_distribution as zipf
from pyndn import Name
from pyndn.security import KeyChain
from pyndn.transport.tcp_transport import TcpTransport
from pyndn.face import Face
from pyndn.util.blob import Blob


class Consumer:
    def __init__(self):
        self.face = Face(TcpTransport(), TcpTransport.ConnectionInfo("127.0.0.1"))
        self.keyChain = KeyChain()
        self.face.setCommandSigningInfo(self.keyChain, self.keyChain.getDefaultCertificateName())
        self.zipf_gen = zipf(0.8, 1000)
        self.run()

    async def sendInterest(self):
        while True:
            # Generate a random content name based on the Zipf distribution
            content_name = Name("/example/content/").appendNumber(choice(range(1000)))
            # Send an Interest for the content
            self.face.expressInterest(content_name, self.onData, self.onTimeout)
            # Wait for a random interval before sending the next Interest
            await asyncio.sleep(expovariate(1.0 / 60))

    def onData(self, interest, data):
        print("Received Data: ", data.getContent)


def onTimeout(self, interest):
    print("Timeout")


def run(self):
    asyncio.get_event_loop().create_task(self.sendInterest())
    self.face.processEvents()


class Producer:
    def __init__(self):
        self.face = Face(TcpTransport(), TcpTransport.ConnectionInfo("127.0.0.1"))
        self.keyChain = KeyChain()
        self.face.setCommandSigningInfo(self.keyChain, self.keyChain.getDefaultCertificateName())
        self.face.registerPrefix(Name("/example/content"), self.onInterest)
        self.face.processEvents()

    async def onInterest(self, prefix, interest, transport, registeredPrefixId):
        # Extract the content name from the Interest
        content_name = interest.getName()
        # Wait for a random time before sending back the Data packet
        await asyncio.sleep(expovariate(1.0 / 2))
        # Send back the Data packet
        data = self.face.makeData(content_name)
        data.setContent(Blob(content_name.toUri()))
        self.keyChain.sign(data)
        self.face.putData(data)


if __name__ == "__main__":
    Consumer()
    Producer()
