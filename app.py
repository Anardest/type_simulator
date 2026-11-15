
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import threading
import queue
import time
import math

from config import (
    DEFAULT_DELAY,
    DEFAULT_WAIT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT
)

from typing_engine import type_text


class KeyboardTyperApp:

    def __init__(self, root):

        self.root = root

        self.root.title(WINDOW_TITLE)
        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )
        self.root.minsize(
            WINDOW_MIN_WIDTH,
            WINDOW_MIN_HEIGHT
        )

        # Очередь для передачи сообщений
        # из рабочего потока в интерфейс
        self.messages = queue.Queue()

        # Событие для остановки печати
        self.stop_event = threading.Event()

        self.is_running = False

        self.create_interface()

        # Проверяем сообщения рабочего потока
        self.root.after(100, self.process_queue)

        # Обработка закрытия окна
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_app
        )

    # ==================================
    # СОЗДАНИЕ ИНТЕРФЕЙСА
    # ==================================

    def create_interface(self):

        main_frame = ttk.Frame(
            self.root,
            padding=15
        )
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        ttk.Label(
            main_frame,
            text=WINDOW_TITLE,
            font=("Arial", 20, "bold")
        ).pack(anchor="w", pady=(0, 15))

        # Поле текста
        ttk.Label(
            main_frame,
            text="Текст для печати:"
        ).pack(anchor="w", pady=(0, 5))

        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True)

        self.text_input = tk.Text(
            text_frame,
            height=15,
            wrap="word",
            font=("Consolas", 11),
            undo=True
        )

        self.text_input.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.text_input.yview
        )

        scrollbar.pack(side="right", fill="y")

        self.text_input.configure(
            yscrollcommand=scrollbar.set
        )

        # Кнопки работы с текстом
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill="x", pady=10)

        ttk.Button(
            file_frame,
            text="Загрузить из файла",
            command=self.load_file
        ).pack(side="left")

        ttk.Button(
            file_frame,
            text="Очистить текст",
            command=self.clear_text
        ).pack(side="left", padx=10)

        # Настройки печати
        settings_frame = ttk.LabelFrame(
            main_frame,
            text="Настройки печати",
            padding=10
        )

        settings_frame.pack(fill="x", pady=10)

        # Задержка между символами
        ttk.Label(
            settings_frame,
            text="Задержка между символами (сек.):"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=5
        )

        self.delay_var = tk.StringVar(
            value=str(DEFAULT_DELAY)
        )

        ttk.Entry(
            settings_frame,
            textvariable=self.delay_var,
            width=15
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=10
        )

        # Время ожидания
        ttk.Label(
            settings_frame,
            text="Ожидание перед печатью (сек.):"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=5
        )

        self.wait_var = tk.StringVar(
            value=str(DEFAULT_WAIT)
        )

        ttk.Entry(
            settings_frame,
            textvariable=self.wait_var,
            width=15
        ).grid(
            row=1,
            column=1,
            sticky="w",
            padx=10
        )

        # Кнопки управления
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=15)

        self.start_button = ttk.Button(
            buttons_frame,
            text="Начать печать",
            command=self.start_typing
        )

        self.start_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 5),
            ipady=5
        )

        self.stop_button = ttk.Button(
            buttons_frame,
            text="Остановить",
            command=self.stop_typing,
            state="disabled"
        )

        self.stop_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(5, 0),
            ipady=5
        )

        # Состояние приложения
        status_frame = ttk.LabelFrame(
            main_frame,
            text="Состояние",
            padding=10
        )

        status_frame.pack(fill="x")

        self.status_var = tk.StringVar(
            value="Готов к работе"
        )

        ttk.Label(
            status_frame,
            textvariable=self.status_var
        ).pack(anchor="w")

        self.progress_var = tk.StringVar(
            value="Прогресс: 0 / 0"
        )

        ttk.Label(
            status_frame,
            textvariable=self.progress_var
        ).pack(anchor="w", pady=(5, 0))

    # ==================================
    # ЗАГРУЗКА И ОЧИСТКА ТЕКСТА
    # ==================================

    def load_file(self):

        file_path = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8-sig"
            ) as file:

                text = file.read()

            self.text_input.delete("1.0", "end")
            self.text_input.insert("1.0", text)

            self.status_var.set(
                "Файл успешно загружен"
            )

        except Exception as error:

            messagebox.showerror(
                "Ошибка",
                f"Не удалось прочитать файл:\n{error}"
            )

    def clear_text(self):

        if self.is_running:
            return

        self.text_input.delete("1.0", "end")

        self.status_var.set("Текст очищен")
        self.progress_var.set("Прогресс: 0 / 0")

    # ==================================
    # ЗАПУСК ПЕЧАТИ
    # ==================================

    def start_typing(self):

        if self.is_running:
            return

        text = self.text_input.get(
            "1.0",
            "end-1c"
        )

        if not text:

            messagebox.showwarning(
                "Нет текста",
                "Сначала введите или загрузите текст."
            )
            return

        # Проверка настроек
        try:
            delay = float(
                self.delay_var.get().replace(",", ".")
            )

            wait = float(
                self.wait_var.get().replace(",", ".")
            )

            if (
                not math.isfinite(delay)
                or not math.isfinite(wait)
                or delay < 0
                or wait < 0
            ):
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Ошибка настроек",
                "Задержка и время ожидания должны быть "
                "неотрицательными числами."
            )
            return

        # Подготавливаем приложение к запуску
        self.stop_event.clear()
        self.is_running = True

        self.start_button.configure(
            state="disabled"
        )

        self.stop_button.configure(
            state="normal"
        )

        self.progress_var.set(
            f"Прогресс: 0 / {len(text)}"
        )

        # Создаём рабочий поток
        worker = threading.Thread(
            target=self.typing_worker,
            args=(text, delay, wait),
            daemon=True
        )

        worker.start()

    # ==================================
    # РАБОЧИЙ ПОТОК
    # ==================================

    def typing_worker(self, text, delay, wait):

        try:
            # Обратный отсчёт
            deadline = time.monotonic() + wait

            while True:

                remaining = deadline - time.monotonic()

                if remaining <= 0:
                    break

                self.messages.put((
                    "status",
                    f"Переключитесь на нужное окно. "
                    f"Начало через {math.ceil(remaining)} сек."
                ))

                if self.stop_event.wait(
                    min(1.0, remaining)
                ):

                    self.messages.put((
                        "finished",
                        ("stopped", 0, len(text))
                    ))

                    return

            if self.stop_event.is_set():

                self.messages.put((
                    "finished",
                    ("stopped", 0, len(text))
                ))

                return

            self.messages.put((
                "status",
                "Печать началась..."
            ))

            # Callback для обновления прогресса
            def update_progress(typed, total):

                self.messages.put((
                    "progress",
                    (typed, total)
                ))

            # Запуск движка печати
            typed = type_text(
                text,
                delay,
                self.stop_event,
                update_progress
            )

            result = (
                "stopped"
                if self.stop_event.is_set()
                else "completed"
            )

            self.messages.put((
                "finished",
                (result, typed, len(text))
            ))

        except Exception as error:

            self.messages.put((
                "error",
                str(error)
            ))

    # ==================================
    # ОСТАНОВКА ПЕЧАТИ
    # ==================================

    def stop_typing(self):

        if not self.is_running:
            return

        self.stop_event.set()

        self.status_var.set(
            "Остановка печати..."
        )

        self.stop_button.configure(
            state="disabled"
        )

    # ==================================
    # ОБРАБОТКА СООБЩЕНИЙ
    # ==================================

    def process_queue(self):

        try:

            while True:

                message_type, data = (
                    self.messages.get_nowait()
                )

                if message_type == "status":

                    self.status_var.set(data)

                elif message_type == "progress":

                    typed, total = data

                    self.progress_var.set(
                        f"Прогресс: {typed} / {total}"
                    )

                elif message_type == "finished":

                    result, typed, total = data

                    self.is_running = False

                    self.start_button.configure(
                        state="normal"
                    )

                    self.stop_button.configure(
                        state="disabled"
                    )

                    self.progress_var.set(
                        f"Прогресс: {typed} / {total}"
                    )

                    if result == "completed":

                        self.status_var.set(
                            "Печать успешно завершена."
                        )

                    else:

                        self.status_var.set(
                            f"Печать остановлена. "
                            f"Введено символов: {typed}"
                        )

                elif message_type == "error":

                    self.is_running = False

                    self.start_button.configure(
                        state="normal"
                    )

                    self.stop_button.configure(
                        state="disabled"
                    )

                    self.status_var.set(
                        f"Ошибка: {data}"
                    )

                    messagebox.showerror(
                        "Ошибка печати",
                        data
                    )

        except queue.Empty:
            pass

        # Повторная проверка очереди через 100 мс
        self.root.after(
            100,
            self.process_queue
        )

    # ==================================
    # ЗАКРЫТИЕ ПРИЛОЖЕНИЯ
    # ==================================

    def close_app(self):

        self.stop_event.set()
        self.root.destroy()
