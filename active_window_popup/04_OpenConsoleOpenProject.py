import psutil
import tkinter as tk
from tkinter import messagebox
import win32gui
import win32process
import os
import re
import subprocess

already_checked = False

project_home_path = "C:\\Users\\DELL\\git\\PIRELLI"

def is_cmd_with_path_opened(folder_path):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'].lower() == 'cmd.exe':
            cmdline = ' '.join(proc.info['cmdline']).lower()
            if folder_path.lower() in cmdline:
                return True
    return False


# Funzione per eseguire il comando git e verificare se è necessario fare pull
def check_git_status_for_pull(project_path):
    global already_checked  # Aggiungi questa linea per dichiarare already_checked come variabile globale
    #if already_checked:
    try:

        # 'git rev-parse --abbrev-ref HEAD' per ottenere il nome del branch corrente
        branch_result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_path, capture_output=True, text=True)
        branch_name = branch_result.stdout.strip()

        # Esegui 'git status' e cattura l'output
        result = subprocess.run(["git", "status"], cwd=project_path, capture_output=True, text=True)
        git_status_output = result.stdout

        if "Your branch is behind" in git_status_output or "have diverged" in git_status_output:
            messagebox.showinfo("Git Pull Necessario", f"Il progetto in {project_path} richiede un 'git pull'!")
        if "Your branch is up to date" in git_status_output:
            messagebox.showinfo("Progetto aggiornato", f"Il progetto in {project_path} è aggiornato sul branch {branch_name}")
        if "Your branch is ahead" in git_status_output:
            messagebox.showinfo("Modifiche non pushate",f"Il progetto {project_path} ha delle modifiche non pushate sul branch {branch_name}")
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
    if ide_name.lower() in process_name.lower():
        project_info = re.search(r'^(.*?) [–-] ', window_title)
        if project_info:
            project_name = project_info.group(1).strip()
            print(f"Nome del progetto estratto: {project_name}")
            project_path = os.path.join(project_home_path, project_name)
            print(f"Percorso del progetto: {project_path}")

            if os.path.exists(project_path):
                check_git_status_for_pull(project_path)
            else:
                print(f"Cartella del progetto non trovata: {project_path}")
        else:
            print("Non è stato possibile determinare il nome del progetto dal titolo della finestra.")


def update_window_title():
    window_title, process_name = get_window_program_info()
    open_console_in_project_folder('idea64.exe',process_name, window_title)
    label.config(text=f"Finestra attualmente attiva: {window_title}\nProgramma: {process_name}")
    root.after(100, update_window_title)


# Crea la finestra principale
root = tk.Tk()
root.title("Monitor Finestra Attiva")
root.attributes("-topmost", True)

label = tk.Label(root, text="Rilevamento finestra attiva in corso...", font=("Arial", 14), padx=20, pady=20)
label.pack()

update_window_title()

root.mainloop()
