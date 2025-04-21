import cv2
import numpy as np
import time
import random
from PIL import ImageFont, ImageDraw, Image

class LedPanel:
    def __init__(self,
                 state_play_duration=120,
                 state_score_duration=5,
                 window_size=(600, 400),
                 font_path="TikTokDisplay-Bold.ttf",
                 font_scale=1.0,
                 font_thickness=2,
                 text_color=(255, 255, 255),
                 cta_video_path = 'video.MP4'):

        self.STATE_PLAY_DURATION = state_play_duration
        self.STATE_SCORE_DURATION = state_score_duration
        self.WINDOW_SIZE = window_size
        self.FONT_PATH = font_path
        self.FONT_SCALE = font_scale
        self.FONT_THICKNESS = font_thickness
        self.TEXT_COLOR = text_color

        # Estados
        self.states = {
            '1': 'CTA',
            '2': 'PLAY',
            '3': 'SCORE'
        }

        self.current_state = 'CTA'
        self.last_state = None
        self.running = True

        # Inicialização de variáveis de controle
        self.cta_video_path = cta_video_path
        self.cta_cap = cv2.VideoCapture(self.cta_video_path)

        self.play_start_time = None
        self.score_start_time = None
        self.score_value = None

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes):02}:{int(seconds):02}"

    def put_text_with_ttf(self, image, text, font_path, font_size, position, color):
        img_pil = Image.fromarray(image)
        draw = ImageDraw.Draw(img_pil)
        font = ImageFont.truetype(font_path, font_size)
        draw.text(position, text, font=font, fill=color)
        return np.array(img_pil)

    def show_state_on_screen(self):
        # Criar janela em modo tela cheia
        cv2.namedWindow("App", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("App", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.resizeWindow("App", 1536, 256)
        cv2.moveWindow("App", 0, 0)

        while self.running:
            key = cv2.waitKey(30) & 0xFF
            if key == ord('1'):
                self.current_state = 'CTA'
            elif key == ord('2'):
                self.current_state = 'PLAY'
            elif key == ord('3'):
                self.current_state = 'SCORE'
            elif key == ord('q'):
                self.running = False
                break

            if self.current_state != self.last_state:
                if self.current_state == 'PLAY':
                    self.play_start_time = time.time()
                elif self.current_state == 'SCORE':
                    self.score_start_time = time.time()
                    self.score_value = f"{random.randint(0, 999):03}"
                self.last_state = self.current_state

            if self.current_state == 'CTA':
                if not self.cta_cap.isOpened():
                    print("Erro ao abrir o vídeo CTA.")
                    break

                ret, frame = self.cta_cap.read()
                if not ret:
                    self.cta_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                frame = cv2.resize(frame, self.WINDOW_SIZE)
                cv2.imshow("App", frame)

            else:
                img = np.full((self.WINDOW_SIZE[1], self.WINDOW_SIZE[0], 3), (0, 86, 31), dtype=np.uint8)

                if self.current_state == 'PLAY':
                    elapsed = time.time() - self.play_start_time
                    remaining = max(0, self.STATE_PLAY_DURATION - int(elapsed))
                    text = f"Tempo restante: {self.format_time(remaining)}"

                    if remaining == 0:
                        self.current_state = 'SCORE'
                        continue

                elif self.current_state == 'SCORE':
                    elapsed = time.time() - self.score_start_time
                    text = f"SCORE: {self.score_value}"

                    if elapsed >= self.STATE_SCORE_DURATION:
                        self.current_state = 'CTA'
                        continue
                else:
                    text = f"Estado: {self.current_state}"

                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, self.FONT_SCALE, self.FONT_THICKNESS)[0]
                text_x = (img.shape[1] - text_size[0]) // 2
                text_y = (img.shape[0] + text_size[1]) // 2

                font_size = 32
                text_position = (text_x, text_y)

                img = self.put_text_with_ttf(img, text, self.FONT_PATH, font_size, text_position, self.TEXT_COLOR)
                cv2.imshow("App", img)

        self.cta_cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = LedPanel()
    app.show_state_on_screen()
