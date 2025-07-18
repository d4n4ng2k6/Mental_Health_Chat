from dotenv import load_dotenv
import gradio as gr
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
#from faster_whisper import WhisperModel
from gtts import gTTS
import tempfile
import json
import os
import openai 
import re

load_dotenv()
openai.api_base = os.getenv("OPENAI_API_BASE")  # from .env
openai.api_key = os.getenv("OPENAI_API_KEY")

#ASRModel = WhisperModel('large',compute_type="int8")
llm = ChatOpenAI(
    model="deepseek/deepseek-chat:free",  # Replace with a valid OpenRouter model
    temperature=0.3,
    openai_api_base=os.getenv("OPENAI_API_BASE")
)
#print("API Key loaded:", repr(os.getenv("OPENAI_API_KEY")))
#Load kuesioner DASS-21
with open("DASS21.json","r") as f:
    dass_questions = json.load(f)["DASS"]

user_response = {}
#likert_options=[
  #  "0 : Tidak sesuai dengan saya sama sekali, atau tidak pernah.",
   # "1 : Sesuai dengan saya sampai tingkat tertentu, atau kadang-kadang.",
   # "2 : Sesuai dengan saya sampai batas yang dapat dipertimbangkan, atau lumayan sering.",
   # "3 : Sangat sesuai dengan saya, atau sering sekali."
#]
intro_message = "Saya adalah konselor anda hari ini! Saya akan menanyakan beberapa pertanyaan untuk mengetahui keadaanmu, Berikan jawaban melalui pilihan tombol yang ada di bawah ini:\n" \
"1 : Tidak sesuai dengan saya sama sekali, atau tidak pernah,\n" \
"2 : Sesuai dengan saya sampai tingkat tertentu, atau kadang-kadang \n" \
"3 : Sesuai dengan saya sampai batas yang dapat dipertimbangkan, atau lumayan sering.\n" \
"4 : Sangat sesuai dengan saya, atau sering sekali.\n\n" \
"Tekan Tombol Mulai !!"

#interpret_prompt = (
    #"Kamu adalah seorang asisten konselor kesehatan mental. Pengguna memberikan jawaban untuk pertanyaan DASS. Petakan jawaban natural ini ke dalam bentuk skala Likert dari 0 sampai 3."
   # "\n\nSkor: 0 = Tidak sesuai dengan saya sama sekali, atau tidak pernah, 1 = Sesuai dengan saya sampai tingkat tertentu, atau kadang-kadang., 2 = Sesuai dengan saya sampai batas yang dapat dipertimbangkan, atau lumayan sering., 3 = Sangat sesuai dengan saya, atau sering sekali.\n"
  #  "Berikan respon HANYA dalam bentuk angka (0, 1, 2, atau 3)."
 #   "\n\nRespon: "
#)
#Pembentukan ulang pertanyaan DASS agar lebih natural
#def frase_ulang(index):
 #   question = dass_questions[index]["text"]
  #  system_prompt = (
   #     "Kamu adalah asisten kesehatan mental yang perhatian."
    #    "Bentuk ulang pertanyaan ini menjadi bentuk pertanyaan kuesioner yang lengkap tetapi terasa natural untuk percakapan chatbot dan jangan membuat lebih dari satu pertanyaan."
     #   f"\n\nPertanyaan: {question}"
    #)
    #result = llm.invoke(system_prompt)
    #return result.content
def clean_text(text):
    return re.sub(r"[*_`]+", "", text)

def beri_respon(pertanyaan,user_input):
    response_prompt = (
        "Kamu adalah asisten konselor kesehatan mental bersertifikat. "
        "Berdasarkan pernyataan dari kuesioner DASS dan jawaban seberapa sering dari pasien, "
        "tuliskan pesan singkat dengan tanda baca yang jelas serta suportif dan berempati, dalam 1-2 kalimat.\n "
        f"Pernyataan: {pertanyaan}\n"
        f"Jawaban User: {user_input}\n"
        "Balasan:"
    )
    result = llm.invoke(response_prompt)
    return result.content.strip()

def catat_jawaban(index,user_input):
    #skor_pemetaan = llm.invoke(user_input).content.strip()
    #try:
     #   skor = int(skor_pemetaan)
     #   skor = max(0, min(3, skor))
    #except:
     #   skor = 1  # fallback to neutral
    match user_input :
        case "Tidak Pernah":
            skor=0
        case "Kadang-Kadang":
            skor=1
        case "Lumayan Sering":
            skor=2
        case "Sering Sekali":
            skor=3
    user_response[index] = {
        "skor": skor,
        "kategori": dass_questions[index]["category"]
    }
def analyze_result():
    results = {"Stress":0,"Anxiety":0,"Depression":0}
    for response in user_response.values():
        results[response["kategori"]]+= response["skor"]
        #print(f"Category : {response["kategori"]}, Score : {response["skor"]} ")
    summary_prompt = (
        "Anda adalah seorang asisten konselor bersertifikat. berdasarkan skor DASS berikut, berikan kesimpulan secara singkat dan suportif serta nasehat untuk user agar menemui guru bimbingan konseling."
        f"\nDepression: {results['Depression']}"
        f"\nAnxiety: {results['Anxiety']}"
        f"\nStress: {results['Stress']}"
    )
    result = llm.invoke(summary_prompt)
    return result.content
def chatbot(user_input, state):
    index = state["index"]
    history = state["history"]
    
    #print(user_input)
    original_question = dass_questions[index]["text"]
    response_text = beri_respon(original_question, user_input)
    catat_jawaban(index,user_input)
    index+=1
   
    # Analyze result
    if index>=len(dass_questions):
        summary = analyze_result()
        summary = clean_text(summary)
        final_response = f"{summary}"
        final_audio = generate_tts(final_response)
        return final_response,final_audio, {"index": index, "history": history, "clear_input":True}
    next_q = dass_questions[index]["text"]
    response = f"{response_text}\n\n{next_q}"
    tts_path = generate_tts(response)
    return response,tts_path, {"index": index, "history": history, "clear_input":True}

#def transcribe(audio_path):
 #   if audio_path == None:
  #      return ""
  #  try:
   #     segments,_ = ASRModel.transcribe(audio_path,language="id")
   #     text = " ".join(segment.text for segment in segments)
   #     return text
   # except Exception as e:
   #     return "", f"Transcription error :{e}"

def generate_tts(text):
    tts = gTTS(text=text,lang="id")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name
#response = llm.invoke([
 #   HumanMessage(content="What is LLM Fine Tunning?")
#])

with gr.Blocks() as app:
    gr.Markdown("### Chatbot Online dengan Voice dan Teks")
    response_box = gr.TextArea(label="Respon Chat", interactive=False, lines= 10)
    audio_output = gr.Audio(label="Assistant Voice", interactive=False, autoplay=True,visible=False)
    state = gr.State({"index": -1, "history": []})
    with gr.Row():
        #text_input = gr.Textbox(label="Message",placeholder="Ketik disini atau rekam suara",lines=2)
        user_answer = gr.Radio(["Tidak Pernah","Kadang-Kadang","Lumayan Sering","Sering Sekali"], label="Seberapa sering anda merasakan ini ??")
        start_btn = gr.Button("Mulai")
    with gr.Row():
        send_btn = gr.Button("Kirim")
        reset_btn = gr.Button("Reset")
        #record_input = gr.Audio(sources="microphone", type="filepath",label=" Rekam suara")
        #transcribe_btn = gr.Button("Transkripsi")

    def chat_wrapper(user_msg, state):
        return chatbot(user_msg, state)

    #text_input.submit(chat_wrapper, inputs=[text_input, state], outputs=[response_box, state])
    def start(state):
        question = dass_questions[state["index"]]["text"]
        audio = generate_tts(question) 
        return question,audio,{"index":0,"history":[]}
    # Automatically trigger the intro message on load
    def trigger_intro():
        intro_response = f"{intro_message}\n\n"
        tts_path = generate_tts(intro_response)
        return intro_response ,tts_path, {"index": 0, "history": []}

    app.load(trigger_intro, inputs=None, outputs=[response_box,audio_output, state])
    #transcribe_btn.click(fn=transcribe,inputs=record_input,outputs=[text_input])
    start_btn.click(fn=start,inputs=state,outputs=[response_box,audio_output,state])
    send_btn.click(fn=chat_wrapper,inputs=[user_answer, state],outputs=[response_box,audio_output, state])
    
app.launch(share=True)


