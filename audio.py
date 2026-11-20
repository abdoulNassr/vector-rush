"""Optional audio support. The game remains playable if Pygame is unavailable."""
from pathlib import Path

class AudioManager:
    def __init__(self):
        self.enabled = False
        self.pygame = None
        self.sounds = {}
        try:
            import pygame
            pygame.mixer.init()
            self.pygame = pygame
            self.enabled = True
            assets = Path(__file__).resolve().parent / "assets"
            for name in ("collect", "level_up", "game_over"):
                path = assets / f"{name}.wav"
                if path.exists():
                    self.sounds[name] = pygame.mixer.Sound(str(path))
            music = assets / "background_music.wav"
            if music.exists():
                pygame.mixer.music.load(str(music))
                pygame.mixer.music.set_volume(0.22)
                pygame.mixer.music.play(-1)
        except Exception:
            # Missing Pygame or unavailable audio device should not stop the game.
            self.enabled = False

    def play(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass

    def close(self):
        if self.enabled:
            try:
                self.pygame.mixer.music.stop()
                self.pygame.mixer.quit()
            except Exception:
                pass
