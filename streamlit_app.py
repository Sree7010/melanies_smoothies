# Import python packages
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
# st.dataframe(data=my_dataframe, use_container_width=True)
# st.stop()

# Convert the Snowpark Dataframe to a Pandas Dataframe so we can use the LOC function
pd_df = my_dataframe.to_pandas()
# st.dataframe(pd_df)
# st.stop()

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:'
    , my_dataframe
    , max_selections=5
)

if ingredients_list:
    ingredients_string =""
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + " "
        
        search_on=pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        # st.write('The search value for ', fruit_chosen,' is ', search_on, '.')
        
        st.subheader(fruit_chosen + 'Nutrition Information')
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/"+ search_on)
        sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)


    # Build a SQL Insert Statement & Test It
    my_insert_stmt = """ insert into smoothies.public.orders(ingredients,name_on_order)
            values('""" + ingredients_string + """ ','"""+name_on_order+"""')"""
    

    time_to_insert = st.button("Submit Order")
    
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f'✅ Your Smoothie is ordered, {name_on_order}!')

# Section for pending orders
st.title(":cup_with_straw: Pending Smoothie Orders! :cup_with_straw:")
st.write("**Orders that need to be filled.**")

# Fetch pending orders (ORDER_FILLED == 0)
my_orders_dataframe = session.table("smoothies.public.orders").filter(col("ORDER_FILLED") == 0).collect()

# If there are pending orders, allow the user to edit them
if my_orders_dataframe:
    # Editable table for pending orders
    editable_df = st.data_editor(my_orders_dataframe)

    # Submit button to save changes after editing the orders
    submitted = st.button("Submit")
    if submitted:
        try:
            # Create original dataset and the edited dataset as Snowflake DataFrames
            og_dataset = session.table("smoothies.public.orders")
            edited_dataset = session.create_dataframe(editable_df)

            # Merge the edited data back into the original dataset
            og_dataset.merge(
                edited_dataset,
                (og_dataset["ORDER_UID"] == edited_dataset["ORDER_UID"]),
                [
                    when_matched().update({"ORDER_FILLED": edited_dataset["ORDER_FILLED"]}),
                ],
            )

            st.success("Orders updated successfully!", icon="👍")

        except Exception as e:
            st.error(f"Error occurred: {e}")

else:
    st.success("There are no pending orders right now", icon="👍")
