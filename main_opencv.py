from flask import Flask
from flask import render_template
from flask import Response
import cv2
import time
import numpy as np

app = Flask(__name__)


with open('input/object_detection_classes_coco.txt', 'r') as f:
    class_names = f.read().split('\n')

# get a different color array for each of the classes
COLORS = np.random.uniform(0, 255, size=(len(class_names), 3))

# load the DNN model
model = cv2.dnn.readNet(model='input/frozen_inference_graph.pb',
                        config='input/ssd_mobilenet_v2_coco_2018_03_29.pbtxt.txt', 
                        framework='TensorFlow')

# capture the video
cap = cv2.VideoCapture(0)
#cap = cv2.VideoCapture('input/video_1.mp4')
#cap = cv2.VideoCapture('http://92.138.8.6:8080')
#cap = cv2.VideoCapture('http://45.13.210.86:8083/mjpg/video.mjpg')
#cap = cv2.VideoCapture('http://88.12.14.201:81/nphMotionJpeg?Resolution=320x240&Quality=Standard')
#cap = cv2.VideoCapture('http://166.140.37.191:8000/-wvhttp-01-/GetOneShot?image_size=640x480&frame_count=1000000000')
#cap = cv2.VideoCapture('http://31.164.79.18:50001/axis-cgi/mjpg/video.cgi?camera=&resolution=640x480')
# get the video frames' width and height for proper saving of videos
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
# create the `VideoWriter()` object
out = cv2.VideoWriter('outputs/video_result.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30, 
                      (frame_width, frame_height))

# detect objects in each frame of the video

def generate():
    while cap.isOpened():
        ret, frame = cap.read() 
        k = cv2.waitKey(10)&0xFF
        if k == 27:
            break
        if ret:
            image = frame
            image_height, image_width, _ = image.shape
            # create blob from image
            blob = cv2.dnn.blobFromImage(image=image, size=(300, 300), mean=(104, 117, 123), # prepara la imagen para ingresarla a la red
                                        swapRB=True)              # mean valores medios que se restan de los canales de color RGB de la imagen. Esto normaliza la entrada y hace que la entrada final sea invariante a diferentes escalas de iluminación.
            # start time to calculate FPS
            start = time.time()
            model.setInput(blob)         #ingresar blob a red
            output = model.forward()     #iniciar calculos para la predicción retornando un blob <class   ##<'numpy.ndarray'> (1, 1, 100, 7)
            # end time after detection
            
            end = time.time()
            # calculate the FPS for current frame detection
            fps = 1 / (end-start)
            # loop over each of the detections
            for detection in output[0, 0, :, :]:        # detection     <class 'numpy.ndarray'> (7,)
                # extract the confidence of the detection
                
                confidence = detection[2]          # confidence    <class 'numpy.float32'> ()
                
                # draw bounding boxes only if the detection confidence is above...
                # ... a certain threshold, else skip 
                if confidence > .4:
                    # get the class id
                    class_id = detection[1]
                    # map the class id to the class 
                    class_name = class_names[int(class_id)-1]
                    color = COLORS[int(class_id)]
                    # get the bounding box coordinates
                    box_x = detection[3] * image_width
                    box_y = detection[4] * image_height
                    # get the bounding box width and height
                    box_width = detection[5] * image_width
                    box_height = detection[6] * image_height
                    # draw a rectangle around each detected object
                    cv2.rectangle(image, (int(box_x), int(box_y)), (int(box_width), int(box_height)), color, thickness=2)
                    # put the class name text on the detected object
                    #str = class_name+
                    cv2.putText(image, class_name , (int(box_x), int(box_y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    # put the FPS text on top of the frame
                    cv2.putText(image, f"{fps:.2f} FPS", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2) 
            
            #cv2.imshow('image', image)
            out.write(image)
            (flag, encodedImage) = cv2.imencode(".jpg",image)
            if not flag:
                continue
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                bytearray(encodedImage) + b'\r\n')
                
            
            #if cv2.waitKey(10) & 0xFF == ord('q'):
            #    break
        else:
            break

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    app.run(debug=False)



cap.release()
cv2.destroyAllWindows()
