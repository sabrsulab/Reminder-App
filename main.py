import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from tkcalendar import Calendar
import pickle
import subprocess
import sys
import os
from datetime import datetime, timedelta
from pystray import Icon as Icon, Menu as Menu, MenuItem as Item
from PIL import Image

global window, reminder_list
current_view_date = datetime.now().date()

class Reminder:
    def __init__(self, message, remind_time, attachments=None):
        if attachments is None:
            attachments = []
        self.message = message
        self.remind_time = remind_time
        self.attachments = attachments


class ToolTip(object):
    def __init__(self, widget):
        self.text = None
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def show_tip(self, text):
        """Display text in tooltip window"""
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def safe_check_reminders():
    now = datetime.now()
    for reminder in reminders:  # Use 'reminders', not 'reminder_list'
        if now > reminder.remind_time:
            def show_reminder():
                messagebox.showinfo("Reminder", reminder.message)
                reminder.remind_time += timedelta(hours=1)
                save_reminders()

            window.after(0, show_reminder)


def save_reminders():
    with open('reminders.pkl', 'wb') as output:
        pickle.dump(reminders, output, pickle.HIGHEST_PROTOCOL)


def load_reminders():
    if os.path.exists('reminders.pkl'):
        with open('reminders.pkl', 'rb') as inp:
            return pickle.load(inp)
    return []


reminders = load_reminders()


def check_reminders():
    now = datetime.now()
    for reminder in reminders:
        if now >= reminder.remind_time:
            messagebox.showinfo("Reminder", reminder.message)
            reminder.remind_time += timedelta(hours=1)  # Reschedule for the next hour
    save_reminders()


def add_reminder():
    global reminders
    attached_files = []  # List to store paths of attached files

    def attach_files():
        nonlocal attached_files  # Allows access to the attached_files list defined in the outer scope
        # Open file dialog to select files and store the result in attached_files
        attached_files = filedialog.askopenfilenames(title="Select file(s) to attach")
        # Optionally, update some UI element here to show the number of attached files

    def save_reminder():
        message = message_entry.get("1.0", tk.END).strip()
        selected_date = cal.selection_get()
        selected_hour = hour_var.get()
        selected_minute = minute_var.get()
        selected_ampm = ampm_var.get()
        remind_time_str = f"{selected_date} {selected_hour}:{selected_minute} {selected_ampm}"
        remind_time = datetime.strptime(remind_time_str, '%Y-%m-%d %I:%M %p')
        # Use the attached_files list when creating the Reminder instance
        reminder = Reminder(message, remind_time, attached_files)
        reminders.append(reminder)
        save_reminders()
        refresh_reminder_list()
        top.destroy()

    top = tk.Toplevel()
    top.title("Add a Reminder")
    top.grab_set()
    top.focus_force()

    tk.Label(top, text="What would you like to be reminded about?").pack()
    message_entry = tk.Text(top, height=3, width=50)
    message_entry.pack()

    tk.Label(top, text="Select Date:").pack()
    cal = Calendar(top, selectmode='day')
    cal.pack(pady=20)

    time_frame = tk.Frame(top)
    time_frame.pack(pady=5)

    hour_var = tk.StringVar(value="12")
    tk.Spinbox(time_frame, from_=1, to=12, textvariable=hour_var, width=5).pack(side=tk.LEFT)
    minute_var = tk.StringVar(value="00")
    tk.Spinbox(time_frame, from_=0, to=59, wrap=True, textvariable=minute_var, width=5, format="%02."
                                                                                               "0f").pack(side=tk.LEFT)
    ampm_var = tk.StringVar(value="AM")
    ttk.Combobox(time_frame, textvariable=ampm_var, values=("AM", "PM"), width=5, state="readonly").pack(side=tk.LEFT)

    # Button for attaching files
    tk.Button(top, text="Attach Files", command=attach_files).pack(pady=5)

    # Button to save the reminder
    tk.Button(top, text="Save Reminder", command=save_reminder).pack(pady=5)


def refresh_reminder_list():
    reminder_list.delete(0, tk.END)
    for reminder in reminders:
        formatted_date = reminder.remind_time.strftime("[%B %d, %Y @ %I:%M%p]")
        display_text = f"{formatted_date}: {reminder.message}"
        reminder_list.insert(tk.END, display_text)


def view_attachments():
    selection = reminder_list.curselection()
    if not selection:
        messagebox.showinfo("Info", "Please select a reminder first.")
        return

    selected_index = selection[0]
    selected_reminder = reminders[selected_index]

    # Create a new window to show the attachments
    attachments_window = tk.Toplevel(window)
    attachments_window.title("Attachments")
    attachments_window.geometry("300x200")

    def open_attachment(path):
        try:
            if os.name == 'nt':  # Windows
                os.startfile(path)
            else:  # macOS, Linux
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    for attachment in selected_reminder.attachments:
        link = tk.Label(attachments_window, text=os.path.basename(attachment), fg="blue", cursor="hand2")
        link.pack()
        link.bind("<Button-1>", lambda e, path=attachment: open_attachment(path))


def refresh_reminder_list_by_date(date):
    reminder_list.delete(0, tk.END)  # Clear existing entries
    for reminder in reminders:
        if reminder.remind_time.date() == date:
            formatted_datetime = reminder.remind_time.strftime("%B %d, %Y @ %I:%M%p")
            display_text = f"{formatted_datetime}: {reminder.message}"
            reminder_list.insert(tk.END, display_text)


def previous_day():
    global current_view_date
    current_view_date -= timedelta(days=1)
    refresh_reminder_list_by_date(current_view_date)


def next_day():
    global current_view_date
    current_view_date += timedelta(days=1)
    refresh_reminder_list_by_date(current_view_date)


def view_date(date):
    global current_view_date
    current_view_date = date
    refresh_reminder_list_by_date(date)


def create_reminder_ui():
    global window, reminder_list, current_view_date
    window = tk.Tk()
    window.title("Reminder App")
    window.geometry("600x400")
    window.resizable(False, False)

    nav_frame = tk.Frame(window)
    nav_frame.pack(fill=tk.X)

    left_spacer = tk.Frame(nav_frame, width=200)
    left_spacer.pack(side=tk.LEFT, expand=True)

    tk.Button(nav_frame, text="<", command=previous_day).pack(side=tk.LEFT)
    tk.Button(nav_frame, text="Current Date", command=lambda: view_date(datetime.now().date())).pack(side=tk.LEFT)
    tk.Button(nav_frame, text=">", command=next_day).pack(side=tk.LEFT)

    right_spacer = tk.Frame(nav_frame, width=200)
    right_spacer.pack(side=tk.LEFT, expand=True)

    icon_path = os.path.join(f"{os.getcwd()}\\images\\Idea.ico")
    window.iconbitmap(icon_path)
    window.withdraw()  # Add this line to hide the window initially
    tk.Button(window, text="Add Reminder", command=add_reminder).pack()
    reminder_list = tk.Listbox(window)
    reminder_list.pack(fill=tk.BOTH, expand=True)
    # tk.Button(window, text="View Attachments", command=view_attachments).pack()
    refresh_reminder_list()
    popup_menu = tk.Menu(window, tearoff=0)
    popup_menu.add_command(label="View Attachments", command=view_attachments)
    popup_menu.add_command(label="Edit Reminder", command=edit_selected_reminder)
    popup_menu.add_command(label="Delete Reminder", command=delete_selected_reminder)

    def on_right_click(event):
        # Attempt to set the selection to the item under the cursor
        try:
            reminder_list.selection_clear(0, tk.END)  # Clear existing selection
            clicked_item = reminder_list.nearest(event.y)  # Identify the item under the cursor
            reminder_list.selection_set(clicked_item)  # Set selection to the item
            reminder_list.activate(clicked_item)  # Ensure the item is active
        except tk.TclError:
            pass  # Handle potential error if right-click is out of bounds

        # Display the popup menu
        try:
            popup_menu.tk_popup(event.x_root, event.y_root)
        finally:
            popup_menu.grab_release()

    reminder_list.bind("<Button-3>", on_right_click)  # Bind right-click event

    # Button to view attachments
    # tk.Button(window, text="View Attachments", command=view_attachments).pack()


def delete_selected_reminder():
    selection = reminder_list.curselection()
    if selection:
        selected_index = selection[0]
        del reminders[selected_index]  # Delete the reminder from the list
        save_reminders()  # Save the updated list of reminders
        refresh_reminder_list()  # Refresh the display


def edit_selected_reminder():
    selection = reminder_list.curselection()
    if not selection:
        messagebox.showinfo("Info", "Please select a reminder first.")
        return

    selected_index = selection[0]
    selected_reminder = reminders[selected_index]

    edit_window = tk.Toplevel(window)
    edit_window.title("Edit Reminder")
    edit_window.geometry("600x400")
    edit_window.resizable(False, False)
    edit_window.grab_set()
    edit_window.focus_force()

    # Message editing
    tk.Label(edit_window, text="Message:").pack()
    message_entry = tk.Text(edit_window, height=3, width=50)
    message_entry.pack()
    message_entry.insert(tk.END, selected_reminder.message)

    # Attachment management
    tk.Label(edit_window, text="Attachments:").pack()
    attachment_listbox = tk.Listbox(edit_window, height=5, width=50)
    attachment_listbox.pack()
    tooltip = ToolTip(attachment_listbox)
    for attachment in selected_reminder.attachments:
        attachment_listbox.insert(tk.END, os.path.basename(attachment))

    def add_attachment():
        new_attachments = filedialog.askopenfilenames(title="Select file(s) to attach")
        if not isinstance(selected_reminder.attachments, list):
            selected_reminder.attachments = list(selected_reminder.attachments)

        for attachment in new_attachments:
            selected_reminder.attachments.append(attachment)
            attachment_listbox.insert(tk.END, os.path.basename(attachment))  # Display basename in the listbox

            # Bind hover events to show full attachment path
            def on_enter(path=attachment):
                tooltip.show_tip(path)

            def on_leave():
                tooltip.hide_tip()

            attachment_listbox.bind("<Enter>", on_enter)
            attachment_listbox.bind("<Leave>", on_leave)

    def remove_attachment():
        selected_attachments = attachment_listbox.curselection()
        for index in selected_attachments[::-1]:  # Reverse to avoid index shifting
            selected_reminder.attachments.pop(index)
            attachment_listbox.delete(index)

    tk.Button(edit_window, text="Add Attachment", command=add_attachment).pack()
    tk.Button(edit_window, text="Remove Selected Attachment", command=remove_attachment).pack()

    def save_changes():
        selected_reminder.message = message_entry.get("1.0", tk.END).strip()
        # No need to update attachments here since they're updated in real-time by add_attachment and remove_attachment
        save_reminders()
        refresh_reminder_list()
        edit_window.destroy()

    tk.Button(edit_window, text="Save Changes", command=save_changes).pack()


def show_window():
    print("Attempting to show window")
    window.after(0, lambda: window.deiconify())


def start_system_tray():
    # Replace "your_icon_path.png" with the path to your actual icon image
    image = Image.open(f"{os.getcwd()}\\images\\Idea.ico")  # Ensure you have an
    # icon image at this path
    menu_items = Menu(Item('Open', show_window), Item('Quit', lambda ico, itm: ico.stop()))
    tray_icon = Icon("ReminderApp", image, "Reminder Application", menu_items)
    tray_icon.run_detached()


def start_scheduler():
    def periodic_check():
        safe_check_reminders()
        window.after(60000, periodic_check)

    window.after(0, periodic_check)


if __name__ == "__main__":
    reminders = load_reminders()
    create_reminder_ui()
    start_scheduler()  # Adjusted to work with Tkinter's event loop
    start_system_tray()
    window.mainloop()
