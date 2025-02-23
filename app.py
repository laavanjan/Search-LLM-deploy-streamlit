import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks import StreamlitCallbackHandler

# 📌 Load API Key safely
if "GROQ_API_KEY" not in st.secrets:
    st.error("🚨 Error: GROQ_API_KEY is missing in Streamlit Secrets!")
    st.stop()  # Stop execution if API key is missing

api_key = st.secrets["GROQ_API_KEY"]

# 📌 Title & Description
st.title("🔎 LangChain - Chat with Search")
st.write("Interact with an AI chatbot that can search the web using Arxiv, Wikipedia, and DuckDuckGo.")

# 📌 Initialize Search Tools (with error handling for DuckDuckGo)
arxiv = ArxivQueryRun(api_wrapper=ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=200))
wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=200))

try:
    search = DuckDuckGoSearchRun(name="Search")
except Exception as e:
    st.warning(f"⚠️ DuckDuckGo search failed: {e}")
    search = None  # Disable search if it fails

# 📌 Initialize Chat Session
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi, I'm a chatbot that can search the web. How can I help you?"}
    ]

# 📌 Display Chat History
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 📌 User Input
if prompt := st.chat_input(placeholder="What is machine learning?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # 📌 Initialize LLM
    llm = ChatGroq(groq_api_key=api_key, model_name="Llama3-8b-8192", streaming=True)
    
    # 📌 Setup Tools (Exclude search if it failed)
    tools = [arxiv, wiki]
    if search:
        tools.append(search)

    search_agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True
    )

    # 📌 Get Response (Handle errors safely)
    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        try:
            response = search_agent.run(st.session_state.messages, callbacks=[st_cb])
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.write(response)
        except Exception as e:
            st.error(f"🚨 Error running the agent: {e}")
