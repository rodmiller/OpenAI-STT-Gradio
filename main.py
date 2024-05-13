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

client = OpenAI(api_key=openai_key)

def transcript(client, audio, model, response_type):
	try:
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

def process(client, output_text, process_type):
	return output_text


def _process_referral(client, output_text):
	assistant = client.beta.assistants.create(
		name="Clinic_Letter_Helper",
		instructions="You are a helpful medical secretary for a gastroenterology registrar. Your task is to correct any spelling discrepancies in the transcribed text or any words that have been mis-transcribed. You are writing a clinic letter which may have several subheadings. Every letter should include a 'clinical summary' which is a paragraph summarising the case at the top - please write this if it is not transcribed. Additionally, letters should include a diagnosis or list of diagnoses, a list of investigations and a plan. There may also be a list of other diagnoses and a list of medications. Please ensure that the words are spelled using British English. Please add punctuation as requested in the transcription and any formatting. There may be sections in the letters which also should be formatted correctly. You do not need to address or sign off the letter. Additionally, please could you generate a separate markdown-formatted task list with check boxes ([ ]) based upon the plan in the letter but only including tests that need to be requested (these are blood tests, radiology and procedures), please include the information needed for tasks that need to be requested - for example if there is a request for a test please write a clinical summary of the case which can be used to request the test.",
		model="gpt-4o",
	)
	thread = client.beta.threads.create()
	message = client.beta.threads.messages.create(
		thread_id=thread.id,
		role="user",
		content=output_text
	)
	run = client.beta.threads.runs.create_and_poll(
		thread_id=thread.id,
		assistant_id=assistant.id,
		instructions=""
	)
	if run.status == 'completed': 
		messages = client.beta.threads.messages.list(
		thread_id=thread.id
		)
		print(messages)
	else:
		print(run.status)
	return messages




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

	process_type = gr.Dropdown(choices=["Referral", "Clinic Letter", "Correspondence Letter"], label="Process Type", value="Referral")

	process_button = gr.Button(value="Process")

	processed_text = gr.Text(label="Processed Text")

	audio.stop_recording(fn=transcript, inputs=[client, audio, model, response_type], outputs=output_text, api_name=False)
	file.upload(fn=transcript, inputs=[file, model, response_type], outputs=output_text)
	process_button.click(fn=process, inputs=[output_text, process_type], outputs=processed_text)

demo.launch()
