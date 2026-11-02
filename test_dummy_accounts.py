"""
Automated UI End-to-End Test Suite for Dummy Accounts & Recommender Workflow.
Uses Streamlit AppTest to simulate real browser interactions.
"""
import os
import json
import hashlib
from streamlit.testing.v1 import AppTest

def test_full_user_lifecycle():
    print("=" * 60)
    print("  Testing Full User Lifecycle with Streamlit AppTest")
    print("=" * 60)
    
    # ── Phase 1: Test Sign Up via UI ──
    print("\n[1/4] Testing UI Sign-Up Flow...")
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    
    dummy_new_user = "test_agent_user"
    dummy_new_pass = "mypassword123"
    
    # Fill Sign Up form
    at.text_input(key="signup_user").input(dummy_new_user)
    at.text_input(key="signup_pass").input(dummy_new_pass)
    at.text_input(key="signup_pass2").input(dummy_new_pass)
    at.button(key="signup_btn").click().run()
    
    # Verify account was created on disk
    user_file = os.path.join("user_data", f"{dummy_new_user}.json")
    assert os.path.exists(user_file), "User file was not created on disk!"
    with open(user_file) as f:
        data = json.load(f)
    assert data["name"] == dummy_new_user
    assert data["password"] == hashlib.sha256(dummy_new_pass.encode()).hexdigest()
    print(f"      Successfully signed up '{dummy_new_user}'. File persisted to {user_file}.")
    
    # Clean up test user
    os.remove(user_file)
    print("      Sign-up test cleaned up.")

    # ── Phase 2: Test Login with Dummy Account 'cinephile' ──
    print("\n[2/4] Testing UI Login Flow with 'cinephile'...")
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    
    at.text_input(key="login_user").input("cinephile")
    at.text_input(key="login_pass").input("password123")
    at.button(key="login_btn").click().run()
    
    assert at.session_state.get("logged_in") is True, "Failed to log in!"
    assert at.session_state.get("username") == "cinephile", "Incorrect username in session!"
    print(f"      Login successful! Welcome banner active for: {at.session_state['username']}")
    print(f"      User history loaded: {at.session_state['user_data']['history']}")
    print(f"      User favorites loaded: {at.session_state['user_data']['favorites']}")

    # ── Phase 3: Movie Search, Mood Selection & Hybrid Recommendations ──
    print("\n[3/4] Testing Movie Selection & Recommendation Generation...")
    # Set search query to 'The Dark Knight'
    at.text_input(key="search").input("The Dark Knight").run()
    selected = at.selectbox[0].value
    print(f"      Selected film from search results: '{selected}'")
    assert "Dark Knight" in selected, f"Unexpected movie selection: {selected}"
    
    # Click Mood '😱 Thrilled' (mood_2)
    mood_btn = None
    for b in at.button:
        if "Thrilled" in b.label:
            mood_btn = b
            break
    if mood_btn:
        mood_btn.click().run()
        print(f"      Selected Mood: {at.session_state.get('selected_mood')}")
    
    # Click 'Analyze & Recommend'
    rec_btn = None
    for b in at.button:
        if "Analyze & Recommend" in b.label:
            rec_btn = b
            break
    assert rec_btn is not None, "Analyze & Recommend button not found!"
    
    print("      Running Hybrid Engine (Content + History + Mood)...")
    rec_btn.click().run()
    
    assert len(at.exception) == 0, f"Exceptions occurred: {[e.message for e in at.exception]}"
    print("      Recommendation generated successfully with zero errors!")

    # Verify user history updated on disk
    with open(os.path.join("user_data", "cinephile.json")) as f:
        cine_data = json.load(f)
    assert selected in cine_data["history"], "Selected movie was not added to user history on disk!"
    print(f"      User history updated on disk. Total searches: {len(cine_data['history'])}")

    # ── Phase 4: Test Logout Flow ──
    print("\n[4/4] Testing Logout...")
    logout_btn = None
    for b in at.button:
        if "Logout" in b.label:
            logout_btn = b
            break
    if logout_btn:
        logout_btn.click().run()
        assert at.session_state.get("logged_in") is False, "Logout did not clear logged_in state!"
        print("      Logout successful! Returned to authentication screen.")

    print("\n" + "=" * 60)
    print("  ALL DUMMY ACCOUNT & UI WORKFLOW TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_user_lifecycle()
