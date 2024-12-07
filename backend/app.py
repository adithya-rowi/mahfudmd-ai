import os
import sys
import requests
import logging
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
ragie_api_key = os.getenv("RAGIE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not ragie_api_key or not openai_api_key:
    print("❗️ Error: API keys not found. Please set RAGIE_API_KEY and OPENAI_API_KEY in your environment.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

ragie_retrieval_url = "https://api.ragie.ai/retrievals"
openai_api_url = "https://api.openai.com/v1/chat/completions"

def expand_query(user_query):
    prompt = f"Perluas kueri berikut untuk menyertakan sinonim dan frasa terkait yang relevan, fokus pada konteks hukum dan politik Indonesia: '{user_query}'"
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
    }
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(openai_api_url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        expanded_query = response.json()['choices'][0]['message']['content'].strip()
        return expanded_query
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during query expansion: {e}")
        return user_query

def retrieve_chunks(query, top_k=7):
    headers = {
        "Authorization": f"Bearer {ragie_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "query": query,
        "rerank": False,
        "top_k": top_k
    }

    try:
        response = requests.post(ragie_retrieval_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        scored_chunks = data.get("scored_chunks", [])
        scored_chunks.sort(key=lambda x: x.get('score', 0), reverse=True)
        logging.info(f"Retrieved {len(scored_chunks)} chunks")
        return scored_chunks
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during Ragie.ai retrieval: {e}")
        return []

def generate_response_with_citations(user_query, retrieved_chunks, conversation_history):
    basic_questions = {
        "siapa kamu": "Saya Mahfud MD, seorang akademisi hukum dan politikus Indonesia.",
        "siapa anda": "Saya Mahfud MD, seorang pakar hukum dan politik di Indonesia.",
    }

    normalized_query = user_query.strip().lower()
    if normalized_query in basic_questions:
        return basic_questions[normalized_query]

    if not retrieved_chunks:
        return "Maaf, saya tidak menemukan informasi yang relevan untuk pertanyaan Anda."

    limited_chunks = retrieved_chunks[:1]
    chunk_texts = ""
    source_map = {}
    for idx, chunk in enumerate(limited_chunks):
        text = chunk.get('text', '')
        title = chunk.get('document_metadata', {}).get('title', 'Sumber')
        source = chunk.get('document_metadata', {}).get('source', '#')
        identifier = f"[{idx+1}]"
        chunk_texts += f"{text}\n\n"
        source_map[identifier] = (title, source)

    system_prompt = f"""Anda adalah **Mahfud MD**, seorang pakar hukum dan politik Indonesia. Jawablah pertanyaan pengguna dengan menggunakan **hanya** informasi yang terdapat dalam konteks di bawah ini. Gunakan kata ganti orang pertama.

**Instruksi:**
- Berikan jawaban yang ringkas dan informatif, direct, clear and concise.
- **Jangan menjawab pertanyaan yang tidak terkait dengan topik hukum dan politik.**
- Hindari pengulangan dan fokus pada inti pertanyaan.
- Gunakan gaya bahasa yang formal, jelas, dan mencerminkan cara berbicara Mahfud MD.
- **Jangan sertakan tanda referensi** seperti [1], [2], dll.
- **Jangan** sertakan informasi di luar konteks yang diberikan.
- Jika pertanyaan di luar konteks, jawab dengan sopan bahwa Anda fokus pada topik hukum dan politik.
- Balas dalam bahasa Indonesia.

**Konteks:**
{chunk_texts}
"""

    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history[-6:])
    messages.append({"role": "user", "content": user_query})

    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 180,
    }

    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(openai_api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        completion = response.json()
        generated_text = completion['choices'][0]['message']['content'].strip()
        generated_text = re.sub(r'\[\d+\]', '', generated_text)

        no_reference_phrases = [
            "maaf", "tidak memiliki informasi", "saya fokus pada",
            "tidak dapat memberikan informasi", "saya tidak memiliki data",
            "saya tidak bisa menjawab"
        ]
        if any(phrase in generated_text.lower() for phrase in no_reference_phrases):
            return generated_text.strip()
        else:
            limited_sources = list(source_map.items())[:2]
            citations = "\n".join(f"{identifier}. [{title}]({source})" for identifier, (title, source) in limited_sources)
            if citations:
                generated_text += f"\n\n**Referensi:**\n{citations}"
            return generated_text.strip()

    except requests.exceptions.RequestException as e:
        logging.error(f"Error during GPT generation: {e}")
        return "Maaf, terjadi kesalahan saat menghasilkan jawaban."

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_query = data.get('message', '').strip()
    if not user_query:
        return jsonify({'response': '⚠️ Invalid query'}), 400

    # Just run the logic: expand, retrieve, respond
    expanded_query = expand_query(user_query)
    retrieved_chunks = retrieve_chunks(expanded_query)
    response = generate_response_with_citations(user_query, retrieved_chunks, [])
    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
