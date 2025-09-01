import subprocess
import os
import sys
from dotenv import load_dotenv
import requests
import time
import getpass
import glob
from send2trash import send2trash
import re

# Global variables to store compression statistics
total_videos = 0
total_compression_time = 0
total_original_size = 0
total_compressed_size = 0

def get_compression_mode():
    """
    This function asks the user to select the compression mode.
    """
    print("Select the compression mode:")
    while True:
        mode = input(
            "How do you want to process the videos?\n"
            " [1] CPU only (High Quality, Slower)\n"
            " [2] Hardware Acceleration (GPU) (Good Quality, Faster)\n"
            " : "
        ).strip()
        if mode in ['1', '2']:
            return 'cpu' if mode == '1' else 'gpu'
        else:
            print("Please enter 1 or 2.")

def get_all_videos(directory):
    """
    This function takes a directory path as input and returns a list of all video paths in that directory and its subdirectories.
    """
    videos = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.mp4')):
                videos.append(os.path.join(root, file))
    return videos

def shutdown_option():
    """
    This function asks the user if they want the Mac to shut down after the compression process is finished.
    """
    print("Thank you for using Compress MP4, your files will be saved in the same directory as the source files!")
    while True:
        shutdown = input("Do you want the Mac to shut down when the compression process is finished? \n [1] YES, shut down \n [2] NO, don't shut down \n : ").strip()
        if shutdown in ['1', '2']:
            break
        else:
            print("Please enter 1 or 2.")

    if shutdown == '1':
        if os.geteuid() != 0:
            print("To shut down the Mac, you must run this script as a superuser. Try running the script with 'sudo'.")
            sys.exit()

    while True:
        compression_option = input("How do you want to compress the videos? \n [1] Enter individual video paths \n [2] Enter a directory path with videos \n : ").strip()
        if compression_option in ['1', '2']:
            break
        else:
            print("Please enter 1 or 2.")
    return shutdown, compression_option

def compress_video(source_path, dest_path, mode):
    """
    This function compresses a video using HandBrakeCLI, showing progress.
    """
    global total_videos, total_compression_time, total_original_size, total_compressed_size

    total_videos += 1
    
    try:
        original_size = os.path.getsize(source_path)
        total_original_size += original_size
    except FileNotFoundError:
        print(f"Error: Source file not found at {source_path}")
        return

    start_time = time.time()

    encoder = 'x264' if mode == 'cpu' else 'vt_h264'

    print(f"\nCompressing with {mode.upper()}: {os.path.basename(source_path)}")

    command = [
        '/Applications/HandBrakeCLI',
        '-i', source_path,
        '-o', dest_path,
        '-f', 'mp4',
        '--optimize',
        '-e', encoder,
        '-q', '26',
        '-r', '30',
        '-E', 'ca_aac',
        '-B', '96',
        '-w', '1920'
    ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

        # Regex to find percentage in HandBrakeCLI output
        progress_regex = re.compile(r"Encoding: task \d+ of \d+, (\d+\.\d+)\s*%")

        for line in process.stdout:
            match = progress_regex.search(line)
            if match:
                percent = float(match.group(1))
                sys.stdout.write(f"\rProgress: {int(percent)}%")
                sys.stdout.flush()

        process.wait()

        if process.returncode != 0:
            print(f"\nError compressing video: {os.path.basename(source_path)}. HandBrakeCLI returned error code {process.returncode}.")
            return

        sys.stdout.write(f"\rProgress: 100% - Complete!      \n")
        sys.stdout.flush()

        compressed_size = os.path.getsize(dest_path)
        total_compressed_size += compressed_size
        total_compression_time += time.time() - start_time

        send2trash(source_path)

    except FileNotFoundError:
        print("\nError: '/Applications/HandBrakeCLI' not found.")
        print("Please ensure HandBrakeCLI is installed in your Applications folder.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred during compression of {os.path.basename(source_path)}: {e}")

def alert_success():
    """
    This function is executed when the script finishes the compression.
    It generates a success alert sound and sends an email.
    """
    global total_videos, total_compression_time, total_original_size, total_compressed_size

    if total_videos == 0:
        print("No videos were compressed.")
        return

    compression_time_minutes, _ = divmod(total_compression_time, 60)
    compression_time_hours, compression_time_minutes = divmod(compression_time_minutes, 60)

    if total_original_size > 0:
        space_saved = total_original_size - total_compressed_size
        percent_space_saved = (space_saved / total_original_size) * 100
        space_saved_gb = space_saved / (1024 ** 3)
    else:
        percent_space_saved = 0
        space_saved_gb = 0

    os.system('afplay ok-notification-alert.wav')
    
    email_message = (
        f"The compression of your videos was completed successfully. Here are the compression statistics:\n\n"
        f"Number of compressed videos: {total_videos}\n"
        f"Total compression time: {int(compression_time_hours)} hr: {int(compression_time_minutes)} min\n"
        f"Compression percentage: {percent_space_saved:.2f}%\n"
        f"Space saved: {space_saved_gb:.2f} GB"
    )

    send_email("Compression successful", email_message, "sammydn7@gmail.com")

def send_email(subject, text, to):
    """
    This function sends an email when the process is finished.
    """
    load_dotenv()
    try:
        response = requests.post(
            "https://api.mailgun.net/v3/mail.colombianmacstore.com.co/messages",
            auth=("api", os.getenv("MAILGUN_API_KEY")),
            data={"from": "noreply@mail.colombianmacstore.com.co",
                  "to": [to],
                  "subject": subject,
                  "text": text})
        if response.status_code == 200:
            print("A confirmation of the completed process has been sent to the email.")
            return True
        else:
            print(f"Error sending the email. Status code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print(f"An error occurred while sending the email: {e}")
        return False

def process_videos(video_paths, mode):
    for source_path in video_paths:
        # Handle escaped spaces from terminal input
        source_path = source_path.replace('\\', '')
        if not os.path.isfile(source_path):
            print(f"File not found: {source_path}. Skipping.")
            continue

        source_path = os.path.abspath(source_path)
        dir_path = os.path.dirname(source_path)
        file_name = os.path.basename(source_path)
        base_name, extension = os.path.splitext(file_name)
        compressed_file_name = f"{base_name}_compressed{extension}"
        dest_path = os.path.join(dir_path, compressed_file_name)

        compress_video(source_path, dest_path, mode)

# --- Main script execution ---
if __name__ == "__main__":
    shutdown, compression_option = shutdown_option()
    compression_mode = get_compression_mode()

    if compression_option == '1':
        try:
            amount_videos = int(input("Enter the number of videos to compress: ").strip())
            video_paths = [
                input(f"Enter the source file path {i+1}: ").strip()
                for i in range(amount_videos)
            ]
            process_videos(video_paths, compression_mode)
        except ValueError:
            print("Invalid input. Please enter a number.")
            sys.exit()
    else:
        directory = input("Enter the directory path with the videos: ").strip().replace('\\', '')
        if not os.path.isdir(directory):
            print("The entered directory does not exist. Please try again.")
            sys.exit()

        video_paths = get_all_videos(directory)
        if not video_paths:
            print("No videos were found in the entered directory. Please try again.")
            sys.exit()

        process_videos(video_paths, compression_mode)

    alert_success()

    if shutdown == '1':
        print("Shutting down the Mac...")
        os.system('shutdown -h now')