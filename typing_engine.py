import ctypes
import re
import threading

from ctypes import wintypes
from typing import Callable

from pynput.keyboard import Controller, Key, KeyCode


# Контроллер клавиатуры
keyboard = Controller()


def detect_current_layout():
    """
    Определяет раскладку клавиатуры активного окна.

    RU -> 0x0419
    EN -> всё остальное.
    """

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    user32.GetForegroundWindow.restype = wintypes.HWND

    user32.GetWindowThreadProcessId.argtypes = (
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD)
    )
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    user32.GetKeyboardLayout.argtypes = (wintypes.DWORD,)
    user32.GetKeyboardLayout.restype = ctypes.c_void_p

    hwnd = user32.GetForegroundWindow()

    if not hwnd:
        return "EN"

    process_id = wintypes.DWORD()

    thread_id = user32.GetWindowThreadProcessId(
        hwnd,
        ctypes.byref(process_id)
    )

    layout_handle = user32.GetKeyboardLayout(thread_id)
    layout_id = int(layout_handle or 0) & 0xFFFF

    if layout_id == 0x0419:
        return "RU"

    return "EN"


def toggle_layout(stop_event: threading.Event):
    """
    Переключает раскладку сочетанием Alt + Shift.

    Возвращает True, если во время ожидания
    была запрошена остановка.
    """

    keyboard.press(Key.alt_l)
    keyboard.press(Key.shift)

    keyboard.release(Key.shift)
    keyboard.release(Key.alt_l)

    return stop_event.wait(0.2)


def is_russian(ch: str) -> bool:
    """Проверяет, является ли символ русской буквой."""

    return re.match(r"[А-Яа-яЁё]", ch) is not None


def press_key(key):
    """Нажимает и отпускает клавишу."""

    keyboard.press(key)
    keyboard.release(key)


def press_dot():
    """Отдельная обработка точки."""

    key = KeyCode.from_vk(190)

    keyboard.press(key)
    keyboard.release(key)


def type_text(
    text: str,
    delay: float,
    stop_event: threading.Event,
    progress_callback: Callable[[int, int], None]
) -> int:
    """
    Печатает текст посимвольно.

    text — текст для печати.
    delay — задержка между символами.
    stop_event — событие остановки.
    progress_callback — функция обновления прогресса.

    Возвращает количество напечатанных символов.
    """

    current_layout = detect_current_layout()

    typed = 0
    total = len(text)

    for ch in text:

        if stop_event.is_set():
            break

        # Обработка специальных символов
        if ch == "\n":
            press_key(Key.enter)

        elif ch == "\t":
            press_key(Key.tab)

        else:
            # Определяем необходимую раскладку
            want_layout = "RU" if is_russian(ch) else "EN"

            if want_layout != current_layout:

                stopped = toggle_layout(stop_event)

                if stopped:
                    break

                current_layout = want_layout

            # Отдельная обработка точки
            if ch == ".":
                press_dot()
            else:
                keyboard.type(ch)

        typed += 1

        # Обновляем прогресс
        if typed % 10 == 0 or typed == total:
            progress_callback(typed, total)

        # Задержка между символами
        if delay > 0 and stop_event.wait(delay):
            break

    return typed
