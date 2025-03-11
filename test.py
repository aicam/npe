import streamlit as st
import requests
import json
from datetime import datetime

# =========================
# 1. Configuration
# =========================
BASE_URL = "https://b49ebf7lsb.execute-api.us-west-1.amazonaws.com/stage"  # <-- Change here if needed

DEFAULT_PROMPT_ROLES = [
    {
        "role": "system",
        "content": "You are a helpful waitress in the restaurant %%RESTAURANT_NAME%% and should answer customers questions with less than 100 words. %%MAIN_CHAR%%"
    },
    {
        "role": "user",
        "content": (
            "You are a helpful waitress in %%RESTAURANT_NAME%%. %%MAIN_CHAR%% %%SECOND_CHAR%% "
            "I will give you the menu information in the format of: <item name> - <category name> , <item description> , "
            "<item tags in form of a string array for example ['Chilli off'] which means item is not chili> , "
            "<price (Prices are in cent, for example 299 means $2.99, just write the convenient format which is $2.99)> , "
            "<item options in the form of option name: array of choices : price separated by ; (price is in addition to the item, for example if item price is 200 and an option is 100 means by choosing this option you add 100 to the base price, if you want to offer an option add the option price to the base price so user understand the total price)>. "
            "Then give you the question of the customer and their chat history with you, you have to answer the question very precisely. "
            "Write less than 100 words and use markdowns for better reading. If you do not know the answer, suggest items that may help. "
            "Use any information that you have about the restaurant and the menu I gave you. You are just a waitress for this restaurant. "
            "If and only if the customer asked to order, just say please contact the server for ordering or provide any link if the instructions have, "
            "acknowledge that you are not capable of ordering. Always check to write name of the items correct (item names should be exactly the same as the items I write for you), "
            "the item names is then checked by front end to show the user the picture of the item, so make sure to write the item exactly as I write here. "
            "If user ask for items with restrictions like gluten free and you could not find any item with this tag or explicit mention in the menu information, "
            "just say you can't find these information in the items and AI is not capable of assuming these itself. Always suggest items. "
            "Also answer in the same language user asked."
        )
    },
    {
        "role": "assistant",
        "content": (
            "Sure. I will read the menu information and answer the customer question to best of my knowledge. "
            "I will check my knowledge in addition to the menu information to answer the question in comprehensive way. "
            "I will always write the name of the items as the exact same you wrote and wrap them with my answer in same language the question is asked."
        )
    },
    {
        "role": "user",
        "content": (
            "Perfect. Menu information based on the format I mentioned is: %%MENU_FULL%%. "
            "Also, this is the information about the menu: %%MENU_DESCRIPTION%%"
        )
    },
    {
        "role": "assistant",
        "content": "Got it. I learnt the menu completely."
    },
    {
        "role": "user",
        "content": "Customer conversation history with you: %%CONVERSATION_HISTORY%% \nCustomer asked: %%Q%%"
    }
]

def default_prompt_string():
    return json.dumps(DEFAULT_PROMPT_ROLES, indent=2)

# =========================
# 2. Main App
# =========================
def main():
    st.title("Simple Chatbot Dashboard with Prompt Editing")

    # Session states
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "prompt" not in st.session_state:
        st.session_state["prompt"] = ""
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = "[]"

    # -----------------------------
    # A) Login (if not logged in)
    # -----------------------------
    if not st.session_state["token"]:
        st.subheader("Login")
        email = st.text_input("Email", value="shayan.rasouli@neobreed.org")
        password = st.text_input("Password", value="1234", type="password")

        if st.button("Login"):
            login_url = f"{BASE_URL}/login"
            payload = {"email": email, "password": password}
            headers = {"Content-Type": "application/json"}
            try:
                resp = requests.post(login_url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == 1:
                        # Save the Bearer token
                        st.session_state["token"] = data["body"]
                        st.success("Logged in successfully!")
                        # After login, immediately fetch user info
                        load_user_info()
                    else:
                        st.error(f"Login failed: {data.get('body', 'Unknown error')}")
                else:
                    st.error(f"Login request failed with code {resp.status_code}.")
            except Exception as ex:
                st.error(f"Error logging in: {str(ex)}")
    else:
        # ----------------------------
        # B) Already logged in
        # ----------------------------
        st.subheader("Logged in")
        st.write(f"**Token:** {st.session_state['token']}")

        # Prompt text area
        st.write("### Prompt Editor (test_prompt)")
        st.session_state["prompt"] = st.text_area(
            label="Edit your Prompt here (JSON or plain text). This will be sent as `test_prompt` on query.",
            value=st.session_state["prompt"],
            height=300
        )

        # Chat history text area
        st.write("### Chat History Editor")
        st.session_state["chat_history"] = st.text_area(
            label=("Paste/edit the chat history as a JSON array\n"
                   "(e.g. [{\"sender\": \"user\", \"message\": \"Hello!\", \"date_time\": \"2025-03-07 12:00:00\", \"feedback\": \"\"}, ...])"),
            value=st.session_state["chat_history"],
            height=300
        )

        # Text field for the new query to the chatbot
        st.write("### Query to Chatbot")
        user_query = st.text_input("Enter your question/query")

        # GPT/Hash IDs
        st.write("### GPT/Hash IDs")
        gpt_response_id = st.text_input("GPT Response ID", value="chatcmpl-B8GADpxKNYad7RVx6ExEgjcaCrq9x")
        user_hash = st.text_input("User Hash", value="ElKhwyQQmMNKJEEH90vlGwHCw6EHwYzIuBXzK7Xx")
        list_hash = st.text_input("List Hash", value="dJGyYOs6MiqHBXBLRSFRQQNeFJoVMU")

        # -----------------------
        # Send query to chatbot
        # -----------------------
        if st.button("Send to Chatbot"):
            try:
                # Parse the chat history JSON
                chat_history_data = json.loads(st.session_state["chat_history"])
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON in chat history: {str(e)}")
                return

            query_payload = {
                "gpt_response_id": gpt_response_id,
                "user_hash": user_hash,
                "list_hash": list_hash,
                "chat_history": chat_history_data,
                "query": user_query,
                "audio": False,
                "test_prompt": st.session_state["prompt"],
            }

            try:
                headers = {"Content-Type": "application/json"}
                send_url = f"{BASE_URL}/chatbot/query/menu"
                resp = requests.post(send_url, json=query_payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    st.write("**Response**:")
                    st.json(data)
                else:
                    st.error(f"Chatbot request failed: {resp.status_code}")
            except Exception as ex:
                st.error(f"Error sending query: {str(ex)}")

        st.write("---")

        # -----------------------
        # Update Core Prompt
        # -----------------------
        st.write("### Update Core Prompt on Server")
        if st.button("Update Core Prompt"):
            # This will permanently update the user prompt on the backend
            update_url = f"{BASE_URL}/user/update"
            headers = {
                "Content-Type": "application/json",
                "Authorization": st.session_state["token"]
            }
            payload = {"prompt": st.session_state["prompt"]}  # uses the text area content

            try:
                resp = requests.post(update_url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == 1:
                        st.success("Core prompt updated successfully!")
                    else:
                        st.error(f"Failed to update prompt: {data.get('body','Unknown error')}")
                else:
                    st.error(f"Update prompt request failed: {resp.status_code}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

        st.write("---")

        # -----------------------
        # Logout
        # -----------------------
        if st.button("Logout"):
            st.session_state["token"] = None
            st.session_state["prompt"] = ""
            st.session_state["chat_history"] = "[]"
            st.experimental_rerun()

# =========================
# 3. Helpers
# =========================
def load_user_info():
    """Fetches the user info from /user and initializes the prompt in session_state."""
    if st.session_state["token"] is None:
        return
    url = f"{BASE_URL}/user"
    headers = {
        "Authorization": st.session_state["token"]
    }
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            user_info = data.get("user_info", {})
            current_prompt = user_info.get("prompt", "")  # e.g. "test"

            # If the user's core prompt is > 100 chars, use it;
            # otherwise, use our default multi-role prompt
            if len(current_prompt) > 100:
                st.session_state["prompt"] = current_prompt
            else:
                st.session_state["prompt"] = default_prompt_string()

            # Initialize chat_history as empty JSON array if not set
            if not st.session_state.get("chat_history"):
                st.session_state["chat_history"] = "[]"
        else:
            st.error(f"Failed to fetch /user info. Status code: {resp.status_code}")
    except Exception as e:
        st.error(f"Error fetching user info: {str(e)}")

if __name__ == "__main__":
    main()
