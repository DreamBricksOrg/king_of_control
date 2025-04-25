import cv2
import numpy as np
import time
import random
from PIL import ImageFont, ImageDraw, Image
from audio_player import AudioPlayer
import threading


class LedPanel(threading.Thread):
    def __init__(self,
                 state_play_duration=120,
                 window_size=(1536, 256),
                 font_path="fonts/DS-DIGI.TTF",
                 font_size=160,
                 text_color=(255, 255, 255),
                 cta_video_path='video.MP4',
                 background_image_path='images/background.png'):

        super().__init__()
        self.lock = threading.Lock()

        self.STATE_PLAY_DURATION = state_play_duration
        self.WINDOW_SIZE = window_size
        self.FONT_PATH = font_path
        self.FONT_SIZE = font_size
        self.TEXT_COLOR = text_color

        self.current_state = 'BLANK'
        self.last_state = None
        self._running = True

        # Recursos
        self.cta_video_path = cta_video_path
        self.cta_cap = cv2.VideoCapture(self.cta_video_path)
        self.background_image = self.load_background_image(background_image_path)
        self.black_image = self.create_black_image()

        self.audio_player = AudioPlayer()

        self.play_start_time = None
        self.score_start_time = None
        self.score_value = None

    def create_black_image(self):
        return np.full((self.WINDOW_SIZE[1], self.WINDOW_SIZE[0], 3), (0, 0, 0), dtype=np.uint8)

    def load_background_image(self, path):
        try:
            img = cv2.imread(path)
            if img is not None:
                return cv2.resize(img, self.WINDOW_SIZE)
            else:
                raise Exception("Imagem de fundo não encontrada.")
        except Exception as e:
            print(f"Erro ao carregar imagem de fundo: {e}")
            return self.black_image

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes):02}:{int(seconds):02}"

    def put_text_with_ttf(self, image, text, font_path, font_size, position, color):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(image_rgb)

        draw = ImageDraw.Draw(img_pil)

        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"Erro ao carregar fonte: {e}")
            font = ImageFont.load_default()

        draw.text(position, text, font=font, fill=color)

        image_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        return image_bgr

    def show_cta_screen(self):
        if not self.cta_cap.isOpened():
            print("Erro ao abrir o vídeo CTA.")
            self._running = False
            return

        ret, frame = self.cta_cap.read()
        if not ret:
            self.cta_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        frame = cv2.resize(frame, self.WINDOW_SIZE)
        cv2.imshow("App", frame)

    def show_play_screen(self):
        img = self.background_image.copy()
        elapsed = time.time() - self.play_start_time
        remaining = max(0, self.STATE_PLAY_DURATION - int(elapsed))
        text = f"{self.format_time(remaining)}"

        if remaining == 0:
            self.current_state = 'SCORE'
            return

        img = self.display_text_centered(img, text, self.FONT_SIZE, offset=(-150, -15))
        cv2.imshow("App", img)

    def show_blank_screen(self):
        cv2.imshow("App", self.black_image)

    def show_score_screen(self):
        img = self.background_image.copy()
        text = f"{self.score_value}"

        img = self.display_text_centered(img, "SCORE:", 24, offset=(-150, -60))
        img = self.display_text_centered(img, "PTS", 24, offset=(60, 50))
        img = self.display_text_centered(img, text, self.FONT_SIZE, offset=(-150, -15))
        cv2.imshow("App", img)

    def display_text_centered(self, img, text, font_size, offset=(0, 0)):
        try:
            font = ImageFont.truetype(self.FONT_PATH, font_size)
        except Exception as e:
            print(f"Erro ao carregar fonte: {e}")
            font = ImageFont.load_default()

        image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(image_rgb)
        draw = ImageDraw.Draw(img_pil)

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        offset_x, offset_y = offset
        text_x = (img.shape[1] - text_width) // 2 + offset_x
        text_y = (img.shape[0] - text_height) // 2 + offset_y

        draw.text((text_x, text_y), text, font=font, fill=self.TEXT_COLOR)

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def run(self):
        cv2.namedWindow("App", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("App", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.resizeWindow("App", 1536, 256)
        cv2.moveWindow("App", 0, 0)

        while self._running:
            with self.lock:
                if self.current_state != self.last_state:
                    print(f"run: {self.current_state}")
                    self.audio_player.stop_all()

                    if self.current_state == 'CTA':
                        self.audio_player.play_loop("champions")
                        self.cta_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    elif self.current_state == 'PLAY':
                        self.audio_player.play_once("torcida")
                        self.play_start_time = time.time()
                    elif self.current_state == 'SCORE':
                        self.audio_player.play_once("gol")
                        self.score_start_time = time.time()
                    elif self.current_state == 'BLANK':
                        self.score_start_time = time.time()

                    self.last_state = self.current_state

                if self.current_state == 'CTA':
                    self.show_cta_screen()
                elif self.current_state == 'PLAY':
                    self.show_play_screen()
                elif self.current_state == 'SCORE':
                    self.show_score_screen()
                elif self.current_state == 'BLANK':
                    self.show_blank_screen()

                key = cv2.waitKey(30) & 0xFF
                if key == ord('1'):
                    ledPanel.set_state('CTA')
                elif key == ord('2'):
                    ledPanel.set_state('PLAY')
                elif key == ord('3'):
                    ledPanel.set_state('SCORE')
                    ledPanel.set_score_value(random.randint(0, 999))
                elif key == ord('q'):
                    ledPanel._running = False
                    break

        self.cta_cap.release()
        cv2.destroyAllWindows()

    def set_state(self, state):
        with self.lock:
            self.current_state = state

    def set_score_value(self, score):
        with self.lock:
            self.score_value = score


if __name__ == "__main__":
    ledPanel = LedPanel()
    ledPanel.start()

    #exit(1)
    print('change state')

    keys = ['0', '1', '2', '3']

    key_idx = 0
    while True:
        #key = cv2.waitKey(30) & 0xFF
        key = keys[key_idx]
        print(key)
        if key == '0':
            ledPanel.set_state('BLANK')
        elif key == '1':
            ledPanel.set_state('CTA')
        elif key == '2':
            ledPanel.set_state('PLAY')
        elif key == '3':
            ledPanel.set_state('SCORE')
            ledPanel.set_score_value(random.randint(0, 9999))
        elif key == 'q':
            ledPanel._running = False
            break

        time.sleep(5)
        key_idx = (key_idx+1)
        #ledPanel.show_state_on_screen()


