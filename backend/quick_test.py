#!/usr/bin/env python3
"""
Quick test script to verify filtering functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import data_store

def quick_test():
    """Quick test of filtering functionality"""
    print("=== Quick Filtering Test ===")
    
    # Test events filtering
    print("\n--- Testing Events Filtering ---")
    
    # Test with no filters (should return first 5 events)
    events_no_filter = data_store.get_events({})
    print(f"No filters: Found {len(events_no_filter)} events")
    
    # Test with area filter
    events_lekki = data_store.get_events({'area': 'lekki'})
    print(f"Area filter (lekki): Found {len(events_lekki)} events")
    
    # Test with event type filter
    events_concert = data_store.get_events({'event_type': 'concert'})
    print(f"Event type filter (concert): Found {len(events_concert)} events")
    
    # Test with both filters
    events_both = data_store.get_events({'area': 'lekki', 'event_type': 'concert'})
    print(f"Both filters (lekki + concert): Found {len(events_both)} events")
    
    # Test accommodations filtering
    print("\n--- Testing Accommodations Filtering ---")
    
    # Test with no filters
    acc_no_filter = data_store.get_accommodations({})
    print(f"No filters: Found {len(acc_no_filter)} accommodations")
    
    # Test with area filter
    acc_lekki = data_store.get_accommodations({'area': 'lekki'})
    print(f"Area filter (lekki): Found {len(acc_lekki)} accommodations")
    
    # Test with budget filter
    acc_budget = data_store.get_accommodations({'max_budget': 30000})
    print(f"Budget filter (30000): Found {len(acc_budget)} accommodations")
    
    # Test with both filters
    acc_both = data_store.get_accommodations({'area': 'lekki', 'max_budget': 30000})
    print(f"Both filters (lekki + 30000): Found {len(acc_both)} accommodations")
    
    # Show sample data
    print("\n--- Sample Data Analysis ---")
    
    all_events = data_store._get_sheet_data('events')
    all_accommodations = data_store._get_sheet_data('accommodations')
    
    if all_events:
        print(f"Total events: {len(all_events)}")
        print("Sample event:")
        print(f"  Title: {all_events[0].get('title', 'N/A')}")
        print(f"  Area: {all_events[0].get('area', 'N/A')}")
        print(f"  Event Type: {all_events[0].get('event_type', 'N/A')}")
        print(f"  Date: {all_events[0].get('date', 'N/A')}")
    
    if all_accommodations:
        print(f"\nTotal accommodations: {len(all_accommodations)}")
        print("Sample accommodation:")
        print(f"  Name: {all_accommodations[0].get('name', 'N/A')}")
        print(f"  Area: {all_accommodations[0].get('area', 'N/A')}")
        print(f"  Type: {all_accommodations[0].get('type', 'N/A')}")
        print(f"  Price: {all_accommodations[0].get('price_per_night', 'N/A')}")
    
    # Show unique areas
    event_areas = set()
    acc_areas = set()
    
    for event in all_events:
        if event.get('area'):
            event_areas.add(str(event.get('area')))
    
    for acc in all_accommodations:
        if acc.get('area'):
            acc_areas.add(str(acc.get('area')))
    
    print(f"\nUnique event areas: {list(event_areas)}")
    print(f"Unique accommodation areas: {list(acc_areas)}")

if __name__ == "__main__":
    try:
        quick_test()
        print("\n✅ Quick test completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 