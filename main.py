import os
import sys
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
import json
from datetime import datetime


load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
user = os.getenv("USER")
device = os.getenv("DEVICE")
print(user)
print(device)

#frontmatter = ""
frontmatter = "---\nMRN: \ndateCreated: '"+datetime.now().date().isoformat()+"'\ntimeCreated: '"+datetime.now().replace(microsecond=0).time().isoformat()+"'\ntags: dictation\n---\n"

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
		result = result + m.content[0].text.value + "\n"
	return result

def transcript(audio, model, response_type, checkbox_value, process_type):
	try:
		gr.Info("Uploading audio...")
		client = OpenAI(api_key=openai_key)
		print(audio)
		gr.Info("Transcribing...")
		audio_file = open(audio, "rb")
		transcriptions = client.audio.transcriptions.create(
			model=model,
			file=audio_file,
			response_format=response_type
		)
	except Exception as error:
		print(str(error))
		raise gr.Error("An error occurred while generating speech. Please check your API key and come back try again.")
	print(checkbox_value)
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
	elif process_type == "Results Letter":
		assistant_id = "asst_VC18ebPqMbuNKmi5MshnWNcM"
	else:
		assistant_id = "asst_QtANS1beG7PvnztjlYjXj0NV"
		#Fall back to correspondence letter helper
	gr.Info("Processing...")
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
	with open("/home/"+user+"/vaults/obsidian/001 Inbox/"+timestamp+".md", "w") as output_file:
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
	#print(checkbox_value)
	if checkbox_value:
		return gr.Button(interactive=False)
	else:
		return gr.Button(interactive=True)


def upload_file(files):
	print(files)

def recordingStopped(audio):
	#print(audio)
	#gr.Info("Recording Stopped now")
	return gr.Button(interactive=True)
	
with gr.Blocks() as demo:
	with gr.Tab("All In One"):
		gr.Markdown("# <center> Physician's Assistant - "+device+"</center>")
		with gr.Row(variant="panel"):
			aio_model = gr.Dropdown(choices=["whisper-1"], label="Model", value="whisper-1")
			aio_response_type = gr.Dropdown(choices=["json", "text", "srt", "verbose_json", "vtt"], label="Response Type", value="text")

		with gr.Row():
			aio_audio = gr.Audio(sources=["microphone"], type="filepath", show_download_button=True)
			aio_file = gr.UploadButton(file_types=[".mp3", ".wav"], label="Select File", type="filepath")

		aio_submit_button = gr.Button(value="Re-Transcribe and Process", interactive=False)

		aio_output_text = gr.Markdown(label="Output Text")

		aio_process_type = gr.Dropdown(choices=["Referral", "Clinic Letter", "Correspondence Letter", "Results Letter"], label="Process Type", value="Results Letter")
		aio_process_button = gr.Button(value="Reprocess")
		aio_always_process_checkbox = gr.Checkbox(label="Process Automatically?", value=True, visible=False)

		aio_processed_text = gr.Markdown(label="Processed Text")

		aio_submit_button.click(fn=transcript, inputs=[aio_audio, aio_model, aio_response_type, aio_always_process_checkbox, aio_process_type], outputs=aio_output_text, api_name=False)
		aio_audio.stop_recording(fn=transcript, inputs=[aio_audio, aio_model, aio_response_type, aio_always_process_checkbox, aio_process_type], outputs=aio_output_text, api_name=False)
		aio_audio.stop_recording(fn=recordingStopped, inputs=[aio_audio], outputs=[aio_submit_button])
		aio_file.upload(fn=transcript, inputs=[aio_file, aio_model, aio_response_type, aio_always_process_checkbox, aio_process_type], outputs=aio_output_text)
		#aio_resubmit_button.click(fn=transcript, inputs=[audio, model, response_type, always_process_checkbox, process_type], outputs=output_text, api_name=False)
		aio_process_button.click(fn=process, inputs=[aio_output_text, aio_process_type], outputs=aio_processed_text)
		#aio_always_process_checkbox.change(fn=checkbox_change, inputs=[always_process_checkbox], outputs=[process_button])
	
	with gr.Tab("Processing"):
		gr.Markdown("# <center> Physician's Assistant - "+device+"</center>")
		p_model = gr.Dropdown(choices=["whisper-1"], label="Model", value="whisper-1")
		p_response_type = gr.Dropdown(choices=["json", "text", "srt", "verbose_json", "vtt"], label="Response Type", value="text")

		p_output_text = gr.Text(label="Transcription to Process")

		with gr.Row():
			p_process_type = gr.Dropdown(choices=["Referral", "Clinic Letter", "Correspondence Letter", "Results Letter"], label="Process Type", value="Results Letter")
			p_process_button = gr.Button(value="Process")
			#p_always_process_checkbox = gr.Checkbox(label="Process Automatically?")

		p_processed_text = gr.Markdown(label="Processed Text")
		
		#p_submit_button.click(fn=transcript, inputs=[p_audio, p_model, p_response_type, p_always_process_checkbox, p_process_type], outputs=p_output_text, api_name=False)
		#p_file.upload(fn=transcript, inputs=[p_file, aio_model, p_response_type, p_always_process_checkbox, p_process_type], outputs=p_output_text)
		#aio_resubmit_button.click(fn=transcript, inputs=[audio, model, response_type, always_process_checkbox, process_type], outputs=output_text, api_name=False)
		p_process_button.click(fn=process, inputs=[p_output_text, p_process_type], outputs=p_processed_text)
		#aio_always_process_checkbox.change(fn=checkbox_change, inputs=[always_process_checkbox], outputs=[process_button])
	
	with gr.Tab("Transcribing"):
		gr.Markdown("# <center> Physician's Assistant - "+device+"</center>")
		
		with gr.Row(variant="panel"):
			t_model = gr.Dropdown(choices=["whisper-1"], label="Model", value="whisper-1")
			t_response_type = gr.Dropdown(choices=["json", "text", "srt", "verbose_json", "vtt"], label="Response Type", value="text")

		with gr.Row():
			t_audio = gr.Audio(sources=["microphone"], type="filepath", show_download_button=True)
			t_file = gr.UploadButton(file_types=[".mp3", ".wav"], label="Select File", type="filepath")

		t_submit_button = gr.Button(value="Retranscribe")
		t_always_process_checkbox = gr.Checkbox(visible=False, value=False)
		t_process_type = p_process_type = gr.Dropdown(choices=["Referral", "Clinic Letter", "Correspondence Letter", "Results Letter"], label="Process Type", value="Results Letter", visible=False)

		t_output_text = gr.Markdown(label="Output Text")
		
		t_audio.stop_recording(fn=transcript, inputs=[t_audio, t_model, t_response_type, t_always_process_checkbox, t_process_type], outputs=t_output_text, api_name=False)
		t_file.upload(fn=transcript, inputs=[t_file, t_model, t_response_type, t_always_process_checkbox, t_process_type], outputs=t_output_text)
		t_submit_button.click(fn=transcript, inputs=[t_audio, t_model, t_response_type, t_always_process_checkbox, t_process_type], outputs=t_output_text, api_name=False)
		#t_process_button.click(fn=process, inputs=[t_output_text, t_process_type], outputs=t_processed_text)
		#aio_always_process_checkbox.change(fn=checkbox_change, inputs=[always_process_checkbox], outputs=[process_button])
		

	


demo.launch(server_port=7860)
