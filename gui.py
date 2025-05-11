# import tkinter as tk
# from tkinter import filedialog, messagebox, ttk
# import os
# import requests
# import json
# from PIL import Image, ImageTk
# import math
#
#
# class ImageGalleryGUI:
# 	def __init__(self, root):
# 		self.root = root
# 		self.root.title("Image Gallery Rating System")
# 		self.root.geometry("1000x700")
#
# 		self.default_folder = '/Users/yuda/Desktop/vs_code_projects/saatchy_art_data/'
# 		self.images = []  # List of tuples: (image_path, image_name, image_id)
# 		self.preferences = {}  # Dictionary of {image_id: 0/1/-1}
# 		self.thumbnail_size = 150
# 		self.columns = 4
#
# 		self.main_frame = tk.Frame(self.root)
# 		self.main_frame.pack(fill=tk.BOTH, expand=True)
#
# 		self.create_top_panel()
# 		self.create_gallery()
# 		self.create_bottom_panel()
#
# 		if os.path.exists(self.default_folder):
# 			self.load_images_from_folder(self.default_folder)
#
# 	def create_top_panel(self):
# 		top_frame = tk.Frame(self.main_frame)
# 		top_frame.pack(fill=tk.X, padx=10, pady=5)
#
# 		tk.Label(top_frame, text="API Endpoint:").pack(side=tk.LEFT)
# 		self.endpoint_entry = tk.Entry(top_frame, width=40)
# 		self.endpoint_entry.pack(side=tk.LEFT, padx=10)
# 		self.endpoint_entry.insert(0, "http://127.0.0.1:8000/predict")
#
# 		tk.Button(top_frame, text="Select Folder", command=self.select_folder).pack(side=tk.LEFT, padx=10)
# 		tk.Button(top_frame, text="Submit Ratings", command=self.submit_preferences, bg="green", fg="white").pack(side=tk.RIGHT, padx=10)
# 		self.status_label = tk.Label(top_frame, text="Ready")
# 		self.status_label.pack(side=tk.RIGHT, padx=20)
#
# 		id_frame = tk.Frame(self.main_frame)
# 		id_frame.pack(fill=tk.X, padx=10, pady=2)
# 		tk.Label(id_frame, text="Latest New ID:").pack(side=tk.LEFT)
# 		self.new_id_label = tk.Label(id_frame, text="None", font=("Arial", 12, "bold"))
# 		self.new_id_label.pack(side=tk.LEFT, padx=10)
#
# 		filter_frame = tk.Frame(self.main_frame)
# 		filter_frame.pack(fill=tk.X, padx=10, pady=2)
# 		tk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
# 		self.filter_var = tk.StringVar(value="All")
# 		tk.OptionMenu(filter_frame, self.filter_var, "All", "Liked", "Disliked", "Unrated", command=self.apply_filter).pack(side=tk.LEFT)
#
# 		size_frame = tk.Frame(self.main_frame)
# 		size_frame.pack(fill=tk.X, padx=10, pady=2)
# 		tk.Label(size_frame, text="Thumbnail Size:").pack(side=tk.LEFT)
# 		self.size_slider = tk.Scale(size_frame, from_=80, to=250, orient=tk.HORIZONTAL, command=self.change_thumbnail_size, length=200)
# 		self.size_slider.set(self.thumbnail_size)
# 		self.size_slider.pack(side=tk.LEFT, padx=5)
#
# 	def create_gallery(self):
# 		self.canvas_frame = tk.Frame(self.main_frame)
# 		self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
#
# 		self.canvas = tk.Canvas(self.canvas_frame, bg="white")
# 		self.scrollbar_y = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
# 		self.scrollbar_x = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
# 		self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)
#
# 		self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
# 		self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
# 		self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
#
# 		self.gallery_frame = tk.Frame(self.canvas, bg="white")
# 		self.canvas_window = self.canvas.create_window((0, 0), window=self.gallery_frame, anchor="nw")
#
# 		self.canvas.bind('<Configure>', self.on_canvas_configure)
# 		self.gallery_frame.bind('<Configure>', self.on_frame_configure)
# 		self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
#
# 	def create_bottom_panel(self):
# 		bottom_frame = tk.Frame(self.main_frame)
# 		bottom_frame.pack(fill=tk.X, padx=10, pady=5)
# 		self.stats_label = tk.Label(bottom_frame, text="Images: 0 | Liked: 0 | Disliked: 0 | Unrated: 0")
# 		self.stats_label.pack(side=tk.LEFT)
#
# 	def on_canvas_configure(self, event):
# 		self.canvas.configure(scrollregion=self.canvas.bbox("all"))
# 		new_columns = max(1, event.width // (self.thumbnail_size + 30))
# 		if new_columns != self.columns:
# 			self.columns = new_columns
# 			self.display_gallery()
#
# 	def on_frame_configure(self, event):
# 		self.canvas.configure(scrollregion=self.canvas.bbox("all"))
#
# 	def on_mousewheel(self, event):
# 		self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
#
# 	def select_folder(self):
# 		folder = filedialog.askdirectory(title="Select Folder Containing Images")
# 		if folder:
# 			self.load_images_from_folder(folder)
#
# 	def load_images_from_folder(self, folder_path):
# 		self.status_label.config(text=f"Loading from {os.path.basename(folder_path)}...")
# 		self.root.update()
#
# 		self.images.clear()
# 		self.preferences.clear()
#
# 		valid_ext = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
# 		for fname in os.listdir(folder_path):
# 			if fname.lower().endswith(valid_ext):
# 				path = os.path.join(folder_path, fname)
# 				try:
# 					img_id = int(''.join(filter(str.isdigit, fname)))
# 					self.images.append((path, fname, img_id))
# 					self.preferences[img_id] = -1
# 				except:
# 					continue
#
# 		self.images.sort(key=lambda x: x[2])
# 		self.display_gallery()
# 		self.update_stats()
# 		self.status_label.config(text=f"Loaded {len(self.images)} images")
#
# 	def filtered_images(self):
# 		f = self.filter_var.get()
# 		return [img for img in self.images if f == "All" or (f == "Liked" and self.preferences[img[2]] == 1) or (f == "Disliked" and self.preferences[img[2]] == 0) or (f == "Unrated" and self.preferences[img[2]] == -1)]
#
# 	def display_gallery(self):
# 		for widget in self.gallery_frame.winfo_children():
# 			widget.destroy()
#
# 		if not self.images:
# 			tk.Label(self.gallery_frame, text="No images to display", bg="white").pack(pady=50)
# 			return
#
# 		for i, (path, name, img_id) in enumerate(self.filtered_images()):
# 			row, col = divmod(i, self.columns)
# 			frame = tk.Frame(self.gallery_frame, bd=1, relief=tk.SOLID, padx=5, pady=5)
# 			frame.grid(row=row, column=col, padx=10, pady=10)
#
# 			try:
# 				img = Image.open(path)
# 				img = self.resize_image(img, self.thumbnail_size)
# 				photo = ImageTk.PhotoImage(img)
# 				frame.image = photo
#
# 				border_color = {1: "green", 0: "red", -1: "gray"}[self.preferences[img_id]]
#
# 				canvas = tk.Canvas(frame, width=self.thumbnail_size, height=self.thumbnail_size, bd=0, highlightthickness=4, highlightbackground=border_color)
# 				canvas.create_image(self.thumbnail_size // 2, self.thumbnail_size // 2, image=photo)
# 				canvas.pack()
#
# 				tk.Label(frame, text=f"ID: {img_id}").pack()
#
# 				btns = tk.Frame(frame)
# 				btns.pack(pady=5)
#
# 				tk.Button(btns, text="👍", bg="lightgreen", command=lambda i=img_id: self.like_image(i)).pack(side=tk.LEFT, padx=2)
# 				tk.Button(btns, text="👎", bg="salmon", command=lambda i=img_id: self.dislike_image(i)).pack(side=tk.RIGHT, padx=2)
#
# 			except Exception as e:
# 				tk.Label(frame, text=f"Error\n{e}", width=20, height=6).pack()
#
# 	def resize_image(self, img, size):
# 		w, h = img.size
# 		ratio = min(size / w, size / h)
# 		return img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
#
# 	def like_image(self, img_id):
# 		self.preferences[img_id] = 1
# 		self.update_gallery_item(img_id)
# 		self.update_stats()
#
# 	def dislike_image(self, img_id):
# 		self.preferences[img_id] = 0
# 		self.update_gallery_item(img_id)
# 		self.update_stats()
#
# 	def update_gallery_item(self, img_id):
# 		self.display_gallery()  # Redraw entire gallery for simplicity
#
# 	def update_stats(self):
# 		total = len(self.images)
# 		liked = sum(1 for v in self.preferences.values() if v == 1)
# 		disliked = sum(1 for v in self.preferences.values() if v == 0)
# 		unrated = total - liked - disliked
# 		self.stats_label.config(text=f"Images: {total} | Liked: {liked} | Disliked: {disliked} | Unrated: {unrated}")
#
# 	def apply_filter(self, *args):
# 		self.display_gallery()
#
# 	def change_thumbnail_size(self, val):
# 		self.thumbnail_size = int(val)
# 		self.display_gallery()
#
# 	def submit_preferences(self):
# 		endpoint = self.endpoint_entry.get().strip()
# 		if not endpoint:
# 			messagebox.showerror("Error", "Please provide an API endpoint URL")
# 			return
#
# 		unrated = [name for name, pref in self.preferences.items() if pref == -1]
# 		if unrated:
# 			response = messagebox.askyesno("Confirmation", f"There are {len(unrated)} unrated images. Submit anyway?")
# 			if not response:
# 				return
#
# 		image_ids = []
# 		targets = []
#
# 		for img_id, preference in self.preferences.items():
# 			if preference != -1:
# 				image_ids.append(img_id)
# 				targets.append(preference)
#
# 		payload = {"image_ids": image_ids, "target": targets}
#
# 		try:
# 			response = requests.post(endpoint, json=payload)
# 			if response.status_code == 200:
# 				try:
# 					data = response.json()
# 					if isinstance(data, list) and all(isinstance(i, int) for i in data):
# 						self.new_id_label.config(text=f"IDs: {', '.join(map(str, data))}")
# 						messagebox.showinfo("Success", f"Preferences submitted. Returned IDs: {data}")
# 						self.load_returned_images(data)
# 					else:
# 						self.new_id_label.config(text=str(data))
# 						messagebox.showinfo("Success", f"Preferences submitted. Response: {data}")
# 				except Exception as e:
# 					messagebox.showinfo("Success", f"Preferences submitted. Raw response: {response.text}")
# 			else:
# 				messagebox.showerror("Error", f"Failed to submit: {response.status_code} - {response.text}")
# 		except Exception as e:
# 			messagebox.showerror("Error", f"Failed to connect to API: {str(e)}")
#
# 	def load_returned_images(self, id_list):
# 		new_images = []
# 		for path, name, img_id in self.images:
# 			if img_id in id_list:
# 				new_images.append((path, name, img_id))
#
# 		if not new_images:
# 			messagebox.showinfo("Info", "None of the returned image IDs matched local images.")
# 			return
#
# 		# Temporarily replace the images with only the new ones
# 		self.images = new_images
# 		self.preferences = {img_id: -1 for _, _, img_id in new_images}
# 		self.display_gallery()
# 		self.update_stats()
#
#
# if __name__ == "__main__":
# 	root = tk.Tk()
# 	app = ImageGalleryGUI(root)
# 	root.mainloop()

# Optimized Image Gallery Rating System
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import requests
import json
from PIL import Image, ImageTk


class ImageGalleryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Gallery Rating System")
        self.root.geometry("1000x700")

        self.default_folder = '/Users/yuda/Desktop/vs_code_projects/saatchy_art_data/'
        self.images = []
        self.preferences = {}
        self.thumbnail_size = 150
        self.columns = 4
        self.photo_cache = {}

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_top_panel()
        self.create_gallery()
        self.create_bottom_panel()

        if os.path.exists(self.default_folder):
            self.load_images_from_folder(self.default_folder)

    def create_top_panel(self):
        top_frame = tk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="API Endpoint:").pack(side=tk.LEFT)
        self.endpoint_entry = tk.Entry(top_frame, width=40)
        self.endpoint_entry.pack(side=tk.LEFT, padx=10)
        self.endpoint_entry.insert(0, "http://127.0.0.1:8000/predict")

        tk.Button(top_frame, text="Select Folder", command=self.select_folder).pack(side=tk.LEFT, padx=10)
        tk.Button(top_frame, text="Submit Ratings", command=self.submit_preferences, bg="green", fg="white").pack(side=tk.RIGHT, padx=10)
        self.status_label = tk.Label(top_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT, padx=20)

        id_frame = tk.Frame(self.main_frame)
        id_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(id_frame, text="Latest New ID:").pack(side=tk.LEFT)
        self.new_id_label = tk.Label(id_frame, text="None", font=("Arial", 12, "bold"))
        self.new_id_label.pack(side=tk.LEFT, padx=10)

        filter_frame = tk.Frame(self.main_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="All")
        tk.OptionMenu(filter_frame, self.filter_var, "All", "Liked", "Disliked", "Unrated", command=self.display_gallery).pack(side=tk.LEFT)

        size_frame = tk.Frame(self.main_frame)
        size_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(size_frame, text="Thumbnail Size:").pack(side=tk.LEFT)
        self.size_slider = tk.Scale(size_frame, from_=80, to=250, orient=tk.HORIZONTAL, command=self.change_thumbnail_size, length=200)
        self.size_slider.set(self.thumbnail_size)
        self.size_slider.pack(side=tk.LEFT, padx=5)

    def create_gallery(self):
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.scrollbar_y = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.gallery_frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.gallery_frame, anchor="nw")

        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.gallery_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def create_bottom_panel(self):
        bottom_frame = tk.Frame(self.main_frame)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        self.stats_label = tk.Label(bottom_frame, text="Images: 0 | Liked: 0 | Disliked: 0 | Unrated: 0")
        self.stats_label.pack(side=tk.LEFT)

    def on_canvas_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        new_columns = max(1, event.width // (self.thumbnail_size + 30))
        if new_columns != self.columns:
            self.columns = new_columns
            self.display_gallery()

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder Containing Images")
        if folder:
            self.load_images_from_folder(folder)

    def load_images_from_folder(self, folder_path):
        self.status_label.config(text=f"Loading from {os.path.basename(folder_path)}...")
        self.root.update()

        self.images.clear()
        self.preferences.clear()
        self.photo_cache.clear()

        valid_ext = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
        for fname in os.listdir(folder_path):
            if fname.lower().endswith(valid_ext):
                path = os.path.join(folder_path, fname)
                try:
                    img_id = int(''.join(filter(str.isdigit, fname)))
                    self.images.append((path, fname, img_id))
                    self.preferences[img_id] = -1
                except:
                    continue

        self.images.sort(key=lambda x: x[2])
        self.display_gallery()
        self.update_stats()
        self.status_label.config(text=f"Loaded {len(self.images)} images")

    def filtered_images(self):
        f = self.filter_var.get()
        return [img for img in self.images if f == "All" or (f == "Liked" and self.preferences[img[2]] == 1) or (f == "Disliked" and self.preferences[img[2]] == 0) or (f == "Unrated" and self.preferences[img[2]] == -1)]

    def display_gallery(self):
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()

        for i, (path, name, img_id) in enumerate(self.filtered_images()):
            row, col = divmod(i, self.columns)
            frame = tk.Frame(self.gallery_frame, bd=1, relief=tk.SOLID, padx=5, pady=5)
            frame.grid(row=row, column=col, padx=10, pady=10)

            try:
                if img_id not in self.photo_cache:
                    img = Image.open(path)
                    img = self.resize_image(img, self.thumbnail_size)
                    self.photo_cache[img_id] = ImageTk.PhotoImage(img)

                border_color = {1: "green", 0: "red", -1: "gray"}[self.preferences[img_id]]

                canvas = tk.Canvas(frame, width=self.thumbnail_size, height=self.thumbnail_size, bd=0, highlightthickness=4, highlightbackground=border_color)
                canvas.create_image(self.thumbnail_size // 2, self.thumbnail_size // 2, image=self.photo_cache[img_id])
                canvas.pack()

                tk.Label(frame, text=f"ID: {img_id}").pack()

                btns = tk.Frame(frame)
                btns.pack(pady=5)

                tk.Button(btns, text="👍", bg="lightgreen", command=lambda i=img_id: self.set_preference(i, 1)).pack(side=tk.LEFT, padx=2)
                tk.Button(btns, text="👎", bg="salmon", command=lambda i=img_id: self.set_preference(i, 0)).pack(side=tk.RIGHT, padx=2)

            except Exception as e:
                tk.Label(frame, text=f"Error\n{e}", width=20, height=6).pack()

    def resize_image(self, img, size):
        w, h = img.size
        ratio = min(size / w, size / h)
        return img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    def set_preference(self, img_id, value):
        self.preferences[img_id] = value
        self.display_gallery()
        self.update_stats()

    def update_stats(self):
        total = len(self.images)
        liked = sum(1 for v in self.preferences.values() if v == 1)
        disliked = sum(1 for v in self.preferences.values() if v == 0)
        unrated = total - liked - disliked
        self.stats_label.config(text=f"Images: {total} | Liked: {liked} | Disliked: {disliked} | Unrated: {unrated}")

    def change_thumbnail_size(self, val):
        self.thumbnail_size = int(val)
        self.photo_cache.clear()
        self.display_gallery()

    def submit_preferences(self):
        endpoint = self.endpoint_entry.get().strip()
        if not endpoint:
            messagebox.showerror("Error", "Please provide an API endpoint URL")
            return

        unrated = [img_id for img_id, pref in self.preferences.items() if pref == -1]
        if unrated:
            response = messagebox.askyesno("Confirmation", f"There are {len(unrated)} unrated images. Submit anyway?")
            if not response:
                return

        image_ids = [img_id for img_id, pref in self.preferences.items() if pref != -1]
        targets = [self.preferences[img_id] for img_id in image_ids]

        try:
            response = requests.post(endpoint, json={"image_ids": image_ids, "target": targets})
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list) and all(isinstance(i, int) for i in data):
                        self.new_id_label.config(text=f"IDs: {', '.join(map(str, data))}")
                        messagebox.showinfo("Success", f"Preferences submitted. Returned IDs: {data}")
                        self.load_returned_images(data)
                    else:
                        self.new_id_label.config(text=str(data))
                        messagebox.showinfo("Success", f"Preferences submitted. Response: {data}")
                except Exception:
                    messagebox.showinfo("Success", f"Preferences submitted. Raw response: {response.text}")
            else:
                messagebox.showerror("Error", f"Failed to submit: {response.status_code} - {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to API: {str(e)}")

    def load_returned_images(self, id_list):
        new_images = [(path, name, img_id) for path, name, img_id in self.images if img_id in id_list]
        if not new_images:
            messagebox.showinfo("Info", "None of the returned image IDs matched local images.")
            return

        self.images = new_images
        self.preferences = {img_id: -1 for _, _, img_id in new_images}
        self.photo_cache.clear()
        self.display_gallery()
        self.update_stats()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGalleryGUI(root)
    root.mainloop()