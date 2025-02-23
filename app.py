import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks import StreamlitCallbackHandler

# 📌 Debug: Check if API key is present
if "GROQ_API_KEY" not in st.secrets:
    st.error("🚨 Error: GROQ_API_KEY is missing in Streamlit Secrets! Please add it in the secrets manager.")
    st.stop()  # Stop execution if API key is missing

api_key = st.secrets["GROQ_API_KEY"]

# 📌 Title & Description
st.title("🔎 LangChain - Chat with Search")
st.write("Interact with an AI chatbot that can search the web using Arxiv, Wikipedia, and DuckDuckGo.")

# 📌 Initialize Search Tools (with error handling)
try:
    arxiv = ArxivQueryRun(api_wrapper=ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=200))
    wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=200))
    search = DuckDuckGoSearchRun(name="Search")  # DuckDuckGo can fail, so we check below
except Exception as e:
    st.error(f"🚨 Error initializing tools: {e}")
    search = None  # Disable search if it fails

# 📌 Debug: Print available tools
st.sidebar.write("✅ Available Tools:")
st.sidebar.write("- Arxiv Search")
st.sidebar.write("- Wikipedia Search")
if search:
    st.sidebar.write("- DuckDuckGo Search")
else:
    st.sidebar.write("⚠️ DuckDuckGo Search **FAILED**")

# 📌 Initialize Chat Session
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi, I'm a chatbot that can search the web. How can I help you?"}
    ]

# 📌 Display Chat History
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 📌 User Input
if prompt := st.chat_input(placeholder="Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # 📌 Initialize LLM with Debugging
    try:
        llm = ChatGroq(groq_api_key=api_key, model_name="Llama3-8b-8192", streaming=True)
    except Exception as e:
        st.error(f"🚨 Error initializing LLM: {e}")
        st.stop()

    # 📌 Setup Tools (Exclude search if it failed)
    tools = [arxiv, wiki]
    if search:
        tools.append(search)

    # 📌 Debug: Print active tools
    st.sidebar.write("🛠 Tools Used by Agent:", [tool.name for tool in tools])

    try:
        search_agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            handle_parsing_errors=True
        )
    except Exception as e:
        st.error(f"🚨 Error initializing LangChain Agent: {e}")
        st.stop()

    # 📌 Get Response (Handle errors safely)
    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        try:
            response = search_agent.run(st.session_state.messages, callbacks=[st_cb])
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.write(response)
        except Exception as e:
            st.error(f"🚨 Error running the agent: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Sorry, an error occurred: {e}"})
            st.write(f"⚠️ Sorry, an error occurred: {e}")
