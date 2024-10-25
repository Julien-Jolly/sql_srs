# pylint: disable = missing-module-docstring
import duckdb

import streamlit as st
import os
import logging
from datetime import date, timedelta

if "data" not in os.listdir():
    logging.error(os.listdir())
    logging.error("creating folder data")
    os.mkdir("data")

if "exercises_sql_tables.duckdb" not in os.listdir("data"):
    exec(open("init_db.py").read())

con = duckdb.connect(database="data/exercises_sql_tables.duckdb", read_only=False)


def check_users_solution(user_query: str) -> None:
    """
    check that user query is correct by
    1. checking the columns
    2. checking the values
    :param user_query: a string containing the query inserted by user
    """
    result = con.execute(user_query).df()
    st.dataframe(result)
    try:
        result = result[solution_df.columns]
        st.dataframe(result.compare(solution_df))
        if result.compare(solution_df).shape == (0, 0):
            st.write("Correct !")
            st.balloons()
    except KeyError as e:
        st.write("some columns are missing")
    n_lines_difference = result.shape[0] - solution_df.shape[0]
    if n_lines_difference != 0:
        st.write(
            f"result has a {n_lines_difference} lines different with the solution_df"
        )


def get_exercise():
    global exercise, answer, solution_df
    with st.sidebar:
        available_themes_df = con.execute(
            "SELECT DISTINCT theme FROM memory_state"
        ).df()
        theme = st.selectbox(
            "What would you like to review ?",
            available_themes_df["theme"].unique(),
            index=None,
            placeholder="Select a theme...",
        )

        if theme:
            st.write(f"You selected: {theme}")
            select_exercise_query = (
                f"SELECT * FROM memory_state WHERE theme = '{theme}'"
            )
        else:
            select_exercise_query = f"SELECT * FROM memory_state"

        exercise = (
            con.execute("SELECT * FROM memory_state").df().sort_values("last_reviewed")
        )

        st.write(exercise)
        exercise_name = exercise.iloc[0]["exercise_name"]
        with open(f"answers/{exercise_name}.sql", "r") as f:
            answer = f.read()

        solution_df = con.execute(answer).df()
        return exercise_name


exercise_name = get_exercise()

st.header("enter your code:")
query = st.text_area(label="votre code SQL ici", key="user_input")

if query:
    check_users_solution(query)


for n_days in [2, 7, 23]:
    if st.button(f"revoir dans {n_days} jours"):
        next_review = date.today() + timedelta(days=n_days)
        con.execute(
            f"UPDATE memory_state SET last_reviewed = '{next_review}' WHERE exercise_name = '{exercise_name}'"
        )
        st.rerun()

if st.button("Reset"):
    con.execute(f"UPDATE memory_state SET last_reviewed = '1970-01-01'")
    st.rerun()


tab2, tab3 = st.tabs(["Tables", "Solution"])

with tab2:
    exercise_tables = exercise.iloc[0]["tables"]
    for table in exercise_tables:
        st.write(f"table: {table}")
        df_table = con.execute(f"SELECT * FROM {table}").df()
        st.dataframe(df_table)

with tab3:
    st.text(answer)
