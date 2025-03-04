import os.path
import os
import subprocess
import tkinter as tk
import util
import cv2
from PIL import Image, ImageTk
import datetime
import time

class App:
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.geometry("1200x520+320+90")
        self.main_window.title("Face Recognition")
        
        # Flag to track if webcam processing is active
        self.webcam_active = False
        
        # Define a placeholder image for when webcam is not available
        self.placeholder_img = None
        
        self.login_button_main = util.get_button(self.main_window, "Login", "green", self.login)
        self.login_button_main.place(x=850, y=300)
        
        self.register_button_main = util.get_button(self.main_window, "Register", "gray", self.register, fg='black')
        self.register_button_main.place(x=850, y=400)
        
        self.webcam_label = util.get_img_label(self.main_window)
        self.webcam_label.place(x=10, y=0, width=700, height=500)
        
        # Initialize database directory
        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)
        
        # Initialize webcam with a separate method to allow for retries
        self.init_webcam()

        self.log_path = './log.txt'
        
    def init_webcam(self):
        """Initialize the webcam and start processing if successful"""
        try:
            # Explicitly release any existing capture
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
                time.sleep(0.5)  # Give it time to fully release
            
            # Try to open the webcam
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow on Windows
            
            # Check if opened successfully
            if self.cap.isOpened():
                # Read a test frame to confirm it's working
                ret, test_frame = self.cap.read()
                if ret:
                    print("Webcam initialized successfully")
                    self.webcam_active = True
                    # Start the webcam processing
                    self.process_webcam()
                else:
                    print("Webcam opened but failed to read frame")
                    self.show_webcam_error()
            else:
                print("Failed to open webcam")
                self.show_webcam_error()
                
        except Exception as e:
            print(f"Error initializing webcam: {e}")
            self.show_webcam_error()
    
    def show_webcam_error(self):
        """Display an error message on the webcam label"""
        self.webcam_active = False
        
        # Create a blank image with error text
        error_img = Image.new('RGB', (700, 500), color=(40, 40, 40))
        imgtk = ImageTk.PhotoImage(image=error_img)
        self.webcam_label.imgtk = imgtk
        self.webcam_label.configure(image=imgtk)
        
        # Schedule a retry
        self.webcam_label.after(3000, self.init_webcam)
    
    def process_webcam(self):
        """Process webcam frames and update the UI"""
        if not self.webcam_active:
            return
            
        try:
            # Try to read a frame
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                # Process the frame
                self.most_recent_frame = frame.copy()
                
                # Convert colors for display
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.most_recent_frame_pil = Image.fromarray(rgb_frame)
                imgtk = ImageTk.PhotoImage(image=self.most_recent_frame_pil)
                
                # Update the label
                self.webcam_label.imgtk = imgtk
                self.webcam_label.configure(image=imgtk)
            else:
                print("Failed to read frame from webcam")
                self.webcam_active = False
                # Try to reinitialize the webcam
                self.init_webcam()
                return
                
        except Exception as e:
            print(f"Error processing webcam frame: {e}")
            self.webcam_active = False
            self.init_webcam()
            return
            
        # Schedule the next frame processing
        self.webcam_label.after(20, self.process_webcam)

    def login(self):
        """Handle login button click"""
        if not hasattr(self, 'most_recent_frame') or not self.webcam_active:
            util.msg_box("Error", "Webcam is not active. Cannot login.")
            return
            
        try:
            u_path = './.tmp.jpg'
            cv2.imwrite(u_path, self.most_recent_frame)
            
            output = subprocess.check_output(['face_recognition', self.db_dir, u_path], stderr=subprocess.STDOUT)
            output = output.decode('utf-8').strip()
            name = output.split(',')[1]
            
            if name in ['unknown_person', 'no_persons_found']:
                util.msg_box("Error", "Unknown user, register user or try again")

            else:
                util.msg_box("Success", 'welcome, {}'.format(name))
                with open(self.log_path, 'a') as f:
                    f.write('{},{}\n'.format(name, datetime.datetime.now()))
                    f.close()
            
        except subprocess.CalledProcessError as e:
            print(f"Face recognition failed:\n{e.output.decode('utf-8')}")
            util.msg_box("Error", "Face recognition failed.")
        except Exception as e:
            print(f"Error during login: {e}")
            util.msg_box("Error", f"An error occurred: {str(e)}")

    def register(self):
        """Handle register button click"""
        if not hasattr(self, 'most_recent_frame') or not self.webcam_active:
            util.msg_box("Error", "Webcam is not active. Cannot register.")
            return
            
        # Create register window
        self.register_new = tk.Toplevel(self.main_window)
        self.register_new.geometry("1200x520+350+100")
        self.register_new.title("Register New User")
        
        # Setup register window elements
        self.accept_button = util.get_button(self.register_new, "Accept", "green", self.accept_register)
        self.accept_button.place(x=800, y=300)
        
        self.cancel_button = util.get_button(self.register_new, "Cancel", "red", self.cancel_register, fg='black')
        self.cancel_button.place(x=800, y=400)
        
        self.capture_label = util.get_img_label(self.register_new)
        self.capture_label.place(x=10, y=0, width=700, height=500)
        
        # Copy current frame to register window
        self.add_img_to_register()
        
        self.entry_text = util.get_entry_text(self.register_new)
        self.entry_text.place(x=800, y=100)
        
        self.text_label = util.get_text_label(self.register_new, "Enter your name")
        self.text_label.place(x=800, y=50)

    def add_img_to_register(self):
        """Add current webcam image to register window"""
        try:
            # Create a copy of the current frame for registration
            self.register_new_user = self.most_recent_frame.copy()
            
            # Display the image in the register window
            imgtk = ImageTk.PhotoImage(image=self.most_recent_frame_pil)
            self.capture_label.imgtk = imgtk
            self.capture_label.configure(image=imgtk)
            
        except Exception as e:
            print(f"Error adding image to register window: {e}")
            util.msg_box("Error", "Failed to capture image for registration.")
            self.register_new.destroy()

    def accept_register(self):
        """Accept the registration"""
        try:
            name = self.entry_text.get(1.0, "end-1c").strip()
            
            if not name:
                util.msg_box("Error", "Please enter a name")
                return
                
            # Save the user image
            user_img_path = os.path.join(self.db_dir, f'{name}.jpg')
            cv2.imwrite(user_img_path, self.register_new_user)
            
            util.msg_box("Success", f"User '{name}' registered successfully")
            self.register_new.destroy()
            
        except Exception as e:
            print(f"Error during registration: {e}")
            util.msg_box("Error", f"Registration failed: {str(e)}")

    def cancel_register(self):
        """Cancel registration and close the window"""
        self.register_new.destroy()

    def start(self):
        """Start the application"""
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.main_window.mainloop()
        
    def on_closing(self):
        """Handle window closing event"""
        try:
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
        except:
            pass
        self.main_window.destroy()

if __name__ == '__main__':
    app = App()
    app.start()