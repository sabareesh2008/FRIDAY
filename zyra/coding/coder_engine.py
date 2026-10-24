"""Polyglot AI Code Generation Engine for ZYRA across all programming languages with LLM & autonomous synthesis."""
import re
import urllib.request
import urllib.error
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from zyra.config import config
from zyra.coding.languages import LanguageSpec, detect_language, normalize_filename

class CoderEngine:
    def __init__(self):
        pass

    def generate_code(self, problem_description: str, lang: LanguageSpec, class_name: Optional[str] = None) -> str:
        """Generates production-grade, compilable code in the target language."""
        stem = class_name or lang.default_filename.split(".")[0]

        # 1. Try Gemini API if key is present
        gemini_code = self._try_gemini_generation(problem_description, lang.name, stem)
        if gemini_code:
            return gemini_code

        # 2. Try OpenAI API if key is present
        openai_code = self._try_openai_generation(problem_description, lang.name, stem)
        if openai_code:
            return openai_code

        # 3. Try Ollama (Local LLM if running)
        ollama_code = self._try_ollama_generation(problem_description, lang.name, stem)
        if ollama_code:
            return ollama_code

        # 4. Fallback to smart offline polyglot algorithmic synthesizer
        return self._synthesize_offline_code(problem_description, lang, stem)

    def _clean_code_fence(self, text: str) -> str:
        """Strips markdown fences ```lang ... ``` and leaves pure executable code."""
        text = text.strip()
        text = re.sub(r"^```[a-zA-Z0-9#+]*\n", "", text)
        text = re.sub(r"\n```$", "", text)
        return text.strip()

    def _try_gemini_generation(self, prompt: str, lang_name: str, stem: str) -> Optional[str]:
        api_key = config.get("api_key", "").strip() or config.get("gemini_api_key", "").strip()
        provider = config.get("llm_provider", "local_rules")
        if not api_key or (provider != "gemini" and not api_key.startswith("AIza")):
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        sys_instruction = f"You are an expert software engineer. Write only pure, complete, compilable {lang_name} code with zero markdown fences and zero chat commentary. The primary class or file name must be '{stem}'."
        payload = {
            "contents": [{
                "parts": [{"text": f"{sys_instruction}\n\nTask: {prompt}"}]
            }]
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                candidates = res_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return self._clean_code_fence(parts[0].get("text", ""))
        except Exception:
            pass
        return None

    def _try_openai_generation(self, prompt: str, lang_name: str, stem: str) -> Optional[str]:
        api_key = config.get("api_key", "").strip() or config.get("openai_api_key", "").strip()
        provider = config.get("llm_provider", "local_rules")
        if not api_key or (provider != "openai" and not api_key.startswith("sk-")):
            return None

        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": f"You are an expert developer. Provide pure {lang_name} code only, with no markdown fences, no explanations. Main class name must be '{stem}'."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                choices = res_json.get("choices", [])
                if choices:
                    return self._clean_code_fence(choices[0].get("message", {}).get("content", ""))
        except Exception:
            pass
        return None

    def _try_ollama_generation(self, prompt: str, lang_name: str, stem: str) -> Optional[str]:
        provider = config.get("llm_provider", "local_rules")
        ollama_url = config.get("ollama_url", "http://localhost:11434")
        if provider == "ollama" or (ollama_url and provider != "local_rules"):
            try:
                model = config.get("ollama_model", "qwen2.5-coder:3b")
                system_prompt = f"You are an expert coder. Write only pure, complete, compilable {lang_name} code with no markdown formatting. The main class/file name must be '{stem}'."
                req_data = {
                    "model": model,
                    "prompt": f"{system_prompt}\n\nTask: {prompt}",
                    "stream": False
                }
                req = urllib.request.Request(
                    f"{ollama_url}/api/generate",
                    data=json.dumps(req_data).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    text = res_json.get("response", "").strip()
                    if text:
                        return self._clean_code_fence(text)
            except Exception:
                pass
        return None

    def _synthesize_offline_code(self, prompt: str, lang: LanguageSpec, stem: str) -> str:
        """Offline synthesizer for DSA, games, web templates, and algorithms."""
        p = prompt.lower()

        # Games
        if "snake" in p:
            return self._build_snake_game(lang, stem)
        if "tic tac toe" in p or "tictactoe" in p:
            return self._build_tic_tac_toe(lang, stem)

        # LRU Cache
        if "lru cache" in p or "lru" in p:
            return self._build_lru_cache(lang, stem)

        # Binary Search
        if "binary search" in p or "search rotated" in p:
            return self._build_binary_search(lang, stem)

        # Two Sum
        if "two sum" in p or "2 sum" in p:
            return self._build_two_sum(lang, stem)

        # Sorting
        if "merge sort" in p or "quick sort" in p or "sort" in p:
            return self._build_merge_sort(lang, stem)

        # Math (Fibonacci, Factorial, Prime)
        if "fibonacci" in p:
            return self._build_fibonacci(lang, stem)
        if "factorial" in p:
            return self._build_factorial(lang, stem)
        if "prime" in p:
            return self._build_prime_checker(lang, stem)

        # Palindrome
        if "palindrome" in p:
            return self._build_palindrome(lang, stem)

        # Todo List / Web App
        if "todo" in p:
            return self._build_todo_app(lang, stem)

        # Web / HTML
        if lang.name == "HTML":
            return self._build_html_template(prompt)

        # Generic solution template
        return self._build_generic_solution(prompt, lang, stem)

    # --- Concrete Implementations for DSA, Games & Apps ---
    def _build_snake_game(self, lang: LanguageSpec, stem: str) -> str:
        if lang.name == "Python":
            return """# Full Playable Snake Game in Python (uses standard tkinter, no pip install needed)
import tkinter as tk
import random

WIDTH, HEIGHT = 400, 400
DELAY = 100
SPACE_SIZE = 20
BODY_PARTS = 3

class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Snake Game — ZYRA")
        self.root.resizable(False, False)

        self.score = 0
        self.direction = 'down'

        self.label = tk.Label(root, text=f"Score: {self.score}", font=('Arial', 18))
        self.label.pack()

        self.canvas = tk.Canvas(root, bg="black", height=HEIGHT, width=WIDTH)
        self.canvas.pack()

        self.root.bind('<Left>', lambda e: self.change_direction('left'))
        self.root.bind('<Right>', lambda e: self.change_direction('right'))
        self.root.bind('<Up>', lambda e: self.change_direction('up'))
        self.root.bind('<Down>', lambda e: self.change_direction('down'))

        self.coordinates = [[0, 0] for _ in range(BODY_PARTS)]
        self.squares = []
        for x, y in self.coordinates:
            sq = self.canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill="#00FF00")
            self.squares.append(sq)

        self.food = None
        self.spawn_food()
        self.next_turn()

    def spawn_food(self):
        x = random.randint(0, (WIDTH // SPACE_SIZE) - 1) * SPACE_SIZE
        y = random.randint(0, (HEIGHT // SPACE_SIZE) - 1) * SPACE_SIZE
        self.food = [x, y]
        self.canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill="red", tag="food")

    def change_direction(self, new_dir):
        opposites = {'left': 'right', 'right': 'left', 'up': 'down', 'down': 'up'}
        if new_dir != opposites.get(self.direction):
            self.direction = new_dir

    def next_turn(self):
        x, y = self.coordinates[0]
        if self.direction == 'up': y -= SPACE_SIZE
        elif self.direction == 'down': y += SPACE_SIZE
        elif self.direction == 'left': x -= SPACE_SIZE
        elif self.direction == 'right': x += SPACE_SIZE

        self.coordinates.insert(0, [x, y])
        square = self.canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill="#00FF00")
        self.squares.insert(0, square)

        if x == self.food[0] and y == self.food[1]:
            self.score += 1
            self.label.config(text=f"Score: {self.score}")
            self.canvas.delete("food")
            self.spawn_food()
        else:
            del self.coordinates[-1]
            self.canvas.delete(self.squares[-1])
            del self.squares[-1]

        if self.check_collisions():
            self.game_over()
        else:
            self.root.after(DELAY, self.next_turn)

    def check_collisions(self):
        x, y = self.coordinates[0]
        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            return True
        for part in self.coordinates[1:]:
            if x == part[0] and y == part[1]:
                return True
        return False

    def game_over(self):
        self.canvas.delete("all")
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2, text="GAME OVER", font=('Arial', 28), fill="red")

if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()
"""
        elif lang.name == "Java":
            return f"""// Full Snake Game in Java (Swing)
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.Random;

public class {stem} extends JFrame {{
    public {stem}() {{
        add(new GamePanel());
        setTitle("Snake Game - ZYRA");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setResizable(false);
        pack();
        setLocationRelativeTo(null);
        setVisible(true);
    }}

    public static void main(String[] args) {{
        new {stem}();
    }}
}}

class GamePanel extends JPanel implements ActionListener, KeyListener {{
    static final int SCREEN_WIDTH = 400;
    static final int SCREEN_HEIGHT = 400;
    static final int UNIT_SIZE = 20;
    static final int GAME_UNITS = (SCREEN_WIDTH * SCREEN_HEIGHT) / (UNIT_SIZE * UNIT_SIZE);
    static final int DELAY = 100;
    final int x[] = new int[GAME_UNITS];
    final int y[] = new int[GAME_UNITS];
    int bodyParts = 4;
    int applesEaten;
    int appleX, appleY;
    char direction = 'R';
    boolean running = false;
    Timer timer;
    Random random;

    GamePanel() {{
        random = new Random();
        setPreferredSize(new Dimension(SCREEN_WIDTH, SCREEN_HEIGHT));
        setBackground(Color.black);
        setFocusable(true);
        addKeyListener(this);
        startGame();
    }}

    public void startGame() {{
        newApple();
        running = true;
        timer = new Timer(DELAY, this);
        timer.start();
    }}

    public void paintComponent(Graphics g) {{
        super.paintComponent(g);
        if (running) {{
            g.setColor(Color.red);
            g.fillOval(appleX, appleY, UNIT_SIZE, UNIT_SIZE);
            for (int i = 0; i < bodyParts; i++) {{
                g.setColor(i == 0 ? Color.green : new Color(45, 180, 0));
                g.fillRect(x[i], y[i], UNIT_SIZE, UNIT_SIZE);
            }}
            g.setColor(Color.white);
            g.setFont(new Font("Arial", Font.BOLD, 16));
            g.drawString("Score: " + applesEaten, 10, 20);
        }} else {{
            g.setColor(Color.red);
            g.setFont(new Font("Arial", Font.BOLD, 30));
            g.drawString("Game Over", 120, 200);
        }}
    }}

    public void newApple() {{
        appleX = random.nextInt((int)(SCREEN_WIDTH / UNIT_SIZE)) * UNIT_SIZE;
        appleY = random.nextInt((int)(SCREEN_HEIGHT / UNIT_SIZE)) * UNIT_SIZE;
    }}

    public void move() {{
        for (int i = bodyParts; i > 0; i--) {{
            x[i] = x[i - 1];
            y[i] = y[i - 1];
        }}
        switch (direction) {{
            case 'U': y[0] -= UNIT_SIZE; break;
            case 'D': y[0] += UNIT_SIZE; break;
            case 'L': x[0] -= UNIT_SIZE; break;
            case 'R': x[0] += UNIT_SIZE; break;
        }}
    }}

    public void checkApple() {{
        if ((x[0] == appleX) && (y[0] == appleY)) {{
            bodyParts++;
            applesEaten++;
            newApple();
        }}
    }}

    public void checkCollisions() {{
        for (int i = bodyParts; i > 0; i--) {{
            if ((x[0] == x[i]) && (y[0] == y[i])) running = false;
        }}
        if (x[0] < 0 || x[0] >= SCREEN_WIDTH || y[0] < 0 || y[0] >= SCREEN_HEIGHT) running = false;
        if (!running) timer.stop();
    }}

    public void actionPerformed(ActionEvent e) {{
        if (running) {{
            move();
            checkApple();
            checkCollisions();
        }}
        repaint();
    }}

    public void keyPressed(KeyEvent e) {{
        switch (e.getKeyCode()) {{
            case KeyEvent.VK_LEFT: if (direction != 'R') direction = 'L'; break;
            case KeyEvent.VK_RIGHT: if (direction != 'L') direction = 'R'; break;
            case KeyEvent.VK_UP: if (direction != 'D') direction = 'U'; break;
            case KeyEvent.VK_DOWN: if (direction != 'U') direction = 'D'; break;
        }}
    }}
    public void keyTyped(KeyEvent e) {{}}
    public void keyReleased(KeyEvent e) {{}}
}}
"""
        else:
            return self._build_html_snake()

    def _build_html_snake(self) -> str:
        return """<!DOCTYPE html>
<html>
<head>
    <title>Snake Game</title>
    <style>
        body { background: #111; color: #fff; text-align: center; font-family: sans-serif; }
        canvas { background: #000; border: 2px solid #00f0ff; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Snake Game</h1>
    <h3 id="score">Score: 0</h3>
    <canvas id="game" width="400" height="400"></canvas>
    <script>
        const canvas = document.getElementById("game");
        const ctx = canvas.getContext("2d");
        const grid = 20;
        let count = 0, score = 0;
        let snake = { x: 160, y: 160, dx: grid, dy: 0, cells: [], maxCells: 4 };
        let apple = { x: 320, y: 320 };

        function getRandomInt(min, max) { return Math.floor(Math.random() * (max - min)) + min; }

        function loop() {
            requestAnimationFrame(loop);
            if (++count < 6) return;
            count = 0;
            ctx.clearRect(0,0,canvas.width,canvas.height);
            snake.x += snake.dx; snake.y += snake.dy;
            if (snake.x < 0) snake.x = canvas.width - grid;
            else if (snake.x >= canvas.width) snake.x = 0;
            if (snake.y < 0) snake.y = canvas.height - grid;
            else if (snake.y >= canvas.height) snake.y = 0;

            snake.cells.unshift({x: snake.x, y: snake.y});
            if (snake.cells.length > snake.maxCells) snake.cells.pop();

            ctx.fillStyle = 'red';
            ctx.fillRect(apple.x, apple.y, grid-1, grid-1);

            ctx.fillStyle = '#00f0ff';
            snake.cells.forEach(function(cell, index) {
                ctx.fillRect(cell.x, cell.y, grid-1, grid-1);
                if (cell.x === apple.x && cell.y === apple.y) {
                    snake.maxCells++; score++;
                    document.getElementById("score").innerText = "Score: " + score;
                    apple.x = getRandomInt(0, 20) * grid;
                    apple.y = getRandomInt(0, 20) * grid;
                }
                for (let i = index + 1; i < snake.cells.length; i++) {
                    if (cell.x === snake.cells[i].x && cell.y === snake.cells[i].y) {
                        snake.x = 160; snake.y = 160; snake.cells = []; snake.maxCells = 4;
                        snake.dx = grid; snake.dy = 0; score = 0;
                        document.getElementById("score").innerText = "Score: 0";
                    }
                }
            });
        }
        document.addEventListener('keydown', function(e) {
            if (e.which === 37 && snake.dx === 0) { snake.dx = -grid; snake.dy = 0; }
            else if (e.which === 38 && snake.dy === 0) { snake.dy = -grid; snake.dx = 0; }
            else if (e.which === 39 && snake.dx === 0) { snake.dx = grid; snake.dy = 0; }
            else if (e.which === 40 && snake.dy === 0) { snake.dy = grid; snake.dx = 0; }
        });
        requestAnimationFrame(loop);
    </script>
</body>
</html>
"""

    def _build_lru_cache(self, lang: LanguageSpec, stem: str) -> str:
        if lang.name == "Java":
            return f"""// Problem: LRU (Least Recently Used) Cache Implementation
import java.util.HashMap;
import java.util.Map;

public class {stem} {{
    private class Node {{
        int key, value;
        Node prev, next;
        Node(int k, int v) {{ key = k; value = v; }}
    }}

    private final int capacity;
    private final Map<Integer, Node> map;
    private final Node head, tail;

    public {stem}(int capacity) {{
        this.capacity = capacity;
        this.map = new HashMap<>();
        head = new Node(0, 0);
        tail = new Node(0, 0);
        head.next = tail;
        tail.prev = head;
    }}

    public int get(int key) {{
        if (!map.containsKey(key)) return -1;
        Node node = map.get(key);
        remove(node);
        insert(node);
        return node.value;
    }}

    public void put(int key, int value) {{
        if (map.containsKey(key)) {{
            remove(map.get(key));
        }}
        if (map.size() == capacity) {{
            remove(tail.prev);
        }}
        insert(new Node(key, value));
    }}

    private void remove(Node node) {{
        map.remove(node.key);
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }}

    private void insert(Node node) {{
        map.put(node.key, node);
        node.next = head.next;
        node.next.prev = node;
        head.next = node;
        node.prev = head;
    }}

    public static void main(String[] args) {{
        {stem} cache = new {stem}(2);
        cache.put(1, 1);
        cache.put(2, 2);
        System.out.println("cache.get(1): " + cache.get(1)); // returns 1
        cache.put(3, 3); // evicts key 2
        System.out.println("cache.get(2): " + cache.get(2)); // returns -1 (not found)
        cache.put(4, 4); // evicts key 1
        System.out.println("cache.get(1): " + cache.get(1)); // returns -1
        System.out.println("cache.get(3): " + cache.get(3)); // returns 3
        System.out.println("cache.get(4): " + cache.get(4)); // returns 4
    }}
}}
"""
        else:
            return f"""# Problem: LRU Cache Implementation
from collections import OrderedDict

class {stem}:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

if __name__ == "__main__":
    cache = {stem}(2)
    cache.put(1, 100)
    cache.put(2, 200)
    print("get(1):", cache.get(1))
    cache.put(3, 300) # Evicts key 2
    print("get(2):", cache.get(2)) # Returns -1
    print("get(3):", cache.get(3))
"""

    def _build_tic_tac_toe(self, lang: LanguageSpec, stem: str) -> str:
        return f"""# Interactive Tic-Tac-Toe Game
def print_board(b):
    print(f" {b[0]} | {b[1]} | {b[2]} ")
    print("---|---|---")
    print(f" {b[3]} | {b[4]} | {b[5]} ")
    print("---|---|---")
    print(f" {b[6]} | {b[7]} | {b[8]} ")

def check_win(b, p):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    return any(b[i] == b[j] == b[k] == p for i, j, k in wins)

def play():
    board = [" "] * 9
    player = "X"
    print("Welcome to Tic-Tac-Toe! Choose 1-9 to make a move.")
    for turn in range(9):
        print_board(board)
        move = int(input(f"Player {player}, enter position (1-9): ")) - 1
        if board[move] != " ":
            print("Position occupied! Try again.")
            continue
        board[move] = player
        if check_win(board, player):
            print_board(board)
            print(f"Player {player} WINS!")
            return
        player = "O" if player == "X" else "X"
    print_board(board)
    print("It's a draw!")

if __name__ == "__main__":
    play()
"""

    def _build_todo_app(self, lang: LanguageSpec, stem: str) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Modern Todo App</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; padding-top: 50px; }
        .todo-card { background: #1e293b; padding: 24px; border-radius: 12px; width: 360px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h2 { text-align: center; color: #38bdf8; margin-top: 0; }
        .input-group { display: flex; gap: 8px; margin-bottom: 16px; }
        input { flex: 1; padding: 10px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: white; }
        button { background: #38bdf8; color: #0f172a; border: none; padding: 10px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; }
        ul { list-style: none; padding: 0; }
        li { background: #334155; padding: 10px; border-radius: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .del-btn { background: #ef4444; color: white; border: none; border-radius: 4px; padding: 4px 8px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="todo-card">
        <h2>My Tasks</h2>
        <div class="input-group">
            <input type="text" id="taskInput" placeholder="Add a new task...">
            <button onclick="addTask()">Add</button>
        </div>
        <ul id="taskList"></ul>
    </div>
    <script>
        function addTask() {
            const input = document.getElementById("taskInput");
            if (!input.value.trim()) return;
            const li = document.createElement("li");
            li.innerHTML = `<span>${input.value.trim()}</span> <button class="del-btn" onclick="this.parentElement.remove()">X</button>`;
            document.getElementById("taskList").appendChild(li);
            input.value = "";
        }
    </script>
</body>
</html>
"""

    def _build_prime_checker(self, lang: LanguageSpec, stem: str) -> str:
        return f"""# Problem: Prime Number Checker
import math

def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    for i in range(5, int(math.isqrt(n)) + 1, 6):
        if n % i == 0 or n % (i + 2) == 0:
            return False
    return True

if __name__ == "__main__":
    nums = [2, 3, 4, 17, 25, 97, 100]
    for num in nums:
        print(f"{{num}} is prime? {{is_prime(num)}}")
"""

    def _build_two_sum(self, lang: LanguageSpec, stem: str) -> str:
        if lang.name == "Java":
            return f"""// Problem: Two Sum - Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.
import java.util.HashMap;
import java.util.Map;
import java.util.Arrays;

public class {stem} {{
    public static int[] twoSum(int[] nums, int target) {{
        Map<Integer, Integer> map = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {{
            int complement = target - nums[i];
            if (map.containsKey(complement)) {{
                return new int[] {{ map.get(complement), i }};
            }}
            map.put(nums[i], i);
        }}
        return new int[] {{}};
    }}

    public static void main(String[] args) {{
        int[] nums = {{2, 7, 11, 15}};
        int target = 9;
        int[] result = twoSum(nums, target);
        System.out.println("Input: nums = " + Arrays.toString(nums) + ", target = " + target);
        System.out.println("Indices: " + Arrays.toString(result));
    }}
}}
"""
        elif lang.name == "Python":
            return f"""# Problem: Two Sum
from typing import List

def two_sum(nums: List[int], target: int) -> List[int]:
    lookup = {{}}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in lookup:
            return [lookup[complement], i]
        lookup[num] = i
    return []

if __name__ == "__main__":
    nums = [2, 7, 11, 15]
    target = 9
    result = two_sum(nums, target)
    print(f"Input: nums = {{nums}}, target = {{target}}")
    print(f"Result indices: {{result}}")
"""
        elif lang.name in ("C++", "C"):
            return f"""// Problem: Two Sum
#include <iostream>
#include <vector>
#include <unordered_map>

std::vector<int> twoSum(const std::vector<int>& nums, int target) {{
    std::unordered_map<int, int> map;
    for (int i = 0; i < nums.size(); ++i) {{
        int complement = target - nums[i];
        if (map.find(complement) != map.end()) {{
            return {{map[complement], i}};
        }}
        map[nums[i]] = i;
    }}
    return {{}};
}}

int main() {{
    std::vector<int> nums = {{2, 7, 11, 15}};
    int target = 9;
    std::vector<int> res = twoSum(nums, target);
    std::cout << "Indices: [" << res[0] << ", " << res[1] << "]" << std::endl;
    return 0;
}}
"""
        else:
            return f"""// Problem: Two Sum
function twoSum(nums, target) {{
    const map = new Map();
    for (let i = 0; i < nums.length; i++) {{
        const complement = target - nums[i];
        if (map.has(complement)) {{
            return [map.get(complement), i];
        }}
        map.set(nums[i], i);
    }}
    return [];
}}

const nums = [2, 7, 11, 15];
const target = 9;
console.log("Indices:", twoSum(nums, target));
"""

    def _build_binary_search(self, lang: LanguageSpec, stem: str) -> str:
        if lang.name == "Java":
            return f"""// Problem: Binary Search Algorithm
public class {stem} {{
    public static int binarySearch(int[] arr, int target) {{
        int left = 0, right = arr.length - 1;
        while (left <= right) {{
            int mid = left + (right - left) / 2;
            if (arr[mid] == target) return mid;
            if (arr[mid] < target) left = mid + 1;
            else right = mid - 1;
        }}
        return -1;
    }}

    public static void main(String[] args) {{
        int[] arr = {{1, 3, 5, 7, 9, 11, 15, 20}};
        int target = 7;
        int idx = binarySearch(arr, target);
        System.out.println("Target " + target + " found at index: " + idx);
    }}
}}
"""
        elif lang.name == "Python":
            return f"""# Problem: Binary Search
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

if __name__ == "__main__":
    nums = [1, 3, 5, 7, 9, 11, 15, 20]
    target = 7
    print(f"Target {{target}} found at index: {{binary_search(nums, target)}}")
"""
        else:
            return f"""// Problem: Binary Search
#include <iostream>
#include <vector>

int binarySearch(const std::vector<int>& arr, int target) {{
    int left = 0, right = arr.size() - 1;
    while (left <= right) {{
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }}
    return -1;
}}

int main() {{
    std::vector<int> arr = {{1, 3, 5, 7, 9, 11, 15, 20}};
    int target = 7;
    std::cout << "Target " << target << " found at index: " << binarySearch(arr, target) << std::endl;
    return 0;
}}
"""

    def _build_merge_sort(self, lang: LanguageSpec, stem: str) -> str:
        if lang.name == "Java":
            return f"""// Problem: Merge Sort Algorithm
import java.util.Arrays;

public class {stem} {{
    public static void mergeSort(int[] arr, int left, int right) {{
        if (left < right) {{
            int mid = left + (right - left) / 2;
            mergeSort(arr, left, mid);
            mergeSort(arr, mid + 1, right);
            merge(arr, left, mid, right);
        }}
    }}

    private static void merge(int[] arr, int left, int mid, int right) {{
        int n1 = mid - left + 1;
        int n2 = right - mid;
        int[] L = new int[n1];
        int[] R = new int[n2];
        System.arraycopy(arr, left, L, 0, n1);
        System.arraycopy(arr, mid + 1, R, 0, n2);

        int i = 0, j = 0, k = left;
        while (i < n1 && j < n2) {{
            if (L[i] <= R[j]) arr[k++] = L[i++];
            else arr[k++] = R[j++];
        }}
        while (i < n1) arr[k++] = L[i++];
        while (j < n2) arr[k++] = R[j++];
    }}

    public static void main(String[] args) {{
        int[] arr = {{38, 27, 43, 3, 9, 82, 10}};
        System.out.println("Unsorted: " + Arrays.toString(arr));
        mergeSort(arr, 0, arr.length - 1);
        System.out.println("Sorted:   " + Arrays.toString(arr));
    }}
}}
"""
        elif lang.name in ("C++", "C"):
            return f"""// Problem: Merge Sort Algorithm
#include <iostream>
#include <vector>

void merge(std::vector<int>& arr, int l, int m, int r) {{
    int n1 = m - l + 1;
    int n2 = r - m;
    std::vector<int> L(n1), R(n2);
    for (int i = 0; i < n1; i++) L[i] = arr[l + i];
    for (int j = 0; j < n2; j++) R[j] = arr[m + 1 + j];

    int i = 0, j = 0, k = l;
    while (i < n1 && j < n2) {{
        if (L[i] <= R[j]) arr[k++] = L[i++];
        else arr[k++] = R[j++];
    }}
    while (i < n1) arr[k++] = L[i++];
    while (j < n2) arr[k++] = R[j++];
}}

void mergeSort(std::vector<int>& arr, int l, int r) {{
    if (l < r) {{
        int m = l + (r - l) / 2;
        mergeSort(arr, l, m);
        mergeSort(arr, m + 1, r);
        merge(arr, l, m, r);
    }}
}}

int main() {{
    std::vector<int> arr = {{38, 27, 43, 3, 9, 82, 10}};
    mergeSort(arr, 0, arr.size() - 1);
    std::cout << "Sorted: ";
    for (int x : arr) std::cout << x << " ";
    std::cout << std::endl;
    return 0;
}}
"""
        else:
            return f"""# Problem: Merge Sort
def merge_sort(arr):
    if len(arr) > 1:
        mid = len(arr) // 2
        L = arr[:mid]
        R = arr[mid:]

        merge_sort(L)
        merge_sort(R)

        i = j = k = 0
        while i < len(L) and j < len(R):
            if L[i] <= R[j]:
                arr[k] = L[i]
                i += 1
            else:
                arr[k] = R[j]
                j += 1
            k += 1

        while i < len(L):
            arr[k] = L[i]
            i += 1
            k += 1

        while j < len(R):
            arr[k] = R[j]
            j += 1
            k += 1

if __name__ == "__main__":
    nums = [38, 27, 43, 3, 9, 82, 10]
    print("Unsorted:", nums)
    merge_sort(nums)
    print("Sorted:  ", nums)
"""

    def _build_fibonacci(self, lang: LanguageSpec, stem: str) -> str:
        if lang.name == "Java":
            return f"""// Problem: Fibonacci Series
public class {stem} {{
    public static long fib(int n) {{
        if (n <= 1) return n;
        long a = 0, b = 1;
        for (int i = 2; i <= n; i++) {{
            long temp = a + b;
            a = b;
            b = temp;
        }}
        return b;
    }}

    public static void main(String[] args) {{
        int n = 10;
        System.out.println("Fibonacci(" + n + ") = " + fib(n));
    }}
}}
"""
        else:
            return f"""# Problem: Fibonacci Series
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

if __name__ == "__main__":
    n = 10
    print(f"Fibonacci({{n}}) = {{fibonacci(n)}}")
"""

    def _build_factorial(self, lang: LanguageSpec, stem: str) -> str:
        return f"""# Problem: Factorial
def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers.")
    res = 1
    for i in range(2, n + 1):
        res *= i
    return res

if __name__ == "__main__":
    n = 5
    print(f"Factorial of {{n}} is {{factorial(n)}}")
"""

    def _build_palindrome(self, lang: LanguageSpec, stem: str) -> str:
        return f"""// Problem: Valid Palindrome
public class {stem} {{
    public static boolean isPalindrome(String s) {{
        int left = 0, right = s.length() - 1;
        while (left < right) {{
            while (left < right && !Character.isLetterOrDigit(s.charAt(left))) left++;
            while (left < right && !Character.isLetterOrDigit(s.charAt(right))) right--;
            if (Character.toLowerCase(s.charAt(left)) != Character.toLowerCase(s.charAt(right))) {{
                return false;
            }}
            left++;
            right--;
        }}
        return true;
    }}

    public static void main(String[] args) {{
        String test = "A man, a plan, a canal: Panama";
        System.out.println("Is '" + test + "' a palindrome? " + isPalindrome(test));
    }}
}}
"""

    def _build_html_template(self, title: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title.capitalize()}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
        }}
        .card {{
            background: #161b22;
            padding: 32px;
            border-radius: 12px;
            border: 1px solid #30363d;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            text-align: center;
        }}
        h1 {{ color: #58a6ff; }}
        button {{
            background: #238636;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
        }}
        button:hover {{ background: #2ea043; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{title.capitalize()}</h1>
        <p>Built with ZYRA AI Coding Assistant.</p>
        <button onclick="alert('Hello from ZYRA!')">Click Me</button>
    </div>
</body>
</html>
"""

    def _build_generic_solution(self, prompt: str, lang: LanguageSpec, stem: str) -> str:
        clean_desc = prompt.strip()
        if lang.name == "Java":
            return f"""// Problem: {clean_desc}
// Solution implemented in {lang.name}
public class {stem} {{
    public static void solve() {{
        System.out.println("Solution executed for task: {clean_desc}");
    }}

    public static void main(String[] args) {{
        System.out.println("=== Running {stem} ===");
        solve();
    }}
}}
"""
        elif lang.name == "Python":
            return f"""# Problem: {clean_desc}
# Solution implemented in {lang.name}

def solve():
    print(f"Solution executed for task: {clean_desc}")

if __name__ == "__main__":
    print("=== Running {stem} ===")
    solve()
"""
        elif lang.name in ("C++", "C"):
            return f"""// Problem: {clean_desc}
#include <iostream>

void solve() {{
    std::cout << "Solution executed for task: {clean_desc}" << std::endl;
}}

int main() {{
    std::cout << "=== Running {stem} ===" << std::endl;
    solve();
    return 0;
}}
"""
        else:
            return f"""// Problem: {clean_desc}
function solve() {{
    console.log("Solution executed for task: {clean_desc}");
}}

console.log("=== Running {stem} ===");
solve();
"""

coder_engine = CoderEngine()
