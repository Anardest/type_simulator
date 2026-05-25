"""
Эмулятор ввода текста с клавиатуры.
Поддерживает автоматическое переключение между русской и английской раскладкой.
Читает текст из файла или стандартного ввода и имитирует его посимвольный ввод.
"""

import sys
import time
import re
import ctypes
import argparse

from pynput.keyboard import Controller, Key, KeyCode

# Настройки по умолчанию
DEFAULT_DELAY = 0.02
DEFAULT_WAIT = 5

keyboard = Controller()


def get_text(args):
    """Получить текст из источника (файл, аргумент или stdin)."""
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Ошибка чтения файла: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.text:
        return args.text

    else:
        print("Введите текст (завершите ввод Ctrl+D / Ctrl+Z):", file=sys.stderr)
        return sys.stdin.read()


def detect_current_layout():
    """
    Определить текущую раскладку клавиатуры.
    RU -> 0x0419
    EN -> всё остальное
    """
    user32 = ctypes.WinDLL('user32', use_last_error=True)

    hwnd = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(hwnd, 0)

    layout_id = user32.GetKeyboardLayout(thread_id)
    lang_id = layout_id & 0xFFFF

    if lang_id == 0x0419:
        return "RU"

    return "EN"


def toggle_layout():
    """Переключить раскладку Alt + Shift."""
    keyboard.press(Key.alt_l)
    keyboard.press(Key.shift)

    keyboard.release(Key.shift)
    keyboard.release(Key.alt_l)

    time.sleep(0.2)


def is_russian(ch):
    """Проверка: русский ли символ."""
    return re.match(r"[А-Яа-яЁё]", ch) is not None


def press_key(key):
    """Нажать и отпустить клавишу."""
    keyboard.press(key)
    keyboard.release(key)


def press_dot():
    """
    Отдельная обработка точки.
    Иногда keyboard.type('.') работает некорректно
    при разных раскладках.
    """
    keyboard.press(KeyCode.from_vk(190))
    keyboard.release(KeyCode.from_vk(190))


def type_text(text, delay):
    """Печатать текст с автоматическим переключением раскладки."""

    current_layout = detect_current_layout()

    for ch in text:

        # Спецсимволы
        if ch == '\n':
            press_key(Key.enter)
            time.sleep(delay)
            continue

        if ch == '\t':
            press_key(Key.tab)
            time.sleep(delay)
            continue

        # Определяем нужную раскладку
        want_layout = "RU" if is_russian(ch) else "EN"

        if want_layout != current_layout:
            toggle_layout()
            current_layout = want_layout

        # Отдельная обработка точки
        if ch == '.':
            press_dot()
        else:
            keyboard.type(ch)

        time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(
        description="Эмуляция ввода текста с автоматическим переключением раскладки."
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "-f",
        "--file",
        help="файл с текстом для ввода"
    )

    group.add_argument(
        "-t",
        "--text",
        help="непосредственно текст для ввода"
    )

    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"задержка между символами (сек), по умолчанию {DEFAULT_DELAY}"
    )

    parser.add_argument(
        "-w",
        "--wait",
        type=int,
        default=DEFAULT_WAIT,
        help=f"время на переключение окна (сек), по умолчанию {DEFAULT_WAIT}"
    )

    args = parser.parse_args()

    text = get_text(args)

    if not text:
        print("Нет текста для ввода.", file=sys.stderr)
        sys.exit(0)

    print(f"Длина текста: {len(text)} символов.")
    print(f"Переключитесь на целевое окно. Ввод начнётся через {args.wait} секунд...")

    time.sleep(args.wait)

    print("Начинаем ввод...")

    try:
        type_text(text, args.delay)

    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")

    except Exception as e:
        print(f"Ошибка при эмуляции ввода: {e}", file=sys.stderr)
        sys.exit(1)

    print("Ввод завершён.")


if __name__ == "__main__":
    main()