import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from email_cleaner import authenticate, list_subscriptions, send_unsubscribe, create_block_filter
import re

class EmailCleanerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Inbox Cleaner")
        self.root.configure(bg="#1e1e2f")
        self.root.geometry("1100x700")
        self.service = authenticate()
        self.subscriptions = list_subscriptions(self.service)
        self.selected_actions = {}

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background="#2e2e3e",
                        foreground="#d0fffa",
                        rowheight=30,
                        fieldbackground="#2e2e3e",
                        borderwidth=0,
                        font=('Consolas', 11))
        style.map('Treeview', background=[('selected', '#9a00ff')])

        self.tree = ttk.Treeview(root, columns=("Brand", "Subject", "Unsubscribe"), show='headings', selectmode="extended")
        self.tree.heading("Brand", text="Brand")
        self.tree.heading("Subject", text="Subject")
        self.tree.heading("Unsubscribe", text="Unsubscribe")

        self.tree.column("Brand", anchor="w", width=180)
        self.tree.column("Subject", anchor="w", width=600)
        self.tree.column("Unsubscribe", anchor="w", width=280)

        for sub in self.get_unique_subs():
            brand = self.get_brand(sub['from'])
            subject = sub['subject'][:100]
            unsub = self.get_primary_unsub(sub['unsubscribe'])
            row_id = self.tree.insert("", "end", values=(brand, subject, unsub))
            self.selected_actions[row_id] = {
                "unsubscribe": tk.BooleanVar(),
                "block": tk.BooleanVar(),
                "meta": sub
            }

        self.tree.grid(row=0, column=0, columnspan=4, sticky='nsew')

        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=4, sticky='ns')

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self.action_frame = tk.Frame(root, bg="#1e1e2f")
        self.action_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky='ew')

        button_style = {
            'font': ('Consolas', 11, 'bold'),
            'bg': '#ff0080',
            'fg': 'white',
            'activebackground': '#ff33a6',
            'activeforeground': 'white',
            'relief': 'flat',
            'padx': 10,
            'pady': 6,
            'borderwidth': 0
        }

        self.mass_unsub = tk.Button(self.action_frame, text="Unsubscribe Selected", command=self.mass_unsubscribe, **button_style)
        self.mass_block = tk.Button(self.action_frame, text="Block Selected", command=self.mass_block, **button_style)

        self.mass_unsub.grid(row=0, column=0, padx=10)
        self.mass_block.grid(row=0, column=1, padx=10)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.root.bind("<Escape>", lambda e: self.root.quit())

    def get_brand(self, sender):
        match = re.match(r'(?:"?([^"<]+)"?\s)?<?(.+@[^>]+)>?', sender)
        return match.group(1) if match and match.group(1) else match.group(2).split('@')[0] if match else sender

    def get_primary_unsub(self, header):
        unsub_links = re.findall(r'<(.*?)>', header)
        for link in unsub_links:
            if link.startswith('http') or link.startswith('mailto:'):
                return link
        return ""

    def get_unique_subs(self):
        seen = set()
        unique = []
        for sub in self.subscriptions:
            key = sub['from']
            if key not in seen:
                seen.add(key)
                unique.append(sub)
        return unique

    def on_double_click(self, event):
        item_id = self.tree.focus()
        if not item_id:
            return
        unsub = self.tree.item(item_id)['values'][2]
        if unsub.startswith('http'):
            webbrowser.open(unsub)
            self.tree.delete(item_id)
        elif unsub.startswith('mailto:'):
            messagebox.showinfo("Manual Unsubscribe", f"You need to manually email:\n\n{unsub}")

    def mass_unsubscribe(self):
        for item_id in self.tree.selection():
            unsub = self.selected_actions[item_id]["meta"]['unsubscribe']
            try:
                send_unsubscribe(self.service, unsub)
                self.tree.delete(item_id)
            except Exception as e:
                print(f"Error unsubscribing: {e}")
        messagebox.showinfo("Done", "Unsubscribe actions complete.")

    def mass_block(self):
        for item_id in self.tree.selection():
            sender = self.selected_actions[item_id]["meta"]['from']
            match = re.search(r'<([^>]+)>', sender)
            addr = match.group(1) if match else sender
            try:
                create_block_filter(self.service, addr)
                self.tree.delete(item_id)
            except Exception as e:
                print(f"Error blocking: {e}")
        messagebox.showinfo("Done", "Block filters added.")

if __name__ == '__main__':
    root = tk.Tk()
    app = EmailCleanerGUI(root)
    root.mainloop()
