import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt

# Import Flask and jsonify
from flask import Flask, jsonify


#******************************
# Database Setup
#******************************
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station


#******************************
# Flask Setup
#******************************
# Create an app
app = Flask(__name__)

# Calculate the date 1 year ago from the last data point in the database
year_ago = dt.date(2017, 8, 23) - dt.timedelta(days=365)

#******************************
# Flask Routes
#******************************

@app.route("/")
def home():
    """List all available api routes."""
    return (
      f"Available Routes:<br/>"
      f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation<a/><br/>"
      f"<a href='/api/v1.0/stations'>/api/v1.0/stations<a/><br/>"
      f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs<a/><br/><br/>"
      f"For the next two routes please enter start or start/end dates of the trip<br/>"
      f"/api/v1.0/&ltstart&gt<br/>"
      f"/api/v1.0/&ltstart&gt/&ltend&gt<br/><br/>"
      f"Note: The dates should be between 2010-01-01 and 2017-08-23"
    )

# Define static routes
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create session from Python to the DB
    session = Session(engine)
    
    # Query the precipitation data for the last year
    prec_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= year_ago).order_by(Measurement.date).all() 
    
    session.close()

    #Convert the query results to a dictionary using date as the key and prcp as the value.
    prec_data_list = []
    for date, prcp in prec_data:
      prec_dict = {}
      prec_dict[date] = prcp
      prec_data_list.append(prec_dict)

    #Return the JSON representation of the dictionary
    return jsonify(prec_data_list)


@app.route("/api/v1.0/stations")
def stations():
    # Create session from Python to the DB
    session = Session(engine)

    # Query all stations
    results = session.query(Measurement.station).distinct().all()

    session.close()

    # Convert into normal list
    all_stations = list(np.ravel(results))
    
    #Return a JSON list of stations from the dataset.
    return jsonify(all_stations)
                                         

@app.route("/api/v1.0/tobs")
def tobs():
    # Create session from Python to the DB
    session = Session(engine)
    
    #Query the dates and temperature observations of the most active station for the last year of data.
    # the most active station counting by TOBS
    most_active_tobs = session.query(Measurement.station, func.count(Measurement.tobs)) \
                            .group_by(Measurement.station) \
                            .order_by(func.count(Measurement.tobs).desc()).first()[0]
    
    # TOBS data for the last year
    tobs_data = session.query(Measurement.date, Measurement.tobs).filter((Measurement.station == most_active_tobs),(Measurement.date >= year_ago)).all()

    session.close()
    
    # Convert the query results to a dictionary
    all_tobs_list=[]
    for date, tobs in tobs_data:  
      all_tobs_dict = {}
      all_tobs_dict["date"] = date
      all_tobs_dict["tobs"] = tobs
      all_tobs_list.append(all_tobs_dict)

    # Return a JSON list of TOBS for the most active station (USC00519281) for the previous year.
    return jsonify(all_tobs_list)


# Define dynamic routes 
@app.route("/api/v1.0/<start>")
def start_date_temp(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.
    temp_result = session.query(func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs)) \
                        .filter(Measurement.date >= start).all() 

    session.close()

    # Convert list of tuples into normal list
    temp_result_list = list(np.ravel(temp_result))

    #Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start date.
    return jsonify({"min temp": temp_result_list[0] 
                    ,"avg temp": temp_result_list[1]
                    ,"max temp": temp_result_list[2]})
   

@app.route("/api/v1.0/<start>/<end>")
def start_end_temp(start, end):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive.
    calc_temp_result = session.query(func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs)) \
                            .filter((Measurement.date >= start),(Measurement.date <= end)).all()
    
    session.close()
    
    # Convert list of tuples into normal list
    calc_temp_list = list(np.ravel(calc_temp_result))

    # Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
    return jsonify({"min temp": calc_temp_list[0] 
                    ,"avg temp": calc_temp_list[1]
                    ,"max temp": calc_temp_list[2]})
  

# Define main behavior
if __name__ == "__main__":
    app.run(debug=True)

