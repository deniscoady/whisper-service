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
from os import listdir
from os.path import isfile, join

app = FastAPI()


class OverviewResponse(BaseModel):
    data: list



@app.get("/overview", response_model = OverviewResponse)
async def overview():
  results = []

  filenames = [ f for f in listdir('/app/results') if isfile(join('results', f)) ]
  for filename in filenames:
     with open(join('results', filename), 'r') as file:
        data = file.read()
        data = json.loads(data)
        results.append(data)

  results.sort(key = lambda d: d['start'], reverse = True)
  return { 'data': results }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)