import os
import sys
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
import json
from datetime import datetime
import numpy as np
from pydub import AudioSegment
import wavio

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
user = os.getenv("USER")
device = ''
device = os.getenv("DEVICE")
print(user)
print(device)

process_types = {
	"Referral": "asst_ZHAae4G9DOxgJcbRd6rdAZrv",
	"Clinic Letter": "asst_m7ObZXl7fZPkz2iFnU2GPwQ5",
	"Results Letter": "asst_VC18ebPqMbuNKmi5MshnWNcM",
	"Correspondence Letter": "asst_QtANS1beG7PvnztjlYjXj0NV",
	"Endoscopy Report": "asst_pVFGXvuDIVZzUjKT2C88KL4R"
}
default_process_type = "Correspondence Letter"
last_process_type = default_process_type


frontmatter = ""
#frontmatter = "---\nMRN: \ndateCreated: '"+datetime.now().date().isoformat()+"'\ntimeCreated: '"+datetime.now().replace(microsecond=0).time().isoformat()+"'\ntags: dictation\n---\n"

title = "# <center> Physician's Assistant - "+device+"</center>"


if openai_key == "<YOUR_OPENAI_KEY>":
	openai_key = ""

if openai_key == "":
	sys.exit("Please Provide Your OpenAI API Key")

def get_user(request):
	return str(request)

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

def transcript(audio, model, response_type, checkbox_value, process_type, state):
	#global audio_data
	#global streaming_rate
	#audio_file = wavio.write("to_transcribe.wav", audio_data, streaming_rate)

	#Last run of streaming audio
	#state = streamingAudio(state, audio)
	#Export the audioSegment to a file
	#state.export("to_transcribe.wav", format="wav")
	sleep(2)
	try:
		print(get_user(gr.Request()))
		gr.Info("Uploading audio...")
		client = OpenAI(api_key=openai_key)
		print(audio)
		gr.Info("Transcribing...")
		audio_file = open("to_transcribe.wav", "rb")
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
	if not process_type:
		process_type = "Correspondence Letter"
	assistant_id = process_types[process_type]
	
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
		save_result(pretty_return(messages), process_type)
		return pretty_return(messages)
	else:
		return run.status
	

def save_result(processed_result, extra_tag):
	timestamp = datetime.now().replace(microsecond=0).isoformat()
	frontmatter = "---\nMRN: \ndateCreated: '"+datetime.now().date().isoformat()+"'\ntimeCreated: '"+datetime.now().replace(microsecond=0).time().isoformat()+"'\ntags: \n - dictation\n - "+extra_tag.replace(" ", "_")+"\n---\n"
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

audio_data = None
streaming_rate = None

def capture_audio(stream, new_chunk):
    """
    Function to capture streaming audio and accumulate it in a global variable.

    Args:
        stream (numpy.ndarray): The accumulated audio data up to this point.
        new_chunk (tuple): A tuple containing the sampling rate and the new audio data chunk.

    Returns:
        numpy.ndarray: The updated stream with the new chunk appended.
    """
    global audio_data
    global streaming_rate

    # Extract sampling rate and audio chunk, normalize the audio
    sr, y = new_chunk
    streaming_rate = sr
    y = y.astype(np.float32)
    y /= np.max(np.abs(y))

    # Concatenate new audio chunk to the existing stream or start a new one
    if stream is not None:
        stream = np.concatenate([stream, y])
    else:
        stream = y

    # Update the global variable with the new audio data
    audio_data = stream
    return stream


def streamingAudio(stream, new_chunk):
	print('New streaming chunk')
	print(new_chunk)
	#print(dir(new_chunk))
	#print(type(new_chunk))
	new_chunk_segment = AudioSegment.from_wav(new_chunk)

	#sr, y = new_chunk
	#y = y.astype(np.float32)
	#y /= np.max(np.abs(y))

	if stream is not None:
		print("Adding chunk to stream")
		stream = stream + new_chunk_segment
		print("Added chunk to stream")
	else:
		print("First chunk")
		stream = new_chunk_segment
	print("Returning stream")
	return stream

	
with gr.Blocks() as demo:
	
	with gr.Tab("All In One"):
		gr.Markdown(title)
		with gr.Row(variant="panel"):
			aio_model = gr.Dropdown(choices=["whisper-1"], label="Model", value="whisper-1")
			aio_response_type = gr.Dropdown(choices=["json", "text", "srt", "verbose_json", "vtt"], label="Response Type", value="text")

		with gr.Row():
			aio_audio = gr.Audio(sources=["microphone"], type="filepath", show_download_button=True)
			aio_file = gr.UploadButton(file_types=[".mp3", ".wav"], label="Select File", type="filepath")

		aio_submit_button = gr.Button(value="Re-Transcribe and Process", interactive=False)

		aio_output_text = gr.Markdown(label="Output Text")

		aio_process_type = gr.Dropdown(choices=list(process_types.keys()), label="Process Type", value=last_process_type)
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
		gr.Markdown(title)
		p_model = gr.Dropdown(choices=["whisper-1"], label="Model", value="whisper-1")
		p_response_type = gr.Dropdown(choices=["json", "text", "srt", "verbose_json", "vtt"], label="Response Type", value="text")

		p_output_text = gr.Text(label="Transcription to Process")

		with gr.Row():
			p_process_type = gr.Dropdown(choices=list(process_types.keys()), label="Process Type", value=last_process_type)
			p_process_button = gr.Button(value="Process")
			#p_always_process_checkbox = gr.Checkbox(label="Process Automatically?")

		p_processed_text = gr.Markdown(label="Processed Text")
		
		#p_submit_button.click(fn=transcript, inputs=[p_audio, p_model, p_response_type, p_always_process_checkbox, p_process_type], outputs=p_output_text, api_name=False)
		#p_file.upload(fn=transcript, inputs=[p_file, aio_model, p_response_type, p_always_process_checkbox, p_process_type], outputs=p_output_text)
		#aio_resubmit_button.click(fn=transcript, inputs=[audio, model, response_type, always_process_checkbox, process_type], outputs=output_text, api_name=False)
		p_process_button.click(fn=process, inputs=[p_output_text, p_process_type], outputs=p_processed_text)
		#aio_always_process_checkbox.change(fn=checkbox_change, inputs=[always_process_checkbox], outputs=[process_button])
	
	with gr.Tab("Transcribing"):
		gr.Markdown(title)
		
		with gr.Row(variant="panel"):
			t_model = gr.Dropdown(choices=["whisper-1"], label="Model", value="whisper-1")
			t_response_type = gr.Dropdown(choices=["json", "text", "srt", "verbose_json", "vtt"], label="Response Type", value="text")

		with gr.Row():
			t_audio = gr.Audio(sources=["microphone"], show_download_button=True, streaming=True, type="filepath")
			t_file = gr.UploadButton(file_types=[".mp3", ".wav"], label="Select File", type="filepath")

		t_submit_button = gr.Button(value="Retranscribe")
		t_always_process_checkbox = gr.Checkbox(visible=False, value=False)
		t_process_type = p_process_type = gr.Dropdown(choices=list(process_types.keys()), label="Process Type", value=last_process_type, visible=False)

		t_output_text = gr.Markdown(label="Output Text")
		t_state = gr.State()

		t_audio.stream(fn=streamingAudio, inputs=[t_state, t_audio], outputs=[t_state])
		t_audio.stop_recording(fn=transcript, inputs=[t_audio, t_model, t_response_type, t_always_process_checkbox, t_process_type, t_state], outputs=t_output_text, api_name=False)
		t_file.upload(fn=transcript, inputs=[t_file, t_model, t_response_type, t_always_process_checkbox, t_process_type], outputs=t_output_text)
		t_submit_button.click(fn=transcript, inputs=[t_audio, t_model, t_response_type, t_always_process_checkbox, t_process_type], outputs=t_output_text, api_name=False)
		#t_process_button.click(fn=process, inputs=[t_output_text, t_process_type], outputs=t_processed_text)
		#aio_always_process_checkbox.change(fn=checkbox_change, inputs=[always_process_checkbox], outputs=[process_button])
		

	


demo.launch(server_port=7860)
