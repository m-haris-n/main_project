import speech_recognition as sr
import pyttsx3
from ultralytics import YOLO
import math
import cv2

ACCESS_POINTS = ["door", "doors", "stairs", "go out", "exit", "enter", "go in"]
ROAM_KEYWORDS = [
    "walk",
    "stroll",
    "obstacle",
]

CLASSNAMES = {
    34: "bed",
    57: "Bottle",
    100: "Ceiling fan",
    104: "Chair",
    114: "Closet",
    136: "Couch",
    147: "Cupboard",
    148: "Curtain",
    153: "Desk",
    164: "Door",
    165: "Door handle",
    214: "Gas stove",
    261: "Human body",
    302: "Land vehicle",
    309: "Light switch",
    322: "Man",
    339: "Mobile phone",
    419: "Refrigerator",
    453: "Shelf",
    489: "Stairs",
    494: "Stool",
    514: "Table",
    526: "Telephone",
    583: "Wheelchair",
    594: "Woman",
}

CLASSIDS = [
    34,
    57,
    100,
    104,
    114,
    136,
    147,
    148,
    153,
    164,
    165,
    214,
    261,
    302,
    309,
    322,
    339,
    419,
    453,
    489,
    494,
    514,
    526,
    583,
    594,
]

engine = pyttsx3.init()
r = sr.Recognizer()
model = YOLO("model.pt")
cam = cv2.VideoCapture(0)


def AudioIn():
    try:
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source)
        print(audio)
        userinput = r.recognize_google(audio)
        return userinput
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
        return None
    except sr.UnknownValueError:
        print("unknown error occurred")
        return None


def AudioOut(command):
    engine.say(command)
    engine.runAndWait()


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


def FindDoor():
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
        success, img = cam.read()
        results = model.predict(
            img,
            classes=CLASSIDS,
        )

        print(results)
        print(type(results))
        # for r in results:
        for r in results:
            boxes = r.boxes
            print(f"\n\n*******BOXES*******\n")

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

                if cls == 322:
                    doorFound = True
                    if box_center in range(cam_center - th, cam_center + th, 1):
                        prevPos = currPos
                        currPos = 0
                        if detect_door_proximity(480, 640, [x1, x2, y1, y2], th=0.6):
                            engine.say("you have reached the door.")
                            engine.runAndWait()
                            return
                        if currPos != prevPos:
                            engine.say("door in center. walk ahead.")

                    elif box_center < cam_center - th:
                        prevPos = currPos
                        currPos = -1
                        if currPos != prevPos:
                            engine.say("door on left")

                    elif box_center > cam_center + th:
                        prevPos = currPos
                        currPos = 1
                        if currPos != prevPos:
                            engine.say("door on right. turn a bit right")

                else:
                    print("class number=", cls, CLASSNAMES[cls])
                    if not doorFound:
                        noDoorCount += 1
                    if noDoorCount > 5:

                        doorFound = False
                        noDoorCount = 0
                    if currPos == 0:
                        if box_center in range(cam_center - th, cam_center + th, 1):
                            engine.say("There is something in front of the door")

        if not doorFound and doorFound != prevDoorFound:

            prevDoorFound = doorFound

            if notFoundCount == 0:
                engine.say("door not found. look and move around")

            if notFoundCount == 5:
                notFoundCount = 0
            else:
                notFoundCount += 1

        engine.runAndWait()
    return doorFound


def FreeRoam():
    # keep informing user about obstacles in the way
    print("free roaming")
    pass


access_req = False
roam_req = False

while True:
    try:
        with sr.Microphone() as source:
            print("listening...\n")
            userinput = AudioIn()
            print(userinput)
            if not userinput:
                continue
            for word in ACCESS_POINTS:
                if word in userinput.lower():
                    access_req = True

            if access_req:
                door = FindDoor()
                access_req = False
            elif roam_req:
                FreeRoam(cam, model)
                roam_req = False

    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
