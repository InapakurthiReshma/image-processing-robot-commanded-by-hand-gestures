import cv2
import numpy as np
import pandas as pd
import subprocess
import urllib.request
import joblib

try:
    a = subprocess.run('arp -a', capture_output=True, text=True)
    out = a.stdout.split()
    url = 'http://'+out[out.index('e8-db-84-e1-4f-34')-1]+'/'
    print("~~ Device Connected ~~")
    print("URL : ", url)
except:
    print("!! Cant't Connect to the Device !!")

def send_command(cmd):
    try:
        urllib.request.urlopen(url+cmd, timeout=1)
    except:
        print("^^ Timeout Error ^^")

dir = ['R', 'L', 'F', 'B', 'S', 'none']
dir_dict = {'R':'Right', 'L':'Left', 'F':'Front', 'B':'Back', 'S':'Stop', 'none':'None'}
dir_ln = [0, 0, 0, 0, 0, 0]

mdl = joblib.load("1RFC_Model_HandSigns_mask.joblib")

vid = cv2.VideoCapture(0)
cnt = 0
prev_command = 'none'
while True:
    _ , main_frame = vid.read()
    main_frame = cv2.flip(main_frame,2)

    cv2.rectangle(main_frame,(100,50),(300,250),(0, 0, 0),2)
    
    frame = main_frame[50:251,100:301]

    # skin_lower = np.array([0, 30, 53], dtype = "uint8")
    # skin_upper = np.array([20, 180, 255], dtype = "uint8")

    # nail_lower = np.array([172, 30, 53], dtype = "uint8")
    # nail_upper = np.array([180, 180, 210], dtype = "uint8")

       #[0, 10, 60]        [0, 58, 50]          [0, 30, 53]
       #[20, 150, 255]     [30, 255, 255]       [20, 150, 255]

    skin_lower = np.array([0, 30, 53]   , dtype = "uint8")
    skin_upper = np.array([20, 150, 255], dtype = "uint8") 

    nail_lower = np.array([172, 30, 53]  , dtype = "uint8")
    nail_upper = np.array([180, 180, 210], dtype = "uint8")

    conv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    skinMask = cv2.inRange(conv_frame, skin_lower, skin_upper)
    nailMask = cv2.inRange(conv_frame, nail_lower, nail_upper)

    skinMask = cv2.GaussianBlur(skinMask, (3, 3), 0)
    nailMask = cv2.GaussianBlur(nailMask, (3, 3), 0)
    
    skin = cv2.bitwise_and(frame, frame, mask = skinMask)
    nail = cv2.bitwise_and(frame, frame, mask = nailMask)
    frame = cv2.bitwise_or(skin, nail)

    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    gr = cv2.resize(frame,(60,60), interpolation=cv2.INTER_CUBIC)

    gr = gr.flatten()
    
    gr = pd.DataFrame(gr).transpose()
    
    # gr = round(gr/255., 2)
    gr = gr/255.
    
    try:
        dir_ln[mdl.predict(gr)[0]] += 1
    except:
        print(mdl.predict(gr)[0])

    cv2.putText(main_frame, dir_dict[prev_command], (140, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,0,250), 2, cv2.LINE_AA)

    cnt += 1

    if cnt == 13:
        command = dir[dir_ln.index(max(dir_ln))]
        print(dir_ln)
        print(command)
        # cv2.putText(main_frame, command, (100, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,250,0), 2, cv2.LINE_AA)
        if command not in ['none']:
            send_command(command)
            prev_command = command

        cnt = 0
        dir_ln = [0, 0, 0, 0, 0, 0]

    cv2.imshow('Scanner', main_frame)
    cv2.imshow('bg_frame', frame)
    
    button_event = cv2.waitKey(1)
    if button_event in (ord('q'), ord('Q')):
        break

vid.release()
cv2.destroyAllWindows()

