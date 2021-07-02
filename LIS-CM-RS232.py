from tkinter.constants import FALSE
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Column
import serial
from serial.serialutil import CR
import sys
from datetime import datetime

#### Function to check available COM port from #1 to #20
def serial_ports():
    """ Lists serial port names
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(20)]
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

#### Function open pop-up error window ####
def popUpError(msg):
    layout = [[sg.Text(msg, key="-ERR-")]]
    window = sg.Window("Error", layout, modal=True)
    choice = None
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        
    window.close()


###### Host to instrument function ######
def senddata(data):
    buffer = ser.read(1)
    if buffer == b'\x06':
        print("CM: <ACK>")
        window['-LOG-'].print("CM: <ACK>")
        cs = checksum(data)
        #print(cs)
        ser.write(STX)
        ser.write(data.encode())
        ser.write(CR)
        ser.write(ETX)
        ser.write(cs.encode())
        ser.write(CR)
        ser.write(LF)
        print("Host: <STX>" + data + "<CR><ETX>" + cs + "<CR><LF>")
        window['-LOG-'].print("Host: <STX>" + data + "<CR><ETX>" + cs + "<CR><LF>") 

###### Checksum function ######
def checksum(string):
    sum = 16
    for i in string:
        sum = sum + ord(i)
    sumhex = hex(sum)
    result = sumhex[len(sumhex)-2:].upper()
    return result

###### Open tranmission rank ######
try:
    tests = []
    file = open("TranmissionRank.txt")
    for line in file:
        #print(line.rstrip() )
        tests.append(line.rstrip().split(","))
except:
    print("Missing Tranmission Rank file. Please check")
    popUpError("Missing Tranmission Rank file. Please check and restart!")

#### Init values ####
timeOut = 60
ENQ = [5]
STX = [2]
ETX = [3]
ACK = [6]
LF = [10]
EOT = [4]

configCom = False
tranmit =False
read =False
recordFlag = False

comList = serial_ports()

sg.theme('DarkBlue3')

first_frame = [[sg.Text('Select COM:'), sg.Text(size=(15,1), key='-COM-')],
          [sg.Combo(values= comList, size= (20,6) , key="-COMBOCOM-")],
          [sg.Text('Select Baud Rate:'), sg.Text(size=(15,1), key='-BAUD-')],
          [sg.Combo(values= [2400,4800,9600,14400,19200,38400], size= (20,6) , key="-COMBOBAUD-")],
          [sg.Button('Save')]]

order_frame = [[]]
for i in range(0,len(tests)):
    order_frame += [[sg.Checkbox(f'{i+1}. ' + tests[i][0], key=i)]]   

first_col = [[ sg.Text(size=(30,1), key='-MODE-', font=20)] ,[sg.Frame("COM Config", layout = first_frame)], [sg.Frame("Test Order", layout = order_frame )] ]

second_frame = [
    [sg.Text("Patient ID")],
    [sg.Input(size=(40,1), key="-PATIENTID-" )],
    [sg.Text("Patient Name")],
    [sg.Input(size=(40,1), key="-PATIENTNAME-" )],
    [sg.Text("Log")],
    [sg.Multiline( key= "-LOG-",size=(80,20))],
    [sg.Button("Send", s=(30,2)), sg.Button("Receive Mode", s=(30,2))]
]
second_col = [[sg.Frame("Patient Information", layout = second_frame )]]


layout =  [[sg.Column(first_col, justification="c" ),sg.Column(second_col)]]
window = sg.Window(title="LIS CONNECTION CHECK - STA COMPACT MAX RS232", layout = layout, margins=(20,20))

while True:  # Event Loop
    event, values = window.read()
    print(event, values)  
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Save':
        # Update the "output" text element to be the value of "input" element
        window['-COM-'].update(values['-COMBOCOM-'])
        window['-BAUD-'].update(values['-COMBOBAUD-'])
        comport = values['-COMBOCOM-']
        baudrate = values['-COMBOBAUD-']
        configCom = True
        ##### init serial port ####
        try:
            ser = serial.Serial()
            ser.baudrate = int(baudrate)
            ser.port = comport
            ser.timeout = timeOut
            ser.open()
        except:
            print("COM Port not available.")
            popUpError("COM Port not available. Please check!")

    if event == 'Send':
        if configCom == False:
            popUpError("Please config COM Port first!")
            continue
        ID = values['-PATIENTID-']
        Name = values['-PATIENTNAME-']
        tranmission = ""
        for i in range(0,len(tests)): #prepare test order
            if values[i] is True:
                tranmission = tranmission + "^^^" + tests[i][1] + "\\"
        print(tranmission)
        tranmit = True
        read = True
        ser.timeout = timeOut

    if event == "Receive Mode":
        read = True
        tranmit = False
        window['-MODE-'].update("RECIVED MODE: READING")
        try:
            ser.timeout = timeOut
        except:
            popUpError("Config COM Port first!")
    

    while read == True:
        try:
            buffer = ser.read(1)
            ser.timeout = 2
            if buffer == b'':
                print("Time Out")
                read = False
                window['-MODE-'].update("")
                continue 
            if buffer == b'\x05':
                bufdata = ''
                print('CM: <ENQ>')
                window['-LOG-'].print("CM: <ENQ>") 
                ser.write(ACK)
                print('Host: <ACK>')
                window['-LOG-'].print("Host: <ACK>") 
                recordFlag = True
                buffer = ser.read(1)
            if recordFlag is True:
                if buffer == b'\x02':
                    bufdata = '<STX>'
                elif buffer == b'\x03':
                    bufdata = bufdata +  '<ETX>'
                elif buffer == b'\x0d':
                    bufdata = bufdata + '<CR>'
                elif buffer == b'\x0a':
                    bufdata = bufdata + '<LF>'
                    ser.write(ACK)
                    print("Host: <ACK>")
                    window['-LOG-'].print("Host: <ACK>") 
                    print("CM: ",bufdata)
                    window['-LOG-'].print("CM: ", bufdata) 
                    data = bufdata.split('STX>')[1].split('<CR><ETX>')[0]
                    print(data)
                    print('Checksum: ',checksum(data))
                elif buffer == b'\x04':
                    recordFlag = False
                    #read = False
                    print("CM: <EOT>")
                    window['-LOG-'].print("CM: <EOT>") 
                    window['-LOG-'].print("========== END ==========") 
                    #window['-MODE-'].update("")
                else:
                    bufdata = bufdata + buffer.decode() 
        except:
            popUpError("Error")
            read = False
            window['-MODE-'].update("")

    while tranmit == True:
        today = datetime.now()
        today_string = today.strftime("%Y%m%d%H%M%S")
        header = "1H|\^&|||99^2.00|||||||P|1.00|" + today_string
        patient = "2P|1|||"+Name+ "^^^"
        order = "3O|1|"+ID+"||"+ tranmission + "|R"
        terminator = "4L|1|N<CR><ETX>07"
        datasend = [header, patient, order, terminator]
        #print(datasend)
        ser.write(ENQ)
        print("Host: <ENQ>")
        window['-LOG-'].print("Host: <ENQ>") 
        for i in datasend:
            senddata(i)
        buffer = ser.read(1)
        if buffer == b'\x06':
            print("CM: <ACK>")
            window['-LOG-'].print("CM: <ACK>") 
            ser.write(EOT)
            print("Host: <EOT>")
            window['-LOG-'].print("Host: <EOT>") 
            tranmit = False
    
    
window.close()