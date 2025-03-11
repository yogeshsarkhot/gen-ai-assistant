import streamlit as st
import requests
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# Title on the page
st.markdown(
    "<h2 style='text-align: center; color: #FFAC1C; font-family: Arial;'>Local free, secure and personalized Generative AI assistant</h2>",
    unsafe_allow_html=True,
)

template = """
You are helpful assistant and meant to give concise response.
User: {question}
Assistant: """

prompt = ChatPromptTemplate.from_template(template)

# Load the local Llama3.2 model that we pulled using ollama
model = OllamaLLM(model="llama3.2")
chain = prompt | model

# Initialize message history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! How may I help you?"}
    ]

# Display the chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Handle user input
if user_input := st.chat_input("What is the query?"):
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input, unsafe_allow_html=True)

    # Ask LLM if it can answer the question correctly due to cutoff date limitation
    cut_off_date_limitation_check_prompt = "Based on your knowledge, can you provide a yes or no answer to following question that remains accurate up to your knowledge cutoff date? If there is a reference to your knowledge cutoff in the answer to the question, then answer no. Question: "
    response = chain.invoke({"question": cut_off_date_limitation_check_prompt + user_input})

    if (response.lower().startswith("no")):
        # Create a search query for Wikipedia
        search_query = user_input

        # Execute Wikipedia search API
        def get_wikipedia_search_results(query):
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json"
            query_response = requests.get(url)
            search_results = query_response.json().get('query', {}).get('search', [])
            return search_results[:5]

        search_results = get_wikipedia_search_results(search_query)

        response = "The answer may vary based on the LLM cutoff date. Let's search Wikipedia for the latest information. Top 5 results from Wikipedia search:<br><ul>"
        # Show top 5 search results
        for i, result in enumerate(search_results[:5]):
            title = result.get('title')
            article_url = f'https://en.wikipedia.org/?curid={result.get('pageid')}'
            table_row = f"<li>**Wikipedia Article {i+1}**: [{title}](%s)</li>" % article_url
            response = response + table_row
            
        response = response + "</ul>"
        with st.chat_message("assistant"):
            st.markdown(response, unsafe_allow_html=True)
        # Add assistant response to session state
        st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        # Generate assistant response
        with st.chat_message("assistant"):
            response = chain.invoke({"question": user_input})
            st.markdown(response, unsafe_allow_html=True)
        # Add assistant response to session state
        st.session_state.messages.append({"role": "assistant", "content": response})
