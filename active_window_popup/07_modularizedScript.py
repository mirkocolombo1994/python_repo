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
current_focus_project = None
is_checking_command = False
command_log_path = "command_log.txt"
check_interval_ms = 3000


### Funzioni Git ###
def get_console_commands(args, project_path):
    """Esegue un comando console nella directory specificata."""
    return subprocess.run(args, cwd=project_path, capture_output=True, text=True)

def get_branch_name(project_path):
    """Recupera il nome del branch corrente in un progetto Git."""
    branch_result = get_console_commands(["git", "rev-parse", "--abbrev-ref", "HEAD"], project_path)
    return branch_result.stdout.strip()

def check_git_status_for_pull_push(project_path, is_periodic=False):
    """Controlla lo stato del progetto per eventuali comandi pull o push."""
    global message
    project_name = get_project_name_from_path(project_path)
    branch_name = get_branch_name(project_path)
    current_time = datetime.now()

    if is_recently_checked(project_path, branch_name, current_time):
        print(f"Branch già verificato per {project_path}, nessun controllo necessario.")
        return

    update_project_check_info(project_path, branch_name, current_time)
    git_status_output = get_git_status_output(project_path)
    message = analyze_git_status(git_status_output, project_path, branch_name)

    if is_periodic:
        status_label.config(text=message)
    else:
        show_messagebox(message)
    update_dict_label()

def get_git_status_output(project_path):
    """Esegue 'git status' e ritorna l'output."""
    result = get_console_commands(["git", "status"], project_path)
    return result.stdout

def analyze_git_status(git_status_output, project_path, branch_name):
    """Analizza l'output di git status e determina i messaggi da mostrare."""
    if "Your branch is behind" in git_status_output or "have diverged" in git_status_output:
        return f"Il progetto in {project_path} richiede un 'git pull'!"
    elif "Changes not staged for commit" in git_status_output or "Untracked files" in git_status_output or "Your branch is ahead" in git_status_output:
        checked_projects[project_path]["pending_push"] = True
        return f"Il progetto in {project_path} ha modifiche locali da pushare."
    elif "Your branch is up to date" in git_status_output:
        return f"Il progetto in {project_path} è aggiornato sul branch {branch_name}"


def handle_git_command():
    """Gestisce i comandi Git per il progetto attivo."""
    process_name, window_title = get_active_window_process()

    # Verifica se il processo attivo è IntelliJ IDEA
    if 'idea64.exe' in process_name:
        project_name = extract_project_name(window_title)

        if project_name:
            project_path = os.path.join(project_home_path, project_name)
            check_git_status_for_pull_push(project_path)  # Aggiorna lo stato del progetto

            if project_path in checked_projects:
                branch_name = checked_projects[project_path]["branch"]
                pending_push = checked_projects[project_path]["pending_push"]
                msg = f"Stato per il progetto {project_path} sul branch {branch_name}:\n"
                msg += "Modifiche locali da pushare" if pending_push else "Nessuna modifica da pushare"
                show_messagebox(msg)
        else:
            print("Non è stato possibile determinare il progetto dalla finestra attiva.")

def periodic_branch_check():
    """Esegue un controllo periodico sullo stato di ogni progetto nel dizionario."""
    for project_path in checked_projects.keys():
        check_git_status_for_pull_push(project_path, is_periodic=True)
    root.after(check_interval_ms, periodic_branch_check)


### Monitoraggio finestra attiva ###
def get_window_program_info():
    """Recupera il titolo e il nome del processo della finestra attiva."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        process_name = process.name()
    except Exception as e:
        window_title, process_name = "Errore", str(e)
    return window_title, process_name

def open_console_in_project_folder(ide_name, process_name, window_title):
    """Verifica se il progetto è cambiato e ne controlla lo stato."""
    global current_focus_project
    if ide_name.lower() in process_name.lower():
        project_name = extract_project_name(window_title)
        if project_name:
            project_path = os.path.join(project_home_path, project_name)
            if project_path != current_focus_project and os.path.exists(project_path):
                current_focus_project = project_path
                check_git_status_for_pull_push(project_path)
            else:
                print(f"Cartella del progetto non trovata o progetto già a fuoco: {project_path}")

def update_window_title():
    """Aggiorna periodicamente il titolo della finestra attiva."""
    window_title, process_name = get_window_program_info()
    open_console_in_project_folder('idea64.exe', process_name, window_title)
    label.config(text=f"Finestra attualmente attiva: {window_title}\nProgramma: {process_name}")
    root.after(1000, update_window_title)


### Gestione dei comandi da tastiera ###
def on_key_press(key):
    """Gestisce i tasti premuti per catturare comandi da eseguire."""
    global command_buffer
    try:
        command_buffer += key.char
    except AttributeError:
        handle_special_keys(key)

def handle_special_keys(key):
    """Gestisce i tasti speciali come spazio e invio."""
    global command_buffer
    if key == keyboard.Key.space:
        command_buffer += " "
    elif key == keyboard.Key.enter:
        save_command_to_file()
        check_command()
        command_buffer = ""

def check_command():
    """Verifica se i comandi sono Git e mostra messaggi di stato."""
    global is_checking_command
    if "git status" in command_buffer or "git add" in command_buffer:
        if is_checking_command:
            return
        is_checking_command = True
        handle_git_command()
        is_checking_command = False

def save_command_to_file():
    """Salva il comando digitato nel file log."""
    with open(command_log_path, "a") as file:
        file.write(command_buffer + "\n")


### Aggiornamento dell'interfaccia e gestione dei messaggi ###
def show_messagebox(msg):
    """Mostra una messagebox con un messaggio di stato."""
    messagebox.showinfo("Stato del progetto", msg)

def update_dict_label():
    """Aggiorna la Label dell'interfaccia con lo stato di tutti i progetti."""
    dict_content = "Stato progetti:\n" + "\n".join(format_project_status(project, info) for project, info in checked_projects.items())
    dict_label.config(text=dict_content)

def format_project_status(project, info):
    """Formatta le informazioni di stato di un progetto."""
    return (f"{project}:\n"
            f"  Branch: {info['branch']}\n"
            f"  Modifiche locali: {'Sì' if info['pending_push'] else 'No'}\n"
            f"  Ultimo controllo: {info['last_checked']}\n")


### Funzioni di supporto ###
def extract_project_name(window_title):
    """Estrae il nome del progetto dal titolo della finestra attiva."""
    project_info = re.search(r'^(.*?) [–-] ', window_title)
    return project_info.group(1).strip() if project_info else None

def is_recently_checked(project_path, branch_name, current_time):
    """Verifica se un progetto è stato controllato di recente."""
    return (project_path in checked_projects and
            checked_projects[project_path]["branch"] == branch_name and
            current_time - checked_projects[project_path]["last_checked"] < timedelta(minutes=30))

def update_project_check_info(project_path, branch_name, current_time):
    """Aggiorna il dizionario con le informazioni di check del progetto."""
    checked_projects[project_path] = {
        "branch": branch_name,
        "pending_push": False,
        "last_checked": current_time
    }

def get_project_name_from_path(project_path):
    """Estrae il nome del progetto dal percorso del progetto."""
    return os.path.basename(project_path)

def get_active_window_process():
    """Recupera il nome del processo e il titolo della finestra attiva."""
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = psutil.Process(pid)
    return process.name().lower(), win32gui.GetWindowText(hwnd)



### Configurazione dell'interfaccia ###
root = tk.Tk()
root.title("Monitor Finestra Attiva")
root.attributes("-topmost", True)

label = tk.Label(root, text="Rilevamento finestra attiva in corso...", font=("Arial", 14), padx=20, pady=20)
label.pack()

status_label = tk.Label(root, text="", font=("Arial", 12), padx=10, pady=10, fg="blue")
status_label.pack()

dict_label = tk.Label(root, text="Stato progetti:", font=("Arial", 10), padx=10, pady=10, fg="green", anchor="w", justify="left")
dict_label.pack()

listener = keyboard.Listener(on_press=on_key_press)
listener.start()

update_window_title()
root.after(check_interval_ms, periodic_branch_check)
root.mainloop()
