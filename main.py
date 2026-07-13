import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
        import numpy as np
        import pandas as pd
        import customtkinter
        import tkinterdnd2
        tkinterdnd2.TkinterDnD.Tk = customtkinter.CTk
    except ImportError as e:
        print(f"Error: Falta una dependencia requerida \u2014 {e}")
        print("Ejecute: pip install -r requirements.txt")
        sys.exit(1)

    from view.main_view import MainApp
    app = MainApp()
    app.run()


if __name__ == "__main__":
    main()
