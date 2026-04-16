"""
Эмулятор ввода текста с клавиатуры.
Читает текст из файла или стандартного ввода и имитирует его посимвольный ввод.
"""

import sys
import time
import argparse
import pyautogui

# Настройки по умолчанию
DEFAULT_DELAY = 0.02      # секунды между нажатиями клавиш
DEFAULT_WAIT = 5          # секунд на переключение окна перед началом ввода


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


def main():
    parser = argparse.ArgumentParser(description="Эмуляция ввода текста с клавиатуры.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--file", help="файл с текстом для ввода")
    group.add_argument("-t", "--text", help="непосредственно текст для ввода")
    parser.add_argument("-d", "--delay", type=float, default=DEFAULT_DELAY,
                        help=f"задержка между символами (сек), по умолчанию {DEFAULT_DELAY}")
    parser.add_argument("-w", "--wait", type=int, default=DEFAULT_WAIT,
                        help=f"время на переключение окна (сек), по умолчанию {DEFAULT_WAIT}")
    args = parser.parse_args()

    text = get_text(args)
    if not text:
        print("Нет текста для ввода.", file=sys.stderr)
        sys.exit(0)

    print(f"Длина текста: {len(text)} символов.")
    print(f"Переключитесь на целевое окно. Ввод начнется через {args.wait} секунд...")
    time.sleep(args.wait)

    print("Начинаем ввод...")
    try:
        # typewrite автоматически преобразует \n в нажатие Enter, \t в Tab и т.д.
        pyautogui.typewrite(text, interval=args.delay)
    except Exception as e:
        print(f"Ошибка при эмуляции ввода: {e}", file=sys.stderr)
        sys.exit(1)

    print("Ввод завершён.")


if __name__ == "__main__":
    main()