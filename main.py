import os
import sys
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
import json
from datetime import datetime


load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")

frontmatter = "---\nMRN: \ndateCreated: "+datetime.now().date().isoformat()+"\ntimeCreated: "+datetime.now().replace(microsecond=0).time().isoformat()+"\ntags: dictations\n---\n"

if openai_key == "<YOUR_OPENAI_KEY>":
	openai_key = ""

if openai_key == "":
	sys.exit("Please Provide Your OpenAI API Key")

def show_json(obj):
    return json.loads(obj.model_dump_json())

def pretty_print(messages):
	#print("Messages")
	for m in messages:
		print(f"{m.role}: {m.content[0].text.value}")
		print()

def pretty_return(messages):
	#print("Messages")
	result = ""
	for m in messages:
		result = result + m.content[0].text.value
	return result

def transcript(audio, model, response_type, checkbox_value, process_type):
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

	if checkbox_value:
		return process(transcriptions, process_type)
	else:
		return transcriptions

def process(output_text, process_type):
	if process_type == "Referral":
		assistant_id = "asst_ZHAae4G9DOxgJcbRd6rdAZrv"
		#thread_id = "thread_aCl8EEYfilXy9XE4T240bpBO"
	elif process_type == "Clinic Letter":
		assistant_id = "asst_m7ObZXl7fZPkz2iFnU2GPwQ5"
	else:
		assistant_id = "asst_QtANS1beG7PvnztjlYjXj0NV"
		#Fall back to correspondence letter helper

	client = OpenAI(api_key=openai_key)
	thread = client.beta.threads.create()
	message = client.beta.threads.messages.create(
		thread_id=thread.id,
		role="user",
		content=output_text
	)
	run = client.beta.threads.runs.create_and_poll(
		thread_id=thread.id,
		assistant_id=assistant_id,
		instructions=""
	)
	if run.status == 'completed': 
		messages = client.beta.threads.messages.list(
			thread_id=thread.id
		)
		save_result(pretty_return(messages))
		return pretty_return(messages)
	else:
		return run.status
	

def save_result(processed_result):
	timestamp = datetime.now().replace(microsecond=0).isoformat()
	with open("/home/robert/vaults/obsidian/001 Inbox/"+timestamp+".md", "w") as output_file:
		output_file.write(frontmatter)
		output_file.write(processed_result)
	return output_file



def process_clinic_letter(output_text):
	assistant_id = "asst_m7ObZXl7fZPkz2iFnU2GPwQ5"
	client = OpenAI(api_key=openai_key)
	thread = client.beta.threads.create()
	message = client.beta.threads.messages.create(
		thread_id=thread.id,
		role="user",
		content=output_text
	)
	run = client.beta.threads.runs.create_and_poll(
		thread_id=thread.id,
		assistant_id=assistant_id,
		instructions=""
	)
	if run.status == 'completed': 
		messages = client.beta.threads.messages.list(
			thread_id=thread.id
		)
		print(messages)
	else:
		print(run.status)
	return pretty_return(messages)


def checkbox_change(checkbox_value):
	print(checkbox_value)
	if checkbox_value:
		return gr.Button(interactive=False)
	else:
		return gr.Button(interactive=True)


def upload_file(files):
	print(files)


with gr.Blocks() as demo:
	gr.Markdown("# <center> Physician's Assistant </center>")
	with gr.Row(variant="panel"):
		model = gr.Dropdown(choices=["whisper-1"], label="Model", value="whisper-1")
		response_type = gr.Dropdown(choices=["json", "text", "srt", "verbose_json", "vtt"], label="Response Type",
									value="text")

	with gr.Row():
		audio = gr.Audio(sources=["microphone"], type="filepath")
		file = gr.UploadButton(file_types=[".mp3", ".wav"], label="Select File", type="filepath")

	output_text = gr.Text(label="Output Text", show_copy_button=True)

	with gr.Row():
		process_type = gr.Dropdown(choices=["Referral", "Clinic Letter", "Correspondence Letter"], label="Process Type", value="Correspondence Letter")
		process_button = gr.Button(value="Process")
		always_process_checkbox = gr.Checkbox(label="Process Automatically?")

	processed_text = gr.Markdown(label="Processed Text")

	audio.stop_recording(fn=transcript, inputs=[audio, model, response_type, always_process_checkbox, process_type], outputs=output_text, api_name=False)
	file.upload(fn=transcript, inputs=[file, model, response_type, always_process_checkbox, process_type], outputs=output_text)
	process_button.click(fn=process, inputs=[output_text, process_type], outputs=processed_text)
	always_process_checkbox.change(fn=checkbox_change, inputs=[always_process_checkbox], outputs=[process_button])

demo.launch()
