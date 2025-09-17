import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import speech_recognition as sr
import pyttsx3
import time
import datetime
import webbrowser
import os
from PIL import Image, ImageTk
import requests
import json
import random

class JarvisAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS AI Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0a0a')
        
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        voices = self.tts_engine.getProperty('voices')
        self.tts_engine.setProperty('voice', voices[1].id)  # 0 for male, 1 for female
        self.tts_engine.setProperty('rate', 180)  # Speed of speech
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Queue for thread-safe operations
        self.queue = queue.Queue()
        
        # State variables
        self.is_listening = False
        self.is_speaking = False
        
        self.setup_gui()
        self.check_queue()
        
        # Adjust for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="JARVIS AI Assistant", 
                               font=("Helvetica", 16, "bold"), foreground="#00ff00")
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Status indicator
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                foreground="#00ff00", font=("Helvetica", 10))
        status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Conversation display
        self.conversation = scrolledtext.ScrolledText(main_frame, width=70, height=20,
                                                     bg='#1a1a1a', fg='#00ff00',
                                                     font=("Courier", 10))
        self.conversation.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.conversation.insert(tk.END, "JARVIS: Hello, I'm ready. How can I help you?\n")
        self.conversation.config(state=tk.DISABLED)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.listen_btn = ttk.Button(button_frame, text="Start Listening", command=self.toggle_listening)
        self.listen_btn.grid(row=0, column=0, padx=5)
        
        ttk.Button(button_frame, text="Clear Conversation", command=self.clear_conversation).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.destroy).grid(row=0, column=2, padx=5)
        
    def toggle_listening(self):
        if not self.is_listening:
            self.is_listening = True
            self.listen_btn.config(text="Stop Listening")
            self.status_var.set("Listening...")
            threading.Thread(target=self.listen_loop, daemon=True).start()
        else:
            self.is_listening = False
            self.listen_btn.config(text="Start Listening")
            self.status_var.set("Ready")
    
    def listen_loop(self):
        while self.is_listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio).lower()
                self.queue.put(("user_input", text))
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                self.queue.put(("message", "JARVIS: I didn't catch that. Could you repeat?"))
            except Exception as e:
                self.queue.put(("error", f"Recognition error: {str(e)}"))
    
    def process_command(self, command):
        self.add_to_conversation(f"You: {command}")
        
        response = ""
        if any(word in command for word in ["hello", "hi", "hey", "greetings"]):
            response = "Hello! How can I assist you today?"
        elif "time" in command:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            response = f"The current time is {current_time}"
        elif "date" in command:
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            response = f"Today is {current_date}"
        elif "search" in command or "google" in command:
            query = command.replace("search", "").replace("google", "").strip()
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query}")
                response = f"Searching Google for {query}"
        elif "youtube" in command:
            query = command.replace("youtube", "").replace("search", "").strip()
            if query:
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
                response = f"Searching YouTube for {query}"
        elif "weather" in command:
            response = self.get_weather()
        elif "joke" in command:
            response = self.tell_joke()
        elif any(word in command for word in ["exit", "quit", "goodbye", "bye"]):
            response = "Goodbye! Have a great day!"
            self.queue.put(("exit", ""))
        else:
            response = "I'm not sure how to help with that. Try asking about time, weather, or search something."
        
        if response:
            self.queue.put(("response", response))
    
    def get_weather(self):
        # This is a placeholder - you'd need to integrate with a real weather API
        return "Weather information is not configured. Please set up a weather API."
    
    def tell_joke(self):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "What do you call a fake noodle? An impasta!",
            "How does a penguin build its house? Igloos it together!"
        ]
        return random.choice(jokes)
    
    def speak(self, text):
        self.is_speaking = True
        self.status_var.set("Speaking...")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
        self.is_speaking = False
        self.status_var.set("Ready")
    
    def add_to_conversation(self, text):
        self.conversation.config(state=tk.NORMAL)
        self.conversation.insert(tk.END, f"{text}\n")
        self.conversation.see(tk.END)
        self.conversation.config(state=tk.DISABLED)
    
    def clear_conversation(self):
        self.conversation.config(state=tk.NORMAL)
        self.conversation.delete(1.0, tk.END)
        self.conversation.insert(tk.END, "JARVIS: Conversation cleared. How can I help you?\n")
        self.conversation.config(state=tk.DISABLED)
    
    def check_queue(self):
        try:
            while True:
                item_type, content = self.queue.get_nowait()
                if item_type == "user_input":
                    self.process_command(content)
                elif item_type == "response":
                    self.add_to_conversation(f"JARVIS: {content}")
                    threading.Thread(target=self.speak, args=(content,), daemon=True).start()
                elif item_type == "message":
                    self.add_to_conversation(content)
                elif item_type == "error":
                    self.add_to_conversation(f"Error: {content}")
                elif item_type == "exit":
                    self.is_listening = False
                    self.listen_btn.config(text="Start Listening")
                    self.status_var.set("Ready")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisAssistant(root)
    root.mainloop()