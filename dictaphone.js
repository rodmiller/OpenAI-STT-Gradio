let audioChunks = [];
let recorder;
let audioBlob;
let audioUrl;
let audio;
let audioContext;
let audioSource;
let analyser;
let dataArray;
let bufferLength;
let canvas = document.getElementById('waveform');
let canvasCtx = canvas.getContext('2d');
let isRecording = false;
let isPlaying = false;
let totalTime = 0;
let currentTime = 0;

document.getElementById('record').addEventListener('click', startRecording);
document.getElementById('stop').addEventListener('click', stopRecording);
document.getElementById('play').addEventListener('click', playAudio);
document.getElementById('pause').addEventListener('click', pauseAudio);
document.getElementById('rewind').addEventListener('click', rewindAudio);
document.getElementById('fastForward').addEventListener('click', fastForwardAudio);
document.getElementById('save').addEventListener('click', saveRecording);

document.addEventListener('keydown', handleKeydown);

function handleKeydown(event) {
    switch(event.key) {
        case 'r':
            startRecording();
            break;
        case 's':
            stopRecording();
            break;
        case 'p':
            playAudio();
            break;
        case ' ':
            pauseAudio();
            break;
        case 'ArrowLeft':
            rewindAudio();
            break;
        case 'ArrowRight':
            fastForwardAudio();
            break;
        case 'S':
            if (event.ctrlKey) {
                event.preventDefault();
                saveRecording();
            }
            break;
    }
}

function startRecording() {
    if (isRecording) return;
    isRecording = true;
    audioChunks = [];
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            recorder = new MediaRecorder(stream);
            recorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };
            recorder.onstop = () => {
                audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                audioUrl = URL.createObjectURL(audioBlob);
                audio = new Audio(audioUrl);
                audio.onloadedmetadata = () => {
                    totalTime = audio.duration;
                    document.getElementById('totalTime').textContent = formatTime(totalTime);
                };
                initAudioContext();
            };
            recorder.start();
        });
}

function stopRecording() {
    if (!isRecording) return;
    isRecording = false;
    recorder.stop();
}

function playAudio() {
    if (isPlaying || !audioUrl) return;
    isPlaying = true;
    audioContext.resume();
    audio.play();
    audio.addEventListener('timeupdate', updateTimer);
}

function pauseAudio() {
    if (!isPlaying) return;
    isPlaying = false;
    audio.pause();
    audioContext.suspend();
}

function rewindAudio() {
    if (!audioUrl) return;
    audio.currentTime = Math.max(0, audio.currentTime - 5);
}

function fastForwardAudio() {
    if (!audioUrl) return;
    audio.currentTime = Math.min(totalTime, audio.currentTime + 5);
}

function updateTimer() {
    currentTime = audio.currentTime;
    document.getElementById('currentTime').textContent = formatTime(currentTime);
    drawWaveform();
}

function formatTime(time) {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

function initAudioContext() {
    audioContext = new AudioContext();
    audioSource = audioContext.createMediaElementSource(audio);
    analyser = audioContext.createAnalyser();
    audioSource.connect(analyser);
    analyser.connect(audioContext.destination);
    analyser.fftSize = 2048;
    bufferLength = analyser.frequencyBinCount;
    dataArray = new Uint8Array(bufferLength);
}

function drawWaveform() {
    if (!analyser) return;
    requestAnimationFrame(drawWaveform);
    analyser.getByteTimeDomainData(dataArray);
    canvasCtx.fillStyle = 'white';
    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = 'black';
    canvasCtx.beginPath();
    const sliceWidth = canvas.width / bufferLength;
    let x = 0;
    for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * canvas.height / 2;
        if (i === 0) {
            canvasCtx.moveTo(x, y);
        } else {
            canvasCtx.lineTo(x, y);
        }
        x += sliceWidth;
    }
    canvasCtx.lineTo(canvas.width, canvas.height / 2);
    canvasCtx.stroke();
}

function saveRecording() {
    if (!audioBlob) return;
    const wavUrl = URL.createObjectURL(audioBlob);
    const a = document.getElementById('downloadLink');
    a.style.display = 'block';
    a.href = wavUrl;
    a.download = 'recording.wav';
    a.textContent = 'Download recording';
    a.click();
}
