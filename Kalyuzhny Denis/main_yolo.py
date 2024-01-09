import sys, os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
import cv2
from ultralytics import YOLO

os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

model = YOLO('yolov8m.pt')

model_cls = YOLO('best.pt')
class VideoPlayerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.video_file = None
        self.next_frame = None
        self.init_ui()
        self.video_frame_number.setPlainText('0')
        self.ids = {}


    def init_ui(self):
        # Создаем элементы интерфейса
        self.video_label = QLabel('Выберите видеофайл')
        self.video_frame_number = QTextEdit()
        self.play_button = QPushButton('Воспроизвести')
        self.select_button = QPushButton('Выбрать видео')

        self.photo_label_1 = QLabel('Пусто')
        self.photo_label_1.setFixedSize(224, 224)
        self.photo_label_2 = QLabel('Пусто')
        self.photo_label_2.setFixedSize(224, 224)

        # Создаем макет
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.video_frame_number)
        left_layout.addWidget(self.video_label)
        left_layout.addWidget(self.play_button)
        left_layout.addWidget(self.select_button)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.photo_label_1)
        right_layout.addWidget(self.photo_label_2)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        # Устанавливаем макет для основного окна
        self.setLayout(main_layout)

        # Назначаем обработчики событий
        self.play_button.clicked.connect(self.toggle_play)
        self.select_button.clicked.connect(self.select_file)

        # Устанавливаем параметры основного окна
        self.setGeometry(300, 300, 400, 200)
        self.setWindowTitle('Пример детекции модели')

        # Переменные для работы с видео
        self.cap = None
        self.playing = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)


    def toggle_play(self):
        if self.playing:
            self.cap.release()
            self.playing = False
            self.play_button.setText('Воспроизвести')
        else:
            if self.video_file:
                self.ids = {}
                self.cap = cv2.VideoCapture(self.video_file)
                frame_num = int(self.video_frame_number.toPlainText())
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                self.playing = True
                self.play_button.setText('Пауза')
                self.timer.start(0)  # обновление кадра каждые 0 миллисекунд


    def update_frame(self):
        frame_num = int(self.video_frame_number.toPlainText())
        ret, orig_frame = self.cap.read()

        if ret:

            orig_size = orig_frame.shape[:2]
            frame = self.resize_img(orig_frame, 640)
            result = self.detect_person(frame)

            if result.boxes and result.boxes.is_track:
                xyxyn = result.boxes.xyxyn.tolist()
                xyxy = result.boxes.xyxy.int().tolist()
                ids = result.boxes.id.int().tolist()
                for tpl in zip(ids, xyxy, xyxyn):
                    idd, xy, xyn = tpl[0], tpl[1], tpl[2]
                    if self.ids.get(idd) is None:
                        self.ids[idd] = {'color':(255, 255, 255), 'to_spot':False}
                    person_img = orig_frame[int(xyn[1] * orig_size[0]):int(xyn[3] * orig_size[0]), int(xyn[0] * orig_size[1]):int(xyn[2] * orig_size[1])]
                    person_img = self.resize_img(person_img, 224)
                    result_cls = self.classify_person(person_img)
                    cls_class = result_cls.probs.top1
                    cls_conf = result_cls.probs.top1conf.tolist()

                    if cls_class == 0:
                        self.ids[idd]['color'] = (0, 0, 255)
                    else:
                        self.ids[idd]['color'] = (0, 255, 0)

                    if idd == max(self.ids):
                        person_img = cv2.cvtColor(person_img, cv2.COLOR_BGR2RGB)
                        h, w, ch = person_img.shape
                        bytes_per_line = ch * w
                        q_image = QImage(person_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                        pixmap = QPixmap.fromImage(q_image)
                        self.photo_label_1.setPixmap(pixmap)

                    elif idd == max(self.ids) - 1:
                        person_img = cv2.cvtColor(person_img, cv2.COLOR_BGR2RGB)
                        h, w, ch = person_img.shape
                        bytes_per_line = ch * w
                        q_image = QImage(person_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                        pixmap = QPixmap.fromImage(q_image)
                        self.photo_label_2.setPixmap(pixmap)

                    color = self.ids[idd]['color']
                    frame = cv2.rectangle(frame, (xy[0], xy[1]), (xy[2], xy[3]), color)
                    frame = cv2.putText(frame, str(idd), (xy[0], xy[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, color)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.video_label.setPixmap(pixmap)
            frame_num += 1
            self.video_frame_number.setPlainText(str(frame_num))

    def resize_img(self, img, max_size):
        h, w, ch = img.shape
        scale = max(h, w) / max_size
        dim = (int(w / scale), int(h / scale))
        new_img = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        return new_img


    def update_frame_2(self):
        frame_num = int(self.video_frame_number.toPlainText())
        ret, frame = self.cap.read()
        if ret:
            frame = self.detect_person(frame)
            cv2.imshow('YOLOv8 Inference', frame)
            frame_num += 1
            self.video_frame_number.setPlainText(str(frame_num))


    def display_frame(self):
        frame = cv2.cvtColor(self.next_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        pixmap.setDevicePixelRatio(2)
        self.video_label.setPixmap(pixmap)

    def detect_person(self, frame):
        result = model.track(frame, persist=True, classes=0, device=0)

        return result[0]

    def classify_person(self, img):
        result = model_cls.predict(img)
        return result[0]

    # def detect_person_stream(self):
    #     results = model.predict(self.video_file, classes=0, conf=0.6, device=0, stream=True)
    #     for result in results:
    #         self.next_frame = result.plot()
    #         self.display_frame()

            # print(0)

    def select_file(self):
        self.video_file, _ = QFileDialog.getOpenFileName(self, 'Выбрать видеофайл', '', 'Video Files (*.mp4 *.avi *.mkv)')
        self.toggle_play()  # При выборе файла автоматически запускаем воспроизведение

def main():
    app = QApplication(sys.argv)
    window = VideoPlayerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
