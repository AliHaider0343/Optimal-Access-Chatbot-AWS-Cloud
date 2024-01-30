import signal
import subprocess
import sys
import threading
import time

from langchain_community.vectorstores.chroma import Chroma

from DocumentsRetriever import retrive_context
import streamlit as st
import pandas as pd
# Function to create the Home page
import multiprocessing
from ChatChain import *

Avaiable_Models=['gemini-pro','gpt-3.5-turbo-1106','gpt-3.5-turbo','gpt-3.5-turbo-instruct','gpt-4','gpt-4-0613']#,'gpt-4-32k-0613','gpt-4-32k']
def home():
    st.image("Images/Logo-Curation-right.png", caption="Dynamic Knowledge base powered Conversational Solution", width=400)

    description = """
    Welcome to Optimal Access, where curation becomes effortless! Our product is a revolutionary, embeddable chatbot solution designed to make content curation a breeze. 

    With Optimal Access, users can provide XML links, enabling the creation of a single chatbot that can curate content from multiple XML sources or focus on a single XML file. What sets our product apart is its exceptional accuracy in providing reliable sources and its unique ability to update the knowledge base at user-specified intervals.
    
    Key Features:
    - Embeddable Chatbots: Seamlessly integrate chatbots into your applications.
    - Multi-XML Support: Create a single chatbot that curates content from multiple XML sources.
    - Flexible Configuration: Customize chatbot behavior based on your specific requirements.
    - Automatic Knowledge Base Updates: Keep your knowledge base up-to-date with scheduled updates.

    Experience the future of content curation with Optimal Access!
    """

    st.write(description)

def stop_thread():
    # Wait for the subprocess thread to finish
    if st.session_state.subprocess_thread and st.session_state.handle:
        st.session_state.handle.terminate()  # Terminate the subprocess
        st.session_state.subprocess_thread.join()

# Function to create the Create Chatbot page
def create_chatbot():
    st.title("Create and Configure your Chatbot.")

    if 'syncing' not in st.session_state:
        st.session_state.syncing=None
    if 'data_ingestion_process' not in st.session_state:
        st.session_state.data_ingestion_process=None

    if st.session_state.syncing is None:
        # Input box for user input
        user_input = st.text_input('Enter your knowledge base URL (XML URL with Comma Seperation without Qoutes) ')
        add_button = st.button('Append Knowledge Base')
        # Append user input to the DataFrame
        dataframe = pd.DataFrame()
        # Other user inputs
        username = st.text_input("Your username")
        chatbot_name = st.text_input("Chatbot name")
        sync_period = st.number_input("Knowledge base Synchronization period (in seconds):", min_value=1, value=60)
        if add_button and user_input:
            urls=user_input.split(',')
            dataframe['Knowledge Base URLS']=urls
            st.write(dataframe)
        create_button=st.button("Create Chatbot")
        if username and chatbot_name and sync_period and user_input and create_button:
            # Process the inputs (customize this part based on your application logic)
            Python = r'myenv/Scripts/python.exe'
            st.session_state.user_id = username
            st.session_state.chatbot_id = chatbot_name
            st.session_state.syncing = True
            if 'status' in st.session_state:
                del st.session_state.status
            def run_subprocess(user_input, username, chatbot_name, sync_period):
                command = [Python, "Data-Ingestion-and-Sync.py", user_input, username, chatbot_name, str(sync_period)]
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                return process
            # Start the subprocess in a separate thread
            st.session_state.data_ingestion_process = run_subprocess(user_input, username, chatbot_name, sync_period)

            #if we use the below code it willd isplay the output in the terminal and doesnt allow su to delete the theread started
            # if 'subprocess_thread' and 'handle' not in st.session_state:
            #     st.session_state.subprocess_thread = threading.Thread(target=run_subprocess)
            #     st.session_state.handle=st.session_state.subprocess_thread.start()
            #print('>>>>>>>>>>>>>>>',st.session_state.subprocess_thread)

            st.success(f"Chatbot is being created with the following inputs:\n"
                       f"Username: {username}\n"
                       f"Chatbot Name: {chatbot_name}\n"
                       f"Sync Period: {sync_period} seconds")
            time.sleep(2)
            st.rerun()
        else:
            st.warning("Please Fill All the Fields and then Hit to Create bot.")

    if st.session_state.syncing==True:
        st.success("Chatbot Already Created and Syncing New Data (Stop the Previous One for New).")
        stop_button = st.button("Stop Chatbot Syncing and Retain Knowledge")
        stop_and_delete_bot=st.button("Stop Chat Bot Syncing and Delete Knowledge")
        if stop_button:
            if st.session_state.data_ingestion_process is not None and st.session_state.data_ingestion_process.poll() is None:
                st.session_state.data_ingestion_process.terminate()
                st.session_state.data_ingestion_process=None
                st.session_state.syncing=None
            st.session_state.status="Chatbot Syncing has been stopped but You can Still Retrive Documents and Chat with Existing Store (That doesnt have the knowledge about latest updates beacuase syncing has been stopped) unless you Create the New Chatbot"
            st.warning(st.session_state.status)

        if stop_and_delete_bot:
            if st.session_state.data_ingestion_process is not None and st.session_state.data_ingestion_process.poll() is None:
                st.session_state.data_ingestion_process.terminate()
                st.session_state.data_ingestion_process = None
                st.session_state.syncing = None
                del st.session_state.user_id
                del st.session_state.chatbot_id
            st.session_state.status="Chatbot Syncing has been stopped and Knowledge base has been Deleted Must Create New Bot to Chat with."
            st.warning(st.session_state.status)

        refresh = st.button("Refresh Chatbot Page")
        if refresh:
            st.rerun()

def get_responce(query,selected_model):
    with multiprocessing.Pool(processes=1) as pool:
        answer,reference_docuemnts_sources = pool.apply(Get_Conversation_chain, args=(st.session_state.user_id, st.session_state.chatbot_id,query,st.session_state.previous_chat,str(selected_model).lower()))
    st.session_state.previous_chat.append({'human':query,'ai':answer})
    st.session_state.interface_chats.append({'Me':query,'AI Chat Bot':answer,'Reference Sources and Context':reference_docuemnts_sources})
    st.rerun()
    #st.write(answer)
    #st.write(reference_docuemnts_sources)

def chat_interface():
    st.title("Chat with Your Dynamic Bot")
    st.markdown("---")
    if 'user_id' and 'chatbot_id' not in st.session_state:
        st.session_state.user_id = None
        st.session_state.chatbot_id = None

    if st.session_state.user_id and st.session_state.chatbot_id:
        if 'status' in st.session_state:
            st.warning(st.session_state.status)
        st.subheader("Chat Interface")
        global Avaiable_Models
        Avaiable_Models = [string.upper() for string in Avaiable_Models]
        selected_model = st.selectbox("Select Large Language Model for Augmentation (by Default it uses GPT 4)", Avaiable_Models,index=Avaiable_Models.index("GPT-4"))
        if 'previous_chat' and 'interface_chats' not in st.session_state:
            st.session_state.previous_chat=[]
            st.session_state.interface_chats = []

        with st.form('Messages-Form'):
            st.write('Previous Chat History and Reference Sources')
            for previous_message in st.session_state.interface_chats:
                st.write(previous_message)
            message = st.text_input("Post a message")
            if st.form_submit_button("Ask AI Bot") and message:
                get_responce(message,selected_model)
            else:
                st.warning("Please write any Query to Proceed.")
    else:
        st.error("Please Create a Chatbot First so you can Chat with it.")
# Function to create the Retrieve Information page
def retrieve_information():

    st.title("Retrieve Information Page")
    st.write("Retrieve information from your chatbot here.")
    st.markdown("---")
    if 'user_id' and 'chatbot_id' not in st.session_state:
        st.session_state.user_id = None
        st.session_state.chatbot_id = None

    if st.session_state.user_id and st.session_state.chatbot_id:
        if 'status' in st.session_state:
            st.warning(st.session_state.status)
        query = st.text_input('Enter your Query ')

        get=st.button('Get Documents')

        if query and get:
            if st.session_state.user_id and st.session_state.chatbot_id:
                # Create a multiprocessing Pool with a single worker
                with multiprocessing.Pool(processes=1) as pool:
                    result = pool.apply(retrive_context, args=(query, st.session_state.user_id, st.session_state.chatbot_id, None))
                for context in result:
                    st.write(context)
                    st.markdown('---')
            else:
                    st.error("Please Create the Chatbot First and then Inquire the Vector Store")
        else:
            st.warning("Please write any Query to Retrieve Documents.")
    else:
        st.error("Please Create a Chatbot First so you can Retrieve the Relevant Documents.")

# Set the title at the top of the Streamlit app
st.set_page_config(
    page_title="Optimal Access Chatbots",
    page_icon="Images/Logo-Curation-left.png",  # You can use an emoji or provide a URL to an icon
    layout="wide",  # Set the layout to wide

)
st.markdown("""
<script>
document.body.style.zoom = 0.8;
</script>
""", unsafe_allow_html=True)

# Main function to handle page navigation
def main():
    pages = {
        "Home": home,
        "Create and Configure Chatbot": create_chatbot,
        "Retrieve Information": retrieve_information,
        "Chat Interface":chat_interface,
    }
    st.sidebar.image("Images/Logo-left.png", caption="Optimal Access Conversational Solution",width=300)

    st.sidebar.title("Optimal Access")
    selection = st.sidebar.selectbox("Select Page to Navigate", list(pages.keys()))
    page = pages[selection]
    page()

if __name__ == "__main__":
    main()

#The only probom is donot gettign the latest data
#Previous Implementation that donot get the updated knowldget but the benefit was that the all the chains
#are and chroma references and retreivers are used once and only the answer chain is Involked but in the latest
#for every reqeust all the things are created from scratch
# import subprocess
# import threading
#
# from langchain_community.vectorstores.chroma import Chroma
#
# from DocumentsRetriever import retrive_context
# import streamlit as st
# import pandas as pd
# # Function to create the Home page
# import multiprocessing
# from ChatChain import *
#
# st.session_state.syncing = None
# subprocess_thread = None
# Avaiable_Models = ['gpt-3.5-turbo-1106', 'gpt-3.5-turbo', 'gpt-3.5-turbo-instruct', 'gpt-4',
#                    'gpt-4-0613']  # ,'gpt-4-32k-0613','gpt-4-32k']
#
#
# def home():
#     st.image("Images/Logo-Curation-right.png", caption="Dynamic Knowledge base powered Conversational Solution",
#              width=400)
#
#     description = """
#     Welcome to Optimal Access, where curation becomes effortless! Our product is a revolutionary, embeddable chatbot solution designed to make content curation a breeze.
#
#     With Optimal Access, users can provide XML links, enabling the creation of a single chatbot that can curate content from multiple XML sources or focus on a single XML file. What sets our product apart is its exceptional accuracy in providing reliable sources and its unique ability to update the knowledge base at user-specified intervals.
#
#     Key Features:
#     - Embeddable Chatbots: Seamlessly integrate chatbots into your applications.
#     - Multi-XML Support: Create a single chatbot that curates content from multiple XML sources.
#     - Flexible Configuration: Customize chatbot behavior based on your specific requirements.
#     - Automatic Knowledge Base Updates: Keep your knowledge base up-to-date with scheduled updates.
#
#     Experience the future of content curation with Optimal Access!
#     """
#
#     st.write(description)
#
#
# # Function to create the Create Chatbot page
# def create_chatbot():
#     st.title("Create and Configure your Chatbot.")
#     global subprocess_thread
#     print(">>>>>>>>>>>>", subprocess_thread)
#     if st.session_state.syncing:
#         st.warning("Chatbot Already Created and Syncing New Data (Stop the Previous One for New).")
#         stop_button = st.button("Stop Chatbot Syncing")
#
#         if stop_button and subprocess_thread:
#             subprocess_thread.join(timeout=1)  # Wait for the thread to finish (terminate it gracefully)
#             st.session_state.syncing = None
#             st.warning("Chatbot Syncing has been stopped.")
#
#     if st.session_state.syncing is None:
#         # Input box for user input
#         user_input = st.text_input('Enter your knowledge base URL (XML URL with Comma Seperation without Qoutes) ')
#         add_button = st.button('Append Knowledge Base')
#         # Append user input to the DataFrame
#         dataframe = pd.DataFrame()
#         # Other user inputs
#         username = st.text_input("Your username")
#         chatbot_name = st.text_input("Chatbot name")
#         sync_period = st.number_input("Knowledge base Synchronization period (in seconds):", min_value=1, value=60)
#         if add_button and user_input:
#             urls = user_input.split(',')
#             dataframe['Knowledge Base URLS'] = urls
#             st.write(dataframe)
#         create_button = st.button("Create Chatbot")
#         if username and chatbot_name and sync_period and user_input and create_button:
#             # Process the inputs (customize this part based on your application logic)
#             Python = r'myenv/Scripts/python.exe'
#             st.session_state.user_id = username
#             st.session_state.chatbot_id = chatbot_name
#             st.session_state.syncing = True
#
#             def run_subprocess():
#                 subprocess.run(
#                     [Python, "Data-Ingestion-and-Sync.py", user_input, username, chatbot_name, str(sync_period)])
#
#             # Start the subprocess in a separate thread
#             subprocess_thread = threading.Thread(target=run_subprocess)
#             subprocess_thread.start()
#
#             st.success(f"Chatbot created with the following inputs:\n"
#                        f"Username: {username}\n"
#                        f"Chatbot Name: {chatbot_name}\n"
#                        f"Sync Period: {sync_period} seconds")
#             st.rerun()
#
#
# def invoke_chain(answer_chain, data):
#     answer = answer_chain.invoke(data)
#     return answer
#
#
# def get_responce(query, selected_model):
#     answer_chain = Get_Conversation_chain(st.session_state.user_id, st.session_state.chatbot_id,
#                                           str(selected_model).lower())
#     if 'previous_chat' not in st.session_state:
#         st.session_state.previous_chat = []
#     answer = invoke_chain(answer_chain, {"question": query, "chat_history": st.session_state.previous_chat})
#
#     st.session_state.previous_chat.append({'human': query, 'ai': answer})
#     st.write(answer)
#     st.write(refrence_docuemnts_sources)
#
#
# def chat_interface():
#     st.title("Chat with Your Dynamic Bot")
#     st.markdown("---")
#     st.subheader("Chat Interface")
#     global Avaiable_Models
#     Avaiable_Models = [string.upper() for string in Avaiable_Models]
#     selected_model = st.selectbox("Select Large Language Model for Augmentation (by Default it uses GPT 4)",
#                                   Avaiable_Models, index=Avaiable_Models.index("GPT-4"))
#     with st.form('Messages-Form'):
#         message = st.text_input("Post a message")
#         if st.form_submit_button("Ask AI Bot") and message:
#             get_responce(message, selected_model)
#         else:
#             st.warning("Please write any Query to Proceed.")
#
#
# # Function to create the Retrieve Information page
# def retrieve_information():
#     st.title("Retrieve Information Page")
#     st.write("Retrieve information from your chatbot here.")
#     query = st.text_input('Enter your Query ')
#
#     get = st.button('Get Documents')
#
#     if query and get:
#         if st.session_state.user_id and st.session_state.chatbot_id:
#             # Create a multiprocessing Pool with a single worker
#             with multiprocessing.Pool(processes=1) as pool:
#                 result = pool.apply(retrive_context,
#                                     args=(query, st.session_state.user_id, st.session_state.chatbot_id, None))
#             for context in result:
#                 st.write(context)
#                 st.markdown('---')
#         else:
#             st.error("Please Create the Chatbot First and then Inquire the Vector Store")
#     else:
#         st.warning("Please write any Query to Retrieve Documents.")
#
#
# # Set the title at the top of the Streamlit app
# st.set_page_config(
#     page_title="Optimal Access Chatbots",
#     page_icon="Images/Logo-Curation-left.png",  # You can use an emoji or provide a URL to an icon
#     layout="wide",  # Set the layout to wide
#
# )
# st.markdown("""
# <script>
# document.body.style.zoom = 0.8;
# </script>
# """, unsafe_allow_html=True)
#
#
# # Main function to handle page navigation
# def main():
#     pages = {
#         "Home": home,
#         "Create and Configure Chatbot": create_chatbot,
#         "Retrieve Information": retrieve_information,
#         "Chat Interface": chat_interface,
#     }
#     st.sidebar.image("Images/Logo-left.png", caption="Optimal Access Conversational Solution", width=300)
#
#     st.sidebar.title("Optimal Access")
#     selection = st.sidebar.selectbox("Select Page to Navigate", list(pages.keys()))
#     page = pages[selection]
#     page()
#
#
# if __name__ == "__main__":
#     main()
