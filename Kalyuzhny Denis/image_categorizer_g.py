import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt6.QtGui import QPixmap, QImageReader
from PyQt6.QtCore import Qt
import os

class ImageCategorizer(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Categorizer')

        # Кнопка выбора каталога
        self.selectDirBtn = QPushButton('Выбор каталога', self)
        self.selectDirBtn.clicked.connect(self.showDialog)

        # Место для вывода изображения
        self.imageLabel = QLabel(self)
        self.imageLabel.setFixedSize(400, 400)

        # Кнопки категорий
        self.categoryBtns = []
        categories = ['светлое', 'темное', 'грустное']

        for category in categories:
            btn = QPushButton(category, self)
            btn.clicked.connect(lambda _, cat=category: self.categorizeImage(cat))
            self.categoryBtns.append(btn)

        # Layout
        buttonLayout = QHBoxLayout()
        for btn in self.categoryBtns:
            buttonLayout.addWidget(btn)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.selectDirBtn)
        mainLayout.addWidget(self.imageLabel)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

        # Текущий каталог и список изображений
        self.currentDir = ''
        self.imageList = []
        self.currentImageIndex = 0

    def showDialog(self):
        # Открытие диалога выбора каталога
        dir_path = QFileDialog.getExistingDirectory(self, 'Выберите каталог', '')
        if dir_path:
            self.currentDir = dir_path
            self.loadImages()
            self.showNextImage()

    def loadImages(self):
        # Загрузка списка изображений в текущем каталоге
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        self.imageList = [f for f in os.listdir(self.currentDir) if os.path.isfile(os.path.join(self.currentDir, f)) and f.lower().endswith(tuple(image_extensions))]

    def showNextImage(self):
        # Отображение следующего изображения
        if self.imageList:
            if self.currentImageIndex >= len(self.imageList):
                self.imageLabel.setText('Изображения закончились')
                return
            image_path = os.path.join(self.currentDir, self.imageList[self.currentImageIndex])

            # Масштабирование изображения
            scaled_image = self.scaleImage(image_path, 400)

            # pixmap = QPixmap(image_path)
            pixmap = QPixmap.fromImage(scaled_image)
            self.imageLabel.setPixmap(pixmap)


    def scaleImage(self, image_path, target_size):
        # Масштабирование изображения к целевому размеру
        image_reader = QImageReader(image_path)
        orig_size = image_reader.size()
        scaled_size = orig_size.scaled(target_size, target_size, Qt.AspectRatioMode.KeepAspectRatio)
        image_reader.setScaledSize(scaled_size)
        image_reader.setAutoTransform(True)
        #
        image = image_reader.read()
        return image

    def categorizeImage(self, category):
        # Перемещение изображения в подкаталог с соответствующим названием
        if self.imageList:
            if self.currentImageIndex >= len(self.imageList):
                return
            source_path = os.path.join(self.currentDir, self.imageList[self.currentImageIndex])
            target_dir = os.path.join(self.currentDir, category)

            # Создание подкаталога, если его нет
            os.makedirs(target_dir, exist_ok=True)

            # Перемещение файла
            target_path = os.path.join(target_dir, self.imageList[self.currentImageIndex])
            os.rename(source_path, target_path)

            # Загрузка следующего изображения
            self.currentImageIndex += 1
            self.showNextImage()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageCategorizer()
    window.show()
    sys.exit(app.exec())
