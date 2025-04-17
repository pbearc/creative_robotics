import serial
import serial.tools.list_ports
import time
import pygame
import sys
import glob
import os
import threading
import queue

# Initialize pygame mixer for audio with MP3 support
pygame.mixer.init()
pygame.mixer.pre_init(44100, -16, 2, 2048)

speed = 9600  # baud rate for Arduino com
rest = 3  # delay between movements

# Global variables for thread communication
stop_threads = False
touch_events_queue = queue.Queue()
command_queue = queue.Queue()

def find_serial_ports():
    """Lists serial port names"""
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def load_sounds():
    sounds = []
    sound_files = [
        "chime.mp3", "card-mixing.mp3", "clean-trap-loop.mp3",
        "bass.mp3", "guitar-loop.mp3", "space-animal.mp3"
    ]
    
    for i, file in enumerate(sound_files):
        try:
            if os.path.exists(file):
                sounds.append(pygame.mixer.Sound(file))
                print(f"Loaded sound {i}: {file}")
            else:
                beep_array = pygame.sndarray.array([4096 * pygame.math.Vector2(1, 0).rotate(x * 0.04 * (i + 1)).x for x in range(4096)])
                default_sound = pygame.sndarray.make_sound(beep_array)
                default_sound.set_volume(0.5)
                sounds.append(default_sound)
                print(f"Could not find {file}, using default tone for A{i}")
        except Exception as e:
            print(f"Error loading sound for A{i}: {e}")
            try:
                buffer = bytearray([128 + 127 * (i % 2) for j in range(4096)])
                default_sound = pygame.mixer.Sound(buffer=buffer)
                sounds.append(default_sound)
            except:
                sounds.append(pygame.mixer.Sound(buffer=bytearray([128 for j in range(1024)])))
    
    return sounds

def select_com_port():
    com_ports = find_serial_ports()
    if not com_ports:
        print("No COM ports found!")
        sys.exit(1)
        
    print("\nAvailable COM ports:")
    for i, port in enumerate(com_ports, 1):
        print(f"{i}. {port}")
    
    while True:
        try:
            choice = int(input("\nSelect COM port (1-{}): ".format(len(com_ports))))
            if 1 <= choice <= len(com_ports):
                return com_ports[choice-1]
            print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a number.")

def send_to_serial(ser, data):
    try:
        ser.write(data.encode('utf-8'))
        print(f"Sent: {data.strip()}")
        return True
    except serial.SerialException as e:
        print(f"Error: {str(e)}")
        return False

def process_file(filename):
    try:
        with open(filename, 'r') as file:
            lines = [line.strip() for line in file if line.strip()]
        
        print(f"\nQueuing {len(lines)} commands from {filename}")
        
        for line in lines:
            command_queue.put(line)
                
        return True
    except FileNotFoundError:
        print(f"\nError: File {filename} not found!")
        return False

def touch_listener_thread(ser, sounds):
    """Thread function to continuously listen for touch events"""
    global stop_threads
    
    print("Touch listener thread started")
    
    while not stop_threads:
        if ser.in_waiting:
            try:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line.startswith("PLAY_SOUND:"):
                    try:
                        pin_number = int(line.split(":")[1])
                        touch_events_queue.put(pin_number)
                        print(f"Received touch event: {line}")
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing touch message: {e}")
                elif line:
                    print(f"Received: {line}")
            except Exception as e:
                print(f"Error reading from serial: {e}")
        time.sleep(0.01)
    
    print("Touch listener thread stopped")

def sound_player_thread(sounds):
    """Thread function to play sounds from the queue"""
    global stop_threads
    
    print("Sound player thread started")
    
    while not stop_threads:
        try:
            pin_number = touch_events_queue.get(block=False)
            if 0 <= pin_number < len(sounds):
                print(f"Playing sound for pin A{pin_number}")
                sounds[pin_number].play()
            touch_events_queue.task_done()
        except queue.Empty:
            time.sleep(0.01)
    
    print("Sound player thread stopped")

def command_processor_thread(ser):
    """Thread function to process commands from the queue"""
    global stop_threads
    
    print("Command processor thread started")
    
    while not stop_threads:
        try:
            cmd = command_queue.get(block=False)
            if cmd:
                print(f"Processing command: {cmd}")
                send_to_serial(ser, cmd + '\n')
                
                # Wait for the command to be processed
                time.sleep(rest)
                
                # Check for any response from Arduino
                while ser.in_waiting and not stop_threads:
                    try:
                        response = ser.readline().decode('utf-8', errors='replace').strip()
                        if response:
                            print(f"Arduino response: {response}")
                    except Exception as e:
                        print(f"Error reading response: {e}")
                        break
            
            command_queue.task_done()
        except queue.Empty:
            time.sleep(0.1)
    
    print("Command processor thread stopped")

def user_interface_thread():
    """Thread function to handle user interface"""
    global stop_threads
    
    print("\nUI thread started. Automatically loading moves.txt")
    # Auto-start with file processing
    filename = 'moves.txt'
    if os.path.exists(filename):
        process_file(filename)
        print(f"Loaded {filename} - robot will now execute all commands")
    else:
        print(f"Warning: {filename} not found. Please create this file with robot movement commands.")
    
    while not stop_threads:
        mode = input("\nChoose mode:\n1. Direct send\n2. List from file\n3. Exit\n> ")
        
        if mode == '1':
            print("\nDirect mode - type commands (type 'exit' to return to menu)")
            while not stop_threads:
                cmd = input("Enter command: ").strip()
                if cmd.lower() == 'exit':
                    break
                if cmd:
                    command_queue.put(cmd)
        elif mode == '2':
            filename = 'moves.txt'
            if os.path.exists(filename):
                process_file(filename)
            else:
                print(f"Error: {filename} not found!")
        elif mode == '3':
            stop_threads = True
            break
        else:
            print("Invalid choice. Enter 1, 2, or 3")

def main():
    selected_port = select_com_port()
    print(f"\nSelected port: {selected_port}")
    
    try:
        ser = serial.Serial(selected_port, speed, timeout=1)
        time.sleep(2)  # Arduino reset delay
    except serial.SerialException as e:
        print(f"Error connecting to {selected_port}: {e}")
        sys.exit(1)

    print("Loading sounds...")
    sounds = load_sounds()

    print("Waiting for Arduino to be ready...")
    ready = False
    timeout_count = 0
    while not ready and timeout_count < 10:
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
        print("Timed out waiting for Arduino. Proceeding anyway...")
    
    # Start all worker threads
    global stop_threads
    
    touch_thread = threading.Thread(target=touch_listener_thread, args=(ser, sounds))
    sound_thread = threading.Thread(target=sound_player_thread, args=(sounds,))
    command_thread = threading.Thread(target=command_processor_thread, args=(ser,))
    ui_thread = threading.Thread(target=user_interface_thread)
    
    touch_thread.daemon = True
    sound_thread.daemon = True
    command_thread.daemon = True
    ui_thread.daemon = True
    
    touch_thread.start()
    sound_thread.start()
    command_thread.start()
    ui_thread.start()
    
    try:
        # Main thread just waits for other threads to finish
        while not stop_threads:
            time.sleep(0.1)
            
            # Check if UI thread has died
            if not ui_thread.is_alive():
                break
            
            # Check if command queue is empty
            if command_queue.empty() and not stop_threads:
                time.sleep(0.5)  # Avoid excessive CPU usage
    
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        # Stop threads and clean up
        stop_threads = True
        
        # Wait for threads to finish
        touch_thread.join(timeout=1.0)
        sound_thread.join(timeout=1.0)
        command_thread.join(timeout=1.0)
        ui_thread.join(timeout=1.0)
        
        print("\nClosing connection")
        ser.close()

if __name__ == "__main__":
    main()
