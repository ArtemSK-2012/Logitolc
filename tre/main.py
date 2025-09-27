from customtkinter import *
from socket import *
import threading

def adjust_color(hex_color, percent):
    """
    Adjust color brightness by percent.
    Якщо percent > 0, робить колір світлішим від базового.
    Якщо percent < 0, робить темнішим.
    """
    hex_color = hex_color.lstrip('#')

    if len(hex_color) != 6:
        return hex_color
    rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    adjusted = []
    for c in rgb:
        if percent > 0:
            new_c = c + (percent / 100.0) * (255 - c)
        else:
            new_c = c + (percent / 100.0) * c

        new_c = int(max(0, min(255, new_c)))
        adjusted.append(new_c)
    return "#{:02x}{:02x}{:02x}".format(*adjusted)


class UsernameDialog(CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Введіть ім'я")
        self.geometry("300x150")
        self.resizable(False, False)
        self.grab_set()

        self.label = CTkLabel(self, text="Введіть ваше ім'я:")
        self.label.pack(pady=10)

        self.entry = CTkEntry(self, placeholder_text="Ваше ім'я")
        self.entry.pack(pady=5)

        self.entry.bind("<Return>", lambda event: self.on_confirm())

        self.confirm_btn = CTkButton(self, text="Підтвердити", command=self.on_confirm)
        self.confirm_btn.pack(pady=10)

        self.username = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_confirm(self):
        name = self.entry.get().strip()
        if name:
            self.username = name
            self.destroy()

    def on_close(self):
        self.username = None
        self.destroy()


class MainWindow(CTk):
    def __init__(self, username):
        super().__init__()
        self.geometry('700x500')
        self.title("LogiTalk")
        self.username = username
        self.selected_emoji = "🙂"


        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)


        self.frame = CTkFrame(self, width=150)
        self.frame.grid(row=0, column=0, rowspan=2, sticky="ns")
        self.frame.grid_propagate(False)

        self.label = CTkLabel(self.frame, text='Ваше Ім`я:')
        self.label.pack(pady=10)

        self.entry = CTkEntry(self.frame)
        self.entry.insert(0, self.username)
        self.entry.pack(pady=5)

        self.save_btn = CTkButton(self.frame, text="Зберегти нік", command=self.save_username)
        self.save_btn.pack(pady=10)

        self.emoji_frame = CTkFrame(self.frame)
        self.emoji_frame.pack(pady=10)

        emojis = ["👻", "💀", "👾", "🤖", "🤠", "🎃", "👽", "👹"]
        for e in emojis:
            btn = CTkButton(self.emoji_frame, text=e, width=30, command=lambda em=e: self.set_emoji(em))
            btn.pack(side="left", padx=2)

        self.label_theme = CTkOptionMenu(self.frame, values=['Темна', 'Світла'], command=self.change_theme)
        self.label_theme.pack(side='bottom', pady=20)



        self.toggle_btn = CTkButton(self, text='☰', command=self.toggle_show_menu, width=30)
        self.toggle_btn.place(x=0, y=0)


        self.chat_frame = CTkScrollableFrame(self)
        self.chat_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(1, weight=1)


        self.input_frame = CTkFrame(self)
        self.input_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=(0,10))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.message_input = CTkEntry(self.input_frame, placeholder_text='Введіть повідомлення:')
        self.message_input.grid(row=0, column=0, sticky="ew", padx=(0,10), pady=5)
        self.message_input.bind("<Return>", lambda event: self.send_message())

        self.send_button = CTkButton(self.input_frame, text='Надіслати', width=100, command=self.send_message)
        self.send_button.grid(row=0, column=1)

        self.is_show_menu = True


        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('0.tcp.eu.ngrok.io', 13982))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався до чату!\n"
            self.sock.send(hello.encode("utf-8"))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"❌ Не вдалось підключитись: {e}", "system")

    def set_emoji(self, emoji):
        self.selected_emoji = emoji

    def send_message(self):
        message = self.message_input.get().strip()
        if message:
            display_name = f"{self.selected_emoji} {self.username}"
            self.add_message(f"{display_name}: {message}", "self")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode("utf-8"))
            except Exception as e:
                self.add_message(f"❌ Не вдалось надіслати повідомлення: {e}", "system")
        self.message_input.delete(0, 'end')

    def add_message(self, text, msg_type="other"):

        label_frame = CTkFrame(self.chat_frame, corner_radius=10)

        text_color = "white"
        theme = get_appearance_mode()

        if msg_type == "self":
            bg_color = "#0078D7"
        elif msg_type == "system":
            bg_color = "#2E2E2E" if theme.lower() == "dark" else "#E0E0E0"
        else:

            if theme.lower() == "dark":
                bg_color = adjust_color("#000000", 20)
            else:
                bg_color = adjust_color("#FFFFFF", -20)

        label_frame.configure(fg_color=bg_color)

        label = CTkLabel(label_frame, text=text, wraplength=400, anchor="w", justify="left", text_color=text_color)
        label.pack(padx=10, pady=5)


        if msg_type == "self":
            label_frame.grid(sticky="e", padx=10, pady=2, column=1)
        elif msg_type == "system":
            label_frame.grid(sticky="nsew", padx=10, pady=2, column=0, columnspan=2)
        else:
            label_frame.grid(sticky="w", padx=10, pady=2, column=0)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="ignore")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except Exception:
                break
        try:
            self.sock.close()
        except:
            pass

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        if len(parts) < 1:
            return
        msg_type = parts[0]
        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                if author == self.username:
                    return
                self.add_message(f"{author}: {message}", "other")
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                self.add_message(f"{author} надіслав зображення: {filename}", "other")
        else:
            self.add_message(line, "system")

    def save_username(self):
        new_name = self.entry.get().strip()
        if new_name:
            old_name = self.username
            self.username = new_name
            try:
                msg = f"TEXT@{self.username}@[SYSTEM] {old_name} змінив ім'я на {self.username}\n"
                self.sock.send(msg.encode("utf-8"))
            except Exception:
                pass
            self.add_message(f"🔄 Нік змінено на {self.username}", "system")

    def toggle_show_menu(self):
        if self.is_show_menu:
            self.frame.grid_remove()
            self.is_show_menu = False
        else:
            self.frame.grid()
            self.is_show_menu = True

    def change_theme(self, choice):

        if choice == "Темна":
            set_appearance_mode("dark")
        else:
            set_appearance_mode("light")


if __name__ == "__main__":
    set_appearance_mode("dark")
    set_default_color_theme("blue")

    root = CTk()
    root.withdraw()

    dialog = UsernameDialog(root)
    root.wait_window(dialog)

    if dialog.username:
        root.destroy()
        win = MainWindow(dialog.username)
        win.mainloop()
    else:
        root.destroy()
