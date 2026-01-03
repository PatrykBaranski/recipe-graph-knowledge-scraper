import streamlit as st
import os
import tempfile
from dotenv import load_dotenv

st.set_page_config(page_title="Asystent kulinarny", layout="wide")

load_dotenv()

try:
    from recipe_data.recipe_data.fridge.fridge import Fridge
    from recipe_data.recipe_data.shopping_list.shopping_list import ShoppingList
    from recipe_data.recipe_data.tools.chatbot_with_tools import FridgeChatbot
    from recipe_data.recipe_data.reader.photo_reader import PhotoReader
except ImportError as e:
    st.error(f"Something went wrong with importing data")
    st.stop()


if 'fridge' not in st.session_state:
    st.session_state.fridge = Fridge()

if 'shopping_list' not in st.session_state:
    st.session_state.shopping_list = ShoppingList()

if 'chatbot' not in st.session_state:
    st.session_state.chatbot = FridgeChatbot()

if 'photo_reader' not in st.session_state:
    st.session_state.photo_reader = PhotoReader()

def main():
    page = st.sidebar.radio("", ["Chatbot", "Lodówka", "Lista Zakupów"])

    st.sidebar.divider()
    st.sidebar.title("Ustawienia Chatbota")
    use_neo4j = st.sidebar.checkbox("Użyj bazy Neo4j")
    rag_type = "Graph RAG"
    if use_neo4j:
        rag_type = st.sidebar.radio("Typ RAG", ["Graph RAG", "RAG"])

    if 'neo4j_settings' not in st.session_state:
        st.session_state.neo4j_settings = {'use_neo4j': False, 'rag_type': 'Graph RAG'}
    
    if st.session_state.neo4j_settings['use_neo4j'] != use_neo4j or \
       st.session_state.neo4j_settings['rag_type'] != rag_type:
           
        st.session_state.neo4j_settings['use_neo4j'] = use_neo4j
        st.session_state.neo4j_settings['rag_type'] = rag_type
        
        with st.spinner("Aktualizowanie narzędzi chatbota..."):
            st.session_state.chatbot.update_tools(use_neo4j=use_neo4j, rag_type=rag_type)
        st.success("Zaktualizowano narzędzia!")

    if page == "Chatbot":
        render_chatbot()
    elif page == "Lodówka":
        render_list_view("Lodówka", st.session_state.fridge)
    elif page == "Lista Zakupów":
        render_list_view("Lista Zakupów", st.session_state.shopping_list)

def render_chatbot():
    st.title("Asystent Kulinarny")
    
    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("Wyczyść historię"):
            st.session_state.messages = []
            st.session_state.chatbot.clear_history()
            st.rerun()

        st.subheader("Lodówka")
        fridge_content = st.session_state.fridge.load_content()
        if not fridge_content:
            st.info("Pusta")
        else:
            for item in fridge_content:
                unit = item.get('unit', '')
                st.text(f"- {item.get('ingredient', 'Unknown')}: {item.get('quantity', '')} {unit}")
        
        st.divider()
        
        st.subheader("Lista Zakupów")
        shopping_list_content = st.session_state.shopping_list.load_content()
        if not shopping_list_content:
            st.info("Pusta")
        else:
            for item in shopping_list_content:
                unit = item.get('unit', '')
                st.text(f"- {item.get('ingredient', 'Unknown')}: {item.get('quantity', '')} {unit}")
    
    with col1:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            with st.chat_message("assistant"):
                with st.spinner("Myślę..."):
                    try:
                        response = st.session_state.chatbot.chat(st.session_state.messages[-1]["content"])
                        print(response)
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        st.error(f"Wystąpił błąd podczas komunikacji z chatbotem: {e}")

        if prompt := st.chat_input("W czym mogę pomóc?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

def render_list_view(title, list_obj):
    st.title(title)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Zawartość")
        list_obj.content = list_obj.load_content()
        
        if not list_obj.content:
            st.info("Lista jest pusta.")
        else:
            for i, item in enumerate(list_obj.content):
                name = item.get('ingredient', 'Nieznany')
                quantity = item.get('quantity', '')
                unit = item.get('unit', '')
                category = item.get('category', '')
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{name}**")
                    if category:
                        c1.caption(f"Kategoria: {category}")
                    c2.write(f"Ilość: {quantity} {unit}")
                    if c3.button("Usuń", key=f"remove_{title}_{i}_{name}"):
                        list_obj.remove_from_content(item)
                        st.rerun()

    with col2:
        st.subheader("Dodaj produkt")
        
        with st.form(f"add_form_{title}"):
            new_item_name = st.text_input("Nazwa produktu")
            c_qty, c_unit = st.columns([1, 1])
            with c_qty:
                new_item_qty = st.number_input("Ilość", min_value=1, value=1)
            with c_unit:
                new_item_unit = st.selectbox("Jednostka", ["szt", "kg", "g", "l", "ml", "opak."], index=0)
            new_item_cat = st.text_input("Kategoria (opcjonalnie)")
            
            submitted = st.form_submit_button("Dodaj")
            if submitted and new_item_name:
                item_to_add = {
                    "ingredient": new_item_name,
                    "quantity": new_item_qty,
                    "unit": new_item_unit,
                    "category": new_item_cat if new_item_cat else "Inne"
                }
                list_obj.add_to_content(item_to_add)
                st.success(f"Dodano {new_item_name}")
                st.rerun()

        st.divider()
        st.subheader("Dodawanie ze zdjęcia")
        uploaded_file = st.file_uploader("Wybierz zdjęcie listy", type=['jpg', 'jpeg', 'png'], key=f"uploader_{title}")
        
        if uploaded_file is not None:
            if st.button("Przetwórz zdjęcie", key=f"process_{title}"):
                with st.spinner("Analizowanie zdjęcia..."):
                    try:
           
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
             
                        items = st.session_state.photo_reader.get_list_from_photo_path(tmp_path)
                        
          
                        os.unlink(tmp_path)
                        
                        if isinstance(items, list):
                            for item in items:
                                list_obj.add_to_content(item)
                            st.success(f"Dodano {len(items)} produktów ze zdjęcia!")
                            st.rerun()
                        elif isinstance(items, dict):
                             if 'ingredients' in items:
                                 for item in items['ingredients']:
                                     list_obj.add_to_content(item)
                                 st.success(f"Dodano {len(items['ingredients'])} produktów ze zdjęcia!")
                                 st.rerun()
                             else:
                                 list_obj.add_to_content(items)
                                 st.success("Dodano produkt ze zdjęcia!")
                                 st.rerun()
                        else:
                            st.error(f"Nieoczekiwany format danych: {type(items)}")
                            
                    except Exception as e:
                        st.error(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    main()
