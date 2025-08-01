#!/usr/bin/env python3
"""
Test script to verify filtering functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import data_store, extract_parameter_value

def test_parameter_extraction():
    """Test the parameter extraction function"""
    print("=== Testing Parameter Extraction ===")
    
    # Test cases for Dialogflow CX parameter format
    test_cases = [
        {
            'name': 'simple_parameters',
            'parameters': {
                'area': 'lekki',
                'event_type': 'concert'
            },
            'expected': {
                'area': 'lekki',
                'event_type': 'concert'
            }
        },
        {
            'name': 'dialogflow_cx_format',
            'parameters': {
                'area': {'value': 'victoria_island'},
                'event_type': {'value': 'beach_party'},
                'max_budget': {'value': '50000'}
            },
            'expected': {
                'area': 'victoria_island',
                'event_type': 'beach_party',
                'max_budget': '50000'
            }
        },
        {
            'name': 'mixed_format',
            'parameters': {
                'area': {'value': 'lekki'},
                'event_type': 'concert',
                'gender': {'value': 'female'}
            },
            'expected': {
                'area': 'lekki',
                'event_type': 'concert',
                'gender': 'female'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing {test_case['name']} ---")
        parameters = test_case['parameters']
        expected = test_case['expected']
        
        for param_name, expected_value in expected.items():
            result = extract_parameter_value(parameters, param_name)
            print(f"  {param_name}: expected '{expected_value}', got '{result}'")
            assert result == expected_value, f"Parameter extraction failed for {param_name}"

def test_event_filtering():
    """Test event filtering with the new parameter extraction"""
    print("\n=== Testing Event Filtering ===")
    
    # Test different parameter formats
    test_cases = [
        {
            'name': 'area_filter',
            'parameters': {'area': 'lekki'},
            'expected_filters': {'area': 'lekki'}
        },
        {
            'name': 'event_type_filter',
            'parameters': {'event_type': 'concert'},
            'expected_filters': {'event_type': 'concert'}
        },
        {
            'name': 'both_filters',
            'parameters': {
                'area': {'value': 'victoria_island'},
                'event_type': {'value': 'beach_party'}
            },
            'expected_filters': {
                'area': 'victoria_island',
                'event_type': 'beach_party'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing {test_case['name']} ---")
        parameters = test_case['parameters']
        expected_filters = test_case['expected_filters']
        
        # Extract filters using the same logic as webhook
        filters = {'query_text': 'test query'}
        
        area_param = extract_parameter_value(parameters, 'area', ['location', 'place'])
        if area_param:
            filters['area'] = str(area_param)
        
        event_type_param = extract_parameter_value(parameters, 'event_type', ['type', 'event_type'])
        if event_type_param:
            filters['event_type'] = str(event_type_param)
        
        print(f"  Extracted filters: {filters}")
        print(f"  Expected filters: {expected_filters}")
        
        # Test the filtering
        events = data_store.get_events(filters)
        print(f"  Found {len(events)} events")

def test_accommodation_filtering():
    """Test accommodation filtering with the new parameter extraction"""
    print("\n=== Testing Accommodation Filtering ===")
    
    test_cases = [
        {
            'name': 'area_filter',
            'parameters': {'area': 'lekki'},
            'expected_filters': {'area': 'lekki'}
        },
        {
            'name': 'budget_filter',
            'parameters': {'max_budget': {'value': '30000'}},
            'expected_filters': {'max_budget': 30000}
        },
        {
            'name': 'both_filters',
            'parameters': {
                'area': {'value': 'victoria_island'},
                'max_budget': {'value': '50000'}
            },
            'expected_filters': {
                'area': 'victoria_island',
                'max_budget': 50000
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing {test_case['name']} ---")
        parameters = test_case['parameters']
        expected_filters = test_case['expected_filters']
        
        # Extract filters using the same logic as webhook
        filters = {}
        
        area_param = extract_parameter_value(parameters, 'area', ['location', 'place'])
        if area_param:
            filters['area'] = str(area_param)
        
        budget_param = extract_parameter_value(parameters, 'max_budget', ['budget', 'price', 'cost', 'amount'])
        if budget_param:
            try:
                filters['max_budget'] = float(budget_param)
            except (ValueError, TypeError):
                print(f"  Warning: Invalid budget value: {budget_param}")
        
        print(f"  Extracted filters: {filters}")
        print(f"  Expected filters: {expected_filters}")
        
        # Test the filtering
        accommodations = data_store.get_accommodations(filters)
        print(f"  Found {len(accommodations)} accommodations")

if __name__ == "__main__":
    try:
        test_parameter_extraction()
        test_event_filtering()
        test_accommodation_filtering()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 