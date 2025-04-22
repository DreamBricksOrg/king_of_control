import simpleaudio as sa
import os

class AudioPlayer:
    def __init__(self, audio_folder="audios"):
        self.audio_folder = audio_folder
        self.cache = {}
        self.loop_play_obj = None
        self.loop_wave_obj = None
        self.loop_playing_obj = None
        self.active_play_objs = {}

    def _get_audio_path(self, name):
        return os.path.join(self.audio_folder, f"{name}.wav")

    def _load_audio(self, name):
        if name not in self.cache:
            path = self._get_audio_path(name)
            if not os.path.isfile(path):
                print(f"Áudio '{name}' não encontrado em '{self.audio_folder}'")
                return None
            try:
                self.cache[name] = sa.WaveObject.from_wave_file(path)
            except Exception as e:
                print(f"Erro ao carregar '{name}': {e}")
                return None
        return self.cache[name]

    def play_once(self, name):
        wave_obj = self._load_audio(name)
        if wave_obj:
            play_obj = wave_obj.play()
            self.active_play_objs[name] = play_obj
            return play_obj

    def play_loop(self, name):
        wave_obj = self._load_audio(name)
        if wave_obj:
            self.stop_loop()
            self.loop_wave_obj = wave_obj
            self._loop_audio()

    def _loop_audio(self):
        def loop_play():
            while self.loop_wave_obj:
                play_obj = self.loop_wave_obj.play()
                self.loop_playing_obj = play_obj
                play_obj.wait_done()
            self.loop_playing_obj = None  # Limpa ao sair do loop

        import threading
        thread = threading.Thread(target=loop_play, daemon=True)
        thread.start()
        self.loop_play_obj = thread

    def stop_loop(self):
        self.loop_wave_obj = None
        if self.loop_playing_obj and self.loop_playing_obj.is_playing():
            self.loop_playing_obj.stop()
        self.loop_playing_obj = None

    def stop_all(self):
        self.stop_loop()
        for play_obj in self.active_play_objs.values():
            if play_obj.is_playing():
                play_obj.stop()
        self.active_play_objs.clear()

    def stop_audio(self, name):
        play_obj = self.active_play_objs.get(name)
        if play_obj and play_obj.is_playing():
            play_obj.stop()
            del self.active_play_objs[name]
