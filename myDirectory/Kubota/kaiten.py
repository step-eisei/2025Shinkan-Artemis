#include <stdio.h>
#include <wiringPi.h>

#define ENCODER_A_PIN 17  // エンコーダのA相ピン
#define ENCODER_B_PIN 27  // エンコーダのB相ピン
#define PPR 11            // エンコーダの1回転あたりのパルス数
#define GEAR_RATIO 15.27  // ギア比
#define delay_time 10     // 待機時間
volatile int pulse_count = 0;    // パルスをカウントするための変数
volatile int direction = 1;      // 回転方向（1: 正転、-1: 逆転）

// パルスが検出されたときに呼ばれる関数
void pulseCounter() {
    // A相の立ち上がりエッジでのB相の状態により方向を判定
    if (digitalRead(ENCODER_B_PIN) == HIGH) {
        direction = 1;  // 正転
    } else {
        direction = -1; // 逆転
    }
    pulse_count += direction;  // 回転方向に応じてカウントを増減
}

int main(void) {
    // GPIOの初期化
    if (wiringPiSetupGpio() == -1) {
        printf("GPIOのセットアップに失敗しました\n");
        return 1;
    }

    // エンコーダのA相とB相ピンを入力モードに設定
    pinMode(ENCODER_A_PIN, INPUT);
    pinMode(ENCODER_B_PIN, INPUT);
    pullUpDnControl(ENCODER_A_PIN, PUD_UP);
    pullUpDnControl(ENCODER_B_PIN, PUD_UP);

    // 割り込み設定（A相の立ち上がりエッジでパルスをカウント）
    if (wiringPiISR(ENCODER_A_PIN, INT_EDGE_RISING, &pulseCounter) < 0) {
        printf("ISRの設定に失敗しました\n");
        return 1;
    }

    while (1) {
        // 10秒間のパルスカウントをリセット
        int start_pulse_count = pulse_count;
        delay(delay_time*1000);  // 10秒間待機
        int end_pulse_count = pulse_count;
        
        // 10秒間にカウントされたパルス数を計算
        int pulses = end_pulse_count - start_pulse_count;
        
        // モーター軸の回転数を計算
        double motor_rpm = (double)abs(pulses) * 60 / (PPR*delay_time);

        // 出力軸（車輪など）の回転数
        double output_rpm = motor_rpm / GEAR_RATIO;

        // 回転方向の表示
        if (pulses > 0) {
            printf("回転方向: 正転\n");
        } else if (pulses < 0) {
            printf("回転方向: 逆転\n");
        } else {
            printf("回転方向: 停止\n");
        }

    
        printf("出力軸のRPM: %.2f\n", output_rpm);
    }

    return 0;
}
