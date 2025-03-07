import RPi.GPIO as GPIO
import time

class Nicrom():
    def __init__(self, pin=33):
        self.pin = pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin,  GPIO.OUT)

    def heat(self, t=3):
        GPIO.output(self.pin, False)
        time.sleep(30)
        GPIO.output(self.pin, True)
        time.sleep(t)
        GPIO.output(self.pin, False)
    
    def end(self):
        GPIO.output(self.pin, False)

def main():
    time.sleep(10)
    nicrom = Nicrom()

    try:
        print("start")
        nicrom.heat(t=10)

        nicrom.end()
        print("end")
    except:
        nicrom.end()
        print("\nerror.")

if __name__ == "__main__":
    main()
