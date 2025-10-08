RPGlator: RPG Maker Game Translator
This application is designed to automatically translate the JSON data files of RPG Maker MV/MZ games using a web-scraping translation service. It simplifies the process of creating localized versions of your game.

Features
GUI-Based Translation: Easy-to-use desktop interface built with Tkinter.

RPG Maker Compatibility: Targets common data files (Data/*.json) while smartly skipping non-translatable assets (like filenames, audio metadata, and graphic paths).

Batch Processing: Uses the deep-translator library for efficient batch translation, reducing the number of individual API calls.

Settings Persistence: Saves your last game path and language preferences.

⚙️ Installation
To run this tool, you need to have Python 3.x installed on your system.

Clone the Repository:

```
Bash
```
```
git clone https://github.com/YourUsername/RPGlator.git
cd RPGlator
```
Install Dependencies:
The core translation functionality relies on the deep-translator library, which provides access to popular web-based translation engines.
```
Bash
```
```
pip install deep-translator tk
```

(Note: tk is the standard Python package for Tkinter, which is often included with Python. If the command above fails, try installing Tkinter via your system's package manager or ensure your Python installation includes it.)

🚀 Usage
Run the application:
```
Bash
```
```
python your_main_file_name.py
```
(Replace your_main_file_name.py with the actual name of your script, likely rpglator_gui.py or similar.)

Click the "..." button to select your game's executable (Game.exe). The tool will automatically locate the www/data folder.

Select the Original Language and the Target Language.

Click "Translate" to start the batch translation process.
