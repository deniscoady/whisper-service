from fastapi import FastAPI, UploadFile, File, HTTPException
from whisperx import load_model
import shutil
import os
from tempfile import NamedTemporaryFile
from pydantic import BaseModel
from datetime import datetime, timedelta
from uuid import uuid4
import json
import shutil
import os

app = FastAPI()

# Load WhisperX model (adjust the model size based on your needs)
model = load_model("large-v3", device="cuda")  # or "cpu" if you don't have a GPU


class TranscriptionResponse(BaseModel):
    text: str


# Convert transcription to VTT format
def convert_to_vtt(transcription_result):
    vtt_output = ["WEBVTT", ""]
    for segment in transcription_result['segments']:
        start = segment['start']  # Start time in seconds
        end = segment['end']  # End time in seconds
        text = segment['text']
        
        # Convert seconds to VTT timestamp format (HH:MM:SS.MS)
        start_vtt = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02}.{int((start % 1) * 1000):03}"
        end_vtt = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02}.{int((end % 1) * 1000):03}"
        
        # Add segment to VTT file
        vtt_output.append(f"{start_vtt} --> {end_vtt}")
        vtt_output.append(text)
        vtt_output.append("")  # Blank line between segments

    return "\n".join(vtt_output)


@app.post("/v1/audio/transcriptions", response_model = TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    OpenAI-compatible endpoint that accepts audio files and returns a transcription.
    """
    try:
        start = datetime.now()
        uuid  = uuid4()

        with open(f'/app/results/{uuid}.json', 'w') as fp:
            data = json.dumps({'uuid': str(uuid), 'start': str(start) })
            fp.write(data)

        # Save the uploaded file to a temporary location
        with NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            shutil.copyfileobj(file.file, temp_audio)
            temp_audio_path = temp_audio.name

        # Perform transcription using WhisperX
        result = model.transcribe(temp_audio_path, batch_size = 32)
        # Prepare transcription result to match OpenAI's format
        # transcription_text = ' '.join([ segment['text'] for segment in result['segments'] ])
        transcription_vtt = convert_to_vtt(result)
        transcription = { "text": transcription_vtt }

        # Clean up the temporary file
        os.remove(temp_audio_path)

        finish = datetime.now()
        duration = finish - start
        with open(f'/app/results/{uuid}.json', 'w') as fp:
            data = json.dumps({
                'uuid': str(uuid), 
                'start': str(start), 
                'finish': str(finish), 
                'duration': str(duration) })
            fp.write(data)

        return transcription

    except Exception as e:
        print(str(e))
        finish = datetime.now()
        with open(f'/app/results/{uuid}.json', 'w') as fp:
            data = json.dumps({
              'uuid'  : str(uuid), 
              'start' : str(start), 
              'finish': str(finish), 
              'error' : str(e) })
            fp.write(data)

        raise HTTPException(status_code=500, detail=f"An error occurred during transcription: {str(e)}")
                
        
if __name__ == "__main__":
    import uvicorn
    shutil.rmtree('results', ignore_errors = True)
    os.mkdir('results')
    uvicorn.run(app, host="0.0.0.0", port=8000)


