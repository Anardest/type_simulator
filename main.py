import tkinter as tk

from app import KeyboardTyperApp


def main():

    root = tk.Tk()

    app = KeyboardTyperApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()
