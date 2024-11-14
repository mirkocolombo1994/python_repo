import psutil
import tkinter as tk
import win32gui
import win32process


def get_window_program_info():
    try:
        # Ottieni l'handle della finestra attiva
        hwnd = win32gui.GetForegroundWindow()

        # Ottieni il titolo della finestra attiva
        window_title = win32gui.GetWindowText(hwnd)

        # Ottieni il PID del processo associato alla finestra attiva
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # Ottieni il nome del programma associato al PID
        process = psutil.Process(pid)
        process_name = process.name()

    except Exception as e:
        window_title = "Errore"
        process_name = str(e)

    return window_title, process_name


def update_window_title():
    # Ottieni le informazioni sulla finestra e sul programma
    window_title, process_name = get_window_program_info()

    # Aggiorna il testo della label
    label.config(text=f"{window_title}\nProgramma: {process_name}")

    # Aggiorna la finestra ogni 1 secondo
    root.after(1000, update_window_title)


# Crea la finestra principale
root = tk.Tk()
root.title("Monitor Finestra Attiva")

# Mantieni la finestra sempre in primo piano
root.attributes("-topmost", True)

# Crea una label per mostrare il nome della finestra attiva e il programma
label = tk.Label(root, text="Rilevamento finestra attiva in corso...", font=("Arial", 14), padx=20, pady=20)
label.pack()

# Avvia l'aggiornamento del titolo della finestra attiva
update_window_title()

# Avvia il ciclo principale della finestra tkinter
root.mainloop()