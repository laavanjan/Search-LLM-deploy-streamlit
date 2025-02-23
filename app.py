import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks import StreamlitCallbackHandler
import os

## Langsmith Tracking using st.secrets
os.environ["LANGCHAIN_API_KEY"] = st.secrets["general"]["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = st.secrets["general"]["LANGCHAIN_PROJECT"]

## Arxiv and Wikipedia Tools
arxiv_wrapper = ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=200)
arxiv = ArxivQueryRun(api_wrapper=arxiv_wrapper)

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=200)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper)

search = DuckDuckGoSearchRun(name="Search")

st.title("🔎 Multi-Source Search Chatbot with Groq and LangChain ")


## Groq API settings
api_key = st.secrets["general"]["GROQ_KEY"]

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi, I'm a chatbot who can search the web. How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg['content'])

if prompt := st.chat_input(placeholder="What is machine learning?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    llm = ChatGroq(groq_api_key=api_key, model_name="qwen-2.5-32b", streaming=True)
    tools = [search, arxiv, wiki]

    search_agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, handling_parsing_errors=True)

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=True)
        response = search_agent.run(st.session_state.messages, callbacks=[st_cb])
        st.session_state.messages.append({'role': 'assistant', "content": response})
        st.write(response)

st.markdown(
    """
    <style>
        /* Push content above footer */
        .main-container {
            padding-bottom: 50px; /* Prevents content from overlapping with footer */
        }

        /* Footer Styling */
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: linear-gradient(135deg, #6a82fb, #fc5c7d);
            color: white;
            text-align: center;
            padding: 12px;
            font-size: 14px;
            font-family: Arial, sans-serif;
            border-top: 2px solid #ffffff33;
            box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.3);
            z-index: 1000;
        }

        .footer b {
            color: #e0fffc;  /* Soft cyan color */
            font-size: 16px;
            transition: color 0.3s ease;
        }

        .footer b:hover {
            color: #ffdd00;  /* Bright yellow hover effect */
        }
    </style>
    
    <div class="footer">
        Developed by <b>Laavanjan</b> | © Faculty of IT B22
    </div>
    """,
    unsafe_allow_html=True
)
