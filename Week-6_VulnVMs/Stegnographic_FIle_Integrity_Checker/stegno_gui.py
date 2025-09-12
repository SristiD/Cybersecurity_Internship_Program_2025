import numpy as np
import cv2
import wave
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from ttkbootstrap import Style
from tkinter import ttk
import os

# ----------------- Utility -----------------
def msgtobinary(msg):
    if type(msg) == str:
        return ''.join([format(ord(i), "08b") for i in msg])
    elif type(msg) == bytes or type(msg) == np.ndarray:
        return [format(i, "08b") for i in msg]
    elif type(msg) == int or type(msg) == np.uint8:
        return format(msg, "08b")
    else:
        raise TypeError("Unsupported type for binary conversion")

def BinaryToDecimal(binary):
    return int(binary, 2)

# ----------------- Text Steg -----------------
def txt_encode(text, cover_file, stego_file):
    ZWC = {"00": u'\u200C', "01": u'\u202C', "11": u'\u202D', "10": u'\u200E'}
    add = ""
    for i in range(len(text)):
        t = ord(text[i])
        if 32 <= t <= 64:
            t1 = t + 48
            t2 = t1 ^ 170
            res = bin(t2)[2:].zfill(8)
            add += "0011" + res
        else:
            t1 = t - 48
            t2 = t1 ^ 170
            res = bin(t2)[2:].zfill(8)
            add += "0110" + res
    res1 = add + "111111111111"
    with open(cover_file, "r") as file1, open(stego_file, "w+", encoding="utf-8") as file3:
        words = []
        for line in file1:
            words += line.split()
        i = 0
        while i < len(res1):
            s = words[int(i / 12)]
            HM_SK = ""
            j = 0
            while j < 12:
                x = res1[j + i] + res1[i + j + 1]
                HM_SK += ZWC[x]
                j += 2
            file3.write(s + HM_SK + " ")
            i += 12
        t = int(len(res1) / 12)
        while t < len(words):
            file3.write(words[t] + " ")
            t += 1
    messagebox.showinfo("Success", "Stego text file generated successfully!")

def txt_decode(stego_file):
    ZWC_reverse = {u'\u200C': "00", u'\u202C': "01", u'\u202D': "11", u'\u200E': "10"}
    temp = ''
    with open(stego_file, "r", encoding="utf-8") as file4:
        for line in file4:
            for words in line.split():
                binary_extract = ""
                for letter in words:
                    if letter in ZWC_reverse:
                        binary_extract += ZWC_reverse[letter]
                if binary_extract == "111111111111":
                    break
                else:
                    temp += binary_extract
    i = 0; a = 0; b = 4; c = 4; d = 12; final = ''
    while i < len(temp):
        t3 = temp[a:b]; a += 12; b += 12; i += 12
        t4 = temp[c:d]; c += 12; d += 12
        if (t3 == '0110'):
            decimal_data = BinaryToDecimal(t4)
            final += chr((decimal_data ^ 170) + 48)
        elif (t3 == '0011'):
            decimal_data = BinaryToDecimal(t4)
            final += chr((decimal_data ^ 170) - 48)
    return final

# ----------------- Image Steg -----------------
def encode_img(img_path, data, save_path):
    img = cv2.imread(img_path)
    if len(data) == 0:
        messagebox.showerror("Error", "Empty data")
        return
    data += '*^*^*'
    binary_data = msgtobinary(data)
    length_data = len(binary_data)
    index_data = 0
    for i in img:
        for pixel in i:
            r, g, b = msgtobinary(pixel)
            if index_data < length_data:
                pixel[0] = int(r[:-1] + binary_data[index_data], 2); index_data += 1
            if index_data < length_data:
                pixel[1] = int(g[:-1] + binary_data[index_data], 2); index_data += 1
            if index_data < length_data:
                pixel[2] = int(b[:-1] + binary_data[index_data], 2); index_data += 1
            if index_data >= length_data:
                break
    cv2.imwrite(save_path, img)
    messagebox.showinfo("Success", f"Encoded data saved in {save_path}")

def decode_img(img_path):
    img = cv2.imread(img_path)
    data_binary = ""
    for i in img:
        for pixel in i:
            r, g, b = msgtobinary(pixel)
            data_binary += r[-1]; data_binary += g[-1]; data_binary += b[-1]
            total_bytes = [data_binary[i: i + 8] for i in range(0, len(data_binary), 8)]
            decoded_data = ""
            for byte in total_bytes:
                decoded_data += chr(int(byte, 2))
                if decoded_data[-5:] == "*^*^*":
                    return decoded_data[:-5]
    return ""

# ----------------- Audio Steg -----------------
def encode_audio(audio_path, secret, stego_path):
    song = wave.open(audio_path, mode='rb')
    nframes = song.getnframes()
    frames = song.readframes(nframes)
    frame_bytes = bytearray(list(frames))
    secret += "*^*^*"
    result = []
    for c in secret:
        bits = bin(ord(c))[2:].zfill(8)
        result.extend([int(b) for b in bits])
    j = 0
    for i in range(len(result)):
        res = bin(frame_bytes[j])[2:].zfill(8)
        if res[-4] == str(result[i]):
            frame_bytes[j] = (frame_bytes[j] & 253)
        else:
            frame_bytes[j] = (frame_bytes[j] & 253) | 2
            frame_bytes[j] = (frame_bytes[j] & 254) | result[i]
        j += 1
    frame_modified = bytes(frame_bytes)
    with wave.open(stego_path, 'wb') as fd:
        fd.setparams(song.getparams())
        fd.writeframes(frame_modified)
    song.close()
    messagebox.showinfo("Success", "Audio stego file created!")

def decode_audio(stego_path):
    song = wave.open(stego_path, mode='rb')
    nframes = song.getnframes()
    frames = song.readframes(nframes)
    frame_bytes = bytearray(list(frames))
    extracted = ""; p = 0
    for i in range(len(frame_bytes)):
        if p == 1: break
        res = bin(frame_bytes[i])[2:].zfill(8)
        if res[-2] == "0":
            extracted += res[-4]
        else:
            extracted += res[-1]
        all_bytes = [extracted[i:i + 8] for i in range(0, len(extracted), 8)]
        decoded_data = ""
        for byte in all_bytes:
            decoded_data += chr(int(byte, 2))
            if decoded_data[-5:] == "*^*^*":
                song.close()
                return decoded_data[:-5]
    song.close()
    return ""

# ----------------- GUI Class -----------------
class StegApp:
    def __init__(self, root):
        self.root = root
        root.title("🎨 Multimedia Steganography")
        root.geometry("800x600")
        style = Style(theme="cosmo")
        notebook = ttk.Notebook(root)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        img_tab = ttk.Frame(notebook, padding=20)
        notebook.add(img_tab, text="🖼️ Image Steg")
        ttk.Button(img_tab, text="🔒 Enter Secret Message in Image", style="success.TButton", command=self.encode_img).pack(pady=20)
        ttk.Button(img_tab, text="🔓 Decode Message", style="info.TButton", command=self.decode_img).pack(pady=20)

        txt_tab = ttk.Frame(notebook, padding=20)
        notebook.add(txt_tab, text="📜 Text Steg")
        ttk.Button(txt_tab, text="🔒 Enter Secret Message in Text", style="success.TButton", command=self.encode_txt).pack(pady=20)
        ttk.Button(txt_tab, text="🔓 Decode Message", style="info.TButton", command=self.decode_txt).pack(pady=20)

        aud_tab = ttk.Frame(notebook, padding=20)
        notebook.add(aud_tab, text="🎵 Audio Steg")
        ttk.Button(aud_tab, text="🔒 Enter Secret Message in Audio", style="success.TButton", command=self.encode_audio).pack(pady=20)
        ttk.Button(aud_tab, text="🔓 Decode Message", style="info.TButton", command=self.decode_audio).pack(pady=20)

    # ---------- IMAGE ----------
    def encode_img(self):
        file_path = filedialog.askopenfilename(title="Select Cover Image")
        if not file_path: return
        msg = simpledialog.askstring("Message", "Enter text to hide:")
        save_path = filedialog.asksaveasfilename(defaultextension=".png")
        if msg and save_path:
            encode_img(file_path, msg, save_path)

    def decode_img(self):
        file_path = filedialog.askopenfilename(title="Select Stego Image")
        if not file_path: return
        try:
            res = decode_img(file_path)
            if res:
                messagebox.showinfo("Hidden Message", res)
            else:
                messagebox.showwarning("Result", "No message found!")
        except Exception as e:
            messagebox.showerror("Decoding Error", str(e))

    # ---------- TEXT ----------
    def encode_txt(self):
        cover = filedialog.askopenfilename(title="Select Cover Text File")
        if not cover: return
        msg = simpledialog.askstring("Message", "Enter text to hide:")
        save_path = filedialog.asksaveasfilename(defaultextension=".txt")
        if msg and save_path:
            txt_encode(msg, cover, save_path)

    def decode_txt(self):
        file = filedialog.askopenfilename(title="Select Stego Text File")
        if not file: return
        try:
            res = txt_decode(file)
            if res:
                messagebox.showinfo("Hidden Text", res)
            else:
                messagebox.showwarning("Result", "No hidden text found!")
        except Exception as e:
            messagebox.showerror("Decoding Error", str(e))

    # ---------- AUDIO ----------
    def encode_audio(self):
        audio = filedialog.askopenfilename(title="Select WAV File")
        if not audio: return
        msg = simpledialog.askstring("Secret", "Enter message")
        save = filedialog.asksaveasfilename(defaultextension=".wav")
        if msg and save:
            encode_audio(audio, msg, save)

    def decode_audio(self):
        file = filedialog.askopenfilename(title="Select Stego WAV")
        if not file: return
        try:
            res = decode_audio(file)
            if res:
                messagebox.showinfo("Hidden Audio Msg", res)
            else:
                messagebox.showwarning("Result", "No message found!")
        except Exception as e:
            messagebox.showerror("Decoding Error", str(e))

# ----------------- Run -----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = StegApp(root)
    root.mainloop()