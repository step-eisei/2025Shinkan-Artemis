from threading import Event
from gpiozero import RotaryEncoder, Button
from gpiozero.pins.pigpio import PiGPIOFactory

# ロータリーエンコーダのピン設定
PIN_ROTAR_A = 22
PIN_ROTAR_B = 25


def main():

    factory = PiGPIOFactory()

    # ロータリーエンコーダ/ボタンのピン設定
    rotor = RotaryEncoder(
        PIN_ROTAR_A, PIN_ROTAR_B, wrap=True, max_steps=180, pin_factory=factory
    )
    rotor.steps = 0
    done = Event()

    def change_rotor():
        # rotor steps (-180..180) to 0..1
        print(f"rotor.steps is {rotor.steps}")

    def stop_script():
        print("Exiting")
        done.set()

    # ロータリーエンコーダ変化時の処理
    rotor.when_rotated = change_rotor


    done.wait()


if __name__ == "__main__":
    main()
