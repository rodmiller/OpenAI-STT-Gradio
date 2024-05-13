import os
import sys
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")

if openai_key == "<YOUR_OPENAI_KEY>":
    openai_key = ""

if openai_key == "":
    sys.exit("Please Provide Your OpenAI API Key")


def transcript(audio, model, response_type):
    try:
        client = OpenAI(api_key=openai_key)
        print(audio)
        audio_file = open(audio, "rb")
        transcriptions = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            response_format=response_type
        )
    except Exception as error:
        print(str(error))
        raise gr.Error("An error occurred while generating speech. Please check your API key and come back try again.")

    return transcriptions

def process(output_text, process_type):
    return output_text


def upload_file(files):
    print(files)


with gr.Blocks() as demo:
    gr.Markdown("# <center> OpenAI Speech To Text API with Gradio </center>")
    with gr.Row(variant="panel"):
        model = gr.Dropdown(choices=["whisper-1"], label="Model", value="whisper-1")
        response_type = gr.Dropdown(choices=["json", "text", "srt", "verbose_json", "vtt"], label="Response Type",
                                    value="text")

    with gr.Row():
        audio = gr.Audio(sources=["microphone"], type="filepath")
        file = gr.UploadButton(file_types=[".mp3", ".wav"], label="Select File", type="filepath")

    output_text = gr.Text(label="Output Text")

    process_type = gr.Dropdown(choices=["Referral", "Clinic Letter", "Correspondence Letter"], label="Process Type", value="process_type")

    process_button = gr.Button(value="Process")

    processed_text = gr.Text(label="Processed Text")

    audio.stop_recording(fn=transcript, inputs=[audio, model, response_type], outputs=output_text, api_name=False)
    file.upload(fn=transcript, inputs=[file, model, response_type], outputs=output_text)
    process_button.click(fn=process, inputs=[output_text, process_type], outputs=processed_text)

demo.launch()
