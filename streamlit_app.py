import streamlit as st
# from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col
import requests

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("**Choose the fruits you want in your Custom Smoothie!** ")

name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Display the Fruit Options List in Your Streamlit in Snowflake (SiS) App. 
cnx = st.connection("snowflake")
session = cnx.session()

my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'),col('SEARCH_ON'))

# Convert the Snowpark Dataframe to a Pandas DataFrame
pd_df = my_dataframe.to_pandas()
st.dataframe(pd_df)

ingredients_list = st.multiselect('Choose up to 5 ingredients:', my_dataframe['FRUIT_NAME'], max_selections=5)

if ingredients_list:
    ingredients_string = ""

    for fruits_chosen in ingredients_list:
        ingredients_string += fruits_chosen + " "

        # Get the search term from the dataframe based on the selected fruit
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruits_chosen, 'SEARCH_ON'].iloc[0]
        
        st.subheader(f'{fruits_chosen} Nutrition Information')

        # Fetch nutrition info from the external API
        try:
            smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
            smoothiefroot_response.raise_for_status()  # Raises an exception for non-2xx responses
            st.json(smoothiefroot_response.json())
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching data for {fruits_chosen}: {e}")

    # Build SQL Insert Statement
    my_insert_stmt = f""" 
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES ('{ingredients_string.strip()}', '{name_on_order}')
    """

    # Button to submit the order
    time_to_insert = st.button("Submit Order")
    
    if time_to_insert:
        try:
            session.sql(my_insert_stmt).collect()
            st.success(f'✅ Your Smoothie is ordered, {name_on_order}!')
        except Exception as e:
            st.error(f"Error placing your order: {e}")
