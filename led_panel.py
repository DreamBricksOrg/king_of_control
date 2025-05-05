import cv2
import numpy as np
import time
import random
from PIL import ImageFont, ImageDraw, Image
from audio_player import AudioPlayer
import threading
from game_status import GameStatus


class LedPanel(threading.Thread):
    def __init__(self,
                 state_play_duration=120,
                 window_size=(1536, 256),
                 font_path="fonts/DS-DIGI.TTF",
                 font_size=160,
                 text_color=(255, 255, 255),
                 countdown_video_path=None,
                 game_video_path=None,
                 goal_video_path=None,
                 cta_image=None,
                 offside_image=None,
                 endgame_image=None,
                 off_image=None,
                 game_audio=None,
                 end_audio=None,
                 cta_audio=None,
                 goal_audio=None,
                 offside_audio=None,
                 countdown_audio=None,

                 background_image_path='images/background.png'):

        super().__init__()
        self.lock = threading.Lock()

        self.STATE_PLAY_DURATION = state_play_duration
        self.WINDOW_SIZE = window_size
        self.FONT_PATH = font_path
        self.FONT_SIZE = font_size
        self.TEXT_COLOR = text_color

        self.current_state = GameStatus.BLANK
        self.last_state = None
        self._running = True

        # Recursos
        self.background_image = self.load_background_image(background_image_path)
        self.black_image = self.create_black_image()
        #self.red_image = self.create_color_image((0, 0, 255))
        #self.red_image = self.create_color_image((128, 128, 128))
        self.red_image = self.load_background_image(r"images\calibration2.png")

        self.cta_image = self.load_background_image(cta_image)
        self.offside_image = self.load_background_image(offside_image)
        self.endgame_image = self.load_background_image(endgame_image)
        self.off_image = self.load_background_image(off_image)

        self.countdown_cap = cv2.VideoCapture(countdown_video_path)
        self.game_cap = cv2.VideoCapture(game_video_path)
        self.goal_cap = cv2.VideoCapture(goal_video_path)

        self.game_cap_delay = 1.0 / self.game_cap.get(cv2.CAP_PROP_FPS)

        self.audio_player = AudioPlayer()

        self.play_start_time = None
        self.score_start_time = None
        self.score_value = None

        self.game_audio = game_audio
        self.end_audio = end_audio
        self.cta_audio = cta_audio
        self.goal_audio = goal_audio
        self.offside_audio = offside_audio
        self.countdown_audio = countdown_audio

    def create_black_image(self):
        return np.full((self.WINDOW_SIZE[1], self.WINDOW_SIZE[0], 3), (0, 0, 0), dtype=np.uint8)

    def create_color_image(self, color):
        return np.full((self.WINDOW_SIZE[1], self.WINDOW_SIZE[0], 3), color, dtype=np.uint8)

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

    def play_video(self, cap):
        if not cap.isOpened():
            print("Erro ao abrir o vídeo")
            self._running = False
            return

        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        frame = cv2.resize(frame, self.WINDOW_SIZE)
        cv2.imshow("App", frame)

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

    def show_blank_screen(self, title="App"):
        cv2.imshow(title, self.black_image)

    def show_red_screen(self, title="App"):
        cv2.imshow(title, self.red_image)

    def show_screen(self, image, title="App"):
        cv2.imshow(title, image)

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

    def create_left_top_window(self, title, width, height):
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.resizeWindow(title, width, height)
        cv2.moveWindow(title, 0, 0)

    def show_calibration_screen(self):
        title = "Calibration"
        self.create_left_top_window(title, 1536, 256)
        self.show_red_screen(title)

    def destroy_calibration_screen(self):
        cv2.destroyWindow("Calibration")

    def run(self):
        #cv2.namedWindow("App", cv2.WINDOW_NORMAL)
        #cv2.setWindowProperty("App", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        #cv2.resizeWindow("App", 1536, 256)
        #cv2.moveWindow("App", 0, 0)
        self.create_left_top_window("App", 1536, 256)

        while self._running:
            with self.lock:
                if self.current_state != self.last_state:
                    print(f"run: {self.current_state}")
                    self.audio_player.stop_all()

                    current_cap = None
                    if self.current_state == GameStatus.CTA:
                        #self.audio_player.play_loop(self.cta_audio)
                        self.show_screen(self.cta_image)

                    elif self.current_state == GameStatus.COUNTDOWN:
                        self.audio_player.play_once(self.countdown_audio)
                        current_cap = self.countdown_cap
                        current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

                    elif self.current_state == GameStatus.GAME:
                        self.audio_player.play_once(self.game_audio)
                        current_cap = self.game_cap
                        current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        #self.show_screen(self.cta_image)

                    elif self.current_state == GameStatus.GOAL:
                        self.audio_player.play_once(self.goal_audio)
                        current_cap = self.goal_cap
                        current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

                    elif self.current_state == GameStatus.OFFSIDE:
                        self.audio_player.play_once(self.offside_audio)
                        self.show_screen(self.offside_image)

                    elif self.current_state == GameStatus.END:
                        self.audio_player.play_once(self.end_audio)
                        self.show_screen(self.endgame_image)

                    elif self.current_state == GameStatus.OFF:
                        self.audio_player.stop_all()
                        self.show_screen(self.off_image)

                    elif self.current_state == GameStatus.BLANK:
                        #self.show_blank_screen()
                        self.show_red_screen()

                    self.last_state = self.current_state

                if self.current_state in [GameStatus.COUNTDOWN, GameStatus.GOAL, GameStatus.GAME]: #
                    self.play_video(current_cap)

            cv2.waitKey(30)

        self.current_cap.release()
        cv2.destroyAllWindows()

    def set_state(self, state):
        with self.lock:
            self.current_state = state

    def set_score_value(self, score):
        with self.lock:
            self.score_value = score


if __name__ == "__main__":
    import parameters as param

    led_panel = LedPanel(
        state_play_duration=param.MAX_TIME,
        countdown_video_path=param.COUNTDOWN_VIDEO,
        game_video_path=param.GAME_VIDEO,
        goal_video_path=param.GOAL_VIDEO,
        cta_image=param.CTA_IMAGE,
        offside_image=param.OFFSIDE_IMAGE,
        endgame_image=param.END_IMAGE,
        game_audio=param.GAME_AUDIO,
        cta_audio=param.CTA_AUDIO,
        goal_audio=param.GOAL_AUDIO,
        off_image=param.OFF_IMAGE,
        end_audio=param.END_AUDIO
    )
    led_panel.start()

    #exit(1)
    print('change state')

    keys = ['0', '1', '2', '3', '4', '5', '6', '7']

    key_idx = 0
    while True:
        #key = cv2.waitKey(30) & 0xFF
        key = keys[key_idx]
        print(key)
        if key == '0':
            led_panel.set_state(GameStatus.BLANK)
        elif key == '1':
            led_panel.set_state(GameStatus.CTA)
        elif key == '2':
            led_panel.set_state(GameStatus.COUNTDOWN)
        elif key == '3':
            led_panel.set_state(GameStatus.GAME)
            #ledPanel.set_score_value(random.randint(0, 9999))
        elif key == '4':
            led_panel.set_state(GameStatus.GOAL)
        elif key == '5':
            led_panel.set_state(GameStatus.OFFSIDE)
        elif key == '6':
            led_panel.set_state(GameStatus.END)
        elif key == '7':
            led_panel.set_state(GameStatus.OFF)
        elif key == 'q':
            led_panel._running = False
            break

        time.sleep(5)
        key_idx = (key_idx+1) % len(keys)
        #ledPanel.show_state_on_screen()


