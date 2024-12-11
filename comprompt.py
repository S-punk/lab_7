import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import send2trash  # Для перемещения файлов в корзину
import stat  # Для изменения прав доступа

def get_file_info(path):
    info = []
    for item in os.listdir(path):
        full_path = os.path.join(path, item)
        is_dir = os.path.isdir(full_path)
        size = os.path.getsize(full_path) if not is_dir else "<DIR>"
        mtime = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
        ext = os.path.splitext(item)[1] if not is_dir else "<DIR>"
        info.append((item, ext, size, mtime))
    return info

def search_files_recursive(query, path):
    results = []
    query_lower = query.lower()
    for root, dirs, files in os.walk(path):
        for item in files + dirs:
            if query_lower in item.lower():
                full_path = os.path.join(root, item)
                is_dir = os.path.isdir(full_path)
                size = os.path.getsize(full_path) if not is_dir else "<DIR>"
                mtime = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
                ext = os.path.splitext(item)[1] if not is_dir else "<DIR>"
                relative_path = os.path.relpath(full_path, path)
                results.append((relative_path, ext, size, mtime))
    return results

def update_file_list(tree, path_var, search_var=None):
    path = path_var.get()
    tree.delete(*tree.get_children())
    path_var.set(os.path.abspath(path))
    if search_var and search_var.get():
        query = search_var.get()
        file_info = search_files_recursive(query, path)
    else:
        file_info = get_file_info(path)
    for item, ext, size, mtime in file_info:
        tree.insert('', 'end', values=(item, ext, size, mtime))

def go_up(tree, path_var, search_var):
    path = os.path.abspath(os.path.join(path_var.get(), '..'))
    path_var.set(path)
    search_var.set("")
    update_file_list(tree, path_var)

def on_item_double_click(event, tree, path_var, search_var):
    selected_item = tree.focus()
    if not selected_item:
        return
    item_name = tree.item(selected_item)['values'][0]
    new_path = os.path.join(path_var.get(), item_name)
    if os.path.isdir(new_path):
        path_var.set(new_path)
        search_var.set("")
        update_file_list(tree, path_var)
    else:
        os.startfile(new_path)

def clear_search(tree, path_var, search_var, clear_button):
    search_var.set("")
    clear_button.pack_forget()
    update_file_list(tree, path_var)

def on_search(event, tree, path_var, search_var, clear_button):
    query = search_var.get()
    if query:
        update_file_list(tree, path_var, search_var)
        clear_button.pack(side='right', padx=5)

def create_new_item(path, is_folder):
    def submit():
        name = entry.get()
        if not name:
            messagebox.showerror("Ошибка", "Имя не может быть пустым!")
            return
        new_path = os.path.join(path, name)
        try:
            if is_folder:
                os.mkdir(new_path)
            else:
                open(new_path, 'w').close()
            dialog.destroy()
            update_file_list(tree, path_var)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать: {e}")

    dialog = tk.Toplevel()
    dialog.title("Создать" + (" папку" if is_folder else " файл"))

    tk.Label(dialog, text="Имя:").pack(padx=5, pady=5)
    entry = tk.Entry(dialog)
    entry.pack(padx=5, pady=5)

    tk.Button(dialog, text="Создать", command=submit).pack(padx=5, pady=5)

def change_permissions(item_path):
    def submit():
        try:
            mode = 0
            if read_var.get():
                mode |= stat.S_IRUSR
            if write_var.get():
                mode |= stat.S_IWUSR
            if exec_var.get():
                mode |= stat.S_IXUSR
            os.chmod(item_path, mode)
            perm_dialog.destroy()
            messagebox.showinfo("Успешно", "Права изменены успешно!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить права: {e}")

    perm_dialog = tk.Toplevel()
    perm_dialog.title("Изменить права")

    read_var = tk.BooleanVar(value=os.access(item_path, os.R_OK))
    write_var = tk.BooleanVar(value=os.access(item_path, os.W_OK))
    exec_var = tk.BooleanVar(value=os.access(item_path, os.X_OK))

    tk.Checkbutton(perm_dialog, text="Чтение", variable=read_var).pack(anchor='w')
    tk.Checkbutton(perm_dialog, text="Запись", variable=write_var).pack(anchor='w')
    tk.Checkbutton(perm_dialog, text="Исполнение", variable=exec_var).pack(anchor='w')

    tk.Button(perm_dialog, text="Сохранить", command=submit).pack(padx=5, pady=5)

def on_right_click(event, tree, path_var):
    def open_item():
        os.startfile(item_path)

    def rename_item():
        def submit():
            new_name = entry.get()
            if not new_name:
                messagebox.showerror("Ошибка", "Имя не может быть пустым!")
                return
            new_path = os.path.join(path_var.get(), new_name)
            try:
                os.rename(item_path, new_path)
                rename_dialog.destroy()
                update_file_list(tree, path_var)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось переименовать: {e}")

        rename_dialog = tk.Toplevel()
        rename_dialog.title("Переименовать")

        tk.Label(rename_dialog, text="Новое имя:").pack(padx=5, pady=5)
        entry = tk.Entry(rename_dialog)
        entry.pack(padx=5, pady=5)

        tk.Button(rename_dialog, text="Переименовать", command=submit).pack(padx=5, pady=5)

    def copy_path():
        root.clipboard_clear()
        root.clipboard_append(item_path)
        root.update()

    def delete_item(permanent):
        try:
            if permanent:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            else:
                send2trash.send2trash(item_path)
            update_file_list(tree, path_var)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

    selected_item = tree.identify_row(event.y)
    if not selected_item:
        menu = tk.Menu(root, tearoff=0)
        menu.add_command(label="Создать файл", command=lambda: create_new_item(path_var.get(), is_folder=False))
        menu.add_command(label="Создать папку", command=lambda: create_new_item(path_var.get(), is_folder=True))
        menu.post(event.x_root, event.y_root)
    else:
        item_name = tree.item(selected_item)['values'][0]
        item_path = os.path.join(path_var.get(), item_name)
        menu = tk.Menu(root, tearoff=0)
        menu.add_command(label="Открыть", command=open_item)
        menu.add_command(label="Переименовать", command=rename_item)
        menu.add_command(label="Копировать путь", command=copy_path)
        menu.add_command(label="Создать копию", command=lambda: shutil.copy(item_path, item_path + "_копия"))
        menu.add_separator()
        menu.add_command(label="Изменить права", command=lambda: change_permissions(item_path))
        menu.add_command(label="Удалить", command=lambda: delete_item(permanent=False))
        menu.add_command(label="Удалить навсегда", command=lambda: delete_item(permanent=True))
        menu.post(event.x_root, event.y_root)

def create_main_window():
    global root, tree, path_var

    root = tk.Tk()
    root.title("Файловый менеджер")

    path_var = tk.StringVar(value=os.getcwd())
    search_var = tk.StringVar()

    # Верхняя панель
    top_frame = tk.Frame(root)
    top_frame.pack(fill='x', padx=5, pady=5)

    path_label = tk.Entry(top_frame, textvariable=path_var, state='readonly', width=80)
    path_label.pack(side='left', fill='x', expand=True, padx=5)

    up_button = tk.Button(top_frame, text="⬆", command=lambda: go_up(tree, path_var, search_var))
    up_button.pack(side='right')

    # Поисковая панель
    search_frame = tk.Frame(root)
    search_frame.pack(fill='x', padx=5, pady=5)

    search_entry = tk.Entry(search_frame, textvariable=search_var, width=80)
    search_entry.pack(side='left', fill='x', expand=True, padx=5)
    search_entry.bind("<Return>", lambda e: on_search(e, tree, path_var, search_var, clear_button))

    clear_button = tk.Button(search_frame, text="X", command=lambda: clear_search(tree, path_var, search_var, clear_button))

    # Таблица с файлами
    columns = ('Имя', 'Расширение', 'Размер', 'Дата изменения')
    tree = ttk.Treeview(root, columns=columns, show='headings', height=20)
    tree.pack(fill='both', expand=True, padx=5, pady=5)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='w')

    tree.bind("<Double-1>", lambda e: on_item_double_click(e, tree, path_var, search_var))
    tree.bind("<Button-3>", lambda e: on_right_click(e, tree, path_var))

    # Начальное обновление списка файлов
    update_file_list(tree, path_var)

    root.mainloop()

if __name__ == "__main__":
    create_main_window()
