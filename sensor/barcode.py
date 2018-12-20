# USAGE
# python barcode_scanner_video.py

# import the necessary packages
from pyzbar import pyzbar
import argparse
import datetime
import time
import cv2

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
                help="path to output CSV file containing barcodes")
args = vars(ap.parse_args())

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
# vs = VideoStream(src=0).start()
cam = cv2.VideoCapture(0)
time.sleep(1)

# open the output CSV file for writing and initialize the set of
# barcodes found thus far
csv = open(args["output"], "w")
found = False

# loop over the frames from the video stream
while not found:
    # grab the frame from the threaded video stream and resize it to
    # have a maximum width of 400 pixels
    _, frame = cam.read()

    # find the barcodes in the frame and decode each of the barcodes
    barcodes = pyzbar.decode(frame)

    if barcodes:
        barcode = barcodes[0]
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        found = True
        csv.write("{},{}\n".format(datetime.datetime.now(),
                                   barcodeData))
        print("{}".format(barcodeData))
        csv.flush()

    # show the output frame
    cv2.imshow("Barcode Scanner", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

# close the output CSV file do a bit of cleanup
print("[INFO] cleaning up...")
csv.close()
cv2.destroyAllWindows()
cam.release()
