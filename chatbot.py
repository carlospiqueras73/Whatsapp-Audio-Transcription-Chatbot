"""
Whatsapp ChatBot Transcriber code in Python
Author: Carlos Piqueras
"""

# Import necessary libraries
from flask import Flask, jsonify, request
from heyoo import WhatsApp
import requests
from google.cloud import speech

# Meta Bearer token
token = '** Your Meta Bearer Token **'

# Initialize Flask application
app = Flask(__name__)

# Main endpoint to receive messages
@app.route("/webhook/", methods = ["POST", "GET"])
def webhook_whatsapp():
    # To verify facebook webhook
    if request.method == "GET":
        # Check that the token is correct
        if request.args.get('hub.verify_token') == '** Your Webhook verifying token **':
            # Return correct work for secure connection
            return request.args.get('hub.challenge')
        else:
            # If the token is not correct, return error
            return "Authentication Error!"
    
    # If we receieve a message (POST)
    else:
        # Receive the data sent from the whatsapp API
        data = request.get_json()

        # Extract phone number from the json file
        phone = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
        try:
            # Extract audio id from the json file
            audio_id = data['entry'][0]['changes'][0]['value']['messages'][0]['audio']['id']
            # Use the facebook Media API to get the audio message info
            audio=requests.get(f"https://graph.facebook.com/v13.0/{audio_id}", headers={"Authorization": f"Bearer {token}"}).json()
            # Extract the url from the audio info
            audio_url = audio['url']
            # Use the URL and the TOKEN to retrieve the audio message
            response = requests.get(audio_url, headers={"Authorization": f"Bearer {token}"}, data={})

            # Select audio content to transcribe
            google_audio = speech.RecognitionAudio(content=response.content)
            # For the configuration: this example is using Spanish, and the encoding is for matching the Whatsapp format
            google_config = speech.RecognitionConfig(language_code="es-ES", encoding='OGG_OPUS', sample_rate_hertz=16000, enable_automatic_punctuation=True)
            # Call Google Cloud API
            transcript_results = speech_to_text(google_config, google_audio)

            # Transcript result
            transcript = transcript_results[0].alternatives[0].transcript
            # Confidence of the transcription (in case you want it for something)
            confidence = transcript_results[0].alternatives[0].confidence

            # Reply to the sender with the transcript of the audio
            send_message(phone,transcript)

        # If there is no audio in the message, the previous block will generate an exception
        except:
            # Reply to the sender with the error message
            send_message(phone,"Sorry, I can only transcribe audios!")
            # Return status code
            return jsonify({"status": "error"}, 400)
        # If no exception has been raised
        else:
            # Return status code
            return jsonify({"status": "success"}, 200)

def send_message(phonenumber,message) -> None:
    """
    Function for sending messages through the Whatsapp ChatBot interface
    """
    # ChatBot phone number id
    chatbot_id = '** Your ChatBot ID **'
    # Initialize the message
    whatsapp_message = WhatsApp(token,chatbot_id)
    # Send the message
    whatsapp_message.send_message(message,phonenumber)

def speech_to_text(config: speech.RecognitionConfig, audio: speech.RecognitionAudio) -> speech.RecognizeResponse:
    """
    Function for calling GCP speech-to-text API
    """
    # Generate connection
    client = speech.SpeechClient.from_service_account_file('key.json')
    # Synchronous speech recognition request
    response = client.recognize(config=config, audio=audio)
    # Return results
    return response.results

# Start the flask application
if __name__ == "__main__":
    app.run(host = '0.0.0.0',
            port = 8080,
            debug = True)