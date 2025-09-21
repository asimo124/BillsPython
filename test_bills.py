#!/usr/bin/env python3
"""
Test script to verify the Bills class works correctly
"""
import mysql.connector
from bills import Bills
from datetime import datetime, date

def test_date_conversion():
    """Test the _ensure_string_date method with different input types"""
    
    # Create a Bills instance for testing
    db = mysql.connector.connect(
        host="localhost",
        user="",
        password="",
        database=""
    )
    
    bill = Bills(10, db)
    
    # Test different date formats
    test_dates = [
        "2023-09-21",           # String
        datetime(2023, 9, 21),  # datetime object
        date(2023, 9, 21),      # date object
        None,                   # None
    ]
    
    print("Testing date conversion:")
    for test_date in test_dates:
        try:
            result = bill._ensure_string_date(test_date)
            print(f"Input: {test_date} ({type(test_date)}) -> Output: {result}")
        except Exception as e:
            print(f"Error with {test_date}: {e}")
    
    db.close()

if __name__ == "__main__":
    test_date_conversion()
