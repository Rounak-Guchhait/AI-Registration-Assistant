import sys
sys.path.insert(0, r'C:\Users\rouna\OneDrive\Documents\Virtual Internship\AI_Registration_Assistant')
from chatbot import RegistrationAssistant

a = RegistrationAssistant()

def convo(messages):
    a.reset_conversation()
    for m in messages:
        r = a.handle_message(m)
        print(f"  You: {m}")
        print(f"  Bot: {r}")

print("=== Test 1: Full registration flow ===")
convo([
    "hello",
    "I want to register",
    "My name is Rounak Guchhait",
    "rounakguchhait@gmail.com",
    "Computer Science",
    "Beginner",
    "yes"
])

print("\n=== Test 2: Invalid email then valid ===")
convo([
    "hi",
    "register",
    "I'm Bryan",
    "notanemail",
    "bryan@gmail.com",
    "Data Science",
    "Intermediate",
    "confirm"
])

print("\n=== Test 3: Help / details / skills queries ===")
convo([
    "what can you do",
    "tell me about the internship",
    "what skills do I need"
])

print("\n=== Test 4: Restart on confirmation no ===")
convo([
    "hey",
    "sign up",
    "Matt Parker",
    "matt@gmail.com",
    "Engineering",
    "no",
    "my name is Matt Parker",
    "matt2@gmail.com",
    "Engineering",
    "Advanced",
    "yes"
])

print("\nALL TESTS COMPLETED")
