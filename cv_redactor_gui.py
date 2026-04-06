#!/usr/bin/env python3
"""
CV Redactor - GUI Application
Simple drag-and-drop interface for CV anonymization
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path
from datetime import datetime
import sys

# Import the pipeline
from universal_pipeline_engine import PipelineOrchestrator


class CVRedactorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CV Redactor - PII Anonymization Tool")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.processing = False
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Header
        header_frame = tk.Frame(self.root, bg="#5865F2", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🔒 CV Redaction Pipeline",
            font=("Arial", 20, "bold"),
            bg="#5865F2",
            fg="white"
        )
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Upload your CV and get a privacy-protected version with all PII removed",
            font=("Arial", 10),
            bg="#5865F2",
            fg="white"
        )
        subtitle_label.pack()
        
        # Main content
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input file selection
        input_frame = tk.LabelFrame(main_frame, text="Select CV to Redact (PDF or DOCX)", padx=10, pady=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        input_entry_frame = tk.Frame(input_frame)
        input_entry_frame.pack(fill=tk.X)
        
        tk.Entry(
            input_entry_frame,
            textvariable=self.input_file,
            font=("Arial", 10),
            state="readonly"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Button(
            input_entry_frame,
            text="Browse CV...",
            command=self.browse_input,
            bg="#5865F2",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20
        ).pack(side=tk.RIGHT)
        
        # Output file selection
        output_frame = tk.LabelFrame(main_frame, text="Save Anonymized CV As", padx=10, pady=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        output_entry_frame = tk.Frame(output_frame)
        output_entry_frame.pack(fill=tk.X)
        
        tk.Entry(
            output_entry_frame,
            textvariable=self.output_file,
            font=("Arial", 10),
            state="readonly"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Button(
            output_entry_frame,
            text="Save As...",
            command=self.browse_output,
            bg="#5865F2",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20
        ).pack(side=tk.RIGHT)
        
        # Process button
        self.process_btn = tk.Button(
            main_frame,
            text="🚀 Redact This CV",
            command=self.process_cv,
            bg="#57F287",
            fg="white",
            font=("Arial", 14, "bold"),
            cursor="hand2",
            height=2
        )
        self.process_btn.pack(fill=tk.X, pady=(10, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=300
        )
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Select a CV file to redact",
            font=("Arial", 10),
            fg="#5865F2"
        )
        self.status_label.pack(pady=(0, 10))
        
        # Log output
        log_frame = tk.LabelFrame(main_frame, text="Processing Log", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            font=("Consolas", 9),
            bg="#f0f0f0",
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg="#f0f0f0", height=40)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(
            footer_frame,
            text="CV Redactor v1.0 | Removes: Names, Emails, Phones, Addresses | Keeps: Skills, Experience",
            font=("Arial", 8),
            bg="#f0f0f0",
            fg="#666"
        )
        footer_label.pack(pady=10)
    
    def browse_input(self):
        """Browse for input CV file"""
        file = filedialog.askopenfilename(
            title="Select CV to Redact",
            filetypes=[
                ("CV Files", "*.pdf *.docx *.doc"),
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx *.doc"),
                ("All Files", "*.*")
            ]
        )
        if file:
            self.input_file.set(file)
            self.log(f"Selected CV: {Path(file).name}")
            
            # Auto-suggest output filename
            input_path = Path(file)
            suggested_output = input_path.parent / f"{input_path.stem}_REDACTED.txt"
            self.output_file.set(str(suggested_output))
            self.log(f"Output will be saved as: {suggested_output.name}")
    
    def browse_output(self):
        """Browse for output file location"""
        # Get initial directory from input file if available
        initial_dir = None
        if self.input_file.get():
            initial_dir = str(Path(self.input_file.get()).parent)
        
        # Suggest filename based on input
        initial_file = None
        if self.input_file.get():
            input_path = Path(self.input_file.get())
            initial_file = f"{input_path.stem}_REDACTED.txt"
        
        file = filedialog.asksaveasfilename(
            title="Save Anonymized CV As",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        if file:
            self.output_file.set(file)
            self.log(f"Output location: {Path(file).name}")
    
    def log(self, message):
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def update_status(self, message, color="#5865F2"):
        """Update status label"""
        self.status_label.config(text=message, fg=color)
        self.root.update()
    
    def process_cv(self):
        """Process single CV in a separate thread"""
        if self.processing:
            messagebox.showwarning("Processing", "Already processing a CV. Please wait...")
            return
        
        # Validate inputs
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        
        if not input_path:
            messagebox.showerror("Error", "Please select a CV file to redact")
            return
        
        if not output_path:
            messagebox.showerror("Error", "Please specify where to save the output")
            return
        
        if not os.path.exists(input_path):
            messagebox.showerror("Error", f"Input file does not exist:\n{input_path}")
            return
        
        # Confirm processing
        result = messagebox.askyesno(
            "Confirm Redaction",
            f"Redact this CV?\n\n"
            f"Input:  {Path(input_path).name}\n"
            f"Output: {Path(output_path).name}\n\n"
            f"All personal information will be removed."
        )
        
        if not result:
            return
        
        # Start processing in thread
        thread = threading.Thread(target=self._process_thread, args=(input_path, output_path))
        thread.daemon = True
        thread.start()
    
    def _process_thread(self, input_path, output_path):
        """Process CV in background thread"""
        self.processing = True
        self.process_btn.config(state=tk.DISABLED, bg="#cccccc")
        self.progress.start()
        
        try:
            self.log("=" * 60)
            self.log("Starting CV redaction...")
            self.log(f"Input:  {Path(input_path).name}")
            self.log(f"Output: {Path(output_path).name}")
            self.log("=" * 60)
            self.update_status("Redacting CV...", "#FFA500")
            
            # Create output folder if needed
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize orchestrator
            self.log("Initializing redaction engine...")
            orchestrator = PipelineOrchestrator(debug=False, config_dir='config')
            
            self.log(f"Processing: {Path(input_path).name}")
            self.update_status(f"Processing: {Path(input_path).name}", "#FFA500")
            
            # Process CV
            redacted_text, profile = orchestrator.process_cv(str(input_path))
            
            # Check if extraction was successful
            if redacted_text.startswith("[ERROR"):
                self.log(f"✗ Error: {redacted_text}")
                self.update_status("✗ Processing failed", "#ED4245")
                messagebox.showerror(
                    "Error",
                    f"Failed to process CV:\n\n{redacted_text}"
                )
                return
            
            # Save output
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(redacted_text)
            
            self.log(f"✓ Saved: {Path(output_path).name}")
            self.log(f"  Type: {profile.cv_type.value}")
            self.log(f"  Size: {len(redacted_text)} characters")
            self.log("")
            
            # Summary
            self.log("=" * 60)
            self.log("Redaction Complete!")
            self.log(f"Output saved to: {output_path}")
            self.log("=" * 60)
            
            self.update_status("✓ Redaction complete!", "#57F287")
            
            # Ask if user wants to open the file
            result = messagebox.askyesno(
                "Success",
                f"CV successfully redacted!\n\n"
                f"Output: {Path(output_path).name}\n\n"
                f"Would you like to open the redacted CV?"
            )
            
            if result:
                # Open file with default text editor
                os.startfile(output_path)
        
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.update_status("✗ Error occurred", "#ED4245")
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
        
        finally:
            self.processing = False
            self.process_btn.config(state=tk.NORMAL, bg="#57F287")
            self.progress.stop()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = CVRedactorGUI(root)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()
