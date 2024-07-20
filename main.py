import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
import speech_recognition as sr
from pydub.generators import Sine
import shutil

# Example usage:
input_file = "input_audio.wav"

# Intermediary folders
output_folder_chunks = "split_chunks"
output_folder_tracks = "combined_tracks"

# Target length of subtitle chunks in seconds
goal = 3


def split_wav_by_silence(input_file, output_folder, silence_thresh=-40, min_silence_len=200, offset=400):

    sound = AudioSegment.from_wav(input_file)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    chunks = split_on_silence(sound, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    start_time_ms = 0

    # Export each chunk as a separate file
    for i, chunk in enumerate(chunks):
        seconds, milliseconds = divmod((start_time_ms + offset), 1000)
        minutes, seconds = divmod(seconds, 60)

        # Name formatting
        minutes_str = str(minutes).zfill(2)
        seconds_str = str(seconds).zfill(2)
        milliseconds_str = str(milliseconds).zfill(3)
        start_time_str = f"00-{minutes_str}-{seconds_str},{milliseconds_str}"

        chunk.export(os.path.join(output_folder, f"{start_time_str}.wav"), format="wav")
        start_time_ms += len(chunk)


def get_audio_length_and_merge(folder_path, output_folder_tracks, goal):

    totallength = 0
    merged_audio = None
    for filename in os.listdir(folder_path):
        if filename.endswith(".wav"):  # Adjust file extension if needed
            file_path = os.path.join(folder_path, filename)

            audio = AudioSegment.from_file(file_path)
            length = len(audio) / 1000.0
            totallength += length
            if totallength == length:
                finalfilename = filename
                merged_audio = audio

            print(f"Length of {filename}: {length} seconds")
            print(f"total length is now {totallength} seconds")

            if totallength < goal:

                if 'merged_audio' not in locals():  # Initialize merged_audio if not already done
                    merged_audio = audio
                else:
                    if totallength != length:
                        merged_audio += audio

            elif totallength == length:

                merged_file = finalfilename
                merged_audio.export(f"{output_folder_tracks}/{merged_file}", format="wav")
                print(f"Merged audio saved as: {merged_file}")

                totallength = 0
                merged_audio = None

            else:

                merged_audio += audio
                merged_file = finalfilename
                merged_audio.export(f"{output_folder_tracks}/{merged_file}", format="wav")
                print(f"Merged audio saved as: {merged_file}")

                totallength = 0
                merged_audio = None


def transcribe_audio_files(folder_path):
    recognizer = sr.Recognizer()
    count = 0
    files = os.listdir(folder_path)
    srt = open("sub.srt", "w")
    srt.close

    for file in files:
        if file.endswith('.wav') or file.endswith('.mp3') or file.endswith('.ogg'):
            file_path = os.path.join(folder_path, file)
            count += 1
            print("Transcribing file:", file_path)


            with sr.AudioFile(file_path) as source:
                audio_data = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio_data)
                srt = open("sub.srt", "a")
                srt.write(str(count))
                srt.write("\n")
                try:
                    srt.write(f"{(str(files[(count - 1)]).rstrip('.wav')).replace('-',':')} --> {(str(files[(count)]).rstrip('.wav')).replace('-',':')}")
                except:
                    srt.write(f"{(str(files[(count - 1)]).rstrip('.wav')).replace('-', ':')} --> {(str(files[(count - 1)]).rstrip('.wav')).replace('-', ':')}")
                srt.write("\n")
                srt.write(text)
                srt.write("\n")
                srt.write("\n")
                srt.close



            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))


# Add silence before audio clips to improve word detection

def add_silence_to_audio_folder(input_folder, seconds_of_silence=3):
    for filename in os.listdir(input_folder):
        if filename.endswith(".wav") or filename.endswith(".mp3"):
            input_path = os.path.join(input_folder, filename)

            audio = AudioSegment.from_file(input_path)

            # Generate silence
            silence = Sine(0).to_audio_segment(duration=seconds_of_silence * 1000)

            audio_with_silence = audio + silence
            audio_with_silence.export(input_path, format="wav")

            print(f"Processed {filename} successfully.")


def cleanup():

    try:
        shutil.rmtree("combined_tracks")
        print("Removed combined_tracks")
    except:
        print("Combined_tracks not found for deletion")

    try:
        shutil.rmtree("split_chunks")
        print("Removed split_chunks")
    except:
        print("split_chunks not found for deletion")


if __name__ == "__main__":
    # Split the input file into chunks based on silence
    split_wav_by_silence(input_file, output_folder_chunks)

    # Combine the chunks into larger tracks close to the target length
    os.mkdir("combined_tracks")
    get_audio_length_and_merge(output_folder_chunks, output_folder_tracks, goal)

    add_silence_to_audio_folder(output_folder_tracks)
    transcribe_audio_files(output_folder_tracks)
    cleanup()


