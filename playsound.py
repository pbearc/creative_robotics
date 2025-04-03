import serial
import time
import pygame
import sys
import glob
import os

# Initialize pygame mixer for audio with MP3 support
pygame.mixer.init()
# Set the preferred audio format for better MP3 support
pygame.mixer.pre_init(44100, -16, 2, 2048)

# Function to find available serial ports
def find_serial_ports():
    """Lists serial port names"""
    result = []
    
    # Check common COM ports on Windows up to COM15
    if sys.platform.startswith('win'):
        for i in range(1, 16):  # Check COM1 through COM15
            port = f'COM{i}'
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
    # Check Linux/Mac ports
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        for port in glob.glob('/dev/tty[A-Za-z]*'):
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
    elif sys.platform.startswith('darwin'):
        for port in glob.glob('/dev/tty.*'):
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
    else:
        print("Warning: Unsupported platform for automatic port detection")
    
    return result

# Load sound files
def load_sounds():
    sounds = []
    # Replace these paths with your actual sound files
    sound_files = [
        "chime.mp3", # A0
        "card-mixing.mp3", # A1
        "clean-trap-loop.mp3", # A2
        "bass.mp3",  # A3
        "guitar-loop.mp3",  # A4
        "space-animal.mp3"   # A5
    ]
    
    # Create a simple default beep sound using pygame
    pygame.mixer.init(44100, -16, 1, 512)
    
    # Try to load each sound, use a default tone if file not found
    for i, file in enumerate(sound_files):
        try:
            if os.path.exists(file):
                sounds.append(pygame.mixer.Sound(file))
                print(f"Loaded sound {i}: {file}")
            else:
                # Create different pitched beeps as fallback sounds
                beep_array = pygame.sndarray.array([4096 * pygame.math.Vector2(1, 0).rotate(x * 0.04 * (i + 1)).x for x in range(4096)])
                default_sound = pygame.sndarray.make_sound(beep_array)
                default_sound.set_volume(0.5)
                sounds.append(default_sound)
                print(f"Could not find {file}, using default tone for A{i}")
        except Exception as e:
            print(f"Error loading sound for A{i}: {e}")
            # Simpler fallback if the above fails
            try:
                buffer = bytearray([128 + 127 * (i % 2) for j in range(4096)])
                default_sound = pygame.mixer.Sound(buffer=buffer)
                sounds.append(default_sound)
                print(f"Using simple fallback tone for A{i}")
            except:
                print(f"Warning: Could not create any sound for A{i}")
                # Create an empty sound to avoid errors
                sounds.append(pygame.mixer.Sound(buffer=bytearray([128 for j in range(1024)])))
    
    return sounds

# Main function
def main():
    # List available ports
    available_ports = find_serial_ports()
    print("Available ports:")
    for i, port in enumerate(available_ports):
        print(f"{i}: {port}")
    
    # Let user select port or enter custom port
    print("Enter the number for a listed port, or type 'custom' to enter a port name manually:")
    selection = input("> ")
    
    if selection.lower() == 'custom':
        port = input("Enter the exact port name (e.g., COM10): ")
    else:
        try:
            port_index = int(selection)
            port = available_ports[port_index]
        except (ValueError, IndexError):
            print("Invalid selection, please enter a valid number or 'custom'")
            print("Defaulting to manual port entry...")
            port = input("Enter the exact port name (e.g., COM10): ")
    
    # Connect to Arduino
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"Connected to {port}")
    except serial.SerialException as e:
        print(f"Error connecting to {port}: {e}")
        print("Please check if the port is correct and not in use by another program.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Wait for Arduino to be ready
    print("Waiting for Arduino to be ready...")
    ready = False
    timeout_count = 0
    while not ready and timeout_count < 10:  # 10 second timeout
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            print(f"Received: {line}")
            if line == "TOUCH_SYSTEM_READY":
                ready = True
                print("Touch system ready!")
        else:
            time.sleep(1)
            timeout_count += 1
            print(f"Waiting... ({timeout_count}/10)")
    
    if not ready:
        print("Timed out waiting for Arduino. Make sure your Arduino is programmed correctly.")
        print("Proceeding anyway...")
    
    # Load sounds
    print("Loading sounds...")
    sounds = load_sounds()
    
    # Main loop
    print("System ready! Touch sensors to play sounds.")
    try:
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                print(f"Received: {line}")
                if line.startswith("PLAY_SOUND:"):
                    try:
                        pin_number = int(line.split(":")[1])
                        if 0 <= pin_number < len(sounds):
                            print(f"Playing sound for pin A{pin_number}")
                            sounds[pin_number].play()
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing message: {e}")
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nClosing connection")
        ser.close()

if __name__ == "__main__":
    main()