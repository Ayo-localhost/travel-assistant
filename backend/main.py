from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import logging
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import storage
from google.cloud import dialogflowcx_v3beta1 as dialogflow_cx
from google.api_core.client_options import ClientOptions
import os
import json
import tempfile
import uuid
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# Dialogflow CX Configuration
PROJECT_ID = "codematic-playground"  # Extracted from your agent URL
AGENT_ID = "10a6c174-ed65-4549-894d-eaa4dfa3d432"  # Extracted from your agent URL
REGION = "global"  # Extracted from your agent URL
LANGUAGE_CODE = "en-US"


# WHATSAPP CONFIGURATION
WHATSAPP_TOKEN="EAAPnZBCqPuu0BPFdXrKko0W4xUhbUt2rLmysynYDvKJmdaUWnGzLT2I3oKJevRTYXE3H1jdrfb8oZCTDz3p9TMihWZBye7bEmZCZA66k2VhZAuMAbPsBP5vLkQrUMpLGoOCgPq4au8Qf6zASFHAbL13u3NP5lwJrStZATkL9bcCJZCRCRcVTWrbweuEgqDjvpablDy7pyV1PjkEevm7ZC4adu1FZB66v7ZBX7U8CqYNKbN0"
VERIFY_TOKEN = "TEAMCARTRANDOMVERIFYTOKEN"
PHONENUMBER_ID = "732548379943793"

# Configure the Dialogflow CX client
if REGION and REGION != "global":
    client_options = ClientOptions(api_endpoint=f"{REGION}-dialogflow.googleapis.com:443")
else:
    client_options = None

# Initialize Dialogflow CX SessionsClient
session_client = dialogflow_cx.SessionsClient(client_options=client_options)

# Google Sheets configuration
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Sheet URLs and their corresponding GIDs
SHEET_CONFIG = {
    'events': {
        'sheet_id': '1WsNwax2gx0VU9NuOglWo8D03VRCrrvccko3p5o0ScxA',
        'gid': '70548245'
    },
    'accommodations': {
        'sheet_id': '1WsNwax2gx0VU9NuOglWo8D03VRCrrvccko3p5o0ScxA',
        'gid': '0'
    },
    'outfits': {
        'sheet_id': '1WsNwax2gx0VU9NuOglWo8D03VRCrrvccko3p5o0ScxA',
        'gid': '1993037430'
    }
}

class GoogleSheetsDataStore:
    def __init__(self):
        self.gc = None
        self._initialize_sheets_client()
    
    def _download_service_account_from_gcs(self):
        """Download service account key from Google Cloud Storage"""
        try:
            # GCS bucket and file details
            bucket_name = 'travel-assistant-demo'
            blob_name = 'service-account-key.json'
            
            # Initialize storage client (uses default credentials or ADC)
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # Download to temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False)
            blob.download_to_filename(temp_file.name)
            
            logging.info(f"Successfully downloaded service account key from GCS: gs://{bucket_name}/{blob_name}")
            return temp_file.name
            
        except Exception as e:
            logging.error(f"Failed to download service account key from GCS: {e}")
            return None
    
    def _initialize_sheets_client(self):
        """Initialize Google Sheets client with service account credentials"""
        try:
            creds = None
            temp_file_path = None
            
            # Method 1: Try to download from GCS
            temp_file_path = self._download_service_account_from_gcs()
            if temp_file_path and os.path.exists(temp_file_path):
                creds = Credentials.from_service_account_file(temp_file_path, scopes=SCOPES)
                logging.info("Loaded credentials from GCS")
                
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
            # Method 2: Try local service account file (fallback)
            elif not creds:
                creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service-account-key.json')
                if os.path.exists(creds_file):
                    creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
                    logging.info("Loaded credentials from local file")
            
            # Method 3: Try environment variables (fallback)
            if not creds:
                creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
                if creds_json:
                    creds_info = json.loads(creds_json)
                    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
                    logging.info("Loaded credentials from environment variables")
            
            if not creds:
                raise Exception("No Google Service Account credentials found in GCS, local file, or environment variables")
            
            self.gc = gspread.authorize(creds)
            logging.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize Google Sheets client: {e}")
            self.gc = None
    
    def _get_sheet_data(self, sheet_type):
        """Get data from a specific Google Sheet"""
        if not self.gc:
            logging.error("Google Sheets client not initialized")
            return []
        
        try:
            config = SHEET_CONFIG[sheet_type]
            sheet_id = config['sheet_id']
            gid = config['gid']
            
            # Open the spreadsheet and specific worksheet
            spreadsheet = self.gc.open_by_key(sheet_id)
            worksheet = spreadsheet.get_worksheet_by_id(int(gid))
            
            # Get all records as dictionaries
            records = worksheet.get_all_records()
            
            # Convert keys to lowercase with underscores
            normalized_records = []
            for record in records:
                normalized_record = {}
                for key, value in record.items():
                    normalized_key = key.lower().replace(' ', '_').replace('-', '_')
                    normalized_record[normalized_key] = value
                normalized_records.append(normalized_record)
            
            logging.info(f"Successfully loaded {len(normalized_records)} records from {sheet_type} sheet")
            return normalized_records
            
        except Exception as e:
            logging.error(f"Error loading {sheet_type} data from Google Sheets: {e}")
            return []
    
    def get_current_week_events(self, filters=None):
        """Get events for current week with optional filters"""
        events = self._get_sheet_data('events')
        
        current_date = datetime.now()
        week_end = current_date + timedelta(days=7)
        
        filtered_events = []
        for event in events:
            try:
                # Handle different date formats
                date_str = str(event.get('date', '')).strip()
                if not date_str or date_str.lower() in ['', 'tbd', 'n/a']:
                    continue
                
                # Try different date formats
                event_date = None
                for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                    try:
                        event_date = datetime.strptime(date_str, date_format)
                        break
                    except ValueError:
                        continue
                
                if not event_date:
                    continue
                
                # Filter by current week
                if current_date <= event_date <= week_end:
                    # Apply additional filters if provided
                    if filters:
                        if filters.get('area') and str(event.get('area', '')).lower() != filters['area'].lower():
                            continue
                        if filters.get('event_type') and str(event.get('event_type', '')).lower() != filters['event_type'].lower():
                            continue
                    
                    filtered_events.append(event)
                    
            except (ValueError, KeyError, TypeError) as e:
                logging.debug(f"Skipping event due to date parsing error: {e}")
                continue
        
        # Sort by date and return top 3
        def get_sort_date(event):
            try:
                date_str = str(event.get('date', '')).strip()
                for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                    try:
                        return datetime.strptime(date_str, date_format)
                    except ValueError:
                        continue
                return datetime.min
            except:
                return datetime.min
        
        filtered_events.sort(key=get_sort_date)
        return filtered_events[:3]
    
    def get_accommodations(self, filters=None):
        """Get accommodation options with filters"""
        accommodations = self._get_sheet_data('accommodations')
        
        filtered_accommodations = []
        
        for accommodation in accommodations:
            # Apply filters
            if filters:
                if filters.get('area') and str(accommodation.get('area', '')).lower() != filters['area'].lower():
                    continue
                    
                if filters.get('max_budget'):
                    try:
                        price_str = str(accommodation.get('price_per_night', '0')).replace(',', '').replace('₦', '').strip()
                        price = float(price_str)
                        if price > filters['max_budget']:
                            continue
                    except (ValueError, TypeError):
                        continue
                        
                if filters.get('type') and str(accommodation.get('type', '')).lower() != filters['type'].lower():
                    continue
            
            filtered_accommodations.append(accommodation)
        
        # Sort by rating and return top 3
        def get_rating(accommodation):
            try:
                rating_str = str(accommodation.get('rating', '0')).strip()
                return float(rating_str)
            except (ValueError, TypeError):
                return 0.0
        
        filtered_accommodations.sort(key=get_rating, reverse=True)
        return filtered_accommodations[:3]
    
    def get_outfit_suggestions(self, event_type, gender=None):
        """Get outfit suggestions for specific event types"""
        outfits = self._get_sheet_data('outfits')
        
        filtered_outfits = []
        
        for outfit in outfits:
            # Filter by event type and gender
            outfit_event_type = str(outfit.get('event_type', '')).lower()
            outfit_gender = str(outfit.get('gender', '')).lower()
            
            if outfit_event_type == event_type.lower():
                if not gender or outfit_gender == gender.lower() or outfit_gender == 'unisex':
                    filtered_outfits.append(outfit)
        
        return filtered_outfits[:3]

# Initialize data store
data_store = GoogleSheetsDataStore()

def format_events_response(events):
    """Format events data for Dialogflow response"""
    if not events:
        return "I couldn't find any events for this week. Check back soon for updates! 🎉"
    
    response_text = "Here are the hottest events this week:\n\n"
    
    for i, event in enumerate(events, 1):
        event_type = str(event.get('event_type', '')).lower()
        emoji = "🎵" if 'concert' in event_type else "🏖️" if 'beach' in event_type else "🔥"
        
        response_text += f"{emoji} **{event.get('title', 'Event')}**\n"
        response_text += f"📅 {event.get('date', 'TBD')} at {event.get('time', 'TBD')}\n"
        response_text += f"📍 {event.get('location', 'TBD')}, {event.get('area', 'Lagos')}\n"
        response_text += f"✨ Vibe: {event.get('vibe', 'Amazing')}\n\n"
    
    response_text += "Want to filter by location, date, or event type? Or need outfit inspiration for any of these? 👗"
    
    return response_text

def format_accommodation_response(accommodations):
    """Format accommodation data for Dialogflow response"""
    if not accommodations:
        return "Sorry, I couldn't find available accommodations right now. Try adjusting your filters! 🏨"
    
    response_text = "Here are top-rated places to stay:\n\n"
    
    for accommodation in accommodations:
        acc_type = str(accommodation.get('type', '')).lower()
        type_emoji = "🏨" if 'hotel' in acc_type else "🏠" if 'shortlet' in acc_type else "🏡"
        
        response_text += f"{type_emoji} **{accommodation.get('name', 'Accommodation')}**\n"
        response_text += f"📍 {accommodation.get('area', 'Lagos')} | ₦{accommodation.get('price_per_night', 'TBD')}/night\n"
        
        features = str(accommodation.get('features', ''))
        if features and features.lower() not in ['', 'n/a', 'none']:
            features_list = features.split(',')[:3]
            features_text = ", ".join([f.strip() for f in features_list])
            response_text += f"✨ {features_text}\n"
        
        response_text += f"⭐ {accommodation.get('rating', 'N/A')}/5.0\n\n"
    
    response_text += "Want to filter by area, budget, or accommodation type? 🔍"
    
    return response_text

def format_outfit_response(outfits, event_type):
    """Format outfit suggestions for response"""
    if not outfits:
        return f"I don't have outfit suggestions for {event_type} right now, but I'm always updating my style database! 💫"
    
    response_text = f"Perfect! Here are stunning {event_type} looks:\n\n"
    
    for i, outfit in enumerate(outfits, 1):
        gender = str(outfit.get('gender', '')).lower()
        gender_emoji = "👩🏽" if gender == 'female' else "👨🏽" if gender == 'male' else "👤"
        
        response_text += f"{gender_emoji} **Look {i}: {outfit.get('style_name', 'Style')}**\n"
        response_text += f"🔸 {outfit.get('description', 'Stylish look')}\n"
        
        items = str(outfit.get('items', ''))
        if items and items.lower() not in ['', 'n/a', 'none']:
            items_list = items.split(',')[:3]
            items_text = " + ".join([item.strip() for item in items_list])
            response_text += f"🔸 {items_text}\n"
        
        response_text += f"🔸 Vibe: {outfit.get('vibe', 'Amazing')}\n\n"
    
    response_text += "Want to see couple's fits, shop these looks, or try a different style? 💑🛍️"
    
    return response_text

@app.route('/chat', methods=['POST'])
def chat_with_agent():
    """
    New endpoint: Receives a message from frontend, sends it to Dialogflow CX agent,
    and returns the agent's response. The agent will call the webhook if needed.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        user_message = data.get('message')
        user_id = data.get('user_id', str(uuid.uuid4()))  # Generate unique session if not provided

        if not user_message:
            return jsonify({"error": "Message field is required"}), 400

        # Create unique session ID for this user
        session_id = f"session-{user_id}"
        
        # Construct the session path for Dialogflow CX
        session_path = session_client.session_path(PROJECT_ID, REGION, AGENT_ID, session_id)

        # Create a TextInput object
        text_input = dialogflow_cx.types.TextInput(text=user_message)

        # Create a QueryInput object with language_code
        query_input = dialogflow_cx.types.QueryInput(
            text=text_input,
            language_code=LANGUAGE_CODE
        )

        # Send the query to Dialogflow CX
        response = session_client.detect_intent(
            request={"session": session_path, "query_input": query_input}
        )

        # Extract the fulfillment text from Dialogflow CX's response
        fulfillment_texts = [
            message.text.text[0]
            for message in response.query_result.response_messages
            if message.text.text
        ]
        fulfillment_text = " ".join(fulfillment_texts)

        # Log the interaction
        logging.info(f"User Query: {response.query_result.text}")
        logging.info(f"Detected Intent: {response.query_result.match.intent.display_name if response.query_result.match.intent else 'N/A'}")
        logging.info(f"Confidence: {response.query_result.match.confidence if response.query_result.match.intent else 'N/A'}")
        logging.info(f"Agent Response: {fulfillment_text}")

        return jsonify({
            "response": fulfillment_text,
            "intent": response.query_result.match.intent.display_name if response.query_result.match.intent else None,
            "confidence": response.query_result.match.confidence if response.query_result.match.intent else None,
            "session_id": session_id
        })

    except Exception as e:
        logging.error(f"Error calling Dialogflow CX API: {e}")
        return jsonify({"error": f"Could not process your request: {str(e)}"}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook handler for all Dialogflow requests"""
    try:
        req = request.get_json()
        
        # Get intent information
        intent_name = req.get('intentInfo', {}).get('displayName', '')
        parameters = req.get('sessionInfo', {}).get('parameters', {})
        
        if 'events' in intent_name.lower():
            # Handle events inquiry
            filters = {}
            if 'area' in parameters:
                filters['area'] = parameters['area']
            if 'event_type' in parameters:
                filters['event_type'] = parameters['event_type']
            
            events = data_store.get_current_week_events(filters)
            response_text = format_events_response(events)
            
        elif 'accommodation' in intent_name.lower():
            # Handle accommodation inquiry
            filters = {}
            if 'area' in parameters:
                filters['area'] = parameters['area']
            if 'max_budget' in parameters:
                try:
                    filters['max_budget'] = float(parameters['max_budget'])
                except (ValueError, TypeError):
                    pass
            if 'accommodation_type' in parameters:
                filters['type'] = parameters['accommodation_type']
            
            accommodations = data_store.get_accommodations(filters)
            response_text = format_accommodation_response(accommodations)
            
        elif 'outfit' in intent_name.lower():
            # Handle outfit suggestions
            event_type = parameters.get('event_type', 'general')
            gender = parameters.get('gender')
            
            outfits = data_store.get_outfit_suggestions(event_type, gender)
            response_text = format_outfit_response(outfits, event_type)
            
        else:
            # Default/fallback response
            response_text = ("Hey there! 🌟 I'm your Lagos travel companion! I can help you find:\n\n"
                           "🔥 Events happening this week\n"
                           "🏠 Places to stay\n"
                           "👗 Outfit suggestions\n\n"
                           "What would you like to explore?")
        
        return jsonify({
            'fulfillmentResponse': {
                'messages': [
                    {
                        'text': {
                            'text': [response_text]
                        }
                    }
                ]
            }
        })
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({
            'fulfillmentResponse': {
                'messages': [
                    {
                        'text': {
                            'text': ['Sorry, I had trouble processing that. Please try again! 🔄']
                        }
                    }
                ]
            }
        })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Lagos Travel Guide - Google Sheets Version',
        'sheets_connected': data_store.gc is not None
    })

@app.route('/test-sheets', methods=['GET'])
def test_sheets():
    """Test endpoint to verify Google Sheets connection"""
    try:
        events = data_store._get_sheet_data('events')
        accommodations = data_store._get_sheet_data('accommodations')
        outfits = data_store._get_sheet_data('outfits')
        
        return jsonify({
            'status': 'success',
            'data_counts': {
                'events': len(events),
                'accommodations': len(accommodations),
                'outfits': len(outfits)
            },
            'sample_data': {
                'events': events[:1] if events else [],
                'accommodations': accommodations[:1] if accommodations else [],
                'outfits': outfits[:1] if outfits else []
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500



def send_template_message(recipient_phone_number):
    """
    Sends a WhatsApp template message using the Meta Graph API.

    Args:
        phone_number_id (str): The ID of your WhatsApp Business Account phone number.
        recipient_phone_number (str): The phone number of the recipient (e.g., "2348012345678").
    """

    url = f"https://graph.facebook.com/v20.0/{PHONENUMBER_ID}/messages"
    
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }

    data = {
        "messaging_product": "whatsapp",
        "to": recipient_phone_number,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {
                "code": "en_US"
            },
           
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        print("Message sent successfully!")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Response content: {response.text}")
        return None
    except requests.exceptions.ConnectionError as err:
        print(f"Error connecting to the server: {err}")
        return None
    except requests.exceptions.Timeout as err:
        print(f"The request timed out: {err}")
        return None
    except requests.exceptions.RequestException as err:
        print(f"An unexpected error occurred: {err}")
        return None


def send_whatsapp_text_message(phone_number_id, recipient_phone_number, message_text):
    """
    Sends a WhatsApp text message using the Meta Graph API.

    Args:
        phone_number_id (str): The ID of your WhatsApp Business Account phone number.
        recipient_phone_number (str): The phone number of the recipient (e.g., "2348012345678").
        message_text (str): The text message to send.
    """
    # Use v20.0 instead of v23.0 - your token might not support v23.0
    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
    
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }

    formatted_number = recipient_phone_number if recipient_phone_number.startswith('+') else f'+{recipient_phone_number}'
    logger.log(f"Sending WhatsApp message to {formatted_number}: {message_text}")

    data = {
        "messaging_product": "whatsapp",
        "to": formatted_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.log(f"WhatsApp message sent successfully to {recipient_phone_number}")
        return response.json()
    except requests.exceptions.RequestException as err:
        logger.error(f"Error sending WhatsApp message: {err}")
        if hasattr(err, 'response') and err.response:
            logger.error(f"Response content: {err.response.text}")
        return None

async def chat_with_dialogflow_cx(user_message, user_id):
    """
    Send a message to Dialogflow CX and get the response.
    
    Args:
        user_message (str): The message from the user
        user_id (str): Unique identifier for the user session
    
    Returns:
        str: The response from Dialogflow CX
    """
    try:
        # Create unique session ID for this user
        session_id = f"whatsapp-session-{user_id}"
        
        # Construct the session path for Dialogflow CX
        session_path = session_client.session_path(PROJECT_ID, REGION, AGENT_ID, session_id)

        # Create a TextInput object
        text_input = dialogflow_cx.types.TextInput(text=user_message)

        # Create a QueryInput object with language_code
        query_input = dialogflow_cx.types.QueryInput(
            text=text_input,
            language_code=LANGUAGE_CODE
        )

        # Send the query to Dialogflow CX
        response = session_client.detect_intent(
            request={"session": session_path, "query_input": query_input}
        )

        # Extract the fulfillment text from Dialogflow CX's response
        fulfillment_texts = [
            message.text.text[0]
            for message in response.query_result.response_messages
            if message.text.text
        ]
        fulfillment_text = " ".join(fulfillment_texts) if fulfillment_texts else "I'm sorry, I didn't understand that. Can you please rephrase?"

        # Log the interaction
        logger.log(f"WhatsApp User Query: {response.query_result.text}")
        logger.log(f"Detected Intent: {response.query_result.match.intent.display_name if response.query_result.match.intent else 'N/A'}")
        logger.log(f"Confidence: {response.query_result.match.confidence if response.query_result.match.intent else 'N/A'}")
        logger.log(f"Agent Response: {fulfillment_text}")

        return fulfillment_text

    except Exception as e:
        logger.error(f"Error calling Dialogflow CX API: {e}")
        return "I'm having trouble processing your request right now. Please try again later."

def chat_with_dialogflow_cx_sync(user_message, user_id):
    """
    Send a message to Dialogflow CX and get the response (synchronous version).
    
    Args:
        user_message (str): The message from the user
        user_id (str): Unique identifier for the user session
    
    Returns:
        str: The response from Dialogflow CX
    """
    try:
        # Create unique session ID for this user
        session_id = f"whatsapp-session-{user_id}"
        
        # Construct the session path for Dialogflow CX
        session_path = session_client.session_path(PROJECT_ID, REGION, AGENT_ID, session_id)

        # Create a TextInput object
        text_input = dialogflow_cx.types.TextInput(text=user_message)

        # Create a QueryInput object with language_code
        query_input = dialogflow_cx.types.QueryInput(
            text=text_input,
            language_code=LANGUAGE_CODE
        )

        # Send the query to Dialogflow CX
        response = session_client.detect_intent(
            request={"session": session_path, "query_input": query_input}
        )

        # Extract the fulfillment text from Dialogflow CX's response
        fulfillment_texts = [
            message.text.text[0]
            for message in response.query_result.response_messages
            if message.text.text
        ]
        fulfillment_text = " ".join(fulfillment_texts) if fulfillment_texts else "I'm sorry, I didn't understand that. Can you please rephrase?"

        # Log the interaction
        logger.log(f"WhatsApp User Query: {response.query_result.text}")
        logger.log(f"Detected Intent: {response.query_result.match.intent.display_name if response.query_result.match.intent else 'N/A'}")
        logger.log(f"Confidence: {response.query_result.match.confidence if response.query_result.match.intent else 'N/A'}")
        logger.log(f"Agent Response: {fulfillment_text}")

        return fulfillment_text

    except Exception as e:
        logger.error(f"Error calling Dialogflow CX API: {e}")
        return "I'm having trouble processing your request right now. Please try again later."


def process_message(message: dict, contact: dict = None):
    """
    Processes an individual incoming WhatsApp message and responds via Dialogflow CX.
    """
    logger.log("--- Processing Incoming WhatsApp Message ---")
    
    message_id = message.get('id')
    from_number = message.get('from')
    message_type = message.get('type')
    
    logger.log(f"Message ID: {message_id}")
    logger.log(f"From: {from_number}")
    logger.log(f"Type: {message_type}")

    if contact:
        logger.log(f"Contact Name: {contact.get('profile', {}).get('name')}")
        logger.log(f"Contact Wa_ID: {contact.get('wa_id')}")


    # Only handle text messages for now
    if message_type == 'text':
        user_message = message.get('text', {}).get('body', '')
        logger.log(f"Text Message: {user_message}")
        
        if user_message.strip():
            try:
                # Get response from Dialogflow CX (using sync version)
                dialogflow_response = chat_with_dialogflow_cx_sync(user_message, from_number)
                
                # Send response back to WhatsApp user
                send_result = send_whatsapp_text_message(
                    phone_number_id=PHONENUMBER_ID,
                    recipient_phone_number=from_number,
                    message_text=dialogflow_response
                )
                
                if send_result:
                    logger.log(f"Successfully responded to WhatsApp message from {from_number}")
                else:
                    logger.error(f"Failed to send WhatsApp response to {from_number}")
                    
            except Exception as e:
                logger.error(f"Error processing WhatsApp message: {e}")
                
                # Send error message back to user
                error_message = "Sorry, I'm having technical difficulties. Please try again later."
                try:
                    send_whatsapp_text_message(
                        phone_number_id=PHONENUMBER_ID,
                        recipient_phone_number=from_number,
                        message_text=error_message
                    )
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {send_error}")
        else:
            logger.warn("Received empty text message")
    else:
        # Handle non-text messages
        logger.log(f"Received non-text message of type: {message_type}")
        
        # Send a response asking for text input
        unsupported_message = "I can only handle text messages right now. Please send me a text message! 😊"
        
        try:
            send_whatsapp_text_message(
                phone_number_id=PHONENUMBER_ID,
                recipient_phone_number=from_number,
                message_text=unsupported_message
            )
        except Exception as send_error:
            logger.error(f"Failed to send unsupported message response: {send_error}")
    
    logger.log("-" * 50)

# Simulate a basic logger
class SimpleLogger:
    def log(self, message):
        print(f"[INFO] {message}")

    def warn(self, message):
        print(f"[WARN] {message}")

    def error(self, message, stack=None):
        print(f"[ERROR] {message}")
        if stack:
            print(f"Stack: {stack}")

    def debug(self, message):
        print(f"[DEBUG] {message}")

logger = SimpleLogger()

# --- Webhook GET Endpoint (Verification) ---
@app.route('/whatsapp/webhook', methods=['GET'])
def verify_webhook():
    """
    Handles the GET request for webhook verification.
    Meta sends a GET request to verify the webhook URL.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    logger.debug(
        f"Verifying webhook: mode={mode}, token={token}, expected={VERIFY_TOKEN},"
        f" challenge={challenge}"
    )

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        logger.log('Webhook verification successful')
        return challenge, 200 # Return challenge with 200 OK
    else:
        logger.warn('Webhook verification failed')
        return 'Verification failed', 403 # Return 403 Forbidden for failure

# --- Webhook POST Endpoint (Incoming Messages) ---
@app.route('/whatsapp/webhook', methods=['POST'])
def handle_webhook():
    """
    Handles POST requests from Meta when new messages or events occur.
    """
    payload = request.get_json()
    logger.log('Received webhook payload:')
    logger.log(json.dumps(payload, indent=2)) # Pretty print the payload for debugging

    try:
        if payload.get('object') != 'whatsapp_business_account':
            logger.warn(f"Received unexpected payload object: {payload.get('object')}")
            return jsonify({"status": "ignored", "reason": "unexpected object"}), 200

        for entry in payload.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') != 'messages':
                    continue

                value = change.get('value')
                if not value or not value.get('messages') or len(value['messages']) == 0:
                    continue

                for message in value['messages']:
                    # Extract contact info if available
                    contact = None
                    if value.get('contacts') and len(value['contacts']) > 0:
                        contact = value['contacts'][0]

                    # Process the message (this is where you'd add your main logic)
                    process_message(message, contact)

        return jsonify({"status": "success"}), 200 # Always return 200 OK to Meta
    except Exception as e:
        logger.error(
            f"Error handling webhook: {e}",
            getattr(e, 'args', None) # Get stack if available (basic attempt)
        )
        # Even on error, return 200 to Meta to prevent retries (handle errors internally)
        return jsonify({"status": "error", "message": str(e)}), 200




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)