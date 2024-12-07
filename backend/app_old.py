import streamlit as st
import requests
import os
import time

# =======================
# 1. API Key Inputs
# =======================
ragie_api_key = "tnt_LDE2bRyjLhs_laR8e7IveNqwl9S8itseKoXzbaqQCeMYD7kPMzkQxHM"  # Replace with your actual API key
openai_api_key = "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"  # Replace with your actual API key

# =======================
# 2. Define Configuration Parameters
# =======================
ragie_retrieval_url = "https://api.ragie.ai/retrievals"
openai_api_url = "https://api.openai.com/v1/chat/completions"
MODEL_NAME = "gpt-4o"
REQUEST_INTERVAL = 2  # Time between requests in seconds

# =======================
# 3. Retrieval Function
# =======================
def retrieve_chunks(query, top_k=6, max_chunks_per_document=4):
    """
    Retrieves relevant document chunks from Ragie.ai based on the user's query.
    
    Args:
        query (str): The user's input query.
        top_k (int): Number of top chunks to retrieve.
        max_chunks_per_document (int): Maximum chunks per document.
    
    Returns:
        list: A list of retrieved chunks.
    """
    headers = {
        "Authorization": f"Bearer {ragie_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "query": query,
        "rerank": True,
        "topK": top_k,
        "maxChunksPerDocument": max_chunks_per_document
    }
    
    try:
        response = requests.post(ragie_retrieval_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # Debugging: Show the payload and response in the Streamlit app
        st.write("### Ragie.ai Debugging")
        st.write("**Payload Sent:**", payload)
        st.write("**Response Received:**", data)
        
        return data.get("scored_chunks", [])
    except Exception as e:
        st.error(f"Error during Ragie.ai retrieval: {e}")
        return []

# =======================
# 4. Generation Function
# =======================
def generate_response_with_citations(user_query, retrieved_chunks):
    """
    Generates a response with citations using OpenAI's GPT-4o model based on retrieved chunks.
    
    Args:
        user_query (str): The user's input query.
        retrieved_chunks (list): List of retrieved document chunks.
    
    Returns:
        str: The generated response with formatted citations.
    """
    chunk_texts = "\n".join(chunk['text'][:1000] for chunk in retrieved_chunks)  # Limit chunk size for token budget

    # Extract document metadata for citations
    document_info = {}
    for chunk in retrieved_chunks:
        doc_id = chunk['document_id']
        if doc_id not in document_info:
            document_metadata = chunk.get('document_metadata', {})
            document_info[doc_id] = {
                "name": document_metadata.get("name", "Untitled"),
                "source_url": document_metadata.get("source", None)
            }
    
    citations = [
        f"[{info['name']}]({info['source_url']})" if info['source_url'] else info['name']
        for info in document_info.values()
    ]
    formatted_citations = ", ".join(citations)

    # System Prompt
    system_prompt = f"""
    You are Mahfud MD, an AI chatbot providing accurate and first-person responses based on the information available to you. Your responses should be informative, concise, and include citations from the provided documents.

    Cite information from the following documents: {formatted_citations}

    ---
    {chunk_texts}
    ---

    User Query: {user_query}
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.3,
        "max_tokens": 500,
        "n": 1
    }
    
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(openai_api_url, headers=headers, json=payload)
        response.raise_for_status()
        completion = response.json()
        return completion['choices'][0]['message']['content'].strip()
    except Exception as e:
        st.error(f"Error during OpenAI generation: {e}")
        return "I'm sorry, I encountered an error while generating a response."

# =======================
# 5. Chat Interface
# =======================
def main():
    st.set_page_config(page_title="Mahfud MD AI Chatbot", page_icon="🤖")
    
    # Sidebar
    st.sidebar.title("Mahfud MD AI Chatbot")
    st.sidebar.write("Use the chat interface below to interact with the chatbot.")
    
    # Main Interface
    st.write("### Hello, I'm Mahfud MD's AI. What would you like to discuss today?")
    
    # Initialize session state for conversation history
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []

    # Display conversation history
    for msg in st.session_state.conversation:
        if msg['role'] == 'user':
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Mahfud MD AI:** {msg['content']}")
    
    # Chat Input
    user_input = st.text_input("Message Mahfud MD:")
    
    if st.button("Send"):
        if user_input.strip() == "":
            st.warning("Please enter a message to send.")
        else:
            # Append user message to conversation
            st.session_state.conversation.append({"role": "user", "content": user_input})
            
            # Retrieve chunks from Ragie.ai
            with st.spinner("Retrieving relevant information..."):
                chunks = retrieve_chunks(user_input)
            if not chunks:
                response = "🔍 I'm sorry, I couldn't find any relevant information to assist you."
            else:
                # Generate response with citations
                with st.spinner("Generating response..."):
                    response = generate_response_with_citations(user_input, chunks)
            
            # Append AI response to conversation
            st.session_state.conversation.append({"role": "assistant", "content": response})
    
    # Clear input field
    st.text_input("Message Mahfud MD:", value="", key="input_box")

if __name__ == "__main__":
    main()
