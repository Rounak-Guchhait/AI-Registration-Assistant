"""
Seed data module for the AI Registration Assistant.

Generates 100 realistic sample registration records with random names,
emails, fields of study, experience levels, and dates within the last
30 days. Automatically seeds the PostgreSQL database (or JSON fallback)
on first startup if the database is empty.
"""

import os
import random
from datetime import datetime, timedelta

from storage import load_registrations, save_registration

# -------------------------------------------------------------------
# Name / email pools
# -------------------------------------------------------------------
FIRST_NAMES = [
    'Rohan', 'Priya', 'Amit', 'Sneha', 'Vikram', 'Ananya', 'Karthik', 'Meera',
    'Arjun', 'Divya', 'Rahul', 'Kavya', 'Nikhil', 'Aisha', 'Siddharth', 'Neha',
    'Aditya', 'Pooja', 'Varun', 'Isha', 'Ravi', 'Tanvi', 'Nikhil', 'Riya',
    'Suresh', 'Deepa', 'Manoj', 'Swati', 'Tarun', 'Ritika', 'Gaurav', 'Shreya',
    'Ankur', 'Simran', 'Pankaj', 'Divyansh', 'Harsh', 'Jaya', 'Nitin', 'Meghna',
    'Vivek', 'Anjali', 'Karan', 'Pallavi', 'Rajesh', 'Snehal', 'Manav', 'Trisha',
    'Mohan', 'Komal', 'Sumit', 'Madhuri', 'Ashish', 'Sonali', 'Parth', 'Roshni',
    'Nikhil', 'Deepak', 'Priti', 'Sanjay', 'Mitali', 'Vishal', 'Anamika', 'Dev',
    'Ritu', 'Ajay', 'Bhavya', 'Aman', 'Kritika', 'Tushar', 'Radhika', 'Yash',
    'Nisha', 'Chirag', 'Sneha', 'Aakash', 'Fatima', 'Harsh', 'Jasmine', 'Jatin',
    'Usha', 'Shashank', 'Shruti', 'Kishan', 'Nandini', 'Akash', 'Dipti', 'Jay',
    'Sonam', 'Amitesh', 'Sana', 'Vinay', 'Pallavi', 'Manisha', 'Subhash', 'Ruchika',
    'Devansh', 'Ekta', 'Anubhav', 'Payal', 'Saurabh', 'Sapna', 'Himanshu', 'Alka',
    'Saurabh', 'Mansi', 'Harshita', 'Pranav', 'Jigisha', 'Kabir'
]

LAST_NAMES = [
    'Kumar', 'Sharma', 'Patel', 'Reddy', 'Singh', 'Verma', 'Gupta', 'Nair',
    'Mehta', 'Iyer', 'Joshi', 'Mukherjee', 'Das', 'Banerjee', 'Rao', 'Menon',
    'Chowdhury', 'Malhotra', 'Kapoor', 'Saxena', 'Bhatt', 'Chauhan', 'Tiwari',
    'Chandra', 'Desai', 'Hegde', 'Shukla', 'Pandey', 'Thakur', 'Kulkarni',
    'Pillai', 'Sinha', 'Yadav', 'Mishra', 'Chatterjee', 'Dutta', 'Ghosh', 'Ray',
    'Srivastava', 'Prasad', 'Srivastav', 'Agarwal', 'Singhal', 'Khandelwal',
    'Bhatia', 'Kohli', 'Chhabra', 'Dhawan', 'Khatri', 'Arora', 'Lal', 'Varma',
    'Taneja', 'Choudhary', 'Dogra', 'Negi', 'Rawat', 'Bisht', 'Jangra', 'Kaur'
]

DOMAINS = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com']

FIELDS = [
    'Computer Science', 'Data Science', 'Information Technology',
    'Engineering', 'Mathematics', 'Statistics', 'Physics',
    'Business', 'Management', 'Chemistry', 'Electronics',
    'Mechanical Engineering', 'Civil Engineering', 'Electrical Engineering'
]

EXPERIENCE_LEVELS = ['Beginner', 'Intermediate', 'Advanced']

# -------------------------------------------------------------------
# Seed function
# -------------------------------------------------------------------
def _generate_records(n=100):
    """Generate n random registration records."""
    records = []
    now = datetime.now()
    for _ in range(n):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f'{first} {last}'
        domain = random.choice(DOMAINS)
        email = f'{first.lower()}.{last.lower()}@{domain}'
        field = random.choice(FIELDS)
        experience = random.choices(
            EXPERIENCE_LEVELS,
            weights=[50, 35, 15],
            k=1
        )[0]
        days_ago = random.randint(0, 30)
        hours = random.randint(0, 23)
        minutes = random.randint(0, 59)
        reg_date = (now - timedelta(days=days_ago)).replace(
            hour=hours, minute=minutes, second=0, microsecond=0
        )
        records.append({
            'name': name,
            'email': email,
            'field': field,
            'experience': experience,
            'registered_at': reg_date.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return records


def seed_database(target=100):
    """
    Ensure the database has at least `target` records.
    If empty, inserts the full set. If partially populated,
    tops it up to reach the target count.
    Returns True if records were inserted, False otherwise.
    """
    existing = load_registrations()
    current = len(existing)
    if current >= target:
        return False
    needed = target - current
    records = _generate_records(needed)
    for rec in records:
        save_registration(rec)
    return True


# If run directly, seed and report.
if __name__ == '__main__':
    ok = seed_database(100)
    if ok:
        print('Seeded 100 registration records.')
    else:
        print('Database already has records — skipping seed.')