import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import threading
from email_cleaner import authenticate, list_subscriptions, send_unsubscribe, create_block_filter
import re
from datetime import datetime

class EmailCleanerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Inbox Cleaner")
        self.root.configure(bg="#16161d")
        self.root.geometry("1200x700")
        self.service = authenticate()
        self.subscriptions = list_subscriptions(self.service, include_unsubscribed=True)
        self.filtered_subs = self.subscriptions.copy()
        self.selected_actions = {}

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background="#1f1f2b",
                        foreground="#f0f0f0",
                        rowheight=28,
                        fieldbackground="#1f1f2b",
                        borderwidth=0,
                        font=('Consolas', 11))
        style.map('Treeview', background=[('selected', '#6a0dad')])

        self.live_feed = tk.Text(root, width=40, bg="#0f0f15", fg="#90ee90", font=("Consolas", 10), state="disabled", relief="flat")
        self.live_feed.grid(row=0, column=4, rowspan=3, sticky="nsew", padx=(5, 0))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_subs)

        search_frame = tk.Frame(root, bg="#16161d")
        search_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(10, 5))

        tk.Label(search_frame, text="🔍 Search Brands:", bg="#16161d", fg="#f0f0f0", font=("Consolas", 11)).pack(side="left")
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Consolas", 11), bg="#222230", fg="#f0f0f0", insertbackground="#f0f0f0", relief="flat", width=30)
        self.search_entry.pack(side="left", padx=(8, 0), ipady=3)

        self.tree = ttk.Treeview(root, columns=("Brand", "Subject", "Unsubscribe"), show='headings', selectmode="extended")
        self.tree.heading("Brand", text="Brand")
        self.tree.heading("Subject", text="Subject")
        self.tree.heading("Unsubscribe", text="Unsubscribe")

        self.tree.column("Brand", anchor="w", width=180)
        self.tree.column("Subject", anchor="w", width=600)
        self.tree.column("Unsubscribe", anchor="w", width=280)
        self.tree.tag_configure("unsubscribed", foreground="#888888")

        self.tree.grid(row=1, column=0, columnspan=4, sticky='nsew')

        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=1, column=4, sticky='ns')

        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self.action_frame = tk.Frame(root, bg="#16161d")
        self.action_frame.grid(row=2, column=0, columnspan=4, pady=10, sticky='ew')

        button_style = {
            'font': ('Consolas', 11, 'bold'),
            'bg': '#6a0dad',
            'fg': 'white',
            'activebackground': '#9a40ff',
            'activeforeground': 'white',
            'relief': 'flat',
            'padx': 10,
            'pady': 6,
            'borderwidth': 0
        }

        self.mass_unsub = tk.Button(self.action_frame, text="Unsubscribe Selected", command=self.mass_unsubscribe, **button_style)
        self.mass_block = tk.Button(self.action_frame, text="Block Selected", command=self.mass_block, **button_style)
        self.refresh_btn = tk.Button(self.action_frame, text="Refresh Inbox", command=self.refresh_inbox, **button_style)

        self.mass_unsub.grid(row=0, column=0, padx=10)
        self.mass_block.grid(row=0, column=1, padx=10)
        self.refresh_btn.grid(row=0, column=2, padx=10)

        self.status_bar = tk.Label(root, text="Ready", anchor='e', font=('Consolas', 10), bg="#1e1e2f", fg="#ff99cc")
        self.status_bar.grid(row=3, column=0, columnspan=4, sticky='ew', padx=10, pady=5)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        self.root.bind("<F5>", lambda e: self.refresh_inbox())

        self.render_subs(self.filtered_subs)

    def log_action(self, message):
        self.live_feed.config(state="normal")
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.live_feed.insert("end", f"[{timestamp}] {message}\n")
        self.live_feed.see("end")
        self.live_feed.config(state="disabled")

    def refresh_inbox(self):
        def _refresh():
            self.update_status("Refreshing inbox...")
            self.refresh_btn.config(state='disabled')
            try:
                self.subscriptions = list_subscriptions(self.service, include_unsubscribed=True)
                self.filtered_subs = self.subscriptions.copy()
                self.render_subs(self.filtered_subs)
                self.log_action("Inbox refreshed complete.")
            except Exception as e:
                self.log_action(f"Refresh failed: {e}")

    def filter_subs(self, *args):
        query = self.search_var.get().lower()
        self.filtered_subs = [sub for sub in self.get_unique_subs(self.subscriptions)
                              if query in self.get_brand(sub['from']).lower()]
        self.render_subs(self.filtered_subs)

    def render_subs(self, subs):
        self.tree.delete(*self.tree.get_children())
        self.selected_actions.clear()
        for sub in self.get_unique_subs(subs):
            brand = self.get_brand(sub['from'])
            subject = sub['subject'][:100]
            unsub = self.get_primary_unsub(sub['unsubscribe'])
            tags = ('unsubscribed',) if sub['already_unsub'] else ()
            row_id = self.tree.insert("", "end", values=(brand, subject, unsub), tags=tags)
            self.selected_actions[row_id] = {
                "unsubscribe": tk.BooleanVar(),
                "block": tk.BooleanVar(),
                "meta": sub
            }

    def get_brand(self, sender):
        match = re.match(r'(?:"?([^"<]+)"?\s)?<?(.+@[^>]+)>?', sender)
        return match.group(1) if match and match.group(1) else match.group(2).split('@')[0] if match else sender

    def get_primary_unsub(self, header):
        unsub_links = re.findall(r'<(.*?)>', header)
        for link in unsub_links:
            if link.startswith('http') or link.startswith('mailto:'):
                return link
        return ""

    def get_unique_subs(self, subs):
        seen = set()
        unique = []
        for sub in subs:
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
            self.log_action("Unsubscribed via browser")
        elif unsub.startswith('mailto:'):
            messagebox.showinfo("Manual Unsubscribe", f"You need to manually email:\n\n{unsub}")
            self.log_action("Manual unsubscribe requested")

    def mass_unsubscribe(self):
        for item_id in self.tree.selection():
            unsub = self.selected_actions[item_id]["meta"]['unsubscribe']
            try:
                send_unsubscribe(self.service, unsub)
                self.tree.delete(item_id)
                self.log_action(f"Unsubscribed from email")
            except Exception as e:
                self.log_action(f"Error unsubscribing: {e}")
        messagebox.showinfo("Done", "Unsubscribe actions complete.")

    def mass_block(self):
        for item_id in self.tree.selection():
            sender = self.selected_actions[item_id]["meta"]['from']
            match = re.search(r'<([^>]+)>', sender)
            addr = match.group(1) if match else sender
            try:
                create_block_filter(self.service, addr)
                self.tree.delete(item_id)
                self.log_action(f"Blocked: {addr}")
            except Exception as e:
                self.log_action(f"block error: {e}")
        messagebox.showinfo("Done", "Block filters added.")

if __name__ == '__main__':
    root = tk.Tk()
    app = EmailCleanerGUI(root)
    root.mainloop()
