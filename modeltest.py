import cv2
from ultralytics import YOLO


model = YOLO("model.pt")
results = model.predict(
    source="0",
    show=True,
    stream=True,
)

flag = True
detected_doors = []
detected_stairs = []

while flag:

    for res in results:
        boxes = res.boxes
        print(f"\n\n****BOX****\n")

        for box in boxes:
            print(f"{box}")
            x1, y1, x2, y2 = [int(x) for x in box.xyxy[0]]
