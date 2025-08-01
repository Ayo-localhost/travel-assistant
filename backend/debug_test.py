#!/usr/bin/env python3
"""
Debug script to test filtering functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import data_store, DateRangeParser

def test_outfit_filtering():
    """Test outfit filtering functionality"""
    print("=== Testing Outfit Filtering ===")
    
    # Get all outfits
    all_outfits = data_store._get_sheet_data('outfits')
    print(f"Total outfits in sheet: {len(all_outfits)}")
    
    if all_outfits:
        print("\nSample outfit data:")
        print(all_outfits[0])
    
    # Test different event types
    event_types = ['concert', 'beach_party', 'club_night', 'brunch', 'detty_december']
    
    for event_type in event_types:
        print(f"\n--- Testing {event_type} ---")
        outfits = data_store.get_outfit_suggestions(event_type)
        print(f"Found {len(outfits)} outfits for {event_type}")
        
        if outfits:
            print("Sample outfit:")
            print(outfits[0])
    
    # Test with gender filter
    print(f"\n--- Testing concert outfits for females ---")
    female_concert_outfits = data_store.get_outfit_suggestions('concert', 'female')
    print(f"Found {len(female_concert_outfits)} female concert outfits")

def test_event_filtering():
    """Test event filtering functionality"""
    print("\n=== Testing Event Filtering ===")
    
    # Get all events
    all_events = data_store._get_sheet_data('events')
    print(f"Total events in sheet: {len(all_events)}")
    
    if all_events:
        print("\nSample event data:")
        print(all_events[0])
    
    # Test different filters
    test_filters = [
        {'area': 'lekki'},
        {'event_type': 'concert'},
        {'area': 'lekki', 'event_type': 'concert'}
    ]
    
    for filters in test_filters:
        print(f"\n--- Testing filters: {filters} ---")
        events = data_store.get_events(filters)
        print(f"Found {len(events)} events")
        
        if events:
            print("Sample event:")
            print(events[0])

def test_accommodation_filtering():
    """Test accommodation filtering functionality"""
    print("\n=== Testing Accommodation Filtering ===")
    
    # Get all accommodations
    all_accommodations = data_store._get_sheet_data('accommodations')
    print(f"Total accommodations in sheet: {len(all_accommodations)}")
    
    if all_accommodations:
        print("\nSample accommodation data:")
        print(all_accommodations[0])
    
    # Test different filters
    test_filters = [
        {'area': 'lekki'},
        {'max_budget': 30000},
        {'area': 'lekki', 'max_budget': 30000}
    ]
    
    for filters in test_filters:
        print(f"\n--- Testing filters: {filters} ---")
        accommodations = data_store.get_accommodations(filters)
        print(f"Found {len(accommodations)} accommodations")
        
        if accommodations:
            print("Sample accommodation:")
            print(accommodations[0])

def test_date_parsing():
    """Test date parsing functionality"""
    print("\n=== Testing Date Parsing ===")
    
    test_queries = [
        "events in october",
        "what's happening this weekend",
        "events next week",
        "concerts this month"
    ]
    
    for query in test_queries:
        start_date, end_date = DateRangeParser.parse_date_query(query)
        print(f"Query: '{query}' -> {start_date} to {end_date}")

if __name__ == "__main__":
    try:
        test_outfit_filtering()
        test_event_filtering()
        test_accommodation_filtering()
        test_date_parsing()
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc() 