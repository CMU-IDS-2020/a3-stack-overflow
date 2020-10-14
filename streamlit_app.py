import streamlit as st
import pandas as pd
import altair as alt

st.title("Let's analyze some Video Game Sales Data 🎮📊.")

data_file = "./vgsales.csv"

@st.cache  # add caching so we load the data only once
def load_data():
	# Load the penguin data from https://github.com/allisonhorst/palmerpenguins.
	df = pd.read_csv(data_file).dropna()

	trimmed_df = df.copy(deep=True)
	trimmed_df.loc[trimmed_df["Publisher"].value_counts()[trimmed_df["Publisher"]].values < 100, "Publisher"] = "Other Publisher"
	trimmed_df.loc[trimmed_df["Platform"].value_counts()[trimmed_df["Platform"]].values < 20, "Platform"] = "Other Platform"
	return df, trimmed_df

def show_dataset(df):
	st.write("## Raw data in the Pandas Data Frame")
	st.write("Dataset shape: ",df.shape)
	if st.checkbox("Show Raw Data"):
		st.write(df)	


def get_melt_year_df(df, columns):
	return df[columns+["Year"]].melt('Year').rename(columns = {'variable':'Region'}) 

def show_yearly_sale(df):

	st.write('## Yearly Sales in Different Regions')

	columns = ['NA_Sales', 'EU_Sales', 'JP_Sales', 'Other_Sales', 'Global_Sales']
	select_box = alt.binding_select(options=columns, name='Select a Region:')
	sel = alt.selection_single(fields=['Region Sale'], bind=select_box, init={'Region Sale': 'Global_Sales'})

	# line chart
	data = get_melt_year_df(df, columns)
	brush = alt.selection_single(encodings=['color'])

	st.write(alt.Chart(data).mark_line(opacity=0.75).encode(
    	x='Year:N',
    	y=alt.Y('value:Q', title='Sale (in millions)', aggregate='sum'),
    	color=alt.condition(brush, "Region:N", alt.value('lightgrey'), scale=alt.Scale(scheme='tableau20')),
	).add_selection(
		brush
	).interactive())

	# bar chart
	st.write(alt.Chart(df).transform_fold(
		columns,
		as_=['Region Sale', 'Sale']
	).transform_filter(
		sel  
	).mark_bar().encode(
			x=alt.X('Year:N'),
			y=alt.Y('Sale:Q', title='Sale (in millions)')
	).add_selection(
		sel
	).properties(
		height=500
	))


def show_game_trend_scatter(df):

	st.write('## Game Trends by Categories')

	columns = ['Global_Sales', 'NA_Sales', 'EU_Sales', 'JP_Sales', 'Other_Sales']
	select_box = alt.binding_select(options=columns, name='Select a Region:')
	sel = alt.selection_single(fields=['Select a Region:'], bind=select_box, init={'Select a Region:': 'Global_Sales'})

	colors = ['Platform', 'Genre', 'Publisher']
	select_box2 = alt.binding_select(options=colors, name='Group By:')
	sel2 = alt.selection_single(fields=['Group By:'], bind=select_box2, init={'Group By:': 'Platform'})

	brush = alt.selection_single(encodings=['color'])

	st.write(alt.Chart(df).mark_point().transform_fold(
		columns,
		as_=['Select a Region:', 'Sale']
	).transform_fold(
		colors,
		as_=['Group By:', 'Group']
	).transform_filter(
		sel  
	).transform_filter(
		sel2 
	).add_selection(
		brush
	).encode(
			x= 'Year:N',
			y= alt.Y('Sale:Q', title='Sale (in millions)', aggregate='sum', scale=alt.Scale(zero=False)),
			color=alt.condition(brush, "Group:N", alt.value('lightgrey'), scale=alt.Scale(scheme='tableau20')),
			tooltip=['Name', 'Platform', 'Genre', 'Publisher']
	).add_selection(
		sel
	).add_selection(
		sel2
	).properties(
		height=500
	).interactive())


@st.cache
def get_game_agg_df(df, regions, k):
	res = {}
	for region in regions:
		res[region] = df[["Name",region]].groupby(["Name"]).agg({region:"sum"}).sort_values(by=[region], ascending=False).iloc[:k,:].reset_index()
	return res


def show_game_region_bar(df):
	st.write('## Top 10 Popular Games in Different Regions')
	
	min_year, max_year = get_year_range(df)
	selected_year = st.slider("View Top 10 Game in Year Range:", min_year, max_year, (min_year, max_year), 1)

	df_selected = df[ (df["Year"] >= selected_year[0]) & (df["Year"] <= selected_year[1])]

	regions = ['Global_Sales', 'NA_Sales', 'EU_Sales', 'JP_Sales', 'Other_Sales']
	new_df = get_game_agg_df(df_selected, regions, 10)
	
	brush = alt.selection_single(encodings=['color'])

	for region in regions:
		st.write(alt.Chart(new_df[region]).mark_bar().encode(
			x=alt.X("Name:N", sort='-y'),
			y=alt.Y(region),
			color=alt.Color("Name:N", scale=alt.Scale(scheme='tableau20'))
		).properties(
			width=600,
			height=350
		))


@st.cache
def get_year_range(df):
	return int(df["Year"].min()), int(df["Year"].max())

def show_genre_region_bar(df):
	
	st.write('## Popular Genre in Different Regions')
	
	brush = alt.selection_single(encodings=['color'])

	min_year, max_year = get_year_range(df)
	selected_year = st.slider("View Popular Genre in Year Range", min_year, max_year, (min_year, max_year), 1)

	new_df = df[ (df["Year"] >= selected_year[0]) & (df["Year"] <= selected_year[1])]

	hist = (alt.Chart(new_df).mark_bar().encode(
		y=alt.Y(alt.repeat('row'), aggregate='sum', type='quantitative'),
	))
	st.write(alt.layer(hist.encode(
		x=alt.X("Genre:N", sort='-y'),
		color=alt.condition(brush, "Genre:N", alt.value('lightgrey'),scale=alt.Scale(scheme='tableau20'))
	)).properties(
		width=500,
		height=200
	).repeat(row=['Global_Sales', 'NA_Sales', 'EU_Sales', 'JP_Sales', 'Other_Sales'], data=new_df).add_selection(
		brush
	))

@st.cache
def get_publisher_agg_df(df, regions, k):
	res = {}
	for region in regions:
		res[region] = df[["Publisher", "Name", region]].groupby(["Publisher"]).agg({region:"sum", "Name":"count"}).sort_values(by=[region], ascending=False).iloc[:k,:].reset_index()
	return res

def show_publisher_region_bar(df):
	st.write('## Popular Publisher in Different Regions')
	
	min_year, max_year = get_year_range(df)
	selected_year = st.slider("View Popular Publisher in Year Range:", min_year, max_year, (min_year, max_year), 1)

	df_selected = df[ (df["Year"] >= selected_year[0]) & (df["Year"] <= selected_year[1])]

	regions = ['Global_Sales', 'NA_Sales', 'EU_Sales', 'JP_Sales', 'Other_Sales']
	new_df = get_publisher_agg_df(df_selected, regions, 10)
	
	brush = alt.selection_single(encodings=['color'])

	for region in regions:
		st.write(alt.Chart(new_df[region]).mark_bar().encode(
			x=alt.X("Publisher:N", sort='-y'),
			y=alt.Y(region, title=region+" (in millions)"),
			color=alt.Color("Publisher:N", scale=alt.Scale(scheme='tableau20')),
			tooltip=[alt.Tooltip(field="Name", title="Total Released Games", type="quantitative")]
		).properties(
			width=600,
			height=350
		))
	

# Intro
st.write("# Video Game Sales Dataset")
df, trimmed_df = load_data()

# Data Set
show_dataset(df)

# General Trend Plots
show_yearly_sale(df)

# Region Plots
show_game_trend_scatter(trimmed_df)
show_game_region_bar(df)
show_genre_region_bar(df)
show_publisher_region_bar(df)
