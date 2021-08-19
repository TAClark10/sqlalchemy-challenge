# Import dependencies
from flask import Flask, request, redirect, jsonify
import numpy as np 
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import re
import datetime as dt

# SET UP FLASK APP
app = Flask(__name__)


# SET UP DATABASE & DB REFERENCES
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station


# CREATE FLASK ROUTES
################################################################
@app.route("/")
# Home page.
# Lists all routes that are available...
def home():
    homepageHTML = (
        f"<h1>Welcome to the Hawaii Climate Analysis API!</h1>"
        f"<h2>Available API Endpoints:</h2><br/>"

        f"<h3>🌧 PRECIPITATION:</h3>"
        f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a><br/><br/><br/><br/>"

        f"<h3>📡 STATIONS:</h3>"
        f"<a href='/api/v1.0/stations'>/api/v1.0/stations</a><br/><br/><br/><br/>"
        
        f"<h3>🌡 TEMPERATURE OBSERVATIONS:</h3>"
        f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs</a><br/><br/><br/><br/>"

        f"<h3>📆 SPECIFIED START DATE:</h3>"
        f"/api/v1.0/temp/MM-DD-YYYY<br/><br/><br/><br/>"

        f"<h3>📆 SPECIFIED START DATE & END DATE:</h3>"
        f"/api/v1.0/temp/MM-DD-YYYY/MM-DD-YYYY"
    )
    return homepageHTML


################################################################
@app.route("/api/v1.0/precipitation") 
# Convert the query results to a dictionary using `date` as the key and `prcp` as the value.
# Return the JSON representation of your dictionary.
def precipitation():
    # Connect to database
    session = Session(engine)

    # Query Measurement
    results = (session.query(Measurement.date, Measurement.tobs)
                      .order_by(Measurement.date))
    
    # Create a dictionary
    precipitation_date_tobs = []
    for each_row in results:
        dt_dict = {}
        dt_dict["date"] = each_row.date
        dt_dict["tobs"] = each_row.tobs
        precipitation_date_tobs.append(dt_dict)


    # Disconnect from database
    session.close()
    return jsonify(precipitation_date_tobs)


################################################################
@app.route("/api/v1.0/stations")
# Return a JSON list of stations from the dataset.
def stations():
    # Connect to database
    session = Session(engine)

    # Query Stations
    results = session.query(Station.name).all()

    # Convert list of tuples into normal list
    station_details = list(np.ravel(results))

    return jsonify(station_details)


    # Disconnect from database
    session.close()
    return jsonify(stations_list)


################################################################
@app.route("/api/v1.0/tobs")
# Query the dates and temperature observations of the most active station for the last year of data.
# Return a JSON list of temperature observations (TOBS) for the previous year.
def tobs():
    # Connect to database
    session = Session(engine)

     # Query Measurements for latest date and calculate query_start_date
    latest_date = (session.query(Measurement.date)
                          .order_by(Measurement.date
                          .desc())
                          .first())
    
    latest_date_str = str(latest_date)
    latest_date_str = re.sub("'|,", "",latest_date_str)
    latest_date_obj = dt.datetime.strptime(latest_date_str, '(%Y-%m-%d)')
    query_start_date = dt.date(latest_date_obj.year, latest_date_obj.month, latest_date_obj.day) - dt.timedelta(days=366)
     
    # Query station names and their observation counts sorted descending and select most active station
    q_station_list = (session.query(Measurement.station, func.count(Measurement.station))
                             .group_by(Measurement.station)
                             .order_by(func.count(Measurement.station).desc())
                             .all())
    
    station_hno = q_station_list[0][0]
    print(station_hno)


    # Return a list of tobs for the year before the final date
    results = (session.query(Measurement.station, Measurement.date, Measurement.tobs)
                      .filter(Measurement.date >= query_start_date)
                      .filter(Measurement.station == station_hno)
                      .all())

    # Create JSON results
    tobs_list = []
    for result in results:
        line = {}
        line["Date"] = result[1]
        line["Station"] = result[0]
        line["Temperature"] = int(result[2])
        tobs_list.append(line)

    return jsonify(tobs_list)

    # Disconnect from database
    session.close()
    return jsonify(tobs_data)


################################################################
@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
# Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
# When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date.
# When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` for dates between the start and end date inclusive.
def start_and_end(start='MM-DD-YYYY', end='MM-DD-YYYY'):
    
    # Connect to database
    session = Session(engine)

     # Date Range (only for help to user in case date gets entered wrong)
    date_range_max = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    date_range_max_str = str(date_range_max)
    date_range_max_str = re.sub("'|,", "",date_range_max_str)
    print (date_range_max_str)

    date_range_min = session.query(Measurement.date).first()
    date_range_min_str = str(date_range_min)
    date_range_min_str = re.sub("'|,", "",date_range_min_str)
    print (date_range_min_str)


    # Check for valid entry of start date
    valid_entry = session.query(exists().where(Measurement.date == start)).scalar()
 
    if valid_entry:

    	results = (session.query(func.min(Measurement.tobs)
    				 ,func.avg(Measurement.tobs)
    				 ,func.max(Measurement.tobs))
    				 	  .filter(Measurement.date >= start).all())

    	tmin =results[0][0]
    	tavg ='{0:.4}'.format(results[0][1])
    	tmax =results[0][2]
    
    	result_printout =( ['Entered Start Date: ' + start,
    						'The lowest Temperature was: '  + str(tmin) + ' F',
    						'The average Temperature was: ' + str(tavg) + ' F',
    						'The highest Temperature was: ' + str(tmax) + ' F'])
    	return jsonify(result_printout)

    return jsonify({"error": f"Input Date {start} not valid. Date Range is {date_range_min_str} to {date_range_max_str}"}), 404

    # Disconnect from database
    session.close()
    return jsonify(temps_filtered_by_date)

# Run the Flask app that was created at the top of this file --> app = Flask(__name__)
################################################################
if __name__ == '__main__':
    app.run(debug=True) # set to false if deploying to a live website server (such as Google Cloud, Heroku, or AWS Elastic Beanstaulk)