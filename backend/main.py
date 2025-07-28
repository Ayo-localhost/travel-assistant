from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class SimpleDataStore:
    def __init__(self):
        # Load template data
        with open('sheets_templates.json', 'r') as f:
            self.data = json.load(f)
        
        # Extract sample data from templates
        self.events = self._extract_events_data()
        self.accommodations = self._extract_accommodations_data()
        self.outfits = self._extract_outfits_data()
    
    def _extract_events_data(self):
        """Extract events from template data"""
        events_template = self.data['events_sheet_template']['worksheets'][0]
        sample_data = events_template['sample_data']
        headers = events_template['headers']
        
        events = []
        for row in sample_data:
            event = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    event[header.lower().replace(' ', '_')] = row[i]
            events.append(event)
        
        return events
    
    def _extract_accommodations_data(self):
        """Extract accommodations from template data"""
        acc_template = self.data['accommodations_sheet_template']['worksheets'][0]
        sample_data = acc_template['sample_data']
        headers = acc_template['headers']
        
        accommodations = []
        for row in sample_data:
            accommodation = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    accommodation[header.lower().replace(' ', '_')] = row[i]
            accommodations.append(accommodation)
        
        return accommodations
    
    def _extract_outfits_data(self):
        """Extract outfits from template data"""
        outfits_template = self.data['outfits_sheet_template']['worksheets'][0]
        sample_data = outfits_template['sample_data']
        headers = outfits_template['headers']
        
        outfits = []
        for row in sample_data:
            outfit = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    outfit[header.lower().replace(' ', '_')] = row[i]
            outfits.append(outfit)
        
        return outfits
    
    def get_current_week_events(self, filters=None):
        """Get events for current week with optional filters"""
        current_date = datetime.now()
        week_end = current_date + timedelta(days=7)
        
        filtered_events = []
        for event in self.events:
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d')
                
                # Filter by current week
                if current_date <= event_date <= week_end:
                    # Apply additional filters if provided
                    if filters:
                        if filters.get('area') and event.get('area', '').lower() != filters['area'].lower():
                            continue
                        if filters.get('event_type') and event.get('event_type', '').lower() != filters['event_type'].lower():
                            continue
                    
                    filtered_events.append(event)
            except (ValueError, KeyError):
                continue
        
        # Sort by date and return top 3
        filtered_events.sort(key=lambda x: x.get('date', ''))
        return filtered_events[:3]
    
    def get_accommodations(self, filters=None):
        """Get accommodation options with filters"""
        filtered_accommodations = []
        
        for accommodation in self.accommodations:
            # Apply filters
            if filters:
                if filters.get('area') and accommodation.get('area', '').lower() != filters['area'].lower():
                    continue
                if filters.get('max_budget'):
                    try:
                        price = int(accommodation.get('price_per_night', '0'))
                        if price > filters['max_budget']:
                            continue
                    except (ValueError, TypeError):
                        continue
                if filters.get('type') and accommodation.get('type', '').lower() != filters['type'].lower():
                    continue
            
            filtered_accommodations.append(accommodation)
        
        # Sort by rating and return top 3
        try:
            filtered_accommodations.sort(key=lambda x: float(x.get('rating', 0)), reverse=True)
        except (ValueError, TypeError):
            pass
        
        return filtered_accommodations[:3]
    
    def get_outfit_suggestions(self, event_type, gender=None):
        """Get outfit suggestions for specific event types"""
        filtered_outfits = []
        
        for outfit in self.outfits:
            # Filter by event type and gender
            if outfit.get('event_type', '').lower() == event_type.lower():
                if not gender or outfit.get('gender', '').lower() == gender.lower() or outfit.get('gender', '').lower() == 'unisex':
                    filtered_outfits.append(outfit)
        
        return filtered_outfits[:3]

# Initialize data store
data_store = SimpleDataStore()

def format_events_response(events):
    """Format events data for Dialogflow response"""
    if not events:
        return "I couldn't find any events for this week. Check back soon for updates! 🎉"
    
    response_text = "Here are the hottest events this week:\n\n"
    
    for i, event in enumerate(events, 1):
        emoji = "🎵" if event.get('event_type') == 'concert' else "🏖️" if event.get('event_type') == 'beach_party' else "🔥"
        
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
        type_emoji = "🏨" if accommodation.get('type') == 'hotel' else "🏠" if accommodation.get('type') == 'shortlet' else "🏡"
        
        response_text += f"{type_emoji} **{accommodation.get('name', 'Accommodation')}**\n"
        response_text += f"📍 {accommodation.get('area', 'Lagos')} | ₦{accommodation.get('price_per_night', 'TBD')}/night\n"
        
        features = accommodation.get('features', '')
        if features:
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
        gender_emoji = "👩🏽" if outfit.get('gender') == 'female' else "👨🏽" if outfit.get('gender') == 'male' else "👤"
        
        response_text += f"{gender_emoji} **Look {i}: {outfit.get('style_name', 'Style')}**\n"
        response_text += f"🔸 {outfit.get('description', 'Stylish look')}\n"
        
        items = outfit.get('items', '')
        if items:
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
                    filters['max_budget'] = int(parameters['max_budget'])
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
        'service': 'Lagos Travel Guide - Basic Version'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)