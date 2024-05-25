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
from time import sleep
import subprocess





def get_git_revision_hash() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()

def get_git_revision_short_hash() -> str:
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()

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
#Test comment

frontmatter = ""
#frontmatter = "---\nMRN: \ndateCreated: '"+datetime.now().date().isoformat()+"'\ntimeCreated: '"+datetime.now().replace(microsecond=0).time().isoformat()+"'\ntags: dictation\n---\n"

title = "# <center> Physician's Assistant - "+device+"</center> \n ### Version: "+get_git_revision_short_hash()


shortcut_js = """
<script>
function shortcutsdown(e) {
	if (e.repeat) return;
    if (e.key == "r") {
        document.querySelector("#aio_audio > div.audio-container.svelte-cbyffp > div.mic-wrap.svelte-1m31gsz > div.controls.svelte-1m31gsz > button").click();
    }
}
function shortcutsup(e) {
    if (e.key == "r") {
        document.querySelector("#aio_audio > div.audio-container.svelte-cbyffp > div.mic-wrap.svelte-1m31gsz > div.controls.svelte-1m31gsz > button").click();
    }
    if (e.key == "t") {
    	document.querySelector("#aio_submit_button").click()
    }
}
document.addEventListener('keyup', shortcutsup, false);
document.addEventListener('keydown', shortcutsdown, false);
</script>
"""




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

def transcript(audio, model, response_type, checkbox_value, process_type, streaming, state):
	#global audio_data
	#global streaming_rate
	#audio_file = wavio.write("to_transcribe.wav", audio_data, streaming_rate)

	#if streaming then do this:
	if streaming:
		#Last run of streaming audio
		#sleep(5)
		state = streamingAudio(state, audio)
		#Export the audioSegment to a file
		print("Assembling chunks")
		assembled_segments = None
		print("Set assembled chunks to None")
		print("STATE: "+ str(state))

		for chunk in state:
			if not assembled_segments:
				print("First Chunk: " + str(chunk))
				assembled_segments = AudioSegment.from_wav(chunk)
			else:
				print("Adding Chunk: "+ str(chunk))
				assembled_segments = assembled_segments + AudioSegment.from_wav(chunk)
		print("Finished compiling segments")
		stamp = datetime.now().replace(microsecond=0).isoformat()
		audio_file_path = "recordings/"+stamp+".wav"
		print("Going to be saving to: " + audio_file_path)
		print("Assembling chunks")
		assembled_segments.export(audio_file_path, format="wav")
		print("File saved to: "+audio_file_path)
	try:
		#print(get_user(gr.Request()))
		gr.Info("Uploading audio...")
		client = OpenAI(api_key=openai_key)
		gr.Info("Transcribing...")
		if not streaming:
			audio_file_path = audio
		#print(audio_file_path)
		audio_file = open(audio_file_path, "rb")
		transcriptions = client.audio.transcriptions.create(
			model=model,
			file=audio_file,
			response_format=response_type
		)
	except Exception as error:
		print(str(error))
		raise gr.Error("An error occurred while generating speech. Please check your API key and come back try again.")
	#print(checkbox_value)
	if checkbox_value:
		return process(transcriptions, process_type), audio_file_path
	else:
		return transcriptions, audio_file_path

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

#last_chunk_time = None
is_transcribing = False


def streamingAudio(stream, new_chunk):
	#print('New streaming chunk')
	#print(datetime.now().isoformat())
	#print(new_chunk)
	#print(dir(new_chunk))
	#print(type(new_chunk))
	#global last_chunk_time
	if not new_chunk:
		return stream
	#new_chunk_segment = AudioSegment.from_wav(new_chunk)
	#last_chunk_time = datetime.now().timestamp()
	#chunk_stamp = 
	#sr, y = new_chunk
	#y = y.astype(np.float32)
	#y /= np.max(np.abs(y))

	#Possibly add a timestamp as a key for each chunk then order them correctly before processing?
	# Only if chunks get out of order!

	if stream is not None:
		#print("Adding chunk to stream")
		stream.append(new_chunk)
		#print("Added chunk to stream")
	else:
		#print("First chunk")
		stream = [new_chunk]
	#print("Returning stream")
	return stream

def streamingAudioUpdateTimestamp():
	if is_transcribing:
		return None
	return datetime.now().timestamp()

def stopTranscribing(last_chunk_timstamp):
	is_transcribing = False
	return datetime.now().timestamp()

def startTranscribing(last_chunk_timstamp):
	is_transcribing = True
	return None

def newChunkReceieved(new_chunk_timestamp):
	print(new_chunk_timestamp)

def streamingChange(checkbox_value):
	print(checkbox_value)
	return gr.Audio(streaming=checkbox_value)

def get_recording_files():
	return [os.path.abspath('./recordings/'+x) for x in os.listdir('./recordings')]


with gr.Blocks(head=shortcut_js) as demo:
	
	with gr.Tab("All In One"):
		gr.Markdown(title)
		with gr.Row(variant="panel"):
			aio_model = gr.Dropdown(choices=["whisper-1"], label="Model", value="whisper-1")
			aio_response_type = gr.Dropdown(choices=["json", "text", "srt", "verbose_json", "vtt"], label="Response Type", value="text")

		with gr.Row():
			aio_audio = gr.Audio(sources=["microphone"], type="filepath", show_download_button=True, streaming=True, elem_id="aio_audio")
			aio_streaming_checkbox = gr.Checkbox(value=True, label="Streaming audio")
			#aio_audio_batch = gr.Audio(sources=["microphone"], type="filepath", show_download_button=True, streaming=False, visible=False, elem_id="aio_audio")
			aio_file = gr.UploadButton(file_types=[".mp3", ".wav"], label="Select File", type="filepath")

		with gr.Row():
			aio_last_chunk = gr.Textbox(value=None, interactive=False, placeholder="Not run yet", label="Timestamp of last chunk")
			
			aio_submit_button = gr.Button(value="Transcribe and Process", interactive=True, elem_id="aio_submit_button")
			#aio_submit_button_batch = gr.Button(value="Transcribe and Process", interactive=True, visible=False, elem_id="aio_submit_button")

		aio_output_audio = gr.Audio(value=None, visible=True, label='Submitted audio')

		aio_output_text = gr.Markdown(label="Output Text")

		aio_process_type = gr.Dropdown(choices=list(process_types.keys()), label="Process Type", value=last_process_type)
		aio_process_button = gr.Button(value="Reprocess")
		aio_always_process_checkbox = gr.Checkbox(label="Process Automatically?", value=True, visible=False)

		aio_processed_text = gr.Markdown(label="Processed Text")
		aio_state = gr.State()

		aio_files = gr.Files(value=get_recording_files())

		aio_streaming_checkbox.change(fn=streamingChange, inputs=[aio_streaming_checkbox], outputs=[aio_audio])
		aio_audio.stream(fn=streamingAudio, inputs=[aio_state, aio_audio], outputs=[aio_state])
		aio_audio.stream(fn=streamingAudioUpdateTimestamp, inputs=None, outputs=[aio_last_chunk])
		aio_submit_button.click(fn=transcript, inputs=[aio_audio, aio_model, aio_response_type, aio_always_process_checkbox, aio_process_type, aio_streaming_checkbox, aio_state], outputs=[aio_output_text, aio_output_audio], api_name=False)
		#aio_audio.stop_recording(fn=transcript, inputs=[aio_audio, aio_model, aio_response_type, aio_always_process_checkbox, aio_process_type, aio_state], outputs=aio_output_text, api_name=False)
		#aio_audio.stop_recording(fn=recordingStopped, inputs=[aio_audio], outputs=[aio_submit_button])
		aio_file.upload(fn=transcript, inputs=[aio_file, aio_model, aio_response_type, aio_always_process_checkbox, aio_process_type, aio_streaming_checkbox, aio_state], outputs=aio_output_text)
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
			t_audio = gr.Audio(sources=["microphone"], show_download_button=True, streaming=True, type="filepath", elem_id="t_audio")
			t_file = gr.UploadButton(file_types=[".mp3", ".wav"], label="Select File", type="filepath")

		with gr.Row():
			t_submit_button = gr.Button(value="Transcribe", elem_id="t_submit_button")
			t_last_chunk = gr.Textbox(value="Not run yet", interactive=False)
			t_audio_stopped_time = gr.Textbox(value="Not run yet", interactive=False)
			t_streaming_checkbox = gr.Checkbox(value=True, label="Streaming audio")
		t_always_process_checkbox = gr.Checkbox(visible=False, value=False)
		t_process_type = gr.Dropdown(choices=list(process_types.keys()), label="Process Type", value=last_process_type, visible=False)
		

		t_output_text = gr.Markdown(label="Output Text")
		t_state = gr.State()

		t_streaming_checkbox.change(fn=streamingChange, inputs=[t_streaming_checkbox], outputs=[t_audio])
		t_audio.stop_recording(fn=stopTranscribing, inputs=[t_last_chunk], outputs=[t_audio_stopped_time])
		t_audio.start_recording(fn=startTranscribing, inputs=[t_last_chunk], outputs=[t_audio_stopped_time])
		#t_last_chunk.change(fn=newChunkReceieved, inputs=p[])
		t_audio.stream(fn=streamingAudio, inputs=[t_state, t_audio], outputs=[t_state, t_last_chunk])
		#t_audio.stop_recording(fn=transcript, inputs=[t_audio, t_model, t_response_type, t_always_process_checkbox, t_process_type, t_state], outputs=t_output_text, api_name=False)
		t_file.upload(fn=transcript, inputs=[t_file, t_model, t_response_type, t_always_process_checkbox, t_process_type, t_streaming_checkbox, t_state], outputs=t_output_text)
		t_submit_button.click(fn=transcript, inputs=[t_audio, t_model, t_response_type, t_always_process_checkbox, t_process_type, t_streaming_checkbox, t_state], outputs=t_output_text, api_name=False)
		#t_process_button.click(fn=process, inputs=[t_output_text, t_process_type], outputs=t_processed_text)
		#aio_always_process_checkbox.change(fn=checkbox_change, inputs=[always_process_checkbox], outputs=[process_button])
		

	


demo.launch(server_port=7860)
