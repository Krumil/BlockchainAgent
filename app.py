from agents import call_agent
from google.cloud import speech_v1p1beta1 as speech
from dotenv import load_dotenv
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
)
from PyQt5.QtCore import QSize
import sys
import os
import speech_recognition as sr
import io

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials.json"


class VoiceControlledChatbot(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(QSize(500, 500))
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Blockchain Agent")
        self.setStyleSheet(
            """
			QWidget {
				background-color: #FFF;
				color: #000;
			}
			"""
        )

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.chatbox = QTextEdit()
        self.chatbox.setReadOnly(True)
        self.chatbox.setStyleSheet(
            """
			QTextEdit {
				background-color: #FFF;
				border: 1px solid #CCC;
				border-radius: 10px;
				font-size: 16px;
				padding: 15px;
				color: #000;
			}
			"""
        )
        self.layout.addWidget(self.chatbox)

        self.speakButton = QPushButton("Speak")
        self.speakButton.clicked.connect(self.listen)
        self.speakButton.setStyleSheet(
            """
			QPushButton {
				background-color: #007BFF;
				border: none;
				font-size: 20px;
				padding: 15px;
				color: #FFF;
				border-radius: 20px;
			}
			QPushButton:hover {
				background-color: #0056b3;
			}
			"""
        )
        self.layout.addWidget(self.speakButton)

    def transcribe_audio_with_word_hints(self, audio_file, hints):
        client = speech.SpeechClient()

        content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,
            language_code="en-US",
            speech_contexts=[speech.SpeechContext(phrases=hints)],
        )

        response = client.recognize(config=config, audio=audio)

        for result in response.results:
            self.chatbox.append(f"You said: {result.alternatives[0].transcript}")
            self.chatbox.append(
                f"Bot said: {call_agent(result.alternatives[0].transcript)}"
            )

    def listen(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            audio = r.listen(source)
            print("Finished listening")

        audio_file = io.BytesIO(audio.get_wav_data())
        self.transcribe_audio_with_word_hints(audio_file, ["WETH", "USDC"])


if __name__ == "__main__":
    app = QApplication(sys.argv)

    chatbot = VoiceControlledChatbot()
    chatbot.show()

    sys.exit(app.exec_())
