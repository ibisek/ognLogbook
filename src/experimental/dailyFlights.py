import os
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px

from dao.logbookDao import getNumStatsPerDay


if __name__ == '__main__':

    NUM_DAYS = 90

    columns = ['date', 'num_flights', 'flight_time', 'hours']
    chartDf = pd.DataFrame(columns=columns)

    today = date.today()
    for d in range(1, NUM_DAYS+1):
        dt = today - timedelta(days=d)
        numFlights, totalFlightTime = getNumStatsPerDay(forDay=dt)
        print(f"date: {dt}; day: -{d}; numFlights: {numFlights}; totalFlightTime: {totalFlightTime / 3600 :.2f} hrs")

        row = pd.DataFrame(columns=columns, index=[dt])
        row['date'] = dt
        row['num_flights'] = numFlights
        row['flight_time'] = totalFlightTime/3600   # [hrs]
        row['hours'] = f"{(totalFlightTime/3600):.1f}"
        chartDf = chartDf._append(row)

    fig = px.bar(chartDf, x="date", y="num_flights",
                 color='num_flights',   # needs to be a float value for continuous color scale
                 color_continuous_scale=px.colors.sequential.OrRd,   # https://plotly.com/python/builtin-colorscales/
                 hover_data=['date', 'num_flights', 'hours'],
                 text_auto='.2s',
                 )  # pattern_shape_sequence=[".", "x", "+"],

    fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    fig.update(layout_coloraxis_showscale=False)
    fig.update_layout(
        title=f"Flights per day over the last {NUM_DAYS} days",
        xaxis_title=None,
        yaxis_title=None,
        legend_title=None,
    )

    fig.show()

    figPath = './static/html/flightsPerDay.html'
    try:
        fig.write_html(figPath)
    except FileNotFoundError:
        print(f"[ERROR] Could not save the figure into '{figPath}' while in '{os.getcwd()}'!")

