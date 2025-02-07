import cv2
import mediapipe as mp
import random
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)


def get_gesture(landmarks, hand_type):
    # 判断各手指是否伸直
    index_tip = landmarks[8]
    index_pip = landmarks[6]
    index_open = index_tip.y < index_pip.y

    middle_tip = landmarks[12]
    middle_pip = landmarks[10]
    middle_open = middle_tip.y < middle_pip.y

    ring_tip = landmarks[16]
    ring_pip = landmarks[14]
    ring_open = ring_tip.y < ring_pip.y

    pinky_tip = landmarks[20]
    pinky_pip = landmarks[18]
    pinky_open = pinky_tip.y < pinky_pip.y

    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    if hand_type == "Left":
        thumb_open = thumb_tip.x > thumb_ip.x
    else:
        thumb_open = thumb_tip.x < thumb_ip.x

    # 改进的手势判断逻辑
    if thumb_open and index_open and middle_open and ring_open and pinky_open:
        return "PAPER"  # 所有手指伸直表示布
    elif index_open and middle_open and not ring_open and not pinky_open:
        return "scissors"  # 食指和中指伸直表示剪刀
    elif (
        not thumb_open
        and not index_open
        and not middle_open
        and not ring_open
        and not pinky_open
    ):
        return "ROCK"  # 所有手指弯曲表示石头
    else:
        return "NO"  # 无法识别的手势


# 状态变量防抖
gesture_history = []
start_time = None
confirmed_gesture = None

while cap.isOpened():
    success, image = cap.read()
    if not success:
        continue

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    current_gesture = "NO"
    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks, results.multi_handedness
        ):
            hand_type = handedness.classification[0].label
            current_gesture = get_gesture(hand_landmarks.landmark, hand_type)

            # 计算手部边界框
            x_min, y_min = image.shape[1], image.shape[0]
            x_max, y_max = 0, 0
            for landmark in hand_landmarks.landmark:
                x, y = int(landmark.x * image.shape[1]), int(
                    landmark.y * image.shape[0]
                )
                if x < x_min:
                    x_min = x
                if x > x_max:
                    x_max = x
                if y < y_min:
                    y_min = y
                if y > y_max:
                    y_max = y

            # 绘制手部边界框
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
            cv2.putText(
                image,
                "hand",
                (x_min, y_min),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                2,
            )
            # # 绘制关键点
            # mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # 防抖处理：连续5帧相同手势才确认
    gesture_history.append(current_gesture)
    if len(gesture_history) > 5:
        gesture_history.pop(0)
        if len(set(gesture_history)) == 1 and gesture_history[0] != "NO":
            confirmed_gesture = gesture_history[0]

    # 在图像上显示
    if confirmed_gesture:
        cv2.putText(
            image,
            f"you: {confirmed_gesture}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    cv2.imshow("RSP_game", image)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # 按下 ESC 键退出
        break
    elif key == ord("f") or key == ord("F"):  # 按下 F 键开始计时
        start_time = time.time()  # 记录开始时间
        print("Start counting...")

    # 如果已经开始计时并且超过3秒
    if start_time is not None and (time.time() - start_time) >= 3:
        if confirmed_gesture:
            computer = random.choice(["ROCK", "scissors", "PAPER"])

            # 判断胜负
            if confirmed_gesture == computer:
                result = "DRAW"
            elif (
                (confirmed_gesture == "ROCK" and computer == "scissors")
                or (confirmed_gesture == "scissors" and computer == "PAPER")
                or (confirmed_gesture == "PAPER" and computer == "ROCK")
            ):
                result = "WIN"
            else:
                result = "LOSE"
            print(f"you: {confirmed_gesture}, AI: {computer}, result: {result}")
            start_time = None  # 清除计时器变量
    elif start_time is not None and (time.time() - start_time) < 3:
        if confirmed_gesture:
            computer = random.choice(["ROCK", "scissors", "PAPER"])
            print(computer)


cap.release()
cv2.destroyAllWindows()
