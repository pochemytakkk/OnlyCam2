import customtkinter as ctk
import cv2 # type: ignore
import socket
import struct
import numpy as np # type: ignore
import threading
import pyvirtualcam # type: ignore
from PIL import Image

HOST = '0.0.0.0'
PORT = 8080

class OnlyCamStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OnlyCam Studio")
        self.geometry("1100x750")
        self.configure(fg_color="#18181b")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_video_area()

        self.running = True
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()

    def setup_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=320, fg_color="#27272a", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(sidebar, text="Устройство", anchor="w", text_color="#a1a1aa").pack(fill="x", padx=15, pady=(20, 5))
        ctk.CTkOptionMenu(sidebar, values=["iPhone 17 Pro Max (USB)"], fg_color="#3f3f46", button_color="#52525b").pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(sidebar, text="Объектив", anchor="w", text_color="#a1a1aa").pack(fill="x", padx=15, pady=(20, 5))
        self.lens_menu = ctk.CTkOptionMenu(sidebar, values=["Сверхширокоугольная 0.5x", "Широкоугольная 1x", "Телефото"], fg_color="#3f3f46", button_color="#52525b")
        self.lens_menu.pack(fill="x", padx=15, pady=5)

    def setup_video_area(self):
        self.video_frame = ctk.CTkFrame(self, fg_color="#000000", corner_radius=8)
        self.video_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="Ожидание подключения по кабелю...", text_color="#52525b")
        self.video_label.pack(expand=True, fill="both")

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        
        try:
            with pyvirtualcam.Camera(width=1280, height=720, fps=30) as cam:
                while self.running:
                    conn, addr = server_socket.accept()
                    data = b""
                    payload_size = struct.calcsize(">L")

                    while self.running:
                        while len(data) < payload_size:
                            packet = conn.recv(8192)
                            if not packet: break
                            data += packet
                        if not data: break

                        packed_msg_size = data[:payload_size]
                        data = data[payload_size:]
                        msg_size = struct.unpack(">L", packed_msg_size)[0]

                        while len(data) < msg_size:
                            data += conn.recv(8192)

                        frame_data = data[:msg_size]
                        data = data[msg_size:]

                        frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            frame = cv2.resize(frame, (1280, 720))
                            
                            cam.send(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            cam.sleep_until_next_frame()

                            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_image = Image.fromarray(rgb_image)
                            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(800, 450))
                            
                            self.video_label.configure(image=ctk_image, text="")
        except Exception as e:
            print(f"Ошибка камеры: {e}")

if __name__ == "__main__":
    app = OnlyCamStudio()
    app.mainloop()