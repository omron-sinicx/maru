import serial
import sys
import time
from serial.tools import list_ports
from rich import print

def calculateCheckSum(array, size):
    sum = 0
    for num in range(size - 1):
        sum += array[num]
    return sum & 0xFF

def generateGetParameterCommand(id, address):
    txdata = [0xFF, 0xFD, 0x05, 0x00, 0x3E, id, address, 0x0A, 0x00]
    txdata[8] = calculateCheckSum(txdata, 9)
    return txdata

def main():
    targetId = 14
    args = sys.argv

    # Exit if no serial port and id specified
    if len(args) < 3:
        ports = list_ports.comports()
        devices = [info.device for info in ports]
        print("Specify serial port and robot id\r\n")
        print("e.g., python getCalib.py COM3 1\r\n")
        print("Port List : \r\n")
        for port in ports:
            print(port)
        sys.exit(0)

    # Open port
    port = serial.Serial(args[1], 1000000, timeout=1)

    targetId = int(args[2])

    # Variables
    commandState = 0
    commandLength = 0
    commandInstruction = 0
    commandData = [0] * 100
    commandPosition = 0

    rightMotorRPM = [0] * 10
    leftMotorRPM = [0] * 10

    # Send GetParameter command
    port.write(generateGetParameterCommand(targetId, 48));
    start = time.time()

    waitLoop = True
    phase = 0

    while(waitLoop):
        rcvArray = port.read_all()

        t = time.time() - start
        if t > 0.5:
            port.write(generateGetParameterCommand(targetId, 48 + phase * 10));
            start = time.time()

        for data in rcvArray:
            if commandState == 0:
                commandPosition = 0

            commandData[commandPosition] = data
            commandPosition = commandPosition + 1

            # Check command
            if commandState == 0: # 0xFF
                if data == 0xFF:
                    commandState = 1

            elif commandState == 1: # 0xFD
                if data == 0xFD:
                    commandState = 2
                else:
                    commandState = 0

            elif commandState == 2: # LEN_L
                commandLength = data
                commandState = 3

            elif commandState == 3: # LEN_H
                commandLength = commandLength + (data << 8)
                commandState = 4

            elif commandState == 4: # Instruction
                commandInstruction = data
                if commandLength == 2:
                    commandState = 6
                else:
                    commandState = 5

            elif commandState == 5: # Param
                 if commandPosition == commandLength + 3:
                    commandState = 6

            elif commandState == 6: # CheckSum
                commandState = 0
                if data != calculateCheckSum(commandData, commandPosition):
                    continue

                if commandInstruction == 0x3F:
                    targetAddress = commandData[6]
                    if targetAddress == 48:
                        rightMotorRPM[0] = commandData[7] + (commandData[8] << 8)
                        rightMotorRPM[1] = commandData[9] + (commandData[10] << 8)
                        rightMotorRPM[2] = commandData[11] + (commandData[12] << 8)
                        rightMotorRPM[3] = commandData[13] + (commandData[14] << 8)
                        rightMotorRPM[4] = commandData[15] + (commandData[16] << 8)
                        time.sleep(0.1)
                        port.write(generateGetParameterCommand(targetId, 58));
                        start = time.time()
                        phase = phase + 1

                    elif targetAddress == 58:
                        rightMotorRPM[5] = commandData[7] + (commandData[8] << 8)
                        rightMotorRPM[6] = commandData[9] + (commandData[10] << 8)
                        rightMotorRPM[7] = commandData[11] + (commandData[12] << 8)
                        rightMotorRPM[8] = commandData[13] + (commandData[14] << 8)
                        rightMotorRPM[9] = commandData[15] + (commandData[16] << 8)
                        time.sleep(0.1)
                        port.write(generateGetParameterCommand(targetId, 68));
                        start = time.time()
                        phase = phase + 1

                    elif targetAddress == 68:
                        leftMotorRPM[0] = commandData[7] + (commandData[8] << 8)
                        leftMotorRPM[1] = commandData[9] + (commandData[10] << 8)
                        leftMotorRPM[2] = commandData[11] + (commandData[12] << 8)
                        leftMotorRPM[3] = commandData[13] + (commandData[14] << 8)
                        leftMotorRPM[4] = commandData[15] + (commandData[16] << 8)
                        time.sleep(0.1)
                        port.write(generateGetParameterCommand(targetId, 78));
                        start = time.time()
                        phase = phase + 1

                    elif targetAddress == 78:
                        leftMotorRPM[5] = commandData[7] + (commandData[8] << 8)
                        leftMotorRPM[6] = commandData[9] + (commandData[10] << 8)
                        leftMotorRPM[7] = commandData[11] + (commandData[12] << 8)
                        leftMotorRPM[8] = commandData[13] + (commandData[14] << 8)
                        leftMotorRPM[9] = commandData[15] + (commandData[16] << 8)

                        rightSelectedRPM = 0;
                        leftSelectedRPM = 0;

                        tmpAbs = 10000
                        # 小さい方と大きい方の選択値を取得
                        if leftMotorRPM[9] < rightMotorRPM[9]:
                            leftSelectedRPM = 9
                            for i in range(10):
                                if rightMotorRPM[i] == 0:
                                    continue
                                if rightMotorRPM[i] > leftMotorRPM[9]:
                                    continue
                                if leftMotorRPM[9] - rightMotorRPM[i] < tmpAbs:
                                    tmpAbs = leftMotorRPM[9] - rightMotorRPM[i]
                                    rightSelectedRPM = i
                            if rightSelectedRPM != 9:
                                rightSelectedRPM = rightSelectedRPM + 1
                        else:
                            rightSelectedRPM = 9
                            for i in range(10):
                                if leftMotorRPM[i] == 0:
                                    continue
                                if leftMotorRPM[i] > rightMotorRPM[9]:
                                    continue
                                if rightMotorRPM[9] - leftMotorRPM[i] < tmpAbs:
                                    tmpAbs = rightMotorRPM[9] - leftMotorRPM[i];
                                    leftSelectedRPM = i;
                            if leftSelectedRPM != 9:
                                leftSelectedRPM = leftSelectedRPM + 1

                        str = "right Motor : {"
                        for i in range(10):
                            if i == rightSelectedRPM:
                                str = str + "[red]"
                            str = str + "{:0>4}".format(rightMotorRPM[i])
                            if i == rightSelectedRPM:
                                str = str + "[/red]"
                            str = str + ", "
                        str = str + "}"
                        print(str)

                        str = "left  Motor : {"
                        for i in range(10):
                            if i == leftSelectedRPM:
                                str = str + "[red]"
                            str = str + "{:0>4}".format(leftMotorRPM[i])
                            if i == leftSelectedRPM:
                                str = str + "[/red]"
                            str = str + ", "
                        str = str + "}"
                        print(str)

                        time.sleep(0.1)
                        waitLoop = False

if __name__ == '__main__':
    main()
