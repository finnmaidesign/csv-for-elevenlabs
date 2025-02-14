import tkinter as tk
from tkinter import filedialog, messagebox
import srt
import csv
from datetime import timedelta


class SRTtoCSVConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("SRT to CSV Converter")
        self.root.geometry("600x400")

        # File paths
        self.srt_file1_path = None
        self.srt_file2_path = None
        self.output_path = None

        # Create UI elements
        self.create_widgets()

    def create_widgets(self):
        # File 1 selection
        tk.Label(self.root, text="First SRT File:").grid(row=0, column=0, padx=5, pady=5)
        self.file1_label = tk.Label(self.root, text="No file selected", width=40)
        self.file1_label.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Browse", command=self.select_file1).grid(row=0, column=2, padx=5, pady=5)

        # File 2 selection
        tk.Label(self.root, text="Second SRT File:").grid(row=1, column=0, padx=5, pady=5)
        self.file2_label = tk.Label(self.root, text="No file selected", width=40)
        self.file2_label.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Browse", command=self.select_file2).grid(row=1, column=2, padx=5, pady=5)

        # File role selection
        tk.Label(self.root, text="Select which file is transcription:").grid(row=2, column=0, columnspan=3, pady=10)
        self.file_role = tk.StringVar(value="file1")
        tk.Radiobutton(self.root, text="First file is transcription", variable=self.file_role,
                       value="file1").grid(row=3, column=0, columnspan=3)
        tk.Radiobutton(self.root, text="Second file is transcription", variable=self.file_role,
                       value="file2").grid(row=4, column=0, columnspan=3)

        # Convert button
        tk.Button(self.root, text="Convert to CSV", command=self.convert_to_csv).grid(row=5, column=0, columnspan=3,
                                                                                      pady=20)

        # Status message
        self.status_label = tk.Label(self.root, text="")
        self.status_label.grid(row=6, column=0, columnspan=3)

    def select_file1(self):
        self.srt_file1_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
        if self.srt_file1_path:
            self.file1_label.config(text=self.srt_file1_path.split("/")[-1])

    def select_file2(self):
        self.srt_file2_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
        if self.srt_file2_path:
            self.file2_label.config(text=self.srt_file2_path.split("/")[-1])

    def format_timedelta(self, td):
        """Format timedelta to 0:00:00,000"""
        total_seconds = td.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        return f"{hours}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')

    def parse_srt_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return list(srt.parse(f))
        except Exception as e:
            messagebox.showerror("Error", f"Error reading SRT file: {str(e)}")
            return None

    def convert_to_csv(self):
        if not self.srt_file1_path or not self.srt_file2_path:
            messagebox.showerror("Error", "Please select both SRT files")
            return

        # Parse SRT files
        subs1 = self.parse_srt_file(self.srt_file1_path)
        subs2 = self.parse_srt_file(self.srt_file2_path)

        if not subs1 or not subs2:
            return

        # Determine which file is translation (we'll use its length as reference)
        if self.file_role.get() == "file1":
            translation_subs = subs2
            transcription_subs = subs1
        else:
            translation_subs = subs1
            transcription_subs = subs2

        # Use translation file length as reference
        reference_length = len(translation_subs)

        # Trim transcription to match translation length if needed
        if len(transcription_subs) > reference_length:
            transcription_subs = transcription_subs[:reference_length]

        # Get output file path
        self.output_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not self.output_path:
            return

        try:
            with open(self.output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                # Write header exactly as Elevenlabs expects
                writer.writerow(['speaker', 'start_time', 'end_time', 'transcription', 'translation'])

                # Write data
                for i in range(reference_length):
                    # Get subtitles if available
                    if self.file_role.get() == "file1":
                        trans_sub = translation_subs[i]
                        script_sub = transcription_subs[i] if i < len(transcription_subs) else None
                    else:
                        trans_sub = translation_subs[i]
                        script_sub = transcription_subs[i] if i < len(transcription_subs) else None

                    # Always use translation timestamps
                    start_time = self.format_timedelta(trans_sub.start)
                    end_time = self.format_timedelta(trans_sub.end)

                    # Get content
                    translation = trans_sub.content
                    transcription = script_sub.content if script_sub else ""

                    # Clean and prepare the content
                    transcription_clean = script_sub.content.replace('\n', ' ').strip() if script_sub else ""
                    translation_clean = trans_sub.content.replace('\n', ' ').strip()

                    # Write row with exact format Elevenlabs expects
                    writer.writerow([
                        'Adam',  # Use Adam as speaker name
                        start_time,
                        end_time,
                        transcription_clean,
                        translation_clean
                    ])

            self.status_label.config(text=f"Successfully converted to: {self.output_path}")
            messagebox.showinfo("Success", "Conversion completed successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Error writing CSV file: {str(e)}")


def main():
    root = tk.Tk()
    app = SRTtoCSVConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()