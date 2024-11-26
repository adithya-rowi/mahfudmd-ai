import whisper
import os

model = whisper.load_model("medium")
audio_dir = "data/transcripts"
output_dir = "data/transcripts"

os.makedirs(output_dir, exist_ok=True)

for file in os.listdir(audio_dir):
    if file.endswith(".mp3") or file.endswith(".webm"):
        audio_path = os.path.join(audio_dir, file)
        print(f"Processing: {audio_path}")

        try:
            result = model.transcribe(audio_path)
            print(f"Transcription completed for {file}")

            output_path = os.path.join(output_dir, file.replace(".webm", ".txt").replace(".mp3", ".txt"))
            print(f"Saving to: {output_path}")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result["text"])

            print(f"Saved transcription to {output_path}")
        except Exception as e:
            print(f"Error processing {file}: {e}")
