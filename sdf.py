import speech_recognition as sr
import pyttsx3
from ultralytics import YOLO
import math
import cv2
import threading

from constants import ACCESS_POINTS, ROAM_KEYWORDS, CLASSIDS, CLASSNAMES
from AudioIO import AudioIn, AudioOut

# ENGINES INITIALIZATION

engine = pyttsx3.init()
engine.setProperty("rate", 145)
r = sr.Recognizer()
model = YOLO("model.pt")
cam = cv2.VideoCapture(0)


# GLOBAL VARS

stop_flag = False
doorReached = False


# FUNCTIONS


def StopLooking():

    global stop_flag
    global doorReached

    while True:
        if doorReached:
            return
        try:
            print("listening for stop command")
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source)
                userinput = r.recognize_google(audio)
                print("user said:", userinput)
                if "stop" in userinput.lower():
                    stop_flag = True
                    return
        except sr.RequestError as e:
            print("Could not request results; {0}".format(e))
        except sr.UnknownValueError:
            print("unknown error occurred")


def detect_door_proximity(img_w, img_h, box, th=0.9):
    x1, x2, y1, y2 = box
    box_w = x2 - x1
    box_h = y2 - y1
    box_area = box_w * box_h
    screen_area = img_w * img_h
    th_area = screen_area * th

    print(f"{box_area} : {th_area}")
    if box_area >= th_area:
        return True
    else:
        return False


def FindAccessPoint(class_id):

    global stop_flag
    global doorReached

    print("finding door")

    loopFlag = True
    doorFound = False
    prevDoorFound = None

    currPos = 2
    prevPos = 3
    notFoundCount = 0
    th = 60
    noDoorCount = 0

    while loopFlag:

        doorFound = False
        success, img = cam.read()
        results = model.predict(
            img,
            classes=CLASSIDS,
        )

        # Check if the user wants to stop
        if stop_flag:
            print("stopping finding access point")
            return

        r = results[0]
        boxes = r.boxes

        for box in boxes:
            cls = int(box.cls[0])
            conf = math.ceil((box.conf[0] * 100)) / 100

            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = (
                int(x1),
                int(y1),
                int(x2),
                int(y2),
            )

            box_center = int((x1 + x2) / 2)
            cam_center = int(640 / 2)

            if cls == class_id:
                doorFound = True
                if box_center in range(cam_center - th, cam_center + th, 1):
                    prevPos = currPos
                    currPos = 0
                    if detect_door_proximity(480, 640, [x1, x2, y1, y2], th=0.6):
                        print(f"you have reached the {CLASSNAMES[class_id]}.")
                        engine.say(f"you have reached the {CLASSNAMES[class_id]}.")
                        doorReached = True
                        engine.runAndWait()
                        return
                    if currPos != prevPos:
                        print(f"{CLASSNAMES[class_id]} in center. walk ahead.")
                        engine.say(f"{CLASSNAMES[class_id]} in center. walk ahead.")

                elif box_center < cam_center - th:
                    prevPos = currPos
                    currPos = -1
                    if currPos != prevPos:
                        print(f"{CLASSNAMES[class_id]} on left. turn a bit left.")
                        engine.say(f"{CLASSNAMES[class_id]} on left. turn a bit left.")

                elif box_center > cam_center + th:
                    prevPos = currPos
                    currPos = 1
                    if currPos != prevPos:
                        print(f"{CLASSNAMES[class_id]} on right. turn a bit right")
                        engine.say(f"{CLASSNAMES[class_id]} on right. turn a bit right")

            else:
                print("class number=", cls, CLASSNAMES[cls])
                if not doorFound:
                    noDoorCount += 1
                if noDoorCount > 5:

                    doorFound = False
                    noDoorCount = 0
                if currPos == 0:
                    if box_center in range(cam_center - th, cam_center + th, 1):
                        print(
                            f"There is a {CLASSNAMES[cls]} in front of the {CLASSNAMES[class_id]}"
                        )
                        engine.say(
                            f"There is a {CLASSNAMES[cls]} in front of the {CLASSNAMES[class_id]}"
                        )

        if not doorFound and doorFound != prevDoorFound:

            prevDoorFound = doorFound

        else:
            if notFoundCount == 10:
                notFoundCount = 0
            else:
                notFoundCount += 1
            if notFoundCount == 0 and not doorFound:
                print(f"{CLASSNAMES[class_id]} not found. look and move around")
                engine.say(f"{CLASSNAMES[class_id]} not found. look and move around")

        engine.runAndWait()


while True:

    acc_pt_id = None

    try:
        with sr.Microphone() as source:
            print("listening...\n")
            userinput = AudioIn(r, sr, source)
            if not userinput:
                continue
            print(userinput)
            for word in ACCESS_POINTS:
                if word in userinput.lower():
                    access_req = True
                    if word == "stairs":
                        acc_pt_id = 489
                    else:
                        acc_pt_id = 164

                    # acc_pt_id = 322  # to be removed later

            if access_req:
                stop_flag = False
                stop_thread = threading.Thread(target=StopLooking)
                stop_thread.start()
                FindAccessPoint(acc_pt_id)
                stop_thread.join()
                access_req = False
            elif roam_req:
                roam_req = False

    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
