import pygetwindow as gw
import tkinter as tk
from tkinter import messagebox


def show_active_window_name():
    # Ottieni la finestra attualmente attiva
    active_window = gw.getActiveWindow()

    if active_window:
        window_title = active_window.title
    else:
        window_title = "Nessuna finestra attiva"

    # Crea una finestra pop-up con tkinter
    root = tk.Tk()
    root.withdraw()  # Nascondi la finestra principale
    messagebox.showinfo("Finestra Attiva", f"Finestra attualmente attiva: {window_title}")
    root.destroy()


def update_window_title():
    # Ottieni la finestra attualmente attiva
    active_window = gw.getActiveWindow()

    if active_window:
        window_title = active_window.title
    else:
        window_title = "Nessuna finestra attiva"

    # Aggiorna il testo della label
    label.config(text=f"{window_title}")

    # Aggiorna la finestra ogni 1 secondo
    root.after(100, update_window_title)


# Crea la finestra principale
root = tk.Tk()
root.title("Monitor Finestra Attiva")

# Mantieni la finestra sempre in primo piano
root.attributes("-topmost", True)

# Crea una label per mostrare il nome della finestra attiva
label = tk.Label(root, text="Rilevamento finestra attiva in corso...", font=("Arial", 14), padx=20, pady=20)
label.pack()

# Avvia l'aggiornamento del titolo della finestra attiva
update_window_title()

# Avvia il ciclo principale della finestra tkinter
root.mainloop()

# Esegui il programma
#if __name__ == "__main__":
#    show_active_window_name()