import subprocess
import tkinter as tk
from tkinter import messagebox
import os
import re
from pynput import keyboard
import win32gui
import win32process
import psutil
from datetime import datetime, timedelta

project_home_path = "C:\\Users\\DELL\\git\\PIRELLI"
checked_projects = {}
command_buffer = ""
current_focus_project = None  # Memorizza il progetto attualmente a fuoco
is_checking_command = False  # Flag per evitare l'esecuzione multipla dei comandi
command_log_path = "command_log.txt"  # Path del file per salvare i comandi
check_interval_ms = 3000  # Intervallo di controllo (60 secondi)


def get_console_commands(args, project_path):
    return subprocess.run(args, cwd=project_path, capture_output=True, text=True)

def get_branch_name(project_path):
    branch_result = get_console_commands(["git", "rev-parse", "--abbrev-ref", "HEAD"], project_path)
    return branch_result.stdout.strip()


# Funzione per eseguire il comando git e verificare se è necessario fare pull o push
def check_git_status_for_pull_push(project_path, is_periodic=False):
    global message
    project_name = project_path.split("\\")[-1]
    try:
        branch_name = get_branch_name(project_path)
        current_time = datetime.now()

        # Controlla se il progetto e il branch sono già stati verificati
        if project_path in checked_projects:
            last_branch = checked_projects[project_path]["branch"]
            last_checked = checked_projects[project_path]["last_checked"]

            # Se il branch è diverso o sono passati meno di 30 minuti dall'ultimo controllo
            if last_branch != branch_name or current_time - last_checked < timedelta(minutes=30):
                checked_projects[project_path]["last_checked"] = current_time  # Aggiorna il tempo dell'ultimo controllo
            else:
                print(f"Branch già verificato per {project_path}, nessun controllo necessario.")
                return

        # Aggiorna il dizionario per tracciare branch e stato delle modifiche
        checked_projects[project_path] = {
            "branch": branch_name,
            "pending_push": False,
            "last_checked": current_time
        }

        # Esegui 'git status' e cattura l'output
        result = get_console_commands(["git", "status"], project_path)
        git_status_output = result.stdout

        # Controlla per eventuali aggiornamenti o necessità di pull
        if "Your branch is behind" in git_status_output or "have diverged" in git_status_output:
            message = f"Il progetto in {project_path} richiede un 'git pull'!"
        elif "Changes not staged for commit" in git_status_output or "Untracked files" in git_status_output or "Your branch is ahead" in git_status_output:
            if not checked_projects[project_path]["pending_push"]:  # Mostra messagebox solo se non già mostrata
                checked_projects[project_path]["pending_push"] = True  # Segna che ci sono modifiche non ancora pushate
            message = f"Il progetto in {project_path} ha modifiche locali da pushare."
        elif "Your branch is up to date" in git_status_output:
            message = f"Il progetto in {project_path} è aggiornato sul branch {branch_name}"

        # Aggiorna la status_label se è un controllo periodico
        if is_periodic:
            status_label.config(text=message)
        else:
            show_messagebox(message)

        # Aggiorna la Label con il contenuto del dizionario aggiornato
        update_dict_label()

    except Exception as e:
        print(f"Errore nell'eseguire git status: {e}")


def get_window_program_info():
    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        process_name = process.name()
    except Exception as e:
        window_title = "Errore"
        process_name = str(e)

    return window_title, process_name


def open_console_in_project_folder(ide_name, process_name, window_title):
    global current_focus_project  # Indica il progetto attualmente a fuoco

    if ide_name.lower() in process_name.lower():
        project_info = re.search(r'^(.*?) [–-] ', window_title)
        if project_info:
            project_name = project_info.group(1).strip()
            project_path = os.path.join(project_home_path, project_name)

            # Se il progetto a fuoco è già stato controllato, esci dalla funzione
            if project_path == current_focus_project:
                return

            # Aggiorna il progetto corrente e controlla il suo stato
            current_focus_project = project_path
            print(f"Nome del progetto estratto: {project_name}")
            print(f"Percorso del progetto: {project_path}")

            if os.path.exists(project_path):
                check_git_status_for_pull_push(project_path)
            else:
                print(f"Cartella del progetto non trovata: {project_path}")
        else:
            print("Non è stato possibile determinare il nome del progetto dal titolo della finestra.")
            current_focus_project = None  # Rimuove il focus del progetto se non rilevato


def update_window_title():
    window_title, process_name = get_window_program_info()
    open_console_in_project_folder('idea64.exe', process_name, window_title)
    label.config(text=f"Finestra attualmente attiva: {window_title}\nProgramma: {process_name}")

    # Reimposta i progetti controllati se la finestra perde il focus
    root.after(1000, update_window_title)


def periodic_branch_check():
    # Controlla lo stato di ogni progetto nel dizionario periodicamente
    for project_path in checked_projects.keys():
        check_git_status_for_pull_push(project_path, is_periodic=True)
    root.after(check_interval_ms, periodic_branch_check)


def get_active_window_process():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = psutil.Process(pid)
    return process.name().lower(), win32gui.GetWindowText(hwnd)


def on_key_press(key):
    global command_buffer
    try:
        command_buffer += key.char  # Aggiungi carattere al buffer
    except AttributeError:
        if key == keyboard.Key.space:
            command_buffer += " "  # Aggiungi spazio per i comandi
        elif key == keyboard.Key.enter:
            save_command_to_file()  # Salva il buffer nel file
            check_command()
            command_buffer = ""  # Resetta il buffer al termine di un comando


def save_command_to_file():
    with open(command_log_path, "a") as file:
        file.write(command_buffer + "\n")  # Aggiunge il comando al file e va a capo


def check_command():
    global command_buffer, is_checking_command
    if "git status" in command_buffer or "git add" in command_buffer:
        if is_checking_command:
            return  # Se è già in corso un controllo, esci
        is_checking_command = True  # Imposta il flag per evitare chiamate multiple

        process_name, window_title = get_active_window_process()

        # Verifica se il processo è IntelliJ IDEA
        if 'idea64.exe' in process_name:
            # Estrae il nome del progetto dal titolo della finestra
            project_info = re.search(r'^(.*?) [–-] ', window_title)
            if project_info:
                project_name = project_info.group(1).strip()
                project_path = os.path.join(project_home_path, project_name)

                # Aggiorna il dizionario prima di mostrare il messaggio
                check_git_status_for_pull_push(project_path)

                # Mostra messaggio in base allo stato salvato
                if project_path in checked_projects:
                    branch_name = checked_projects[project_path]["branch"]
                    pending_push = checked_projects[project_path]["pending_push"]
                    msg = f"Stato per il progetto {project_path} sul branch {branch_name}:\n"
                    msg += "Modifiche locali da pushare" if pending_push else "Nessuna modifica da pushare"
                    show_messagebox(msg)
            else:
                print("Non è stato possibile determinare il progetto dalla finestra attiva.")
        is_checking_command = False  # Reset del flag dopo aver completato il controllo

def show_messagebox(msg):
    messagebox.showinfo("Stato del progetto", msg)

# Aggiorna la Label con il contenuto di checked_projects
def update_dict_label():
    dict_content = "Stato progetti:\n"
    for project, info in checked_projects.items():
        dict_content += f"{project}:\n"
        dict_content += f"  Branch: {info['branch']}\n"
        dict_content += f"  Modifiche locali: {'Sì' if info['pending_push'] else 'No'}\n"
        dict_content += f"  Ultimo controllo: {info['last_checked']}\n\n"
    dict_label.config(text=dict_content)

# Crea la finestra principale
root = tk.Tk()
root.title("Monitor Finestra Attiva")
root.attributes("-topmost", True)

label = tk.Label(root, text="Rilevamento finestra attiva in corso...", font=("Arial", 14), padx=20, pady=20)
label.pack()

status_label = tk.Label(root, text="", font=("Arial", 12), padx=10, pady=10, fg="blue")
status_label.pack()


dict_label = tk.Label(root, text="Stato progetti:", font=("Arial", 10), padx=10, pady=10, fg="green", anchor="w", justify="left")
dict_label.pack()

# Avvio del listener della tastiera
listener = keyboard.Listener(on_press=on_key_press)
listener.start()

update_window_title()
periodic_branch_check()  # Avvia il controllo periodico dei branch

root.mainloop()
