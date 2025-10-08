import os
import json
import time
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from threading import Thread


from deep_translator import GoogleTranslator


class TranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.title("RPGlator")
        self.root.geometry("600x650")
        self.root.configure(bg="#2b2b2b")
        self.root.resizable(False, False)

        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.do_move)

        self.is_translating = False
        self.translator = None
        self.WWW_PATH = ""
        self.CONFIG_FILE = "rpglator_config.json"

        # Ayar Değişkenleri (API KEY KALDIRILDI)
        self.TRANSLATION_NAME = tk.StringVar(value="{lang}_RPGlator")
        self.CURRENT_TRANSLATOR = tk.StringVar(value="Google Translator (Web Scraping)")
        self.SEPARATE_FILES = tk.BooleanVar(value=False)
        self.original_lang_var = tk.StringVar(value="English")
        self.new_lang_var = tk.StringVar(value="Turkish")
        self.game_entry_var = tk.StringVar(value="")

        # RPG Maker Veri Atlamaları
        self.SKIP_FILES = {'actors.json', 'animations.json'}
        # 'description' eklendi - genellikle çevrilebilir, ancak bu örnekte koruyucu atlama olarak tutuldu.
        self.SKIP_KEYS_LOWER = {
            'filename', 'meta', 'note', 'picture', 'charactername',
            'battlername', 'face', 'image', 'bgm', 'bgs', 'me', 'se',
            'description'  # 'description' notlarda bazen not alanı olarak kullanılabiliyor
        }
        self.AUDIO_KEYS = {'name', 'volume', 'pitch', 'pan'}
        self.BATCH_SIZE = 50  # Toplu çeviri için dize boyutu

        self.ALL_LANGUAGES = {
            "English": "en", "Turkish": "tr", "Japanese": "ja",
            "Chinese (Simplified)": "zh-CN", "Korean": "ko",
            "Spanish": "es", "French": "fr", "German": "de",
            "Russian": "ru", "Portuguese": "pt", "Arabic": "ar",
            "Italian": "it", "Vietnamese": "vi"  # Daha fazla dil eklendi
        }

        self.load_settings()
        self.setup_ui()

    # --- Ayar Kayıt/Yükleme Metotları (Yeni) ---
    def load_settings(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.TRANSLATION_NAME.set(settings.get('translation_name', self.TRANSLATION_NAME.get()))
                    self.SEPARATE_FILES.set(settings.get('separate_files', self.SEPARATE_FILES.get()))
                    self.CURRENT_TRANSLATOR.set(settings.get('current_translator', self.CURRENT_TRANSLATOR.get()))
                    self.original_lang_var.set(settings.get('original_lang', self.original_lang_var.get()))
                    self.new_lang_var.set(settings.get('target_lang', self.new_lang_var.get()))
                    self.game_entry_var.set(settings.get('last_game_path', self.game_entry_var.get()))
                    self.WWW_PATH = settings.get('last_www_path', self.WWW_PATH)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        settings = {
            'translation_name': self.TRANSLATION_NAME.get(),
            'separate_files': self.SEPARATE_FILES.get(),
            'current_translator': self.CURRENT_TRANSLATOR.get(),
            'original_lang': self.original_lang_var.get(),
            'target_lang': self.new_lang_var.get(),
            'last_game_path': self.game_entry_var.get(),
            'last_www_path': self.WWW_PATH
        }
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    # --- Pencere Taşıma Metotları (Ana Pencere) ---
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    # --- Arayüz Kurulumu ---
    def setup_ui(self):
        # ... (Stil ayarları) ...
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground="#3c3c3c", background="#3c3c3c",
                        foreground="white", borderwidth=1, relief="solid")
        style.map('TCombobox', fieldbackground=[('readonly', '#3c3c3c')])
        style.configure("TProgressbar", thickness=20, background="#007acc", troughcolor="#3c3c3c")

        # Üst kontrol çubuğu
        control_frame = tk.Frame(self.root, bg="#1e1e1e", height=30)
        control_frame.pack(fill=tk.X)

        tk.Label(control_frame, text="RPGlator", bg="#1e1e1e", fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=10)

        close_btn = tk.Button(control_frame, text="✕", command=lambda: (self.save_settings(), self.root.destroy()),
                              bg="#1e1e1e", fg="white", relief=tk.FLAT,
                              activebackground="#ff0000", activeforeground="white",
                              font=("Segoe UI", 12, "bold"), padx=10, cursor="hand2")
        close_btn.pack(side=tk.RIGHT)

        minimize_btn = tk.Button(control_frame, text="—", command=self.root.iconify,
                                 bg="#1e1e1e", fg="white", relief=tk.FLAT,
                                 activebackground="#3c3c3c", activeforeground="white",
                                 font=("Segoe UI", 12, "bold"), padx=10, cursor="hand2")
        minimize_btn.pack(side=tk.RIGHT)

        # Üst menü bar
        menubar_frame = tk.Frame(self.root, bg="#2b2b2b")
        menubar_frame.pack(fill=tk.X, pady=(5, 0))

        menu_items = ["Translation", "Functions", "Classes", "Tools", "Log", "Settings", "About"]
        for item in menu_items:
            if item == "Translation":
                tk.Button(menubar_frame, text=item, bg="#2b2b2b", fg="#007acc",
                          font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                          padx=10, state="disabled").pack(side=tk.LEFT)
            elif item == "Settings":
                tk.Button(menubar_frame, text=item, bg="#2b2b2b", fg="white",
                          font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                          padx=10, command=self.open_settings).pack(side=tk.LEFT)
            else:
                # Diğer butonlar şimdilik fonksiyon içermez
                tk.Button(menubar_frame, text=item, bg="#2b2b2b", fg="white",
                          font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
                          padx=10).pack(side=tk.LEFT)

        # Ana frame
        main_frame = tk.Frame(self.root, bg="#2b2b2b")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Game dosya seçimi
        game_frame = tk.Frame(main_frame, bg="#2b2b2b")
        game_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(game_frame, text="Game Executable:", bg="#2b2b2b", fg="white",
                 font=("Segoe UI", 10), anchor="w", width=15).pack(side=tk.LEFT)

        game_entry_frame = tk.Frame(game_frame, bg="#3c3c3c", highlightbackground="#555", highlightthickness=1)
        game_entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.game_entry = tk.Entry(game_entry_frame, textvariable=self.game_entry_var, bg="#3c3c3c", fg="white",
                                   font=("Segoe UI", 9), relief=tk.FLAT,
                                   insertbackground="white", bd=0)
        self.game_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=3)

        browse_btn = tk.Button(game_entry_frame, text="...", command=self.browse_game,
                               bg="#3c3c3c", fg="white", relief=tk.FLAT,
                               font=("Segoe UI", 9, "bold"), bd=0,
                               padx=10, cursor="hand2")
        browse_btn.pack(side=tk.RIGHT, padx=2, pady=2)

        # Translator
        gen_frame = tk.Frame(main_frame, bg="#2b2b2b")
        gen_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(gen_frame, text="Translator:", bg="#2b2b2b", fg="white",
                 font=("Segoe UI", 10), anchor="w", width=15).pack(side=tk.LEFT)

        # Sadece Google Translator (Web Scraping) seçeneği bırakıldı
        generator_combo = ttk.Combobox(gen_frame, textvariable=self.CURRENT_TRANSLATOR,
                                       font=("Segoe UI", 9), state="readonly",
                                       values=["Google Translator (Web Scraping)"])
        generator_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Original Language
        orig_frame = tk.Frame(main_frame, bg="#2b2b2b")
        orig_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(orig_frame, text="Original Language:", bg="#2b2b2b", fg="white",
                 font=("Segoe UI", 10), anchor="w", width=15).pack(side=tk.LEFT)

        orig_combo = ttk.Combobox(orig_frame, textvariable=self.original_lang_var,
                                  font=("Segoe UI", 9), state="readonly",
                                  values=list(self.ALL_LANGUAGES.keys()))
        orig_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # New Language
        new_frame = tk.Frame(main_frame, bg="#2b2b2b")
        new_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(new_frame, text="Target Language:", bg="#2b2b2b", fg="white",
                 font=("Segoe UI", 10), anchor="w", width=15).pack(side=tk.LEFT)

        new_combo = ttk.Combobox(new_frame, textvariable=self.new_lang_var,
                                 font=("Segoe UI", 9), state="readonly",
                                 values=list(self.ALL_LANGUAGES.keys()))
        new_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Checkboxes
        checkbox_frame = tk.Frame(main_frame, bg="#2b2b2b")
        checkbox_frame.pack(fill=tk.X, pady=(0, 15))

        self.python_var = tk.BooleanVar(value=False)  # extract_var kaldırıldı

        tk.Checkbutton(checkbox_frame, text="Create Separate Translated Files (Requires Game Relaunch)",
                       variable=self.SEPARATE_FILES,
                       bg="#2b2b2b", fg="white", selectcolor="#2b2b2b",
                       font=("Segoe UI", 9), activebackground="#2b2b2b",
                       activeforeground="white").pack(side=tk.LEFT, padx=(0, 15))

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # Translate button
        self.translate_btn = tk.Button(main_frame, text="Translate",
                                       command=self.start_translation,
                                       bg="#007acc", fg="white",
                                       font=("Segoe UI", 11, "bold"),
                                       relief=tk.FLAT, cursor="hand2",
                                       height=2)
        self.translate_btn.pack(fill=tk.X, pady=(0, 15))

        # Status label
        status_frame = tk.Frame(main_frame, bg="#2b2b2b")
        status_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(status_frame, text="Status:", bg="#2b2b2b", fg="white",
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        self.status_label = tk.Label(status_frame, text="Ready", bg="#2b2b2b",
                                     fg="#4ec9b0", font=("Segoe UI", 10))
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))

        # Log area
        log_frame = tk.Frame(main_frame, bg="#1e1e1e", highlightbackground="#555", highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                                  bg="#1e1e1e", fg="#d4d4d4",
                                                  font=("Consolas", 9), relief=tk.FLAT,
                                                  insertbackground="white")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # UI başlatıldığında, kayıtlı oyun yolunu kontrol et
        if self.game_entry_var.get() and self.WWW_PATH:
            self.log(f"Loaded previous game path: {self.game_entry_var.get()}")

    # --- Ayarlar Penceresi Metotları ---
    def open_settings(self):
        if hasattr(self, 'settings_window') and tk.Toplevel.winfo_exists(self.settings_window):
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.overrideredirect(True)
        self.settings_window.geometry("480x350")  # Pencere boyutu küçültüldü
        self.settings_window.configure(bg="#2b2b2b")
        self.settings_window.transient(self.root)
        self.settings_window.resizable(False, False)

        self.settings_x = 0
        self.settings_y = 0
        self.settings_window.bind('<Button-1>', self.start_move_settings)
        self.settings_window.bind('<B1-Motion>', self.do_move_settings)

        # Kontrol çubuğu
        control_frame = tk.Frame(self.settings_window, bg="#1e1e1e", height=30)
        control_frame.pack(fill=tk.X)

        tk.Label(control_frame, text="Settings", bg="#1e1e1e", fg="white",
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=10)

        tk.Button(control_frame, text="✕", command=self.close_settings,
                  bg="#1e1e1e", fg="white", relief=tk.FLAT,
                  activebackground="#ff0000", activeforeground="white",
                  font=("Segoe UI", 12, "bold"), padx=10, cursor="hand2").pack(side=tk.RIGHT)

        tk.Button(control_frame, text="—", command=self.settings_window.iconify,
                  bg="#1e1e1e", fg="white", relief=tk.FLAT,
                  activebackground="#3c3c3c", activeforeground="white",
                  font=("Segoe UI", 12, "bold"), padx=10, cursor="hand2").pack(side=tk.RIGHT)

        # Ana içerik
        main_frame = tk.Frame(self.settings_window, bg="#2b2b2b")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Translation Name
        tk.Label(main_frame, text="Translation Folder Name Template:", bg="#2b2b2b", fg="white",
                 font=("Segoe UI", 10), anchor="w").pack(fill=tk.X, pady=(0, 5))

        name_entry = tk.Entry(main_frame, textvariable=self.TRANSLATION_NAME,
                              bg="#3c3c3c", fg="white", relief=tk.FLAT,
                              insertbackground="white")
        name_entry.pack(fill=tk.X, pady=(0, 20))
        tk.Label(main_frame, text="Use {lang} placeholder for target language code.", bg="#2b2b2b", fg="#888",
                 font=("Segoe UI", 8), anchor="w").pack(fill=tk.X, pady=(0, 10))

        # API Key bölümü kaldırıldı/bilgi mesajı eklendi
        tk.Label(main_frame, text="Note: This version uses Google Translator (Web Scraping).\nNo API Key is required.",
                 bg="#2b2b2b", fg="#4ec9b0",
                 font=("Segoe UI", 9, "italic"), anchor="w").pack(fill=tk.X, pady=(0, 30))

        # Restore Settings button
        restore_btn = tk.Button(main_frame, text="Restore Default Settings",
                                bg="#3c3c3c", fg="white",
                                font=("Segoe UI", 10),
                                relief=tk.FLAT, cursor="hand2", pady=8,
                                command=self.restore_settings)
        restore_btn.pack(fill=tk.X)

        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings)
        self.settings_window.update_idletasks()
        w = self.settings_window.winfo_width()
        h = self.settings_window.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (w // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (h // 2)
        self.settings_window.geometry(f'+{x}+{y}')

    def start_move_settings(self, event):
        self.settings_x = event.x
        self.settings_y = event.y

    def do_move_settings(self, event):
        deltax = event.x - self.settings_x
        deltay = event.y - self.settings_y
        x = self.settings_window.winfo_x() + deltax
        y = self.settings_window.winfo_y() + deltay
        self.settings_window.geometry(f"+{x}+{y}")

    def close_settings(self):
        self.settings_window.destroy()

    def restore_settings(self):
        """Ayarları varsayılan değerlerine sıfırlar."""
        self.TRANSLATION_NAME.set("{lang}_RPGlator")
        self.SEPARATE_FILES.set(False)
        self.CURRENT_TRANSLATOR.set("Google Translator (Web Scraping)")
        self.save_settings()  # Varsayılan ayarları kaydet
        messagebox.showinfo("Settings", "Default settings restored.")

    # --- Dosya İşlemleri ve Çeviri Hazırlığı ---
    def log(self, message, is_error=False):
        """Loglama işlemini root.after() ile UI thread'e taşır."""
        color = "#d4d4d4"
        if is_error:
            color = "#ff0000"
        elif "WARNING" in message.upper():
            color = "#ffcc00"
        elif "COMPLETED" in message.upper():
            color = "#4ec9b0"

        def insert_log():
            self.log_text.tag_config(color, foreground=color)
            self.log_text.insert(tk.END, message + "\n", color)
            self.log_text.see(tk.END)

        self.root.after(0, insert_log)

    def browse_game(self):
        exe_path = filedialog.askopenfilename(
            title="Select Game Executable (Game.exe)",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )

        if not exe_path:
            return

        base_dir = os.path.dirname(exe_path)
        www_path = ""

        # MV/MZ için 'www' kontrolü
        test_path_mv_mz = os.path.join(base_dir, "www")

        if os.path.exists(test_path_mv_mz) and os.path.exists(os.path.join(test_path_mv_mz, "data")):
            www_path = test_path_mv_mz
        # Ace/XP/VX için 'data' kontrolü (www yoksa)
        elif os.path.exists(os.path.join(base_dir, "data")):
            www_path = base_dir

        if www_path:
            self.game_entry_var.set(exe_path)
            self.WWW_PATH = www_path
            self.log(f"Game selected: {os.path.basename(exe_path)}")
            self.log(f"RPG Maker data folder found: {www_path}\n")
            self.save_settings()  # Başarılı seçimde kaydet
        else:
            messagebox.showerror("Error",
                                 "RPG Maker 'data' folder not found! Please select a valid Game.exe.")

    def get_lang_code(self, lang_name):
        return self.ALL_LANGUAGES.get(lang_name, "auto")  # "auto" Google Translator için uygun

    def start_translation(self):
        if self.is_translating:
            messagebox.showwarning("Warning", "Translation already in progress!")
            return

        if not self.WWW_PATH or not os.path.exists(self.WWW_PATH):
            messagebox.showerror("Error", "Please select a valid game executable first!")
            return

        source_lang = self.get_lang_code(self.original_lang_var.get())
        target_lang = self.get_lang_code(self.new_lang_var.get())
        translator_choice = self.CURRENT_TRANSLATOR.get()

        if source_lang == target_lang:
            messagebox.showwarning("Warning", "Source and target languages are the same!")
            return

        self.log_text.delete(1.0, tk.END)

        self.is_translating = True
        self.translate_btn.config(state=tk.DISABLED, text="Translating...")
        self.status_label.config(text="Processing...", fg="#ffcc00")
        self.save_settings()

        # Çeviri işini ayrı bir Thread'de başlat
        Thread(target=self.translation_worker, args=(source_lang, target_lang, translator_choice), daemon=True).start()

    # --- Çeviri Çalışanı (Worker) Metotları ---
    def translation_worker(self, source_lang, target_lang, translator_choice):
        try:
            # Sadece GoogleTranslator kullanılırken api_key gerekli değildir
            self.translator = GoogleTranslator(source=source_lang, target=target_lang)

            data_path = os.path.join(self.WWW_PATH, "data")
            output_dir = data_path

            if self.SEPARATE_FILES.get():
                folder_name = self.TRANSLATION_NAME.get().replace("{lang}", target_lang)
                output_dir = os.path.join(self.WWW_PATH, folder_name, "data")
                os.makedirs(output_dir, exist_ok=True)
                self.log(f"Separate translation folder created: {os.path.join(self.WWW_PATH, folder_name)}")

            json_files = [
                f for f in os.listdir(data_path)
                if f.endswith('.json')
                   and not f.endswith('_backup.json')
                   and f.lower() not in self.SKIP_FILES
            ]

            self.log(f"Found {len(json_files)} JSON files to translate.")
            self.log(
                f"Using {translator_choice}: {self.original_lang_var.get()} ({source_lang}) → {self.new_lang_var.get()} ({target_lang})\n")

            self.root.after(0, lambda: self.progress.config(maximum=len(json_files)))

            success_count = 0
            for idx, json_file in enumerate(json_files, 1):
                input_filepath = os.path.join(data_path, json_file)
                output_filepath = os.path.join(output_dir, json_file)
                self.log(f"[{idx}/{len(json_files)}] Processing: {json_file}")

                if self.translate_json_file(input_filepath, output_filepath):
                    success_count += 1

                self.root.after(0, lambda i=idx: self.progress.config(value=i))

            self.log("\n" + "=" * 60)
            self.log(f"TRANSLATION COMPLETED!")
            self.log(f"Successfully translated: {success_count}/{len(json_files)} files")
            self.log("=" * 60)
            self.root.after(0, lambda: self.status_label.config(text="Complete", fg="#4ec9b0"))

            messagebox.showinfo("Success",
                                f"Translation completed!\n{success_count}/{len(json_files)} files translated.")

        except Exception as e:
            self.log(f"CRITICAL ERROR: {type(e).__name__}: {e}", is_error=True)
            self.root.after(0, lambda: self.status_label.config(text="Error", fg="#ff0000"))
            messagebox.showerror("Critical Error", f"An error occurred during translation: {e}")
        finally:
            self.is_translating = False
            self.root.after(0, lambda: self.translate_btn.config(state=tk.NORMAL, text="Translate"))
            self.root.after(0, lambda: self.progress.config(value=0))

    def translate_json_file(self, input_filepath, output_filepath):
        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 1. Yedekleme oluştur
            backup_path = input_filepath.replace('.json', '_backup.json')
            if not os.path.exists(backup_path):
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.log(f"  Backup created: {os.path.basename(backup_path)}")

            # 2. Tüm çevrilebilir metinleri topla (Batch için)
            texts_to_translate = []
            structure_map = []  # Metinlerin orijinal konumunu kaydet

            def collect_translatable_texts(key, value, parent_obj):
                if isinstance(value, str):
                    if self.is_translatable(key, value, parent_obj):
                        texts_to_translate.append(value)
                        structure_map.append({'type': 'str', 'key': key, 'parent': parent_obj})
                        return True
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if collect_translatable_texts(None, item, value):
                            structure_map[-1]['list_index'] = i
                elif isinstance(value, dict):
                    for k, v in value.items():
                        if collect_translatable_texts(k, v, value):
                            structure_map[-1]['dict_key'] = k
                return False

            collect_translatable_texts(None, data, None)

            if not texts_to_translate:
                self.log("  No translatable text found.")
                return True

            self.log(f"  Found {len(texts_to_translate)} strings for translation. Starting batch translation...")

            # 3. Toplu çeviri yap
            translated_texts = []
            for i in range(0, len(texts_to_translate), self.BATCH_SIZE):
                batch = texts_to_translate[i:i + self.BATCH_SIZE]

                try:
                    # GoogleTranslator'da tek seferde birden fazla dize çevirilebilir.
                    batch_results = self.translator.translate(batch=batch)

                    if not isinstance(batch_results, list):
                        # Bazen deep_translator tek elemanlı liste yerine direkt string döndürebilir
                        batch_results = [batch_results]

                    translated_texts.extend(batch_results)
                    self.log(f"  Batch {i // self.BATCH_SIZE + 1} translated ({len(batch)} strings).")
                except Exception as e:
                    self.log(f"  WARNING: Batch translation failed ({e}). Returning original texts for this batch.",
                             is_error=True)
                    # Hata olursa orijinal metinleri kullan
                    translated_texts.extend(batch)

                time.sleep(0.5)  # API'yi yavaşlatmak için küçük bir bekleme (Web Scraping için önerilir)

            # 4. Çevrilmiş metinleri orijinal yapıya geri yerleştir
            def insert_translated_texts(current_data):
                nonlocal translated_texts

                if isinstance(current_data, list):
                    for i in range(len(current_data)):
                        if isinstance(current_data[i], str) and current_data[i] in texts_to_translate:
                            # Diziyi güncellerken, çevrilmiş metin listesinden al ve metin listesinden çıkar
                            original_index = texts_to_translate.index(current_data[i])
                            current_data[i] = translated_texts[original_index]
                            texts_to_translate.pop(original_index)
                            translated_texts.pop(original_index)
                        elif isinstance(current_data[i], (dict, list)):
                            insert_translated_texts(current_data[i])

                elif isinstance(current_data, dict):
                    for key in list(current_data.keys()):
                        value = current_data[key]
                        if isinstance(value, str) and value in texts_to_translate:
                            original_index = texts_to_translate.index(value)
                            current_data[key] = translated_texts[original_index]
                            texts_to_translate.pop(original_index)
                            translated_texts.pop(original_index)
                        elif isinstance(value, (dict, list)):
                            insert_translated_texts(value)

            # **UYARI: Basitleştirilmiş Yerleştirme**
            # Basit olması için 'insert_translated_texts' yerine, çevrilmiş dize listesini kullanarak
            # orijinal 'process_value' mantığını kullanıyorum, ancak çeviri fonksiyonu artık yerel bir
            # listeden çekim yapacak. (Daha temiz bir yaklaşım için 'structure_map' kullanılabilir, ancak bu daha karmaşıktır.)

            translated_data = self.rebuild_data_with_translation(data, iter(translated_texts))

            # 5. Kaydet
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=2)

            self.log(f"  Completed")
            return True

        except Exception as e:
            self.log(f"  ERROR: Could not complete {os.path.basename(input_filepath)}: {e}", is_error=True)
            return False

    def rebuild_data_with_translation(self, value, translated_iterator):
        """Çevrilmiş metinler iterator'ünden çekerek JSON yapısını yeniden oluşturur."""
        if isinstance(value, str):
            if self.is_translatable(None, value, None):
                try:
                    return next(translated_iterator)
                except StopIteration:
                    self.log("  WARNING: Mismatch in translated text count. Returning original value.", is_error=True)
                    return value
            return value
        elif isinstance(value, list):
            return [self.rebuild_data_with_translation(item, translated_iterator) for item in value]
        elif isinstance(value, dict):
            return {k: self.rebuild_data_with_translation(v, translated_iterator) for k, v in value.items()}
        return value

    def is_audio_object(self, obj):
        if not isinstance(obj, dict):
            return False
        return any(key in obj for key in self.AUDIO_KEYS)

    def is_translatable(self, key, value, parent_obj=None):
        if not isinstance(value, str) or len(value.strip()) < 2:
            return False

        # 1. RPG Maker Kontrol Kodlarını Koru (Sadece kodu değil, kodun çevrelediği metni de çevirmek gerekebilir)
        # Örn: \n, \C[1]
        if re.match(r'^\s*[\\][A-Z][\[\d\]]*\s*$', value.strip()):
            return False

        # 2. Anahtar Atlamaları
        if key and key.lower() in self.SKIP_KEYS_LOWER:
            return False
        if key == 'name' and parent_obj and self.is_audio_object(parent_obj):
            return False

        # 3. İçerik Atlamaları
        value = value.strip()

        # Dosya yolu / URL
        if re.search(r'\.(ogg|png|m4a|wav|jpg|jpeg|mp3|webp|gif|webm|json|js)$', value, re.IGNORECASE) or re.search(
                r'[/\\]|^https?://', value):
            return False

        # Hex renk kodu
        if re.match(r'^#[0-9A-Fa-f]{6}$', value):
            return False

        # Sadece kod/değişken adı gibi görünüyorsa (daha az kısıtlayıcı)
        if re.match(r'^[A-Z0-9_]{2,15}$', value):  # Sadece büyük harf, sayı ve alt çizgi
            return False

        # Sadece sayılar/semboller (çeviriye gerek yok)
        if re.match(r'^[\d\s\W]+$', value) and not re.search(r'[a-zA-ZğüşıöçĞÜŞİÖÇ]', value):
            return False

        return True


if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorGUI(root)
    # Kapatma olayında ayarları kaydet
    root.protocol("WM_DELETE_WINDOW", lambda: (app.save_settings(), root.destroy()))
    root.mainloop()