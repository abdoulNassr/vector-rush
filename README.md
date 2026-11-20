# Vector Rush

Arcade game in Python + Tkinter. Collect black balls, avoid red balls.

## Install and run

```bash
pip install -r requirements.txt     # only needed for sound
python main.py                      # run it from a terminal
```

Python 3.10+ with Tkinter. Sound is optional: without pygame the game runs silently.
`pygame` and `pygame-ce` both work, but do not install both in the same environment.

## Controls

| Key | Action |
|-----|--------|
| UP / DOWN | Accelerate / decelerate |
| LEFT / RIGHT | Rotate left / right |
| SPACE or ENTER | Start (title screen) |
| SPACE / ENTER | Restart / exit (game over screen) |
| **+ / -** | **Make all text bigger / smaller (saved)** |
| F11 / ESC | Fullscreen on / off |

## Window and text size

- The window starts at about 90% of your screen and can be resized freely
  (minimum 960 x 640), or maximized, or put in fullscreen with F11.
- All text follows the window size. Screens are laid out from measured text,
  so nothing overlaps or leaves the window.
- Text still too small? Press **+** until it is comfortable. The choice is saved
  in `settings.json`.
- To change the size of one kind of text, edit the `FONT` table in `config.py`
  (sizes are for a 1280 x 800 window and are scaled automatically).

## Rules

- Black ball: +5 points. Red ball: -1 life (3 lives, 2 s invulnerability after a hit).
- Every 15 points: new level, more balls, higher speed.
- Walls reflect the player and the balls.
- The best score and the last 10 runs are saved in `scores.json`.

## Files

| File | Role |
|------|------|
| `main.py` | Window setup (size, centering, minimum size) |
| `game.py` | State, game loop, collisions, difficulty, resizing, keyboard |
| `player.py` / `ball.py` | Movement and wall reflection |
| `ui.py` | Start screen, game over screen, top bar (HUD) |
| `config.py` | Colors, window limits, **all text sizes** |
| `scores.py` | Best score and recent runs |
| `audio.py` | Optional sound |
