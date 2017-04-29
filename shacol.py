# !/usr/bin/env python

import sys
import redis
import random
import timeit
import psutil
import hashlib
import pybloof
import argparse
import binascii
import cuckoofilter


class Shacol(object):
    def __init__(self, bits, inputFile, hashGroup=False, text=False, first=False, bloom=False, memory=False):
        self.bits = int(bits)
        self.inputFile = inputFile
        self.hashGroup = hashGroup
        self.text = text
        self.first = first
        self.bloom = bloom
        self.memory = memory

        self.bestTime = sys.maxsize
        self.hashPartLength = int(int(self.bits) / 4)
        self.shaList = []
        self.hashPart = str()

        if '.txt' in str(inputFile):
            with open(self.inputFile, 'r', encoding='utf-8') as dataFromFile:
                if self.hashGroup:
                    if self.text:
                        for textInFile in dataFromFile:
                            self.shaList.append(
                                hashlib.sha256(textInFile.encode('utf-8').hexdigest()[0:self.hashPartLength]))
                    else:
                        for hashInFile in dataFromFile:
                            self.shaList.append(hashInFile[0:self.hashPartLength])
                else:
                    if self.text:
                        self.hashPart = hashlib.sha256(dataFromFile.read().encode('utf-8')).hexdigest()[
                                        0:self.hashPartLength]
                    else:
                        self.hashPart = dataFromFile.readline()[0:self.hashPartLength]
            dataFromFile.close()
        elif inputFile:
            self.hashPart = hashlib.sha256(inputFile.encode('utf-8')).hexdigest()[
                                        0:self.hashPartLength]



    def getInfo(self):
        printHashes = str()
        for i in self.shaList:
            printHashes += i + '\t'
        # print absolute path to input file
        print('\nYou are trying to find a collision with %s hash for %db with SHA-2.\n' %
              ('first' if self.first else 'arbitary', self.bits) +
              'Using %s as input file with %s.' %
              (self.inputFile,
               'one hash inside' if not self.hashGroup else 'with one hash per line inside.') +
              '\nInput %s %s' % ('hash is  '
                                 if not self.hashGroup else 'hashes are ',
                                 self.hashPart if not self.hashGroup else printHashes))

    def changeBitLength(self, newBitLength):
        self.bits = newBitLength
        self.hashPartLength = int(int(self.bits) / 4)


    def findCollisionStr(self, hashPart=None):
        """
        Function with the best performance - storing hashes in SET by STRING

        :param hashPart: the input hash loaded from a file
        """
        try:
            if not hashPart:
                hashPart = self.hashPart
                hashPartLength = self.hashPartLength
            else:
                hashPartLength = len(hashPart)

            if '.txt' not in str(self.inputFile):
                inputString = self.inputFile
            else:
                inputString = ''

            status = 1
            strHashSet = {str()} # length start with 1
            newHashPart = hashPart

            start = timeit.default_timer()

            while newHashPart not in strHashSet:
                strHashSet.add(newHashPart)
                status += 1
                if status == 10000000:
                    print('\n' * 100)
                    print('SET length:', len(strHashSet))
                    print('Run time:', round((timeit.default_timer() - start) / 60, 3), 'minutes')
                    status = 0
                lastTemp = newHashPart
                newHash = hashlib.sha256(newHashPart.encode('utf-8')).hexdigest()
                newHashPart = newHash[0:hashPartLength]

            stop = timeit.default_timer()

            totalTime = round(stop - start, 12)
            totalMemory = round(sys.getsizeof(strHashSet) / 1024 / 1024, 3)
            indexOfFirst = 0
            firstCollision = ''
            indexOfLast = len(strHashSet)
            lastCollision = newHashPart
            newHashPart = hashPart

            print('\n\n##### findCollisionStr - Collision found process succeeded! #####\n')
            if inputString:
                print('Input string:', inputString)
            print('Input hashPart:', hashPart)
            print("Collision found after %s seconds" % (totalTime))
            print('Collision hash:', lastCollision)

            while newHashPart != lastCollision:
                indexOfFirst += 1
                firstTemp = newHashPart
                newHash = hashlib.sha256(newHashPart.encode('utf-8')).hexdigest()
                newHashPart = newHash[0:hashPartLength]

            print('Index of first collision:', indexOfFirst)
            print('Index of last collision:', indexOfLast)
            print('Cycles between collision hashes:', indexOfLast-indexOfFirst)
            print('Hash 1 before collision:', firstTemp)
            print('Hash 2 before collision:', lastTemp)
            print('\nSet string structure used', round(sys.getsizeof(strHashSet) / 1024 / 1024, 3), 'MB')
            del strHashSet

            return {"inputString": inputString, "inputHash": hashPart, "time": totalTime,"indexOfFirst": indexOfFirst,
                "indexOfLast": indexOfLast, "collisionHash": newHashPart, "cyclesBetCol": indexOfLast-indexOfFirst,
                "firstTemp": firstTemp, "lastTemp": lastTemp, "dataStructConsum": totalMemory}

        except Exception as e:
            print(str(e))

    def findCollisionInt(self, hashPart=None):
        """
        The most effective versions of storing hash - INT in SET

        :param hashPart: the input hash loaded from a file
        """
        try:
            if not hashPart:
                hashPart = self.hashPart
                hashPartLength = self.hashPartLength
            else:
                hashPartLength = len(hashPart)

            if '.txt' not in str(self.inputFile):
                inputString = self.inputFile
            else:
                inputString = ''

            status = 1
            intHashSet = {int()}
            newHashPart = int(binascii.hexlify(bytes(hashPart, 'utf-8')), 16)

            start = timeit.default_timer()

            while newHashPart not in intHashSet:
                intHashSet.add(newHashPart)
                status += 1
                if status == 10000000:
                    print('\n' * 100)
                    print('Set length:', len(intHashSet))
                    print('Run time:', round((timeit.default_timer() - start) / 60, 3), 'minutes')
                    status = 0
                strHashPart = binascii.unhexlify(hex(newHashPart)[2:])
                lastTemp = strHashPart.decode('utf-8')
                newHash = hashlib.sha256(strHashPart).hexdigest()
                newHash = newHash[0:hashPartLength]
                newHashPart = int(binascii.hexlify(bytes(newHash, 'utf-8')), 16)

            stop = timeit.default_timer()
            totalTime = round(stop - start, 12)
            totalMemory = round(sys.getsizeof(intHashSet) / 1024 / 1024, 3)
            indexOfFirst = 0
            firstCollision = ''
            indexOfLast = len(intHashSet)
            lastCollision = newHash
            newHashPart = hashPart

            print('\n\n##### findCollisionInt - Collision found process succeeded! #####\n')
            if inputString:
                print('Input string:', inputString)
            print('Input hashPart:', hashPart)
            print("Collision found after %s seconds" % (totalTime))
            print('Collision hash:', lastCollision)

            while newHashPart != lastCollision:
                indexOfFirst += 1
                firstTemp = newHashPart
                newHash = hashlib.sha256(newHashPart.encode('utf-8')).hexdigest()
                newHashPart = newHash[0:hashPartLength]

            print('Index of first collision:', indexOfFirst)
            print('Index of last collision:', indexOfLast)
            print('Cycles between collision hashes:', indexOfLast-indexOfFirst)
            print('Hash 1 before collision:', firstTemp)
            print('Hash 2 before collision:', lastTemp)

            print('\nSet int structure used', round(sys.getsizeof(intHashSet) / 1024 / 1024, 3), 'MB')
            del intHashSet

            return {"inputString": inputString, "inputHash": hashPart, "time": totalTime,"indexOfFirst": indexOfFirst,
                "indexOfLast": indexOfLast, "collisionHash": lastCollision, "cyclesBetCol": indexOfLast-indexOfFirst,
                "firstTemp": firstTemp, "lastTemp": lastTemp, "dataStructConsum": totalMemory}

        except Exception as e:
            print(str(e))

    def findBestHash(self, maxSet=100000000, memoryCheck=False):
        """
        Function provides the best possible input string with the least time consumption.
        Offers memory check in intervals.
        """
        try:
            memOver = False
            hashPartLength = self.hashPartLength
            charStr = 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/!@#$%&?'
            bestTime = sys.maxsize
            random.seed()

            while True:
                rndStr = ''
                intHashSet = {int()}
                charLen = random.randint(1, 64)
                for number in range(charLen):
                    rndStr += ''.join(random.sample(charStr, 1))
                print('\nGenerate new string input: ', rndStr, '\n')

                firstHash = hashlib.sha256(rndStr.encode('utf-8')).hexdigest()
                firstHashPart = firstHash[0:hashPartLength]
                newHashPart = int(binascii.hexlify(bytes(firstHashPart, 'utf-8')), 16)

                print('Finding collision started')
                start = timeit.default_timer()
                while newHashPart not in intHashSet:
                    if memoryCheck:
                        virtualMem = psutil.virtual_memory().available
                        if virtualMem < 134217728:
                            print('\n!!! Memory capacity reached !!! Set count:', len(intHashSet))
                            memOver = True
                            break
                    else:
                        if len(intHashSet) >= maxSet:
                            print('\n--- Stated limit reached --- Set count:', len(intHashSet))
                            memOver = True
                            break

                    intHashSet.add(newHashPart)
                    strHashPart = binascii.unhexlify(hex(newHashPart)[2:])
                    newHash = hashlib.sha256(strHashPart).hexdigest()
                    newHash = newHash[0:hashPartLength]
                    newHashPart = int(binascii.hexlify(bytes(newHash, 'utf-8')), 16)

                stop = timeit.default_timer()
                totalTime = round(stop - start, 10)
                totalMemory = round(sys.getsizeof(intHashSet) / 1048576, 3)
                cycles = len(intHashSet) + 1

                if not memOver:
                    print('\n##### Collision found process succeeded! #####')
                    print('Input string:', rndStr)
                    print('Input hash:', firstHash)
                    print('Input hash part:', firstHashPart)
                    print("Collision found after %s seconds" % (totalTime))
                    if (totalTime < bestTime): bestTime = totalTime
                    print('Count of the cycles:', cycles)
                    print('Collision hash:', newHash)
                    index = 0
                    for intHash in intHashSet:
                        index += 1
                        if intHash == newHashPart:
                            print('Index of collision hash:', index)
                            break
                    print('Cycles between collision hashes:', cycles-index)
                    print('Set int structure used', totalMemory, 'MB')
                    print('\nThe best time yet:', bestTime)
                else:
                    memOver = False

                del intHashSet
                print('SET was emptied successfully')

        except Exception as e:
            print(str(e))

    def findCollisionFirst(self, hashPart=None):
        """
        Function to be thread by individually calling - looking for a collision with first hashPart
        """
        try:
            if not hashPart:
                hashPart = self.hashPart
                hashPartLength = self.hashPartLength
            else:
                hashPartLength = len(hashPart)

            count = 0
            status = 0

            newHashPart = hashlib.sha256(hashPart.encode('utf-8')).hexdigest()[0:hashPartLength]

            start = timeit.default_timer()
            while hashPart != newHashPart:
                newHashPart = hashlib.sha256(newHashPart.encode('utf-8')).hexdigest()[0:hashPartLength]
                count += 1
                status += 1
                if status == 100000000:
                    print(count)
                    status = 0

            stop = timeit.default_timer()
            totalTime = round(stop - start, 12)
            print('\n##### findCollisionFirst - Collision found process succeeded! #####')
            print("Collision found after %s seconds" % (totalTime))
            print(('Count of the cycles:', count))
            print(('Collision hash:', newHashPart))

            return {"inputHash": hashPart, "time": totalTime, "cycles": count, "collisionHash": newHashPart}

        except Exception as e:
            print(str(e))

    def findCollisionWithDBSet(self, hashPart=None):
        """
        Function is looking for a collision with hashPart
        """
        try:
            pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
            r = redis.Redis(connection_pool=pool)
            r.flushdb()

            if not hashPart:
                hashPart = self.hashPart
                hashPartLength = self.hashPartLength
            else:
                hashPartLength = len(hashPart)

            count = 0
            status = 0

            start = timeit.default_timer()
            while not r.sismember('hset', hashPart):
                r.sadd('hset', hashPart)
                count += 1
                status += 1
                if status == 10000000:
                    status = 0
                    print('\n' * 100)
                    print('Count of cycles:', count)
                    print('Run time:', round((timeit.default_timer() - start) / 60, 3), 'minutes')

                hashPart = hashlib.sha256(hashPart.encode('utf-8')).hexdigest()[0:hashPartLength]

            stop = timeit.default_timer()
            totalTime = round(stop - start, 12)
            print('\n##### DBSet method - Collision found process succeeded! #####')
            print("Collision found after %s seconds" % (totalTime))
            print(('Count of the cycles:', r.scard('hset')))
            print(('Collision hash:', hashPart))
            # print 'Index of collision hash:'
            return {"inputHash": hashPart, "time": totalTime, "cycles": count, "collisionHash": hashPart}

        except Exception as e:
            print(str(e))

    def findCollisionBloom(self, hashPart=None):
        """
        The test method using performance Bloom filter.

        :param hashPart: the input hash loaded from a file
        """
        try:
            if not hashPart:
                hashPart = self.hashPart
                hashPartLength = self.hashPartLength
            else:
                hashPartLength = len(hashPart)

            status = 0
            bloomCount = 0
            checkCount = 0

            newHashPart = bytes(hashPart, 'utf-8')
            bloomFilter = pybloof.StringBloomFilter(size=1000000000,hashes=9)
            start = timeit.default_timer()

            while True:
                if newHashPart not in bloomFilter:
                    bloomFilter.add(newHashPart)
                    bloomCount += 1
                    status += 1
                    if status == 10000000:
                        print('\n' * 100)
                        print('Count of cycles:', bloomCount)
                        print('Run time:', round((timeit.default_timer() - start), 3),'s')
                        status = 0

                    strHashPart = binascii.unhexlify(newHashPart)
                    newHash = hashlib.sha256(strHashPart).hexdigest()
                    newHash = newHash[0:hashPartLength]
                    newHashPart = bytes(newHash, 'utf-8')
                else:
                    print("### Potencional collision successfully passed! ###")
                    print("Suspicious hash: ", newHash)
                    print('Count of cycles:', bloomCount)
                    print('Time:', round((timeit.default_timer() - start), 3),'s')

                    checkCount = 0
                    collisionHash = newHashPart
                    newHashPart = bytes(hashPart, 'utf-8')
                    while newHashPart != collisionHash:
                        checkCount += 1
                        status += 1
                        if status == 10000000:
                            print('\n' * 100)
                            print('Suspicious hash found! :) Searching for collision index...')
                            print('Count of cycles:', checkCount)
                            print('Run time:', round((timeit.default_timer() - start), 3),'s')
                            status = 0
                        strHashPart = binascii.unhexlify(newHashPart)
                        newHash = hashlib.sha256(strHashPart).hexdigest()
                        newHash = newHash[0:hashPartLength]
                        newHashPart = bytes(newHash, 'utf-8')

                    if checkCount != bloomCount:
                        break
                    else:
                        print('False positive hash detected :(')
                        bloomFilter.add(newHashPart)
                        bloomCount += 1
                        status += 1
                        strHashPart = binascii.unhexlify(newHashPart)
                        newHash = hashlib.sha256(strHashPart).hexdigest()
                        newHash = newHash[0:hashPartLength]
                        newHashPart = bytes(newHash, 'utf-8')

            stop = timeit.default_timer()
            totalTime = round(stop - start, 12)

            print('\n##### findCollisionBloom - Collision found process succeeded! \o/ #####')
            print('\nInput hashPart:', hashPart)
            print("Collision found after %s seconds" % (totalTime))
            print('Count of the cycles:', bloomCount)
            print('Index of collision hash:', checkCount)
            print('Cycles between collision hashes:', bloomCount-checkCount)
            print('Collision hash:', newHash)
            print('\nBloom filter used', round(sys.getsizeof(bloomFilter) / 1024 / 1024, 3), 'MB')

            return {"inputHash": hashPart, "time": totalTime, "cycles": bloomCount, "collisionHash": newHash,
                    "indexOfCollision": checkCount, "cyclesBetCol": bloomCount-checkCount}

        except Exception as e:
            print(str(e))

    def findCollisionCuckoo(self, hashPart=None):
        """
        The test method using Cuckoo filter.

        :param hashPart: the input hash loaded from a file
        """
        try:
            if not hashPart:
                hashPart = self.hashPart
                hashPartLength = self.hashPartLength
            else:
                hashPartLength = len(hashPart)

            status = 0
            cuckooCount = 0
            checkCount = 0

            newHashPart = bytes(hashPart, 'utf-8')
            cf = cuckoofilter.CuckooFilter(capacity=10000000, fingerprint_size=1)
            print('Cuckoo initialized... ')
            start = timeit.default_timer()

            while True:
                if not cf.contains(newHashPart):
                    cf.insert(newHashPart)
                    cuckooCount += 1
                    status += 1
                    if status == 10000000:
                        print('\n' * 100)
                        print('Count of cycles:', cuckooCount)
                        print('Run time:', round((timeit.default_timer() - start), 3),'s')
                        status = 0

                    strHashPart = binascii.unhexlify(newHashPart)
                    newHash = hashlib.sha256(strHashPart).hexdigest()
                    newHash = newHash[0:hashPartLength]
                    newHashPart = bytes(newHash, 'utf-8')
                else:
                    print("### Potencional collision successfully passed! ###")
                    print("Suspicious hash: ", newHash)
                    print('Count of cycles:', cuckooCount)
                    print('Time:', round((timeit.default_timer() - start), 3),'s')

                    collisionHash = newHashPart
                    newHashPart = bytes(hashPart, 'utf-8')
                    while newHashPart != collisionHash:
                        checkCount += 1
                        status += 1
                        if status == 10000000:
                            print('\n' * 100)
                            print('Suspicious hash found! :) Searching for collision index...')
                            print('Count of cycles:', checkCount)
                            print('Run time:', round((timeit.default_timer() - start), 3),'s')
                            status = 0
                        strHashPart = binascii.unhexlify(newHashPart)
                        newHash = hashlib.sha256(strHashPart).hexdigest()
                        newHash = newHash[0:hashPartLength]
                        newHashPart = bytes(newHash, 'utf-8')

                    if checkCount != cuckooCount:
                        break
                    else:
                        print('False positive hash detected :(')
                        cf.insert(newHashPart)
                        cuckooCount += 1
                        status += 1
                        strHashPart = binascii.unhexlify(newHashPart)
                        newHash = hashlib.sha256(strHashPart).hexdigest()
                        newHash = newHash[0:hashPartLength]
                        newHashPart = bytes(newHash, 'utf-8')

            stop = timeit.default_timer()
            totalTime = round(stop - start, 12)

            print('\n##### findCollisionCuckoo - Collision found process succeeded! \o/ #####')
            print('\nInput hashPart:', hashPart)
            print("Collision found after %s seconds" % (totalTime))
            print('Count of the cycles:', cuckooCount)
            print('Index of collision hash:', checkCount)
            print('Cycles between collision hashes:', checkCount-cuckooCount)
            print('Collision hash:', newHash)

            print('\nCuckoo filter used', round(sys.getsizeof(cf) / 1024 / 1024, 3), 'MB')

            return {"inputHash": hashPart, "time": totalTime, "cycles": cuckooCount, "collisionHash": newHash,
                    "indexOfCollision": checkCount, "cyclesBetCol": checkCount-cuckooCount}

        except Exception as e:
            print(str(e))


def main():
    # Input parameters

    parser = argparse.ArgumentParser(usage='$prog [options] -b 32 -i hash.txt',
                                     description='SHA collision finder', add_help=True,
                                     epilog='SHA collision finder. Written by Jan Stangler, Ondrej\
                                      Gajdusek, Sarka Chwastkova, VUT FEKT, ICT1 project, 2017')
    parser.add_argument('-b', '--bits', action='store', dest='bits',
                        help='-b 32 (Number of hash bits to find collision)', required=True)
    parser.add_argument('-i', '--input', action='store', dest='inputFile',
                        help='-i input.txt The input file with hashes', required=False)
    parser.add_argument('-hg', '--hashgroup', action='store_true', dest='hashGroup',
                        help='-h The input file has hashes per line', required=False)
    parser.add_argument('-t', '--text', action='store_true', dest='text',
                        help='-t The input file of random text', required=False)
    parser.add_argument('-f', '--first', action='store_true', dest='first',
                        help='-f Collision with the first one hash', required=False)
    parser.add_argument('--bloom', action='store_true', dest='bloom',
                        help='--bloom Bloom filter is used.', required=False)
    parser.add_argument('-m', '--memory', action='store_true', dest='memory',
                        help='-m Memory check during a process.', required=False)
    parser.add_argument('-c', '--capacity', action='store', dest='capacity',
                        help='-c Set a length of default storage - SET.', required=False)
    parser.add_argument('-r', '--redis', action='store_true', dest='redis',
                        help='-r Store hashes in redis database.', required=False)
    args = parser.parse_args()

    # Instance of the class Shacol
    shacol = Shacol(args.bits, args.inputFile, args.hashGroup, args.text, args.first, args.bloom, args.memory)
    shacol.getInfo()

    print("Do you want to proceed?")
    input('\nPress Enter to continue...')

    if args.inputFile:
        if args.hashGroup:
            for hashes in shacol.shaList:
                if args.first:
                    shacol.findCollisionFirst(hashes)
                else:
                    shacol.findCollisionInt(hashes)
        else:
            if args.first:
                shacol.findCollisionFirst()
            else:
                if args.memory:
                    if args.capacity:
                        shacol.findExperimental(maxSet=args.capacity,memoryCheck=True)
                    else:
                        if args.redis:
                            shacol.findCollisionWithDBSet(memoryCheck=True)
                        else:
                            shacol.findExperimental(memoryCheck=True)
                else:
                    if args.capacity:
                        shacol.findExperimental(maxSet=args.capacity)
                    else:
                        if args.redis:
                            shacol.findCollisionWithDBSet()
                        else:
                            #shacol.findCollisionBloom()
                            #shacol.findCollisionCuckoo()
                            #shacol.findExperimental()
                            shacol.findCollisionStr()
                            shacol.findCollisionInt()
    else:
        if args.bloom:
            if args.memory:
                if args.capacity:
                    shacol.findBestHashBloom(maxSet=args.capacity,memoryCheck=True)
                else:
                    shacol.findBestHashBloom(memoryCheck=True)
            else:
                if args.capacity:
                    shacol.findBestHashBloom(maxSet=args.capacity)
                else:
                    shacol.findBestHashBloom()
        else:
            if args.memory:
                if args.capacity:
                    shacol.findBestHash(maxSet=args.capacity,memoryCheck=True)
                else:
                    shacol.findBestHash(memoryCheck=True)
            else:
                if args.capacity:
                    shacol.findBestHash(maxSet=args.capacity)
                else:
                    shacol.findBestHash()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted... Terminating')
        sys.exit()
