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
import calendar
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# Dialogflow CX Configuration
PROJECT_ID = "codematic-playground"
AGENT_ID = "10a6c174-ed65-4549-894d-eaa4dfa3d432"
REGION = "global"
LANGUAGE_CODE = "en-US"

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


class DateRangeParser:
    """Utility class to parse various date range queries"""
    
    @staticmethod
    def parse_date_query(query_text):
        """Parse natural language date queries and return date range"""
        if not query_text:
            return None, None
            
        query_lower = query_text.lower()
        current_date = datetime.now()
        
        # Month name patterns
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Check for specific month queries
        for month_name, month_num in months.items():
            if month_name in query_lower:
                # Default to current year or next year if month has passed
                year = current_date.year
                if month_num < current_date.month:
                    year += 1
                
                # Get first and last day of the month
                start_date = datetime(year, month_num, 1)
                last_day = calendar.monthrange(year, month_num)[1]
                end_date = datetime(year, month_num, last_day)
                
                logging.info(f"Parsed month query: {month_name} -> {start_date} to {end_date}")
                return start_date, end_date
        
        # This week
        if 'this week' in query_lower or 'current week' in query_lower:
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)
            return week_start, week_end
        
        # Next week
        if 'next week' in query_lower:
            week_start = current_date + timedelta(days=7-current_date.weekday())
            week_end = week_start + timedelta(days=6)
            return week_start, week_end
        
        # This month
        if 'this month' in query_lower or 'current month' in query_lower:
            month_start = current_date.replace(day=1)
            next_month = month_start.replace(month=month_start.month % 12 + 1, day=1)
            month_end = next_month - timedelta(days=1)
            return month_start, month_end
        
        # Weekend patterns
        if 'weekend' in query_lower or 'this weekend' in query_lower:
            days_until_saturday = (5 - current_date.weekday()) % 7
            saturday = current_date + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            return saturday, sunday
        
        # Today/tomorrow patterns
        if 'today' in query_lower:
            return current_date, current_date
        
        if 'tomorrow' in query_lower:
            tomorrow = current_date + timedelta(days=1)
            return tomorrow, tomorrow
        
        # Default to current week if no specific date found
        logging.info("No specific date pattern found, defaulting to current week")
        week_end = current_date + timedelta(days=7)
        return current_date, week_end


class GoogleSheetsDataStore:
    def __init__(self):
        self.gc = None
        self._initialize_sheets_client()
    
    def _download_service_account_from_gcs(self):
        """Download service account key from Google Cloud Storage"""
        try:
            bucket_name = 'travel-assistant-demo'
            blob_name = 'service-account-key.json'
            
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
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
                raise Exception("No Google Service Account credentials found")
            
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
            
            spreadsheet = self.gc.open_by_key(sheet_id)
            worksheet = spreadsheet.get_worksheet_by_id(int(gid))
            
            records = worksheet.get_all_records()
            
            # Normalize keys
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
    
    def _normalize_area_value(self, area_value):
        """Normalize area values for comparison"""
        if not area_value:
            return None
        
        area_str = str(area_value).lower().strip()
        
        # Area mappings for flexible matching
        area_mappings = {
            'victoria_island': ['vi', 'victoria island', 'island', 'vic island', 'victoria_island'],
            'lekki': ['lekki', 'lekki phase 1', 'phase 1', 'admiralty', 'lekki_phase_1'],
            'ikeja': ['ikeja', 'mainland', 'gra', 'ikeja_gra'],
            'ikoyi': ['ikoyi', 'old ikoyi', 'banana island', 'banana_island'],
            'surulere': ['surulere', 'suru', 'national theatre area', 'national_theatre']
        }
        
        # Check for direct matches first
        for canonical, variations in area_mappings.items():
            if area_str in variations or area_str == canonical:
                return canonical
        
        return area_str
    
    def _parse_date_from_string(self, date_str):
        """Parse date string with multiple format support"""
        if not date_str or str(date_str).lower().strip() in ['', 'tbd', 'n/a', 'none']:
            return None
        
        date_str = str(date_str).strip()
        
        # Try different date formats
        date_formats = [
            '%Y-%m-%d',      # 2024-12-16
            '%d/%m/%Y',      # 16/12/2024
            '%m/%d/%Y',      # 12/16/2024
            '%d-%m-%Y',      # 16-12-2024
            '%Y/%m/%d',      # 2024/12/16
            '%d %B %Y',      # 16 December 2024
            '%B %d, %Y',     # December 16, 2024
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        
        logging.debug(f"Could not parse date: {date_str}")
        return None

    def _normalize_event_type(self, event_type_value):
        """Normalize event type values for flexible comparison."""
        if not event_type_value:
            return None

        event_str = str(event_type_value).lower().strip().replace(' ', '_')

        # Event type mappings
        event_mappings = {
            'concert': ['concert', 'music_show', 'show', 'live_music'],
            'beach_party': ['beach_party', 'beach', 'pool_party'],
            'club_night': ['club_night', 'club', 'party', 'turn_up'],
            'brunch': ['brunch', 'day_party'],
            'detty_december': ['detty_december', 'december_fest']
        }

        for canonical, variations in event_mappings.items():
            if event_str in variations:
                return canonical

        return event_str
        
    def get_events(self, filters=None, date_range=None):
        """Get events with improved filtering and date range support"""
        events = self._get_sheet_data('events')
        
        if not events:
            logging.warning("No events data found")
            return []
        
        filtered_events = []
        
        # Parse date range
        start_date, end_date = None, None
        if date_range:
            start_date, end_date = date_range
        elif filters and filters.get('query_text'):
            start_date, end_date = DateRangeParser.parse_date_query(filters['query_text'])
        
        logging.info(f"Filtering events with date range: {start_date} to {end_date}")
        
        for event in events:
            try:
                # Parse event date
                event_date = self._parse_date_from_string(event.get('date'))
                
                if not event_date:
                    logging.debug(f"Skipping event with unparseable date: {event.get('title', 'Unknown')}")
                    continue
                
                # Apply date range filter
                if start_date and end_date:
                    if not (start_date.date() <= event_date.date() <= end_date.date()):
                        continue
                
                # Apply area filter
                if filters and filters.get('area'):
                    event_area = self._normalize_area_value(event.get('area'))
                    filter_area = self._normalize_area_value(filters['area'])
                    
                    if event_area != filter_area:
                        logging.debug(f"Area filter mismatch: {event_area} != {filter_area}")
                        continue
                
                # Apply event type filter
                if filters and filters.get('event_type'):
                    event_type = str(event.get('event_type', '')).lower().strip()
                    filter_type = str(filters['event_type']).lower().strip()
                    
                    if event_type != filter_type:
                        logging.debug(f"Event type filter mismatch: {event_type} != {filter_type}")
                        continue
                
                filtered_events.append(event)
                
            except Exception as e:
                logging.debug(f"Error processing event: {e}")
                continue
        
        # Sort by date
        def get_sort_date(event):
            event_date = self._parse_date_from_string(event.get('date'))
            return event_date if event_date else datetime.min
        
        filtered_events.sort(key=get_sort_date)
        
        logging.info(f"Found {len(filtered_events)} events after filtering")
        return filtered_events[:5]  # Return top 5 instead of 3
    
    def get_accommodations(self, filters=None):
        """Get accommodation options with improved filters"""
        accommodations = self._get_sheet_data('accommodations')
        
        if not accommodations:
            logging.warning("No accommodations data found")
            return []
        
        filtered_accommodations = []
        
        for accommodation in accommodations:
            try:
                # Apply area filter
                if filters and filters.get('area'):
                    acc_area = self._normalize_area_value(accommodation.get('area'))
                    filter_area = self._normalize_area_value(filters['area'])
                    
                    if acc_area != filter_area:
                        logging.debug(f"Area filter mismatch: {acc_area} != {filter_area}")
                        continue
                
                # Apply budget filter
                if filters and filters.get('max_budget'):
                    try:
                        price_str = str(accommodation.get('price_per_night', '0')).replace(',', '').replace('₦', '').replace('NGN', '').strip()
                        # Extract numeric value from price string
                        price_match = re.search(r'(\d+(?:\.\d+)?)', price_str)
                        if price_match:
                            price = float(price_match.group(1))
                            if price > float(filters['max_budget']):
                                logging.debug(f"Budget filter: {price} > {filters['max_budget']}")
                                continue
                        else:
                            logging.debug(f"Could not parse price: {price_str}")
                    except (ValueError, TypeError) as e:
                        logging.debug(f"Error parsing price: {e}")
                        continue
                
                # Apply accommodation type filter
                if filters and filters.get('accommodation_type'):
                    acc_type = str(accommodation.get('type', '')).lower().strip()
                    filter_type = str(filters['accommodation_type']).lower().strip()
                    
                    if acc_type != filter_type:
                        logging.debug(f"Type filter mismatch: {acc_type} != {filter_type}")
                        continue
                
                filtered_accommodations.append(accommodation)
                
            except Exception as e:
                logging.debug(f"Error processing accommodation: {e}")
                continue
        
        # Sort by rating (descending)
        def get_rating(accommodation):
            try:
                rating_str = str(accommodation.get('rating', '0')).strip()
                rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_str)
                return float(rating_match.group(1)) if rating_match else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        filtered_accommodations.sort(key=get_rating, reverse=True)
        
        logging.info(f"Found {len(filtered_accommodations)} accommodations after filtering")
        return filtered_accommodations[:5]  # Return top 5
    
    def get_outfit_suggestions(self, event_type, gender=None):
        """Get outfit suggestions for specific event types"""
        outfits = self._get_sheet_data('outfits')
        
        if not outfits:
            logging.warning("No outfits data found")
            return []
        
        filtered_outfits = []
        filter_event_type = self._normalize_event_type(event_type) # Normalize the input
        
        for outfit in outfits:
            try:
                # Filter by event type
                outfit_event_type = self._normalize_event_type(outfit.get('event_type'))
                
                if outfit_event_type != filter_event_type:
                    continue
                
                # Filter by gender
                outfit_gender = str(outfit.get('gender', '')).lower().strip()
                
                if gender:
                    filter_gender = str(gender).lower().strip()
                    if outfit_gender != filter_gender and outfit_gender != 'unisex':
                        continue
                
                filtered_outfits.append(outfit)
                
            except Exception as e:
                logging.debug(f"Error processing outfit: {e}")
                continue
        
        logging.info(f"Found {len(filtered_outfits)} outfits after filtering")
        return filtered_outfits[:5]  # Return up to 5 outfits


# Initialize data store
data_store = GoogleSheetsDataStore()


def format_events_response(events, filters=None):
    """Format events data for Dialogflow response"""
    if not events:
        filter_info = ""
        if filters:
            if filters.get('area'):
                filter_info += f" in {filters['area'].title()}"
            if filters.get('event_type'):
                filter_info += f" for {filters['event_type'].replace('_', ' ').title()}"
        
        return f"I couldn't find any events{filter_info}. Try adjusting your search or check back soon! 🎉"
    
    response_text = "Here are the hottest events I found:\n\n"
    
    for i, event in enumerate(events, 1):
        event_type = str(event.get('event_type', '')).lower()
        emoji = "🎵" if 'concert' in event_type else "🏖️" if 'beach' in event_type else "🔥"
        
        response_text += f"{emoji} **{event.get('title', 'Event')}**\n"
        response_text += f"📅 {event.get('date', 'TBD')} at {event.get('time', 'TBD')}\n"
        response_text += f"📍 {event.get('location', 'TBD')}, {event.get('area', 'Lagos')}\n"
        response_text += f"✨ Vibe: {event.get('vibe', 'Amazing')}\n\n"
    
    response_text += "Want to filter by location, date, or event type? Or need outfit inspiration? 👗"
    
    return response_text


def format_accommodation_response(accommodations, filters=None):
    """Format accommodation data for Dialogflow response"""
    if not accommodations:
        filter_info = ""
        if filters:
            if filters.get('area'):
                filter_info += f" in {filters['area'].title()}"
            if filters.get('max_budget'):
                filter_info += f" under ₦{filters['max_budget']}"
        
        return f"Sorry, I couldn't find available accommodations{filter_info}. Try adjusting your filters! 🏨"
    
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
        return f"I don't have outfit suggestions for {event_type.replace('_', ' ')} right now, but I'm always updating my style database! 💫"
    
    response_text = f"Perfect! Here are stunning {event_type.replace('_', ' ')} looks:\n\n"
    
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
    Endpoint: Receives a message from frontend, sends it to Dialogflow CX agent,
    and returns the agent's response.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        user_message = data.get('message')
        user_id = data.get('user_id', str(uuid.uuid4()))

        if not user_message:
            return jsonify({"error": "Message field is required"}), 400

        session_id = f"session-{user_id}"
        session_path = session_client.session_path(PROJECT_ID, REGION, AGENT_ID, session_id)

        text_input = dialogflow_cx.types.TextInput(text=user_message)
        query_input = dialogflow_cx.types.QueryInput(
            text=text_input,
            language_code=LANGUAGE_CODE
        )

        response = session_client.detect_intent(
            request={"session": session_path, "query_input": query_input}
        )

        fulfillment_texts = [
            message.text.text[0]
            for message in response.query_result.response_messages
            if message.text.text
        ]
        fulfillment_text = " ".join(fulfillment_texts)

        logging.info(f"User Query: {response.query_result.text}")
        logging.info(f"Detected Intent: {response.query_result.match.intent.display_name if response.query_result.match.intent else 'N/A'}")
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
        
        # Get intent information and query text
        intent_name = req.get('intentInfo', {}).get('displayName', '')
        parameters = req.get('sessionInfo', {}).get('parameters', {})
        query_text = req.get('text', '')  # Original user query for date parsing
        
        logging.info(f"Webhook called with intent: {intent_name}")
        logging.info(f"Parameters: {parameters}")
        logging.info(f"Query text: {query_text}")
        
        if 'events' in intent_name.lower():
            # Handle events inquiry
            filters = {'query_text': query_text}  # Include original query for date parsing
            
            if 'area' in parameters and parameters['area']:
                filters['area'] = parameters['area']
                logging.info(f"Applied area filter: {parameters['area']}")
            
            if 'event_type' in parameters and parameters['event_type']:
                filters['event_type'] = parameters['event_type']
                logging.info(f"Applied event type filter: {parameters['event_type']}")
            
            events = data_store.get_events(filters)
            response_text = format_events_response(events, filters)
            
        elif 'accommodation' in intent_name.lower():
            # Handle accommodation inquiry
            filters = {}
            
            if 'area' in parameters and parameters['area']:
                filters['area'] = parameters['area']
                logging.info(f"Applied area filter: {parameters['area']}")
            
            if 'max_budget' in parameters and parameters['max_budget']:
                try:
                    filters['max_budget'] = float(parameters['max_budget'])
                    logging.info(f"Applied budget filter: {parameters['max_budget']}")
                except (ValueError, TypeError):
                    logging.warning(f"Invalid budget value: {parameters['max_budget']}")
            
            if 'accommodation_type' in parameters and parameters['accommodation_type']:
                filters['accommodation_type'] = parameters['accommodation_type']
                logging.info(f"Applied accommodation type filter: {parameters['accommodation_type']}")
            
            accommodations = data_store.get_accommodations(filters)
            response_text = format_accommodation_response(accommodations, filters)
            
        elif 'outfit' in intent_name.lower():
            # Handle outfit suggestions
            event_type = parameters.get('event_type', 'general')
            gender = parameters.get('gender')
            
            logging.info(f"Getting outfits for event_type: {event_type}, gender: {gender}")
            
            outfits = data_store.get_outfit_suggestions(event_type, gender)
            response_text = format_outfit_response(outfits, event_type)
            
        else:
            # Default/fallback response
            response_text = ("Hey there! 🌟 I'm your Lagos travel companion! I can help you find:\n\n"
                           "🔥 Events happening this week, month, or any specific time\n"
                           "🏠 Places to stay in any area of Lagos\n"
                           "👗 Outfit suggestions for any event\n\n"
                           "Try asking: 'What events are in October?' or 'Show me hotels in Lekki under 30000'")
        
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
        'service': 'Lagos Travel Guide - Enhanced Version',
        'sheets_connected': data_store.gc is not None
    })


@app.route('/test-sheets', methods=['GET'])
def test_sheets():
    """Test endpoint to verify Google Sheets connection and filtering"""
    try:
        # Test basic data loading
        events = data_store._get_sheet_data('events')
        accommodations = data_store._get_sheet_data('accommodations')
        outfits = data_store._get_sheet_data('outfits')
        
        # Test filtering
        test_filters = {
            'area': 'lekki',
            'event_type': 'concert'
        }
        
        filtered_events = data_store.get_events(test_filters)
        
        # Test accommodation filtering
        acc_filters = {
            'area': 'victoria_island',
            'max_budget': 50000
        }
        
        filtered_accommodations = data_store.get_accommodations(acc_filters)
        
        # Test date range parsing
        date_parser = DateRangeParser()
        october_range = date_parser.parse_date_query("events in october")
        
        return jsonify({
            'status': 'success',
            'data_counts': {
                'events': len(events),
                'accommodations': len(accommodations),
                'outfits': len(outfits)
            },
            'filtered_results': {
                'events_in_lekki_concerts': len(filtered_events),
                'accommodations_vi_under_50k': len(filtered_accommodations)
            },
            'date_parsing_test': {
                'october_range': {
                    'start': october_range[0].isoformat() if october_range[0] else None,
                    'end': october_range[1].isoformat() if october_range[1] else None
                }
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


@app.route('/test-filters', methods=['POST'])
def test_filters():
    """Test endpoint to debug filtering issues"""
    try:
        data = request.get_json()
        filter_type = data.get('type', 'events')  # events, accommodations, outfits
        filters = data.get('filters', {})
        
        if filter_type == 'events':
            results = data_store.get_events(filters)
        elif filter_type == 'accommodations':
            results = data_store.get_accommodations(filters)
        elif filter_type == 'outfits':
            event_type = filters.get('event_type', 'general')
            gender = filters.get('gender')
            results = data_store.get_outfit_suggestions(event_type, gender)
        else:
            return jsonify({'error': 'Invalid filter type'}), 400
        
        return jsonify({
            'filter_type': filter_type,
            'filters_applied': filters,
            'results_count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)