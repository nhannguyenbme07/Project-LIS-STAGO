import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import Column
import socket
import sys
from datetime import datetime




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
    buffer = s.recv(1)
    if buffer == b'\x06':
        print("SCE: <ACK>")
        window['-LOG-'].print("SCE: <ACK>")
        cs = checksum(data)
        s.sendall(STX)
        s.sendall(data.encode())
        s.sendall(CR)
        s.sendall(ETX)
        s.sendall(cs.encode())
        s.sendall(CR)
        s.sendall(LF)
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
ENQ = b'\x05'
STX = b'\x02'
ETX = b'\x03'
ACK = b'\x06'
LF = b'\x0A'
EOT = b'\x04'
CR = b'\x0D'

configCom = False
tranmit = False
read =False
recordFlag = False

sg.theme('BrownBlue')

first_frame = [[sg.Text('Server IP (SCE IP):'), sg.Text(size=(15,1), key='-COM-')],
          [sg.Input( size= (30,6) , key="-IP-")],
          [sg.Text('Server Port (SCE Port):'), sg.Text(size=(15,1), key='-BAUD-')],
          [sg.Input(size= (30,6) , key="-PORT-")],
          [sg.Button('Save')]]

order_frame = [[]]
for i in range(0,len(tests)):
    order_frame += [[sg.Checkbox(f'{i+1}. ' + tests[i][0], key=i)]]   

first_col = [[sg.Frame("Tranmission Config", layout = first_frame)], [sg.Frame("Test Order", layout = order_frame )] ]

second_frame = [
    [sg.Text("Patient ID")],
    [sg.Input(size=(40,1), key="-PATIENTID-" )],
    [sg.Text("Patient Name")],
    [sg.Input(size=(40,1), key="-PATIENTNAME-" )],
    [sg.Text("Log")],
    [sg.Multiline( key= "-LOG-",size=(60,20))],
    [sg.Button("Send", s=(30,2)), sg.Button("Receive Mode", s=(30,2))]
]
second_col = [[sg.Frame("Patient Information", layout = second_frame )]]


layout =  [[sg.Column(first_col, justification="c" ),sg.Column(second_col)]]
window = sg.Window(title="LIS CONNECTION CHECK - SCE Server", layout = layout, margins=(20,20))

while True:  # Event Loop
    event, values = window.read()
    print(event, values)  
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Save':
        # Update the "output" text element to be the value of "input" element
        configCom = True
        ##### init connection with server ####
        try:
            HOST = values['-IP-']
            PORT = int(values['-PORT-'])
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeOut)
            s.connect((HOST, PORT))
        except:
            print("Can't connect to SCE. Please check your input information or connection.")
            popUpError("Can't connect to SCE. Please check and try again.")

    if event == 'Send':
        if configCom == False:
            popUpError("Please config IP and Port first!")
            continue
        ID = values['-PATIENTID-']
        Name = values['-PATIENTNAME-']
        tranmission = ""
        for i in range(0,len(tests)): #prepare test order
            if values[i] is True:
                tranmission = tranmission + "^^^" + tests[i][1] + "\\"
        print(tranmission)
        tranmit = True

    if event == "Receive Mode":
        read = True
        tranmit = False
        try:
            s.settimeout(timeOut)
        except:
            popUpError("Please config IP and Port first!")

    while read == True:
        
        try:
            buffer =  s.recv(1)
            s.settimeout(3)
            if buffer == b'\x05':
                bufdata = ''
                print('SCE: <ENQ>')
                window['-LOG-'].print("SCE: <ENQ>") 
                s.sendall(ACK)
                print('Host: <ACK>')
                window['-LOG-'].print("Host: <ACK>") 
                recordFlag = True
                #buffer =  s.recv(1)
            if recordFlag is True:
                if buffer == b'\x02':
                    bufdata = '<STX>'
                elif buffer == b'\x03':
                    bufdata = bufdata +  '<ETX>'
                elif buffer == b'\x0d':
                    bufdata = bufdata + '<CR>'
                elif buffer == b'\x0a':
                    bufdata = bufdata + '<LF>'
                    s.sendall(ACK)
                    print("Host: <ACK>")
                    window['-LOG-'].print("Host: <ACK>") 
                    print("SCE: ",bufdata)
                    window['-LOG-'].print("SCE: ", bufdata) 
                    data = bufdata.split('STX>')[1].split('<CR><ETX>')[0]
                    print(data)
                    print('Checksum: ',checksum(data))
                elif buffer == b'\x04':
                    recordFlag = False
                    #read = False
                    print("SCE: <EOT>")
                    window['-LOG-'].print("SCE: <EOT>") 
                    window['-LOG-'].print("========== END ==========") 
                else:
                    bufdata = bufdata + buffer.decode() 
        except socket.timeout:
            print("Time Out")
            read = False
            continue
        except:
            popUpError("Error")
            read = False

    while tranmit == True:
        today = datetime.now()
        today_string = today.strftime("%Y%m%d%H%M%S")
        header = "1H|\^&|||99^2.00||||||||LIS2-A2|"
        patient = "2P|1|"+ ID +"||XXXX|"+ Name +"|||"
        order = "3O|1|" + ID +"||" + tranmission + "|R||20210609055234||||N||||||||||||||"
        terminator = "4L|1|N"
        datasend = [header, patient, order, terminator]
        #print(datasend)
        s.sendall(ENQ)
        print("Host: <ENQ>")
        window['-LOG-'].print("Host: <ENQ>") 
        for i in datasend:
            senddata(i)
        buffer = s.recv(1)
        if buffer == b'\x06':
            print("SCE: <ACK>")
            window['-LOG-'].print("SCE: <ACK>") 
            s.sendall(EOT)
            print("Host: <EOT>")
            window['-LOG-'].print("Host: <EOT>") 
            tranmit = False

window.close()