import pyxel
import json
import copy

# 定数の設定
WINDOW_WIDTH = 240
WINDOW_HEIGHT = 240

#BUTTON_WIDTH = 80
#BUTTON_HEIGHT = 20
BUTTON_WIDTH = 75
BUTTON_HEIGHT = 15
BUTTON_SPACING = 10
BUTTON_AREA_HEIGHT = 100  # ボタンエリアの高さ（縦にボタンを並べるため拡大）
STATUS_AREA_HEIGHT = 30   # 表示エリアの高さ

COLORS = [8, 11, 12, 13, 14, 15, 6, 7]  # 使用可能なPyxelの色番号
DEFAULT_TOP_SCORES = [5120, 2560, 1280, 640, 320, 160, 80, 40, 20, 10]  # デフォルトのトップ10スコア

class Button:
    def __init__(self, x, y, width, height, label):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label

    def is_hovered(self, mx, my):
        return self.x <= mx <= self.x + self.width and self.y <= my <= self.y + self.height

    def draw(self, is_hovered):
        color = pyxel.COLOR_LIGHT_BLUE if is_hovered else pyxel.COLOR_GRAY
        pyxel.rect(self.x, self.y, self.width, self.height, color)
        text_x = self.x + (self.width // 2) - (len(self.label) * 2)
        text_y = self.y + (self.height // 2) - 4
        pyxel.text(text_x, text_y, self.label.capitalize(), pyxel.COLOR_WHITE)

class SameGame:
    def __init__(self):
        # BGM関連の初期化
        self.bgm_files = {
            "opening": "assets/opening_music.json",
            "selection": "assets/selection_music.json",
            "gameplay": "assets/gameplay_music.json",
            "gameover": "assets/gameover_music.json",
            "no_moves": "assets/no_moves_music.json",
            "victory": "assets/victory_music.json",
            "critical": "assets/critical_music.json",
        }
        self.bgm_data = {}
        self.current_bgm = None

        self.load_bgms()

        self.difficulty_levels = {
            "Easy": {"grid_rows": 5, "grid_cols": 5, "colors": 3, "time_limit": None, "score_multiplier": 1.0},
            "Normal": {"grid_rows": 7, "grid_cols": 12, "colors": 4, "time_limit": None, "score_multiplier": 1.2},
            "Hard": {"grid_rows": 9, "grid_cols": 15, "colors": 5, "time_limit": 60, "score_multiplier": 1.5},
            "Very Hard": {"grid_rows": 8, "grid_cols": 15, "colors": 6, "time_limit": 45, "score_multiplier": 2.0},
            "Expert": {"grid_rows": 10, "grid_cols": 20, "colors": 8, "time_limit": 30, "score_multiplier": 3.0},
        }
        self.current_difficulty = "Easy"
        self.grid_rows = self.difficulty_levels[self.current_difficulty]["grid_rows"]
        self.grid_cols = self.difficulty_levels[self.current_difficulty]["grid_cols"]
        self.num_colors = self.difficulty_levels[self.current_difficulty]["colors"]
        self.time_limit = self.difficulty_levels[self.current_difficulty]["time_limit"]
        self.score_multiplier = self.difficulty_levels[self.current_difficulty]["score_multiplier"]

        pyxel.init(WINDOW_WIDTH, WINDOW_HEIGHT)
        pyxel.mouse(True)
        pyxel.title = "SameGame"
        self.state = "opening"
        self.high_scores = DEFAULT_TOP_SCORES[:]
        self.current_score_rank = None
        self.start_time = None
        self.initial_grid = []
        self.bgm_tracks = self.setup_bgm()
        self.current_bgm = None

        self.reset_game(initial=True)
        self.create_sounds()

        self.difficulty_buttons = []
        self.create_difficulty_buttons()

        self.current_bgm = None  # 現在再生中のBGMを記録
        pyxel.run(self.update, self.draw)

    def load_bgms(self):
        for state, file_path in self.bgm_files.items():
            try:
                with open(file_path, "rt") as fin:
                    self.bgm_data[state] = json.loads(fin.read())
            except Exception as e:
                print(f"Error loading BGM file {file_path}: {e}")

    def setup_bgm(self):
        """Initialize BGM mappings for states and game logic."""
        return {
            "opening": 0,              # Intro BGM (track 0)
            "difficulty_selection": 1, # Difficulty selection BGM (track 1)
            "game": 2,                 # Main game BGM (track 2)
            "time_up": 3,              # Game over BGM (track 3)
            "no_moves": 4,             # No moves BGM (track 4)
            "game_cleared": 5,         # Game cleared BGM (track 5)
        }

    def play_bgm(self, state):
        """指定された状態に対応するBGMを再生"""
        if self.current_bgm == state:
            return  # 既に再生中
        self.current_bgm = state
    
        if state in self.bgm_data:
            bgm_channels = [1, 2, 3]  # チャンネル1〜3をBGM用に使用
            for ch, sound in zip(bgm_channels, self.bgm_data[state]):
                pyxel.sound(ch).set(*sound)
                pyxel.play(ch, ch, loop=True)  # 各チャンネルでBGMをループ再生
    
        def stop_bgm(self):
                pyxel.stop()

    def create_difficulty_buttons(self):
        # 各難易度のラベルと説明
        difficulties = [
            {"label": "Easy",      "description": "Small grid, few colors"},
            {"label": "Normal",    "description": "Larger grid, more colors"},
            {"label": "Hard",      "description": "Timed play"},
            {"label": "Very Hard", "description": "Shorter time"},
            {"label": "Expert",    "description": "Maximum challenge"},
        ]
        # ボタンを縦に並べるための開始位置を計算（中央に配置）
        start_x = (WINDOW_WIDTH - BUTTON_WIDTH) // 2 - 60
        start_y = 40
        for i, diff in enumerate(difficulties):
            x = start_x
            y = start_y + i * (BUTTON_HEIGHT + BUTTON_SPACING)
            self.difficulty_buttons.append(Button(x, y, BUTTON_WIDTH, BUTTON_HEIGHT, diff["label"]))
        self.difficulties = difficulties  # 説明のために保持

    def create_sounds(self):
        """ゲーム内の効果音を準備"""
        self.base_notes = ["c2", "d2", "e2", "f2", "g2", "a2", "b2", "c3"]
        for i in range(len(COLORS)):
            pyxel.sound(i).set(
                notes=self.base_notes[i % len(self.base_notes)],
                tones="p",
                volumes="5",
                effects="n",
                speed=15,
            )

    def reset_game(self, initial=False):
        if initial or not hasattr(self, 'initial_grid'):
            self.grid = [
                [pyxel.rndi(0, self.num_colors - 1) for _ in range(self.grid_cols)]
                for _ in range(self.grid_rows)
            ]
            self.initial_grid = copy.deepcopy(self.grid)
        else:
            self.grid = copy.deepcopy(self.initial_grid)
        self.start_time = pyxel.frame_count if self.time_limit else None
        self.score = 0

    def update(self):
        mx, my = pyxel.mouse_x, pyxel.mouse_y

        if self.state == "opening":
            if self.current_bgm != "opening":
                self.play_bgm("opening")
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.state = "difficulty_selection"

        elif self.state == "difficulty_selection":
            if self.current_bgm != "selection":
                self.play_bgm("selection")
            for button in self.difficulty_buttons:
                if button.is_hovered(mx, my):
                    if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                        self.current_difficulty = button.label
                        self.apply_difficulty_settings()
                        self.state = "game"

        elif self.state == "game":
            if self.current_bgm != "gameplay":
                self.play_bgm("gameplay")

            # マウスクリックを処理
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.handle_click(pyxel.mouse_x, pyxel.mouse_y)

            if self.time_limit and pyxel.frame_count - self.start_time > self.time_limit * 30:
                self.state = "time_up"
            elif not self.has_valid_moves():
                self.state = "no_moves"
            elif self.is_grid_empty():
                self.state = "game_cleared"

        elif self.state == "time_up":
            if self.current_bgm != "gameover":
                self.play_bgm("gameover")
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.update_high_scores()
                self.state = "score_display"

        elif self.state == "no_moves":
            if self.current_bgm != "no_moves":
                self.play_bgm("no_moves")
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.update_high_scores()
                self.state = "score_display"

        elif self.state == "game_cleared":
            if self.current_bgm != "victory":
                self.play_bgm("victory")
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.update_high_scores()
                self.state = "score_display"

        elif self.state == "score_display":
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.state = "high_score_display"

        elif self.state == "high_score_display":
            if self.current_bgm != "opening":
                self.play_bgm("opening")
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.state = "opening"

    def apply_difficulty_settings(self):
        settings = self.difficulty_levels[self.current_difficulty]
        self.grid_rows = settings["grid_rows"]
        self.grid_cols = settings["grid_cols"]
        self.num_colors = settings["colors"]
        self.time_limit = settings["time_limit"]
        self.score_multiplier = settings["score_multiplier"]
        self.reset_game(initial=True)

    def handle_click(self, mx, my):
        """盤面クリック時の処理"""
        game_area_y = BUTTON_AREA_HEIGHT
        game_area_height = WINDOW_HEIGHT - BUTTON_AREA_HEIGHT - STATUS_AREA_HEIGHT
        cell_size = min(WINDOW_WIDTH // self.grid_cols, game_area_height // self.grid_rows)
        grid_x_start = (WINDOW_WIDTH - (cell_size * self.grid_cols)) // 2
        grid_y_start = game_area_y + (game_area_height - (cell_size * self.grid_rows)) // 2
    
        x = (mx - grid_x_start) // cell_size
        y = (my - grid_y_start) // cell_size
    
        if 0 <= x < self.grid_cols and 0 <= y < self.grid_rows:
            color = self.grid[y][x]
            if color == -1:
                return
    
            # 消去処理
            blocks_to_remove = self.find_connected_blocks(x, y, color)
            if len(blocks_to_remove) > 1:
                for bx, by in blocks_to_remove:
                    self.grid[by][bx] = -1
    
                # 効果音専用チャンネル（0番）で再生
                pyxel.play(0, color)
                self.score += int(len(blocks_to_remove) * (len(blocks_to_remove) ** 2) * self.score_multiplier)
                self.apply_gravity()
                self.shift_columns_left()

    def find_connected_blocks(self, x, y, color):
        stack = [(x, y)]
        visited = set()
        connected = []

        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            if self.grid[cy][cx] == color:
                connected.append((cx, cy))
                for nx, ny in [(cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)]:
                    if 0 <= nx < self.grid_cols and 0 <= ny < self.grid_rows:
                        stack.append((nx, ny))
        return connected

    def apply_gravity(self):
        for x in range(self.grid_cols):
            column = [self.grid[y][x] for y in range(self.grid_rows) if self.grid[y][x] != -1]
            for y in range(self.grid_rows):
                self.grid[self.grid_rows - y - 1][x] = column[-(y + 1)] if y < len(column) else -1

    def shift_columns_left(self):
        new_grid = []
        for x in range(self.grid_cols):
            # 列が全て -1 ではないときだけ新しいグリッドに追加
            if any(self.grid[y][x] != -1 for y in range(self.grid_rows)):
                new_grid.append([self.grid[y][x] for y in range(self.grid_rows)])
        # 空の列を追加してグリッドサイズを維持
        while len(new_grid) < self.grid_cols:
            new_grid.append([-1] * self.grid_rows)
        # グリッドを更新
        for x in range(self.grid_cols):
            for y in range(self.grid_rows):
                self.grid[y][x] = new_grid[x][y]

    def has_valid_moves(self):
        for y in range(self.grid_rows):
            for x in range(self.grid_cols):
                color = self.grid[y][x]
                if color != -1 and len(self.find_connected_blocks(x, y, color)) > 1:
                    return True
        return False

    def is_grid_empty(self):
        for row in self.grid:
            for cell in row:
                if cell != -1:
                    return False
        return True

    def update_high_scores(self):
        if self.score not in self.high_scores:
            self.high_scores.append(self.score)
        self.high_scores.sort(reverse=True)
        self.high_scores = self.high_scores[:10]
        try:
            self.current_score_rank = self.high_scores.index(self.score)
        except ValueError:
            self.current_score_rank = None

    def draw(self):
        # 画面をクリア
        pyxel.cls(0)

        if self.state == "opening":
            pyxel.text(WINDOW_WIDTH // 2 - 60, WINDOW_HEIGHT // 2 - 10, "Welcome to SameGame", pyxel.COLOR_WHITE)
            pyxel.text(WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT // 2 + 10, "Click to Start", pyxel.COLOR_WHITE)

        elif self.state == "difficulty_selection":
            pyxel.text(WINDOW_WIDTH // 2 - 60, 10, "Select Difficulty", pyxel.COLOR_YELLOW)
            for i, button in enumerate(self.difficulty_buttons):
                is_hovered = button.is_hovered(pyxel.mouse_x, pyxel.mouse_y)
                button.draw(is_hovered)
                # 説明文をボタンの右側に表示
                description = self.difficulties[i]["description"]
                pyxel.text(button.x + button.width + 10, button.y + 5, description, pyxel.COLOR_WHITE)

        elif self.state == "game":
            # 盤面とボタン・ステータスを描画
            self.draw_buttons()
            self.draw_grid()
            self.draw_score_and_time()

        elif self.state in ["time_up", "no_moves", "gave_up", "game_cleared"]:
            # 盤面を消さずにそのまま描画し、上にテキストを重ねる
            self.draw_buttons()
            self.draw_grid()
            self.draw_score_and_time()

            # それぞれの状態に応じたメッセージを上書き
            if self.state == "time_up":
                pyxel.text(WINDOW_WIDTH // 2 - 30, WINDOW_HEIGHT // 2 - 10, "Time's Up!", pyxel.COLOR_RED)
            elif self.state == "no_moves":
                pyxel.text(WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT // 2 - 10, "No Moves Available!", pyxel.COLOR_RED)
            elif self.state == "gave_up":
                pyxel.text(WINDOW_WIDTH // 2 - 60, WINDOW_HEIGHT // 2 - 10, "You gave up this game.", pyxel.COLOR_RED)
            elif self.state == "game_cleared":
                pyxel.text(WINDOW_WIDTH // 2 - 70, WINDOW_HEIGHT // 2 - 10, "Congratulations!", pyxel.COLOR_GREEN)
                pyxel.text(WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT // 2 + 10, "You cleared the game!", pyxel.COLOR_WHITE)

            pyxel.text(WINDOW_WIDTH // 2 - 30, WINDOW_HEIGHT // 2 + 10, f"Score: {int(self.score)}", pyxel.COLOR_WHITE)
            pyxel.text(WINDOW_WIDTH // 2 - 40, WINDOW_HEIGHT // 2 + 30, "Click to Continue", pyxel.COLOR_WHITE)

        elif self.state == "score_display":
            pyxel.text(WINDOW_WIDTH // 2 - 30, WINDOW_HEIGHT // 2 - 20, "Your Score", pyxel.COLOR_YELLOW)
            pyxel.text(WINDOW_WIDTH // 2 - 20, WINDOW_HEIGHT // 2, f"{int(self.score)}", pyxel.COLOR_YELLOW)
            pyxel.text(WINDOW_WIDTH // 2 - 40, WINDOW_HEIGHT // 2 + 20, "Click to Continue", pyxel.COLOR_WHITE)

        elif self.state == "high_score_display":
            pyxel.text(WINDOW_WIDTH // 2 - 60, 10, "Top 10 High Scores", pyxel.COLOR_YELLOW)
            for i, score in enumerate(self.high_scores):
                color = pyxel.COLOR_YELLOW if i == self.current_score_rank else pyxel.COLOR_WHITE
                pyxel.text(WINDOW_WIDTH // 2 - 30, 30 + i * 10, f"{i + 1}: {score}", color)
            pyxel.text(WINDOW_WIDTH // 2 - 40, WINDOW_HEIGHT - 20, "Click to Return", pyxel.COLOR_WHITE)

    def draw_buttons(self):
        """
        ボタンエリア(上部)の描画
        Retry/ Quit ボタンを左に配置し、
        難易度を右端に表示する。
        """
        # Retry ボタン
        retry_x = BUTTON_SPACING
        retry_y = (BUTTON_AREA_HEIGHT - BUTTON_HEIGHT) // 2
        pyxel.rect(retry_x, retry_y, BUTTON_WIDTH, BUTTON_HEIGHT, pyxel.COLOR_GRAY)
        pyxel.text(retry_x + 10, retry_y + 5, "Retry", pyxel.COLOR_WHITE)

        # Quit ボタン
        quit_x = BUTTON_SPACING + BUTTON_WIDTH + BUTTON_SPACING
        quit_y = (BUTTON_AREA_HEIGHT - BUTTON_HEIGHT) // 2
        pyxel.rect(quit_x, quit_y, BUTTON_WIDTH, BUTTON_HEIGHT, pyxel.COLOR_GRAY)
        pyxel.text(quit_x + 10, quit_y + 5, "Quit", pyxel.COLOR_WHITE)

        # 難易度名をボタンエリア右端に表示
        difficulty_text_x = WINDOW_WIDTH - 60
        difficulty_text_y = (BUTTON_AREA_HEIGHT - 8) // 2
        pyxel.text(difficulty_text_x, difficulty_text_y, self.current_difficulty, pyxel.COLOR_WHITE)

    def draw_grid(self):
        """
        盤面を描画
        """
        game_area_y = BUTTON_AREA_HEIGHT
        game_area_height = WINDOW_HEIGHT - BUTTON_AREA_HEIGHT - STATUS_AREA_HEIGHT
        cell_size = min(WINDOW_WIDTH // self.grid_cols, game_area_height // self.grid_rows)
        grid_x_start = (WINDOW_WIDTH - (cell_size * self.grid_cols)) // 2
        grid_y_start = game_area_y + (game_area_height - (cell_size * self.grid_rows)) // 2

        for y in range(self.grid_rows):
            for x in range(self.grid_cols):
                color = self.grid[y][x]
                if color != -1:
                    pyxel.rect(
                        grid_x_start + x * cell_size,
                        grid_y_start + y * cell_size,
                        cell_size,
                        cell_size,
                        COLORS[color]
                    )

    def draw_score_and_time(self):
        """
        画面下部にスコアと時間のみを描画
        """
        # スコア表示
        score_text = f"Score: {int(self.score)}"
        pyxel.text(10, WINDOW_HEIGHT - STATUS_AREA_HEIGHT + 5, score_text, pyxel.COLOR_WHITE)

        # タイマー表示
        if self.time_limit:
            remaining_time = max(0, self.time_limit - (pyxel.frame_count - self.start_time) // 30)
            time_text = f"Time: {remaining_time}s"
        else:
            time_text = "Time: --"
        time_text_width = len(time_text) * 4  # おおまかな文字幅
        pyxel.text(WINDOW_WIDTH - time_text_width - 10, WINDOW_HEIGHT - STATUS_AREA_HEIGHT + 5, time_text, pyxel.COLOR_WHITE)


# ゲームの開始
SameGame()
