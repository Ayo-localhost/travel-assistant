from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import logging
import gspread
from google.oauth2.service_account import Credentials
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

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
    
    def _initialize_sheets_client(self):
        """Initialize Google Sheets client with service account credentials"""
        try:
            # Try to load credentials from service account file
            creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service-account-key.json')
            
            if os.path.exists(creds_file):
                creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
            else:
                # Try to load from environment variables (for deployment)
                import json
                creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
                if creds_json:
                    creds_info = json.loads(creds_json)
                    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
                else:
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
        'sheets_connected': self.gc is not None if hasattr(data_store, 'gc') else False
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)