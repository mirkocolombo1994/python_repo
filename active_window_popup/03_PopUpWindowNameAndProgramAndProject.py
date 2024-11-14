import psutil
import tkinter as tk
import win32gui
import win32process
import os
import re


# Funzione per enumerare tutte le finestre e trovare il titolo che contiene il percorso della cartella
def is_window_with_path_opened(folder_path):
    def enum_windows_proc(hwnd, result_list):
        # Ottiene il testo del titolo della finestra
        window_text = win32gui.GetWindowText(hwnd)
        # Controlla se il testo contiene il percorso della cartella
        if folder_path.lower() in window_text.lower():
            result_list.append(hwnd)
        return True

    result = []
    win32gui.EnumWindows(enum_windows_proc, result)
    return len(result) > 0  # Ritorna True se una finestra con quel percorso è già aperta


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


def open_project_folder(ide_name, process_name, window_title):
    print(ide_name)
    print(process_name)
    print(window_title)
    if ide_name.lower() in process_name.lower():
        project_info = re.search(r'^(.*?) [–-] ', window_title)
        if project_info:
            project_name = project_info.group(1).strip()
            print(f"Nome del progetto estratto: {project_name}")  # Debug: mostra il nome del progetto

            # Modifica il percorso se necessario
            project_path = os.path.join("C:\\Users\\DELL\\git\\PIRELLI", project_name)

            print(f"Percorso del progetto da aprire: {project_path}")  # Debug: mostra il percorso

            if not is_window_with_path_opened(project_path):
                if os.path.exists(project_path):
                    os.startfile(project_path)
                else:
                    print(f"Cartella del progetto non trovata: {project_path}")
            else:
                print(f"Una finestra con la cartella {project_path} è già aperta.")
        else:
            print("Non è stato possibile determinare il nome del progetto dal titolo della finestra.")

def update_window_title():
    # Ottieni le informazioni sulla finestra e sul programma
    print("get_window_program_info")
    window_title, process_name = get_window_program_info()

    # Verifica se la finestra attiva è IntelliJ IDEA
    print("open_project_folder")
    open_project_folder('idea64.exe', process_name, window_title)

    # Aggiorna il testo della label7
    print("label.config")
    label.config(text=f"{window_title}\nProgramma: {process_name}")

    # Aggiorna la finestra ogni 1 secondo
    print("timer")
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
