import webbrowser
import os

html_path = os.path.abspath("compare_videos.html")
webbrowser.open(f"file:///{html_path}")
print(f"Opened comparison at: file:///{html_path}")